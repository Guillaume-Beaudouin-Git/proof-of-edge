"""C9 — prime Coinbase (Coinbase − Binance) → continuation BTC (PREREG gelé)."""
from __future__ import annotations

import io
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from common.stats import hac_t, sharpe, walk_forward_folds, fold_table, beta_r2, summary, breakeven_costs  # noqa: E402
from common.report import write_csv  # noqa: E402

OUT = ROOT / "c9_coinbase_premium" / "out"
OUT.mkdir(exist_ok=True)
CACHE = ROOT / "cache"
HOLDOUT_START = pd.Timestamp("2024-01-01")
ANN365 = 365
UA = {"User-Agent": "Mozilla/5.0 (research)"}
KCOLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "count", "tbv", "tbqv", "ignore"]


def binance_spot_1h(sym: str) -> pd.Series:
    out = CACHE / f"binance_spot1h_{sym}.parquet"
    if out.exists():
        df = pd.read_parquet(out)
    else:
        parts = []
        for per in pd.period_range("2017-08", pd.Timestamp.now("UTC").strftime("%Y-%m"), freq="M"):
            url = f"https://data.binance.vision/data/spot/monthly/klines/{sym}/1h/{sym}-1h-{per}.zip"
            for i in range(4):
                try:
                    r = requests.get(url, headers=UA, timeout=120)
                    if r.status_code == 404:
                        break
                    if r.status_code == 200:
                        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                            raw = z.read(z.namelist()[0])
                        hdr = 0 if raw[:20].decode("utf-8", "ignore").startswith("open_time") else None
                        d = pd.read_csv(io.BytesIO(raw), header=hdr, names=KCOLS if hdr is None else None)
                        if hdr == 0:
                            d.columns = KCOLS[: len(d.columns)]
                        ot = pd.to_numeric(d["open_time"], errors="coerce")
                        d["ts"] = pd.to_datetime(ot, unit="us" if ot.max() > 1e14 else "ms")
                        parts.append(d[["ts", "close"]])
                        break
                except Exception:  # noqa: BLE001
                    time.sleep(1 + i)
        df = pd.concat(parts).drop_duplicates("ts").sort_values("ts")
        df.to_parquet(out)
    return pd.Series(df["close"].astype(float).values, index=pd.to_datetime(df["ts"]))


