#!/usr/bin/env python3
"""Live record of the FTMO funded account: source extracts -> CSVs, summary.json, static page.

Two stages, so that anyone can rerun the second from what is committed:

  extract   reads the private runtime ledger of the live system (EA state snapshots,
            fills, billed swaps, nightly reconciliation log) and writes sanitised
            extracts into ``source/``. Run by the author only; needs the raw files.
  build     reads ``source/`` and writes ``data/equity_daily.csv``, ``data/trades.csv``,
            ``summary.json`` and the static page ``docs/live/index.html``. Pure function
            of ``source/``: no network, no secrets, pandas + stdlib only.

Every number on the page is read from ``summary.json``; the page template never
computes anything.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE / "source"
DEFAULT_DATA = HERE / "data"
DEFAULT_SUMMARY = HERE / "summary.json"
DEFAULT_PAGE = HERE.parents[1] / "docs" / "live" / "index.html"

INITIAL_BALANCE = 10_000.0
DAILY_LOSS_LIMIT = 0.05        # of initial balance, from the 00:00 CE(S)T balance
MAX_LOSS_LIMIT = 0.10          # of initial balance, static floor
FTMO_PROFILE = "https://profile.ftmo.com/user/E6X6MTH381"

# EA fill reasons -> sleeve. Anything else is reported as "other".
OVERNIGHT_REASONS = {"ger40_on", "ger40_off", "rebalance", "us100_off", "backstop_open",
                     "backstop_close", "breaker_flat", "target_lock_flat"}
ORB_REASONS = {"funded_orb_entry", "funded_orb_exit", "micro_entry", "micro_stop",
               "micro_be", "micro_time"}
ENTRY_REASONS = {"ger40_on", "rebalance", "backstop_open", "funded_orb_entry", "micro_entry"}

SNAPSHOT_COLUMNS = ["date", "ts_open_paris", "phase", "balance_open", "equity_open",
                    "anchor_balance", "daily_floor", "static_floor", "ts_close_paris",
                    "balance_close", "equity_close", "close_source"]
FILL_COLUMNS = ["ts_paris", "reason", "symbol", "side", "lots", "req_price", "fill_price",
                "slip_bps", "latency_ms"]
SWAP_COLUMNS = ["date_paris", "symbol", "lots_held", "notional_usd", "swap_usd"]
POSITION_COLUMNS = ["ts_paris", "mark", "symbol", "lots", "dir", "notional_usd"]
POINT_VALUE_COLUMNS = ["date", "symbol", "usd_per_point_per_lot"]
RECONCILE_COLUMNS = ["date", "mode", "pnl_real", "pnl_model", "delta_total", "d_signal",
                     "d_cost", "d_timing", "d_micro", "residual_usd", "tol_usd",
                     "unexplained", "n_fills"]
ADJUSTMENT_COLUMNS = ["date", "amount_usd", "note"]

TS_FMT = "%Y.%m.%d %H:%M:%S"


def _symbol(raw: str) -> str:
    """Broker symbol -> instrument name (``US100.cash`` -> ``US100``)."""
    return str(raw).split(".")[0].upper()


def _sleeve(reason: str) -> str:
    if reason in OVERNIGHT_REASONS:
        return "overnight"
    if reason in ORB_REASONS:
        return "orb"
    return "other"


def _parse_ts(s: str) -> pd.Timestamp:
    return pd.Timestamp(datetime.strptime(str(s), TS_FMT))


# --------------------------------------------------------------------------- extract

def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def extract(runtime: Path, mt5_files: Path, out: Path, start: str, phase: str = "FUNDED") -> None:
    """Sanitised extracts of the live ledger, restricted to one account (``phase``).

    Dropped on purpose: order/deal/position tickets, magic numbers, MT5 comment field,
    any path column, anything that is not needed by ``build``.
    """
    out.mkdir(parents=True, exist_ok=True)
    start_ts = pd.Timestamp(start)

    snaps, positions, point_values = [], [], []
    for p in sorted((runtime / "sod").glob("state_*.json")):
        day = p.stem[len("state_"):]
        if pd.Timestamp(day) < start_ts:
            continue
        s = _read_json(p)
        if not s or s.get("phase") != phase:
            continue
        eod = _read_json(runtime / "eod" / f"eod_{day}.json")
        pre = _read_json(runtime / "eod" / f"preswap_{day}.json")
        close, close_source = None, ""
        if eod and eod.get("balance") is not None:
            close, close_source = eod, "eod_2258"
        elif pre and pre.get("balance") is not None:
            close, close_source = pre, "preswap_close"
        snaps.append(dict(
            date=day, ts_open_paris=s["ts_paris"], phase=s["phase"],
            balance_open=float(s["balance"]), equity_open=float(s["equity"]),
            anchor_balance=float(s.get("anchor_balance", s["balance"])),
            daily_floor=float(s["daily_floor"]), static_floor=float(s["static_floor"]),
            ts_close_paris=(close or {}).get("ts_paris", f"{day.replace('-', '.')} 22:58:00") if close else "",
            balance_close=float(close["balance"]) if close else "",
            equity_close=float(close["equity"]) if close else "",
            close_source=close_source))
        for mark, src in (("open", s), ("close", close or {})):
            for pos in src.get("positions", []) or []:
                positions.append(dict(
                    ts_paris=s["ts_paris"] if mark == "open" else snaps[-1]["ts_close_paris"],
                    mark=mark, symbol=_symbol(pos["symbol"]), lots=float(pos["lots"]),
                    dir=int(pos["dir"]), notional_usd=float(pos["notional_usd"])))
        for sym, spec in (s.get("symbol_specs") or {}).items():
            tv, ts = float(spec.get("tick_value", 0)), float(spec.get("tick_size", 0))
            if tv > 0 and ts > 0:
                point_values.append(dict(date=day, symbol=_symbol(sym),
                                         usd_per_point_per_lot=round(tv / ts, 6)))
    pd.DataFrame(snaps, columns=SNAPSHOT_COLUMNS).to_csv(out / "snapshots.csv", index=False)
    pd.DataFrame(positions, columns=POSITION_COLUMNS).to_csv(out / "positions.csv", index=False)
    pd.DataFrame(point_values, columns=POINT_VALUE_COLUMNS).to_csv(out / "point_values.csv", index=False)

    phase_code = {"P1": 1, "P2": 2, "FUNDED": 3}[phase]
    fills = pd.read_csv(mt5_files / "fills.csv")
    fills = fills[fills["phase"].astype(int) == phase_code].copy()
    fills = fills[fills["ts_paris"].map(_parse_ts) >= start_ts]
    fills["symbol"] = fills["symbol"].map(_symbol)
    fills[FILL_COLUMNS].to_csv(out / "fills.csv", index=False)

    swaps = pd.read_csv(mt5_files / "swaps_billed.csv")
    swaps = swaps[pd.to_datetime(swaps["date_paris"]) >= start_ts].copy()
    swaps["symbol"] = swaps["symbol"].map(_symbol)
    swaps[SWAP_COLUMNS].to_csv(out / "swaps.csv", index=False)

    rec = pd.read_csv(runtime / "reconcile_log.csv")
    rec = rec[pd.to_datetime(rec["date"]) >= start_ts].copy()
    rec["mode"] = rec["detail_path"].astype(str).map(
        lambda s: "degraded" if s == "degraded" else "full")
    rec[RECONCILE_COLUMNS].to_csv(out / "reconcile.csv", index=False)

    adj = out / "adjustments.csv"
    if not adj.exists():
        pd.DataFrame(columns=ADJUSTMENT_COLUMNS).to_csv(adj, index=False)
    print(f"extract: {len(snaps)} days, {len(fills)} fills, {len(swaps)} swap rows, "
          f"{len(rec)} reconcile rows -> {out}")


# --------------------------------------------------------------------------- build

@dataclass
class Source:
    snapshots: pd.DataFrame
    fills: pd.DataFrame
    swaps: pd.DataFrame
    positions: pd.DataFrame
    point_values: pd.DataFrame
    reconcile: pd.DataFrame
    adjustments: pd.DataFrame
    hashes: dict[str, str]


def load_source(src: Path) -> Source:
    def read(name: str, columns: list[str]) -> pd.DataFrame:
        p = src / name
        if not p.exists():
            return pd.DataFrame(columns=columns)
        df = pd.read_csv(p)
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise ValueError(f"{p}: missing columns {missing}")
        return df

    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(src.glob("*.csv"))}
    return Source(
        snapshots=read("snapshots.csv", SNAPSHOT_COLUMNS),
        fills=read("fills.csv", FILL_COLUMNS),
        swaps=read("swaps.csv", SWAP_COLUMNS),
        positions=read("positions.csv", POSITION_COLUMNS),
        point_values=read("point_values.csv", POINT_VALUE_COLUMNS),
        reconcile=read("reconcile.csv", RECONCILE_COLUMNS),
        adjustments=read("adjustments.csv", ADJUSTMENT_COLUMNS),
        hashes=hashes)


def marks_from_snapshots(snapshots: pd.DataFrame, adjustments: pd.DataFrame) -> pd.DataFrame:
    """One row per equity mark (00:00 open, 22:58 close), with the external adjustments
    removed so that the curve measures trading only."""
    rows = []
    for _, r in snapshots.iterrows():
        rows.append(dict(ts=_parse_ts(r["ts_open_paris"]), date=r["date"], mark="open",
                         balance=float(r["balance_open"]), equity=float(r["equity_open"])))
        if isinstance(r["ts_close_paris"], str) and r["ts_close_paris"] and r["equity_close"] != "":
            if not pd.isna(r["equity_close"]):
                rows.append(dict(ts=_parse_ts(r["ts_close_paris"]), date=r["date"], mark="close",
                                 balance=float(r["balance_close"]), equity=float(r["equity_close"])))
    m = pd.DataFrame(rows).sort_values("ts").reset_index(drop=True)
    adj_by_date = adjustments.groupby("date")["amount_usd"].sum() if len(adjustments) else pd.Series(dtype=float)
    cum = 0.0
    adj_col = []
    for _, r in m.iterrows():
        if r["mark"] == "open" and r["date"] in adj_by_date.index:
            cum += float(adj_by_date[r["date"]])
        adj_col.append(cum)
    m["cum_adjustment"] = adj_col
    m["equity_adj"] = m["equity"] - m["cum_adjustment"]
    return m


def daily_table(marks: pd.DataFrame, snapshots: pd.DataFrame, fills: pd.DataFrame,
                swaps: pd.DataFrame, adjustments: pd.DataFrame) -> pd.DataFrame:
    """Trading-day rows. P&L of day d = adjusted equity at the next trading day's 00:00
    mark minus the 00:00 mark of d, so the column sums exactly to the total."""
    opens = marks[marks["mark"] == "open"].set_index("date")
    days = [d for d in snapshots["date"] if pd.Timestamp(d).day_of_week < 5 and d in opens.index]
    snap = snapshots.set_index("date")
    fills_day = fills["ts_paris"].astype(str).str[:10].str.replace(".", "-", regex=False) if len(fills) else pd.Series(dtype=str)
    swaps_day = swaps.groupby("date_paris")["swap_usd"].sum() if len(swaps) else pd.Series(dtype=float)
    adj_dates = sorted(adjustments["date"].tolist()) if len(adjustments) else []

    rows = []
    cum = 0.0
    for i, d in enumerate(days):
        o = opens.loc[d]
        nxt = days[i + 1] if i + 1 < len(days) else None
        if nxt is not None:
            close_eq_adj = float(opens.loc[nxt, "equity_adj"])
            close_eq_raw = float(opens.loc[nxt, "equity"])
            window_end = opens.loc[nxt, "ts"]
            pnl = close_eq_adj - float(o["equity_adj"])
            complete = True
        else:
            later = marks[(marks["ts"] > o["ts"])]
            if len(later):
                last = later.iloc[-1]
                close_eq_adj, close_eq_raw, window_end = float(last["equity_adj"]), float(last["equity"]), last["ts"]
                pnl = close_eq_adj - float(o["equity_adj"])
            else:
                close_eq_adj, close_eq_raw, window_end, pnl = float("nan"), float("nan"), o["ts"], float("nan")
            complete = False
        window = marks[(marks["ts"] >= o["ts"]) & (marks["ts"] <= window_end)]
        min_eq_raw = float(window["equity"].min())
        adj_in_window = sum(float(adjustments.loc[adjustments["date"] == a, "amount_usd"].sum())
                            for a in adj_dates if d < a <= (nxt or "9999"))
        if not math.isnan(pnl):
            cum += pnl
        daily_floor = float(snap.loc[d, "daily_floor"])
        static_floor = float(snap.loc[d, "static_floor"])
        rows.append(dict(
            date=d, weekday=pd.Timestamp(d).day_name()[:3],
            balance_open=round(float(o["balance"]), 2), equity_open=round(float(o["equity"]), 2),
            equity_close=None if math.isnan(close_eq_raw) else round(close_eq_raw, 2),
            pnl_usd=None if math.isnan(pnl) else round(pnl, 2),
            adjustment_usd=round(adj_in_window, 2),
            cum_pnl_usd=round(cum, 2), complete=complete,
            daily_floor_usd=round(daily_floor, 2), static_floor_usd=round(static_floor, 2),
            min_mark_equity=round(min_eq_raw, 2),
            dist_daily_floor_usd=round(min_eq_raw - daily_floor, 2),
            dist_static_floor_usd=round(min_eq_raw - static_floor, 2),
            n_fills=int((fills_day == d).sum()) if len(fills) else 0,
            swaps_usd=round(float(swaps_day.get(d, 0.0)), 2)))
    df = pd.DataFrame(rows)
    curve = INITIAL_BALANCE + df["cum_pnl_usd"]
    hwm = curve.cummax().clip(lower=INITIAL_BALANCE)
    df["equity_curve"] = curve.round(2)
    df["drawdown_usd"] = (curve - hwm).round(2)
    df["drawdown_pct"] = ((curve - hwm) / INITIAL_BALANCE * 100).round(3)
    return df


def pair_trades(fills: pd.DataFrame, point_values: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Pair fills into round trips per (symbol, sleeve): entry reasons open, the others close.

    Returns the closed round trips and the fills that could not be paired: entries whose
    exit is not in the fill log (the EA logs its own orders only; a server-side stop or a
    kill-file flatten is not logged) and exits without an entry. Their P&L is in the equity
    series regardless; they are only missing from the trade statistics.
    """
    if not len(fills):
        return pd.DataFrame(), []
    f = fills.copy()
    f["ts"] = f["ts_paris"].map(_parse_ts)
    f["sleeve"] = f["reason"].map(_sleeve)
    f["sgn"] = f["side"].str.upper().map({"BUY": 1, "SELL": -1})
    f = f.sort_values("ts").reset_index(drop=True)
    pv = point_values.copy()
    pv["date"] = pd.to_datetime(pv["date"])

    def point_value(symbol: str, ts: pd.Timestamp) -> float:
        sub = pv[(pv["symbol"] == symbol) & (pv["date"] <= ts.normalize())]
        if len(sub):
            return float(sub.iloc[-1]["usd_per_point_per_lot"])
        sub = pv[pv["symbol"] == symbol]
        return float(sub.iloc[0]["usd_per_point_per_lot"]) if len(sub) else float("nan")

    def as_unmatched(symbol: str, sleeve: str, e: dict, kind: str) -> dict:
        return dict(ts=e["ts"].strftime("%Y-%m-%d %H:%M:%S"), kind=kind, symbol=symbol, sleeve=sleeve,
                    side="long" if e["sgn"] > 0 else "short", lots=round(e["lots"], 2),
                    price=e["price"], reason=e["reason"])

    trades, unmatched = [], []
    books: dict[tuple, list[dict]] = {}
    for _, r in f.iterrows():
        key = (r["symbol"], r["sleeve"])
        book = books.setdefault(key, [])
        lots, sgn = float(r["lots"]), int(r["sgn"])
        fill = dict(ts=r["ts"], price=float(r["fill_price"]), lots=lots, sgn=sgn,
                    reason=r["reason"], slip=float(r["slip_bps"]))
        if r["reason"] in ENTRY_REASONS:
            # an entry while the previous entry of the same sleeve is still open on an
            # earlier day: that exit was not logged (the EA logs its own orders only)
            stale = [e for e in book if e["ts"].normalize() < r["ts"].normalize()]
            for e in stale:
                unmatched.append(as_unmatched(r["symbol"], r["sleeve"], e, "entry_without_exit"))
                book.remove(e)
            book.append(fill)
            continue
        # exit: close against the open entries, oldest first
        while lots > 1e-9 and book:
            e = book[0]
            if e["sgn"] == sgn:
                break
            q = min(lots, e["lots"])
            pts = (fill["price"] - e["price"]) * e["sgn"]
            pvv = point_value(r["symbol"], r["ts"])
            trades.append(dict(
                entry_ts=e["ts"].strftime("%Y-%m-%d %H:%M:%S"),
                exit_ts=r["ts"].strftime("%Y-%m-%d %H:%M:%S"),
                symbol=r["symbol"], sleeve=r["sleeve"], side="long" if e["sgn"] > 0 else "short",
                lots=round(q, 2), entry_price=e["price"], exit_price=fill["price"],
                points=round(pts, 2), usd_per_point_per_lot=pvv,
                pnl_usd=round(pts * q * pvv, 2),
                notional_usd=round(e["price"] * q * pvv, 2),
                holding_hours=round((r["ts"] - e["ts"]).total_seconds() / 3600, 2),
                entry_reason=e["reason"], exit_reason=r["reason"],
                entry_slip_bps=e["slip"], exit_slip_bps=fill["slip"]))
            e["lots"] -= q
            lots -= q
            if e["lots"] <= 1e-9:
                book.pop(0)
        if lots > 1e-9:
            fill["lots"] = lots
            unmatched.append(as_unmatched(r["symbol"], r["sleeve"], fill, "exit_without_entry"))
    for (symbol, sleeve), book in books.items():
        for e in book:
            unmatched.append(as_unmatched(symbol, sleeve, e, "entry_without_exit"))
    unmatched.sort(key=lambda u: u["ts"])
    cols = ["entry_ts", "exit_ts", "symbol", "sleeve", "side", "lots", "entry_price", "exit_price",
            "points", "usd_per_point_per_lot", "pnl_usd", "notional_usd", "holding_hours",
            "entry_reason", "exit_reason", "entry_slip_bps", "exit_slip_bps"]
    return pd.DataFrame(trades, columns=cols), unmatched


def _trade_stats(t: pd.DataFrame) -> dict:
    if not len(t):
        return dict(n=0, win_rate_pct=None, avg_pnl_usd=None, gross_pnl_usd=0.0,
                    median_holding_hours=None, avg_notional_usd=None, best_usd=None, worst_usd=None)
    wins = (t["pnl_usd"] > 0).sum()
    return dict(n=int(len(t)), win_rate_pct=round(100 * wins / len(t), 1),
                avg_pnl_usd=round(float(t["pnl_usd"].mean()), 2),
                gross_pnl_usd=round(float(t["pnl_usd"].sum()), 2),
                median_holding_hours=round(float(t["holding_hours"].median()), 1),
                avg_notional_usd=round(float(t["notional_usd"].mean()), 0),
                best_usd=round(float(t["pnl_usd"].max()), 2), worst_usd=round(float(t["pnl_usd"].min()), 2))


def _git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=HERE, check=True,
                              capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001 - no git, no hash
        return "n/a"


def summarise(src: Source, marks: pd.DataFrame, daily: pd.DataFrame, trades: pd.DataFrame,
              unmatched: list[dict], build_ts: datetime) -> dict:
    complete = daily[daily["complete"]].copy()
    pnl = complete["pnl_usd"].astype(float)
    n = int(len(pnl))
    mean, std = float(pnl.mean()) if n else 0.0, float(pnl.std(ddof=1)) if n > 1 else float("nan")
    first_mark, last_mark = marks.iloc[0], marks.iloc[-1]
    curve = INITIAL_BALANCE + daily["cum_pnl_usd"]
    hwm = curve.cummax().clip(lower=INITIAL_BALANCE)
    dd = curve - hwm
    i_trough = int(dd.idxmin())
    i_peak = int(curve.iloc[: i_trough + 1].idxmax())
    worst_row = complete.loc[pnl.idxmin()] if n else None
    best_row = complete.loc[pnl.idxmax()] if n else None
    active = pnl[pnl.abs() > 0.005]
    i_min_daily = int(daily["dist_daily_floor_usd"].idxmin())
    i_min_static = int(daily["dist_static_floor_usd"].idxmin())
    current_equity = float(last_mark["equity"])
    current_floor_daily = float(src.snapshots.iloc[-1]["daily_floor"])
    total_pnl = float(daily["cum_pnl_usd"].iloc[-1])

    per_symbol = {}
    symbols = sorted(set(src.positions["symbol"]) | set(trades["symbol"]) if len(trades) else set(src.positions["symbol"]))
    n_marks = int(len(marks))
    for sym in symbols:
        pos = src.positions[src.positions["symbol"] == sym]
        held_marks = pos.groupby("ts_paris")["notional_usd"].sum().abs()
        t = trades[trades["symbol"] == sym] if len(trades) else pd.DataFrame()
        sw = src.swaps[src.swaps["symbol"] == sym]
        per_symbol[sym] = dict(
            trades=_trade_stats(t),
            marks_with_position_pct=round(100 * len(held_marks) / n_marks, 1) if n_marks else None,
            avg_notional_when_held_usd=round(float(held_marks.mean()), 0) if len(held_marks) else 0.0,
            max_notional_usd=round(float(held_marks.max()), 0) if len(held_marks) else 0.0,
            avg_notional_pct_of_initial=round(100 * float(held_marks.sum()) / n_marks / INITIAL_BALANCE, 2) if n_marks else None,
            swaps_usd=round(float(sw["swap_usd"].sum()), 2), swap_nights=int(len(sw)))
    per_sleeve = {s: _trade_stats(trades[trades["sleeve"] == s]) if len(trades) else _trade_stats(pd.DataFrame())
                  for s in ("overnight", "orb", "other")}
    per_sleeve = {k: v for k, v in per_sleeve.items() if v["n"] or k != "other"}

    rec = src.reconcile
    rec_full = rec[rec["mode"] == "full"]
    reconcile = dict(
        days_logged=int(len(rec)), days_full=int(len(rec_full)),
        days_degraded=int((rec["mode"] == "degraded").sum()),
        days_unexplained=int(rec["unexplained"].fillna(0).astype(int).sum()),
        max_abs_residual_usd=round(float(rec_full["residual_usd"].abs().max()), 2) if len(rec_full) else None,
        sum_pnl_real_full_days_usd=round(float(rec_full["pnl_real"].sum()), 2) if len(rec_full) else None,
        sum_pnl_model_full_days_usd=round(float(rec_full["pnl_model"].sum()), 2) if len(rec_full) else None)

    expected_weekdays = pd.bdate_range(daily["date"].iloc[0], daily["date"].iloc[-1]).strftime("%Y-%m-%d")
    missing = sorted(set(expected_weekdays) - set(daily["date"]))

    return {
        "schema": "proof-of-edge.live_record.v1",
        "built_at_utc": build_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_commit": _git_head(),
        "source_sha256": src.hashes,
        "external_anchor": FTMO_PROFILE,
        "account": {
            "firm": "FTMO", "programme": "Swing, two-step evaluation, funded",
            "currency": "USD", "initial_balance_usd": INITIAL_BALANCE,
            "daily_loss_limit_pct": DAILY_LOSS_LIMIT * 100, "max_loss_limit_pct": MAX_LOSS_LIMIT * 100,
            "static_floor_usd": INITIAL_BALANCE * (1 - MAX_LOSS_LIMIT),
            "instruments": symbols, "timezone": "Europe/Paris (marks at 00:00 and 22:58)"},
        "period": {
            "first_mark": first_mark["ts"].strftime("%Y-%m-%d %H:%M"),
            "last_mark": last_mark["ts"].strftime("%Y-%m-%d %H:%M"),
            "first_trade": trades["entry_ts"].min() if len(trades) else None,
            "last_fill": src.fills["ts_paris"].map(_parse_ts).max().strftime("%Y-%m-%d %H:%M") if len(src.fills) else None,
            "calendar_days": int((last_mark["ts"].normalize() - first_mark["ts"].normalize()).days),
            "trading_days": int(len(daily)), "complete_trading_days": n,
            "missing_weekdays": missing, "n_marks": n_marks},
        "pnl": {
            "total_usd": round(total_pnl, 2),
            "return_pct_of_initial": round(100 * total_pnl / INITIAL_BALANCE, 3),
            "current_equity_usd": round(current_equity, 2),
            "current_balance_usd": round(float(last_mark["balance"]), 2),
            "external_adjustments_usd": round(float(src.adjustments["amount_usd"].sum()), 2) if len(src.adjustments) else 0.0,
            "adjustments": src.adjustments.to_dict(orient="records"),
            "swaps_total_usd": round(float(src.swaps["swap_usd"].sum()), 2) if len(src.swaps) else 0.0},
        "daily": {
            "n": n, "mean_usd": round(mean, 2), "std_usd": None if math.isnan(std) else round(std, 2),
            "t_stat": None if (n < 2 or std == 0 or math.isnan(std)) else round(mean / std * math.sqrt(n), 2),
            "best_usd": round(float(best_row["pnl_usd"]), 2) if n else None,
            "best_date": best_row["date"] if n else None,
            "worst_usd": round(float(worst_row["pnl_usd"]), 2) if n else None,
            "worst_date": worst_row["date"] if n else None,
            "active_days": int(len(active)),
            "positive_active_days_pct": round(100 * float((active > 0).mean()), 1) if len(active) else None,
            "worst_day_pct_of_daily_limit": round(100 * abs(float(worst_row["pnl_usd"])) / (INITIAL_BALANCE * DAILY_LOSS_LIMIT), 1) if n and worst_row["pnl_usd"] < 0 else 0.0},
        "drawdown": {
            "max_usd": round(float(dd.min()), 2),
            "max_pct_of_initial": round(100 * float(dd.min()) / INITIAL_BALANCE, 3),
            "peak_date": daily["date"].iloc[i_peak], "trough_date": daily["date"].iloc[i_trough],
            "current_usd": round(float(dd.iloc[-1]), 2),
            "basis": "trading-only equity curve (external adjustments removed), on the 00:00 Paris marks"},
        "barriers": {
            "daily_loss_floor_rule": "balance at 00:00 CE(S)T minus 5 % of the initial balance",
            "max_loss_floor_rule": "static: initial balance minus 10 %",
            "min_distance_daily_floor_usd": round(float(daily["dist_daily_floor_usd"].min()), 2),
            "min_distance_daily_floor_pct_of_initial": round(100 * float(daily["dist_daily_floor_usd"].min()) / INITIAL_BALANCE, 2),
            "min_distance_daily_floor_date": daily["date"].iloc[i_min_daily],
            "min_distance_static_floor_usd": round(float(daily["dist_static_floor_usd"].min()), 2),
            "min_distance_static_floor_date": daily["date"].iloc[i_min_static],
            "current_distance_daily_floor_usd": round(current_equity - current_floor_daily, 2),
            "current_distance_static_floor_usd": round(current_equity - INITIAL_BALANCE * (1 - MAX_LOSS_LIMIT), 2),
            "basis": "minimum over the 00:00 and 22:58 Paris marks; intraday lows are not in the export"},
        "trades": {
            "n_round_trips": int(len(trades)), "all": _trade_stats(trades),
            "by_sleeve": per_sleeve,
            "unmatched_fills": unmatched,
            "n_fills": int(len(src.fills)),
            "mean_abs_slippage_bps": round(float(src.fills["slip_bps"].abs().mean()), 2) if len(src.fills) else None,
            "basis": "FIFO pairing of the EA fill log per instrument and sleeve; gross of swaps; FTMO indices carry no commission"},
        "per_instrument": per_symbol,
        "reconciliation": reconcile,
    }