def main() -> None:
    cb = {p: pd.read_parquet(CACHE / "coinbase" / f"{p}_1h.parquet") for p in ["BTC-USD", "ETH-USD"]}
    cb = {p: pd.Series(d["close"].astype(float).values, index=pd.to_datetime(d["ts"])) for p, d in cb.items()}
    bn = {"BTC-USD": binance_spot_1h("BTCUSDT"), "ETH-USD": binance_spot_1h("ETHUSDT")}
    prem = {}
    for p in cb:
        df = pd.concat([cb[p].rename("cb"), bn[p].rename("bn")], axis=1, join="inner").dropna()
        prem[p] = np.log(df["cb"] / df["bn"])
    P = pd.concat([prem["BTC-USD"].rename("btc"), prem["ETH-USD"].rename("eth")], axis=1).dropna()
    # exclusion dépeg USDT (proxy) : primes BTC et ETH simultanément > 1 % de même signe
    depeg = (P.btc.abs() > 0.01) & (P.eth.abs() > 0.01) & (np.sign(P.btc) == np.sign(P.eth))
    pr = P.btc.copy(); pr[depeg] = np.nan
    z = (pr - pr.rolling(720, min_periods=360).mean()) / pr.rolling(720, min_periods=360).std()
    px = bn["BTC-USD"].reindex(z.index)
    r1 = np.log(px).diff()  # rendement de l'heure t (close t-1 → close t)
    vol_h = r1.rolling(720, min_periods=360).std()
    w = (0.10 / (vol_h * np.sqrt(8760))).shift(1).clip(upper=10)
    print("primes :", P.index.min(), P.index.max(), "heures", len(P), "dépeg exclues", int(depeg.sum()), "| z>2 :", int((z > 2).sum()), "z<-2 :", int((z < -2).sum()))

    def run_strategy(zsig: pd.Series, h: int) -> tuple[pd.Series, pd.DataFrame]:
        """Trades non chevauchants ; signal au close t ⇒ rendement close t → close t+h."""
        idx = zsig.index
        pnl_h = pd.Series(0.0, index=idx)
        trades = []
        i = 0
        zv = zsig.values
        n = len(idx)
        while i < n - h:
            zi = zv[i]
            if np.isnan(zi) or abs(zi) <= 2:
                i += 1
                continue
            side = 1.0 if zi > 0 else -1.0
            t_in, t_out = idx[i], idx[i + h]
            if (t_out - t_in) > pd.Timedelta(hours=h + 2):  # trou de données
                i += 1
                continue
            ret = np.log(px.iloc[i + h] / px.iloc[i])
            wt = w.iloc[i] if not np.isnan(w.iloc[i]) else 0.0
            pnl_h.iloc[i + 1:i + h + 1] += side * wt * r1.iloc[i + 1:i + h + 1].values
            trades.append({"t": t_in, "side": side, "z": zi, "gross_bps": side * ret * 1e4})
            i += h
        daily = pnl_h.groupby(pnl_h.index.normalize()).sum()
        full = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
        return daily.reindex(full).fillna(0.0), pd.DataFrame(trades)

    rows, hold_rows, fold_rows, leg_rows, plc_rows, be_rows, l38_rows = [], [], [], [], [], [], []
    bh_daily = (w * r1).groupby(r1.index.normalize()).sum()
    for h in (1, 4, 24):
        daily, tr = run_strategy(z, h)
        daily = daily[daily.index >= "2017-01-01"]
        dis, dho = daily[daily.index < HOLDOUT_START], daily[daily.index >= HOLDOUT_START]
        s = summary(dis, f"h{h}"); s.update({"config": f"h{h}", "sample": "IS"}); s["sharpe"] = sharpe(dis, ANN365); rows.append(s)
        hh = summary(dho, f"h{h}"); hh.update({"config": f"h{h}", "sample": "HOLDOUT"}); hh["sharpe"] = sharpe(dho, ANN365); hold_rows.append(hh)
        ft = fold_table(dis[dis.index >= "2018-01-01"], walk_forward_folds(dis[dis.index >= "2018-01-01"].index, 5, 1.0)); ft.insert(0, "config", f"h{h}"); fold_rows.append(ft)
        tri = tr[tr.t < HOLDOUT_START] if len(tr) else tr
        for side, lab in [(1.0, "long_z>2"), (-1.0, "short_z<-2")]:
            x = tri[tri.side == side]["gross_bps"] if len(tri) else pd.Series(dtype=float)
            if len(x) > 10:
                m, t, _ = hac_t(x)
                leg_rows.append({"config": f"h{h}", "leg": lab, "n_trades": len(x), "mean_bps": m, "t_hac": t})
        if len(tri) > 10:
            yrs = (tri.t.max() - tri.t.min()).days / 365.25
            be = breakeven_costs(tri["gross_bps"].values, len(tri) / yrs); be.update({"config": f"h{h}", "trades_per_year": len(tri) / yrs}); be_rows.append(be)
        l = beta_r2(dis, bh_daily.reindex(dis.index).fillna(0.0)); l["config"] = f"h{h}"; l38_rows.append(l)
        # L26 : signal retardé d'une heure
        d1, _ = run_strategy(z.shift(1), h); d1 = d1[(d1.index >= "2017-01-01") & (d1.index < HOLDOUT_START)]
        s1 = summary(d1, f"h{h}_delay1"); s1.update({"config": f"h{h}_delay1", "sample": "IS"}); s1["sharpe"] = sharpe(d1, ANN365); rows.append(s1)
        # placebos décalés
        plcs = []
        for k in (24, 48, 72, 168, -24, -48, -72, -168):
            dk, _ = run_strategy(z.shift(k), h); dk = dk[(dk.index >= "2017-01-01") & (dk.index < HOLDOUT_START)]
            plcs.append(sharpe(dk, ANN365))
        plc_rows.append({"config": f"h{h}", "observed_sharpe_is": sharpe(dis, ANN365), "placebo_max": max(plcs), "placebo_mean": float(np.mean(plcs)), "n_above": int(sum(p >= sharpe(dis, ANN365) for p in plcs))})
        pd.DataFrame({"date": daily.index, "pnl": daily.values}).to_csv(OUT / f"daily_pnl_h{h}.csv", index=False, float_format="%.6g")
        d1_full, _ = run_strategy(z.shift(1), h)
        pd.DataFrame({"date": d1_full.index, "pnl": d1_full.values}).to_csv(OUT / f"daily_pnl_h{h}_delay1.csv", index=False, float_format="%.6g")
    write_csv(pd.DataFrame(rows).drop(columns=["label"]), OUT / "summary_is.csv"); write_csv(pd.DataFrame(hold_rows).drop(columns=["label"]), OUT / "summary_holdout.csv")
    write_csv(pd.concat(fold_rows), OUT / "folds.csv"); write_csv(pd.DataFrame(leg_rows), OUT / "legs.csv"); write_csv(pd.DataFrame(plc_rows), OUT / "placebo.csv")
    write_csv(pd.DataFrame(be_rows), OUT / "breakeven.csv"); write_csv(pd.DataFrame(l38_rows), OUT / "l38.csv")
    fmt = lambda v: f"{v:.3g}"  # noqa: E731
    cols = ["config", "sample", "n_days", "n_active_days", "sharpe", "t_hac", "mean_bps_day", "maxdd_at_10vol", "skew", "worst_day_at_10vol"]
    print("== IS ==\n" + pd.DataFrame(rows)[cols].to_string(index=False, float_format=fmt))
    print("== HOLDOUT ==\n" + pd.DataFrame(hold_rows)[cols].to_string(index=False, float_format=fmt))
    print("== plis ==\n" + pd.concat(fold_rows).to_string(index=False, float_format=fmt))
    print("== jambes ==\n" + pd.DataFrame(leg_rows).to_string(index=False, float_format=fmt))
    print("== placebos ==\n" + pd.DataFrame(plc_rows).to_string(index=False, float_format=fmt))
    print("== L38 ==\n" + pd.DataFrame(l38_rows).to_string(index=False, float_format=fmt))
    print("== point mort ==\n" + pd.DataFrame(be_rows).to_string(index=False, float_format=fmt))


if __name__ == "__main__":
    main()