# --------------------------------------------------------------------------- page

def _fmt_usd(x, signed=False) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    s = f"{abs(x):,.2f}"
    if signed:
        return ("+" if x >= 0 else "−") + "$" + s
    return ("−" if x < 0 else "") + "$" + s


def _fmt_usd0(x, signed=False) -> str:
    """Whole dollars, for axis ticks."""
    if x is None:
        return "n/a"
    s = f"{abs(x):,.0f}"
    if signed:
        return ("+" if x >= 0 else "\u2212") + "$" + s
    return ("\u2212" if x < 0 else "") + "$" + s


def _fmt_pct(x, signed=False, nd=2) -> str:
    if x is None:
        return "n/a"
    s = f"{abs(x):.{nd}f} %"
    if signed:
        return ("+" if x >= 0 else "−") + s
    return ("−" if x < 0 else "") + s


def _nice_ticks(lo: float, hi: float, n: int = 5) -> list[float]:
    if hi <= lo:
        hi = lo + 1
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(raw))
    step = min((s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= raw), default=mag)
    start = math.floor(lo / step) * step
    ticks = []
    v = start
    while v <= hi + 1e-9:
        ticks.append(round(v, 10))
        v += step
    return ticks


def _svg_frame(width: int, height: int, pad: dict) -> dict:
    return dict(w=width, h=height, l=pad["l"], r=pad["r"], t=pad["t"], b=pad["b"],
                pw=width - pad["l"] - pad["r"], ph=height - pad["t"] - pad["b"])


def _x_scale(dates: list[str], fr: dict):
    n = len(dates)
    def sx(i: int) -> float:
        return fr["l"] + (fr["pw"] * (i / (n - 1)) if n > 1 else fr["pw"] / 2)
    return sx


def _month_ticks(dates: list[str]) -> list[tuple[int, str]]:
    ticks, seen = [], set()
    for i, d in enumerate(dates):
        key = d[:7]
        if key not in seen:
            seen.add(key)
            ticks.append((i, pd.Timestamp(d).strftime("%b %Y") if not ticks else pd.Timestamp(d).strftime("%b")))
    return ticks


def _axes(fr: dict, dates: list[str], y_ticks: list[float], sy, y_fmt) -> str:
    sx = _x_scale(dates, fr)
    out = []
    for v in y_ticks:
        y = sy(v)
        out.append(f'<line class="grid" x1="{fr["l"]}" x2="{fr["l"] + fr["pw"]}" y1="{y:.1f}" y2="{y:.1f}"/>')
        out.append(f'<text class="tick" x="{fr["l"] - 8}" y="{y + 4:.1f}" text-anchor="end">{y_fmt(v)}</text>')
    for i, label in _month_ticks(dates):
        x = sx(i)
        out.append(f'<line class="tickmark" x1="{x:.1f}" x2="{x:.1f}" y1="{fr["t"] + fr["ph"]}" y2="{fr["t"] + fr["ph"] + 5}"/>')
        out.append(f'<text class="tick" x="{x:.1f}" y="{fr["t"] + fr["ph"] + 18}" text-anchor="middle">{label}</text>')
    out.append(f'<line class="axis" x1="{fr["l"]}" x2="{fr["l"] + fr["pw"]}" y1="{fr["t"] + fr["ph"]}" y2="{fr["t"] + fr["ph"]}"/>')
    return "\n".join(out)


def svg_line(dates: list[str], values: list[float], *, title: str, y_fmt, baseline: float | None,
             tooltip, fill: bool, css_class: str, height: int = 260) -> str:
    fr = _svg_frame(760, height, dict(l=64, r=16, t=12, b=30))
    lo, hi = min(values), max(values)
    if baseline is not None:
        lo, hi = min(lo, baseline), max(hi, baseline)
    span = (hi - lo) or 1.0
    lo, hi = lo - 0.08 * span, hi + 0.08 * span
    ticks = _nice_ticks(lo, hi)
    lo, hi = min(lo, ticks[0]), max(hi, ticks[-1])
    sx = _x_scale(dates, fr)
    def sy(v: float) -> float:
        return fr["t"] + fr["ph"] * (1 - (v - lo) / (hi - lo))
    pts = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(values))
    parts = [f'<svg class="chart {css_class}" viewBox="0 0 {fr["w"]} {fr["h"]}" role="img" aria-label="{html.escape(title)}">',
             f"<title>{html.escape(title)}</title>", _axes(fr, dates, ticks, sy, y_fmt)]
    if baseline is not None:
        y0 = sy(baseline)
        parts.append(f'<line class="baseline" x1="{fr["l"]}" x2="{fr["l"] + fr["pw"]}" y1="{y0:.1f}" y2="{y0:.1f}"/>')
    if fill and baseline is not None:
        y0 = sy(baseline)
        parts.append(f'<polygon class="area" points="{sx(0):.1f},{y0:.1f} {pts} {sx(len(values) - 1):.1f},{y0:.1f}"/>')
    parts.append(f'<polyline class="line" points="{pts}"/>')
    # hover layer: one invisible column per observation, native <title> tooltip
    n = len(dates)
    half = (fr["pw"] / max(n - 1, 1)) / 2
    for i, (d, v) in enumerate(zip(dates, values)):
        x0 = max(fr["l"], sx(i) - half)
        x1 = min(fr["l"] + fr["pw"], sx(i) + half)
        parts.append(f'<g class="hit"><rect x="{x0:.1f}" y="{fr["t"]}" width="{max(x1 - x0, 1):.1f}" height="{fr["ph"]}"/>'
                     f'<circle cx="{sx(i):.1f}" cy="{sy(v):.1f}" r="4"/><title>{html.escape(tooltip(d, v))}</title></g>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_bars(dates: list[str], values: list[float], *, title: str, tooltip, height: int = 220) -> str:
    fr = _svg_frame(760, height, dict(l=64, r=16, t=12, b=30))
    lo, hi = min(0.0, min(values)), max(0.0, max(values))
    span = (hi - lo) or 1.0
    lo, hi = lo - 0.08 * span, hi + 0.08 * span
    ticks = _nice_ticks(lo, hi)
    lo, hi = min(lo, ticks[0]), max(hi, ticks[-1])
    sx = _x_scale(dates, fr)
    def sy(v: float) -> float:
        return fr["t"] + fr["ph"] * (1 - (v - lo) / (hi - lo))
    n = len(dates)
    slot = fr["pw"] / max(n, 1)
    bw = max(2.0, slot - 2)
    parts = [f'<svg class="chart bars" viewBox="0 0 {fr["w"]} {fr["h"]}" role="img" aria-label="{html.escape(title)}">',
             f"<title>{html.escape(title)}</title>", _axes(fr, dates, ticks, sy, lambda v: _fmt_usd0(v, signed=True))]
    y0 = sy(0.0)
    parts.append(f'<line class="baseline" x1="{fr["l"]}" x2="{fr["l"] + fr["pw"]}" y1="{y0:.1f}" y2="{y0:.1f}"/>')
    for i, (d, v) in enumerate(zip(dates, values)):
        x = sx(i) - bw / 2
        y1 = sy(v)
        top, h = (min(y0, y1), abs(y0 - y1))
        cls = "pos" if v > 0 else ("neg" if v < 0 else "zero")
        parts.append(f'<g class="hit"><rect class="bar {cls}" x="{x:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{max(h, 1):.1f}" rx="1"/>'
                     f'<rect class="hitbox" x="{x - 1:.1f}" y="{fr["t"]}" width="{bw + 2:.1f}" height="{fr["ph"]}"/>'
                     f'<title>{html.escape(tooltip(d, v))}</title></g>')
    parts.append("</svg>")
    return "\n".join(parts)


def render_page(s: dict, daily: pd.DataFrame, trades: pd.DataFrame) -> str:
    dates = daily["date"].tolist()
    curve = daily["equity_curve"].astype(float).tolist()
    dd = daily["drawdown_usd"].astype(float).tolist()
    complete = daily[daily["complete"]]
    bar_dates = complete["date"].tolist()
    bars = complete["pnl_usd"].astype(float).tolist()

    equity_svg = svg_line(dates, curve, title="Equity, trading only, 00:00 Paris marks",
                          y_fmt=lambda v: f"${v:,.0f}", baseline=INITIAL_BALANCE,
                          tooltip=lambda d, v: f"{d}: {_fmt_usd(v)} ({_fmt_usd(v - INITIAL_BALANCE, signed=True)})",
                          fill=False, css_class="equity")
    dd_svg = svg_line(dates, dd, title="Drawdown from high-water mark, USD",
                      y_fmt=lambda v: _fmt_usd0(v), baseline=0.0,
                      tooltip=lambda d, v: f"{d}: {_fmt_usd(v)} ({v / INITIAL_BALANCE * 100:.2f} % of initial)",
                      fill=True, css_class="drawdown", height=180)
    bars_svg = svg_bars(bar_dates, bars, title="Daily P&L, 00:00 to 00:00 Paris, USD",
                        tooltip=lambda d, v: f"{d}: {_fmt_usd(v, signed=True)}")

    p, d, dr, b, t, pe, rec = (s["pnl"], s["daily"], s["drawdown"], s["barriers"], s["trades"],
                               s["period"], s["reconciliation"])
    acc = s["account"]

    def row(label: str, value: str, note: str = "") -> str:
        n = f'<td class="note">{note}</td>' if note else "<td></td>"
        return f"<tr><th scope=\"row\">{label}</th><td class=\"num\">{value}</td>{n}</tr>"

    key_rows = "\n".join([
        row("Account", f"{acc['firm']}, {acc['programme']}, {_fmt_usd(acc['initial_balance_usd'])}"),
        row("First mark", pe["first_mark"] + " Paris", "account funded, book flat"),
        row("First trade", (pe["first_trade"] or "n/a")),
        row("Last mark", pe["last_mark"] + " Paris"),
        row("Days live", f"{pe['calendar_days']} calendar, {pe['trading_days']} trading",
            f"{pe['complete_trading_days']} complete 00:00-to-00:00 days"),
        row("P&L, trading only", _fmt_usd(p["total_usd"], signed=True), _fmt_pct(p["return_pct_of_initial"], signed=True) + " of initial"),
        row("Current equity", _fmt_usd(p["current_equity_usd"]), f"balance {_fmt_usd(p['current_balance_usd'])}"),
        row("External adjustments", _fmt_usd(p["external_adjustments_usd"], signed=True), "removed from the curve, see notes"),
        row("Swaps billed", _fmt_usd(p["swaps_total_usd"], signed=True), "included in P&L"),
        row("Max drawdown", f"{_fmt_usd(dr['max_usd'])} ({_fmt_pct(dr['max_pct_of_initial'])} of initial)",
            f"{dr['peak_date']} to {dr['trough_date']}"),
        row("Current drawdown", _fmt_usd(dr["current_usd"])),
        row("Daily P&L", f"mean {_fmt_usd(d['mean_usd'], signed=True)}, sd {_fmt_usd(d['std_usd'])}",
            f"t = {d['t_stat']}, n = {d['n']}" if d["t_stat"] is not None else f"n = {d['n']}"),
        row("Best / worst day", f"{_fmt_usd(d['best_usd'], signed=True)} / {_fmt_usd(d['worst_usd'], signed=True)}",
            f"{d['best_date']} / {d['worst_date']}"),
        row("Active days positive", _fmt_pct(d["positive_active_days_pct"], nd=1), f"{d['active_days']} days with non-zero P&L"),
        row("Round trips", str(t["n_round_trips"]),
            f"win rate {_fmt_pct(t['all']['win_rate_pct'], nd=1)}, avg {_fmt_usd(t['all']['avg_pnl_usd'], signed=True)}"),
        row("Unpaired fills", str(len(t["unmatched_fills"])), "entry or exit missing from the fill log; P&L is in the equity series"),
        row("Mean |slippage|", f"{t['mean_abs_slippage_bps']} bps", f"{t['n_fills']} fills"),
    ])

    barrier_rows = "\n".join([
        row("Daily loss floor", acc["daily_loss_limit_pct"].__str__() + " %", b["daily_loss_floor_rule"]),
        row("Closest approach, daily floor", f"{_fmt_usd(b['min_distance_daily_floor_usd'])} ({_fmt_pct(b['min_distance_daily_floor_pct_of_initial'])} of initial)",
            b["min_distance_daily_floor_date"]),
        row("Worst day vs daily limit", _fmt_pct(d["worst_day_pct_of_daily_limit"], nd=1) + " of the limit used",
            f"limit {_fmt_usd(acc['initial_balance_usd'] * acc['daily_loss_limit_pct'] / 100)}"),
        row("Max loss floor", f"{acc['max_loss_limit_pct']} %, {_fmt_usd(acc['static_floor_usd'])}", b["max_loss_floor_rule"]),
        row("Closest approach, max loss floor", _fmt_usd(b["min_distance_static_floor_usd"]), b["min_distance_static_floor_date"]),
        row("Current distances", f"daily {_fmt_usd(b['current_distance_daily_floor_usd'])}, max loss {_fmt_usd(b['current_distance_static_floor_usd'])}"),
    ])

    inst_rows = []
    for sym, v in s["per_instrument"].items():
        ts = v["trades"]
        inst_rows.append(
            f"<tr><th scope=\"row\">{html.escape(sym)}</th>"
            f"<td class=\"num\">{ts['n']}</td>"
            f"<td class=\"num\">{_fmt_pct(ts['win_rate_pct'], nd=1) if ts['n'] else 'n/a'}</td>"
            f"<td class=\"num\">{_fmt_usd(ts['avg_pnl_usd'], signed=True) if ts['n'] else 'n/a'}</td>"
            f"<td class=\"num\">{_fmt_usd(ts['gross_pnl_usd'], signed=True)}</td>"
            f"<td class=\"num\">{_fmt_usd(v['swaps_usd'], signed=True)}</td>"
            f"<td class=\"num\">{v['marks_with_position_pct']} %</td>"
            f"<td class=\"num\">{_fmt_usd(v['avg_notional_when_held_usd'])}</td>"
            f"<td class=\"num\">{_fmt_usd(v['max_notional_usd'])}</td>"
            f"<td class=\"num\">{v['avg_notional_pct_of_initial']} %</td></tr>")
    sleeve_rows = []
    for name, ts in t["by_sleeve"].items():
        label = {"overnight": "Overnight index (US100, GER40)", "orb": "Opening-range breakout (US100)", "other": "Other"}[name]
        sleeve_rows.append(
            f"<tr><th scope=\"row\">{label}</th><td class=\"num\">{ts['n']}</td>"
            f"<td class=\"num\">{_fmt_pct(ts['win_rate_pct'], nd=1) if ts['n'] else 'n/a'}</td>"
            f"<td class=\"num\">{_fmt_usd(ts['avg_pnl_usd'], signed=True) if ts['n'] else 'n/a'}</td>"
            f"<td class=\"num\">{_fmt_usd(ts['gross_pnl_usd'], signed=True)}</td>"
            f"<td class=\"num\">{ts['median_holding_hours'] if ts['n'] else 'n/a'}</td>"
            f"<td class=\"num\">{_fmt_usd(ts['best_usd'], signed=True) if ts['n'] else 'n/a'} / {_fmt_usd(ts['worst_usd'], signed=True) if ts['n'] else 'n/a'}</td></tr>")

    adj_items = "".join(f"<li>{html.escape(a['date'])}: {_fmt_usd(float(a['amount_usd']), signed=True)}. {html.escape(str(a['note']))}</li>"
                        for a in p["adjustments"]) or "<li>none</li>"
    unmatched_items = "".join(
        f"<li>{html.escape(u['ts'])} {html.escape(u['symbol'])} {u['side']} {u['lots']} lots, {html.escape(u['reason'])}: {html.escape(u['kind'].replace('_', ' '))}</li>"
        for u in t["unmatched_fills"]) or "<li>none</li>"
    missing_items = ", ".join(pe["missing_weekdays"]) or "none"
    hash_items = "".join(f"<li><code>{html.escape(k)}</code> <code class=\"hash\">{v}</code></li>" for k, v in s["source_sha256"].items())

    rec_line = (f"{rec['days_logged']} nights logged, {rec['days_full']} with a full model replay, "
                f"{rec['days_degraded']} degraded (close-freeze fallback); {rec['days_unexplained']} flagged above tolerance; "
                f"largest residual {_fmt_usd(rec['max_abs_residual_usd'])}; real {_fmt_usd(rec['sum_pnl_real_full_days_usd'], signed=True)} "
                f"vs model {_fmt_usd(rec['sum_pnl_model_full_days_usd'], signed=True)} on the replayed days.")

    css = CSS
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="noindex">
<title>Live record</title>
<meta name="description" content="Live record of the FTMO funded account behind proof-of-edge: equity, drawdown, daily P&amp;L, barriers.">
<style>{css}</style>
</head>
<body>
<main>
<header>
<p class="kicker"><a href="../../">proof-of-edge</a> / live record</p>
<h1>FTMO funded account, live record</h1>
<p class="lede">A {_fmt_usd(acc['initial_balance_usd'])} {acc['firm']} funded account ({acc['programme']}), traded by a fully
automated book: overnight index exposure on US100 and GER40, and an opening-range breakout on US100.
Marks are the broker's balance and equity as read by the Expert Advisor at 00:00 and 22:58 Paris;
the curve below is trading only, with external balance adjustments removed and listed.
External anchor: <a href="{FTMO_PROFILE}" rel="noopener">FTMO verified trader profile</a>.</p>
</header>

<section class="tiles" aria-label="Headline figures">
<div class="tile"><span class="label">P&amp;L since funding</span><span class="value">{_fmt_usd(p['total_usd'], signed=True)}</span><span class="sub">{_fmt_pct(p['return_pct_of_initial'], signed=True)} of initial</span></div>
<div class="tile"><span class="label">Max drawdown</span><span class="value">{_fmt_pct(dr['max_pct_of_initial'])}</span><span class="sub">{_fmt_usd(dr['max_usd'])}</span></div>
<div class="tile"><span class="label">Days live</span><span class="value">{pe['calendar_days']}</span><span class="sub">{pe['trading_days']} trading days</span></div>
<div class="tile"><span class="label">Closest to daily floor</span><span class="value">{_fmt_usd(b['min_distance_daily_floor_usd'])}</span><span class="sub">of a {_fmt_usd(acc['initial_balance_usd'] * acc['daily_loss_limit_pct'] / 100)} allowance</span></div>
<div class="tile"><span class="label">Round trips</span><span class="value">{t['n_round_trips']}</span><span class="sub">win rate {_fmt_pct(t['all']['win_rate_pct'], nd=1)}</span></div>
</section>

<section>
<h2>Equity</h2>
<p class="caption">Trading-only equity on the 00:00 Paris marks, USD. Dotted line: initial balance. Hover a point for the value.</p>
{equity_svg}
</section>

<section>
<h2>Drawdown</h2>
<p class="caption">Distance to the high-water mark of the same curve, USD.</p>
{dd_svg}
</section>

<section>
<h2>Daily P&amp;L</h2>
<p class="caption">00:00 to 00:00 Paris, so each bar includes that night's swaps. Friday bars run to Monday 00:00.</p>
{bars_svg}
</section>

<section>
<h2>Key figures</h2>
<div class="scroll"><table class="kv"><tbody>
{key_rows}
</tbody></table></div>
</section>

<section>
<h2>FTMO barriers</h2>
<div class="scroll"><table class="kv"><tbody>
{barrier_rows}
</tbody></table></div>
<p class="caption">Distances are measured on the 00:00 and 22:58 marks; intraday lows are not in the export, so the true closest approach can only be smaller.</p>
</section>

<section>
<h2>By instrument</h2>
<div class="scroll"><table class="wide">
<thead><tr><th>Instrument</th><th>Round trips</th><th>Win rate</th><th>Avg trade</th><th>Gross P&amp;L</th><th>Swaps</th><th>Marks with position</th><th>Avg notional when held</th><th>Max notional</th><th>Avg exposure, % of initial</th></tr></thead>
<tbody>
{''.join(inst_rows)}
</tbody></table></div>
<p class="caption">Trade P&amp;L is gross of swaps and converted at the broker's point value of the exit day. Exposure is the notional reported by the terminal at each mark.</p>
</section>

<section>
<h2>By sleeve</h2>
<div class="scroll"><table class="wide">
<thead><tr><th>Sleeve</th><th>Round trips</th><th>Win rate</th><th>Avg trade</th><th>Gross P&amp;L</th><th>Median hold, h</th><th>Best / worst</th></tr></thead>
<tbody>
{''.join(sleeve_rows)}
</tbody></table></div>
</section>

<section>
<h2>Notes on the data</h2>
<ul>
<li><strong>External balance adjustments</strong> (removed from the curve, counted outside P&amp;L): <ul>{adj_items}</ul></li>
<li><strong>Fills that could not be paired</strong> ({len(t['unmatched_fills'])}): <ul>{unmatched_items}</ul></li>
<li><strong>Missing weekdays</strong> in the mark series: {html.escape(missing_items)}.</li>
<li><strong>Nightly reconciliation</strong> (real P&amp;L against a replay of the model on the day's prices): {rec_line}</li>
</ul>
</section>

<footer>
<p>Built {s['built_at_utc']} UTC, working tree at repository commit <code>{s['source_commit']}</code> (the data files land in the commit that follows it).
Source extracts and their SHA-256:</p>
<ul class="hashes">{hash_items}</ul>
<p>Data: <a href="../../studies/live_record/data/equity_daily.csv">equity_daily.csv</a>,
<a href="../../studies/live_record/data/trades.csv">trades.csv</a>,
<a href="../../studies/live_record/summary.json">summary.json</a>.
Method and provenance: <a href="../../studies/live_record/README.md">studies/live_record/README.md</a>.
Every figure on this page is read from <code>summary.json</code>.</p>
</footer>
</main>
</body>
</html>
"""


CSS = """
:root {
  color-scheme: light;
  --surface: #fcfcfb; --surface-2: #f3f2ef; --border: #dedcd6;
  --text: #0b0b0b; --text-2: #52514e; --text-3: #7a7873;
  --line: #2a78d6; --pos: #2a78d6; --neg: #e34948; --zero: #b3b1aa; --dd: #e34948;
  --grid: #e9e8e3; --axis: #b3b1aa;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --surface: #1a1a19; --surface-2: #232322; --border: #3a3936;
    --text: #f0efec; --text-2: #c3c2b7; --text-3: #8f8d86;
    --line: #3987e5; --pos: #3987e5; --neg: #e66767; --zero: #5c5a55; --dd: #e66767;
    --grid: #2c2c2a; --axis: #5c5a55;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --surface: #1a1a19; --surface-2: #232322; --border: #3a3936;
  --text: #f0efec; --text-2: #c3c2b7; --text-3: #8f8d86;
  --line: #3987e5; --pos: #3987e5; --neg: #e66767; --zero: #5c5a55; --dd: #e66767;
  --grid: #2c2c2a; --axis: #5c5a55;
}
* { box-sizing: border-box; }
html { background: var(--surface); }
body { margin: 0; background: var(--surface); color: var(--text);
  font: 15px/1.55 ui-serif, Georgia, "Times New Roman", serif; }
main { max-width: 820px; margin: 0 auto; padding: 32px 16px 48px; overflow-wrap: anywhere; }
header { margin-bottom: 28px; }
.kicker { font: 13px/1.4 ui-monospace, Menlo, Consolas, monospace; color: var(--text-3); margin: 0 0 6px; }
.kicker a { color: inherit; }
h1 { font-size: 26px; line-height: 1.2; margin: 0 0 12px; font-weight: 600; letter-spacing: -0.01em; }
h2 { font-size: 17px; margin: 36px 0 6px; font-weight: 600; }
.lede { color: var(--text-2); margin: 0; }
a { color: var(--text); text-decoration-color: var(--axis); }
.caption { color: var(--text-2); font-size: 13.5px; margin: 0 0 10px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
.tile { border: 1px solid var(--border); border-radius: 6px; padding: 12px 14px; background: var(--surface-2); display: flex; flex-direction: column; gap: 2px; }
.tile .label { font-size: 12.5px; color: var(--text-2); }
.tile .value { font: 600 22px/1.2 ui-monospace, Menlo, Consolas, monospace; font-variant-numeric: tabular-nums; }
.tile .sub { font-size: 12.5px; color: var(--text-3); }
.chart { width: 100%; height: auto; display: block; }
.chart .grid { stroke: var(--grid); stroke-width: 1; }
.chart .axis { stroke: var(--axis); stroke-width: 1; }
.chart .tickmark { stroke: var(--axis); stroke-width: 1; }
.chart .tick { fill: var(--text-3); font: 12px ui-monospace, Menlo, Consolas, monospace; }
.chart .baseline { stroke: var(--axis); stroke-width: 1; stroke-dasharray: 3 3; }
.chart .line { fill: none; stroke: var(--line); stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
.chart.drawdown .line { stroke: var(--dd); }
.chart.drawdown .area { fill: var(--dd); fill-opacity: 0.12; }
.chart .bar.pos { fill: var(--pos); }
.chart .bar.neg { fill: var(--neg); }
.chart .bar.zero { fill: var(--zero); }
.chart .hit rect { fill: transparent; }
.chart .hit .hitbox { fill: transparent; }
.chart .hit circle { fill: var(--line); stroke: var(--surface); stroke-width: 2; opacity: 0; }
.chart.drawdown .hit circle { fill: var(--dd); }
.chart .hit:hover circle { opacity: 1; }
.chart .hit:hover .bar { filter: brightness(0.85); }
table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }
thead th { color: var(--text-2); font-weight: 500; font-size: 12.5px; }
tbody th { font-weight: 500; }
.wide tbody th { white-space: nowrap; }
td.num { font: 13.5px ui-monospace, Menlo, Consolas, monospace; font-variant-numeric: tabular-nums; white-space: nowrap; }
td.note { color: var(--text-3); font-size: 12.5px; }
.kv th { width: 30%; }
.kv td.num { width: 32%; white-space: normal; }
.scroll { overflow-x: auto; }
ul { padding-left: 20px; }
li { margin: 2px 0; }
footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--border); color: var(--text-2); font-size: 13px; }
code { font: 12.5px ui-monospace, Menlo, Consolas, monospace; }
code.hash { word-break: break-all; color: var(--text-3); }
.hashes { list-style: none; padding: 0; }
@media (max-width: 560px) { h1 { font-size: 22px; } .kv th { width: 36%; } .tile .value { font-size: 19px; } }
"""


# --------------------------------------------------------------------------- CLI

def build(source: Path, data: Path, summary_path: Path, page: Path | None,
          build_ts: datetime | None = None) -> dict:
    src = load_source(source)
    if not len(src.snapshots):
        raise SystemExit(f"no snapshots in {source}; nothing to build")
    build_ts = build_ts or datetime.now(timezone.utc)
    marks = marks_from_snapshots(src.snapshots, src.adjustments)
    daily = daily_table(marks, src.snapshots, src.fills, src.swaps, src.adjustments)
    trades, unmatched = pair_trades(src.fills, src.point_values)
    summary = summarise(src, marks, daily, trades, unmatched, build_ts)

    data.mkdir(parents=True, exist_ok=True)
    daily.to_csv(data / "equity_daily.csv", index=False)
    trades.to_csv(data / "trades.csv", index=False)
    summary_path.write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    if page is not None:
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(render_page(summary, daily, trades))
    print(f"build: {len(daily)} days, {len(trades)} round trips, P&L {summary['pnl']['total_usd']:+.2f}, "
          f"max DD {summary['drawdown']['max_usd']:.2f} -> {data}, {summary_path}" + (f", {page}" if page else ""))
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract", help="raw runtime ledger -> sanitised source/ extracts (author only)")
    e.add_argument("--runtime", type=Path, required=True, help="folder holding sod/, eod/, reconcile_log.csv")
    e.add_argument("--mt5-files", type=Path, required=True, help="folder holding fills.csv and swaps_billed.csv")
    e.add_argument("--out", type=Path, default=DEFAULT_SOURCE)
    e.add_argument("--start", default="2026-08-18", help="first 00:00 mark of the account (YYYY-MM-DD)")
    e.add_argument("--phase", default="FUNDED", choices=["P1", "P2", "FUNDED"])
    b = sub.add_parser("build", help="source/ -> data/, summary.json, page")
    b.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    b.add_argument("--data", type=Path, default=DEFAULT_DATA)
    b.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    b.add_argument("--page", type=Path, default=DEFAULT_PAGE)
    b.add_argument("--no-page", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "extract":
        extract(a.runtime, a.mt5_files, a.out, a.start, a.phase)
    else:
        build(a.source, a.data, a.summary, None if a.no_page else a.page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
