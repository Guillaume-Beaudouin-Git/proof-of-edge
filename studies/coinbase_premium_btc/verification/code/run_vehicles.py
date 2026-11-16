"""§5-§6 : véhicules (perp HL, MBT CME via IBKR, nano Coinbase via IBKR, spot long seul), corrélations (L38, Strategy A).

Usage : /usr/bin/python3 -I -B run_vehicles.py <out_dir>
Frais (sources dans NOTE.md, consultées le 2026-10-30) :
  HL perp palier 0 : taker 4,5 bps, maker 1,5 bps par côté ; fourchette mesurée 0,13 bp (5 instantanés l2Book).
  MBT (0,1 BTC) IBKR : commission 0,85 $ + frais bourse non-membre 1,15 $ + régulateur ≈ 0,02 $ par côté ; tick 0,50 $.
  Nano BIT (0,01 BTC, Coinbase Derivatives) IBKR : 0,20 $ + bourse 0,10 $ + compensation 0,09 $ + NFA 0,02 $ par côté.
  Spot Binance VIP 0 : 0,10 % par côté.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c9lib as L  # noqa: E402
from c9lib import np, pd  # noqa: E402

OUT = Path(sys.argv[1])
NT: dict[str, int] = {}
EQUITY_EUR = 12_000.0
MBT_RT_USD = 2 * (0.85 + 1.15 + 0.02) + 0.50
NANO_RT_USD = 2 * (0.20 + 0.10 + 0.09 + 0.02) + 0.05
HL_TAKER_RT = 2 * 4.5e-4 + 0.13e-4
HL_MAKER_RT = 2 * 1.5e-4
SPOT_RT = 2 * 10e-4
CME_247 = pd.Timestamp("2026-05-29 21:00")  # 16:00 CT le 29/05/2026 (CDT = UTC−5)


def count(f: str, k: int = 1) -> None:
    NT[f] = NT.get(f, 0) + k


def fred(series: str) -> pd.Series:
    p = L.RAW / "fred" / f"{series}.csv"
    if not p.exists():
        req = urllib.request.Request(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}",
                                     headers={"User-Agent": "c9-verif"})
        p.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    df = pd.read_csv(p)
    s = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    s.index = pd.to_datetime(df.iloc[:, 0])
    return s.dropna()


def hl_candles() -> pd.Series:
    p = L.RAW / "hl_candles_btc_1h.json"
    if not p.exists():
        end = int(time.time() * 1000)
        start = end - 5000 * 3600 * 1000
        body = json.dumps({"type": "candleSnapshot", "req": {"coin": "BTC", "interval": "1h",
                                                             "startTime": start, "endTime": end}}).encode()
        req = urllib.request.Request("https://api.hyperliquid.xyz/info", data=body,
                                     headers={"Content-Type": "application/json"})
        p.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    c = json.loads(p.read_text())
    s = pd.Series([float(x["c"]) for x in c], index=pd.to_datetime([x["t"] for x in c], unit="ms"))
    return s[~s.index.duplicated()].sort_index()


def funding_per_trade(pn: L.Panel, tr: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Funding payé (fraction du notionnel, signé : >0 = coût) sur la fenêtre tenue ; source par trade."""
    hl = pd.DataFrame(json.loads((L.RAW / "funding" / "hl_btc.json").read_text()))
    hl_s = pd.Series(hl["fundingRate"].astype(float).values, index=pd.to_datetime(hl["time"], unit="ms").round("min"))
    bn = pd.DataFrame(json.loads((L.RAW / "funding" / "binance_btcusdt.json").read_text()))
    bn_s = pd.Series(bn["fundingRate"].astype(float).values, index=pd.to_datetime(bn["fundingTime"], unit="ms").round("min"))
    hl_start = hl_s.index[0]
    bn_start = bn_s.index[0]
    cost, src = [], []
    for e, x, s in zip(tr["entry"], tr["exit"], tr["side"]):
        t0, t1 = e + pd.Timedelta(hours=1), x + pd.Timedelta(hours=1)  # instants de clôture
        if t0 >= hl_start:
            f = hl_s.loc[(hl_s.index > t0) & (hl_s.index <= t1)].sum()
            src.append("HL")
        elif t0 >= bn_start:
            f = bn_s.loc[(bn_s.index > t0) & (bn_s.index <= t1)].sum()
            src.append("Binance")
        else:
            f = 0.0
            src.append("aucun")
        cost.append(s * f)
    return pd.Series(cost, index=tr.index), pd.Series(src, index=tr.index)


def cme_open(ts_utc: pd.Timestamp) -> bool:
    """Globex crypto avant le 29/05/2026 : dim 17:00 CT → ven 16:00 CT, pause 16:00-17:00 CT lun-jeu."""
    if ts_utc >= CME_247:
        return True
    ct = ts_utc.tz_localize("UTC").tz_convert("America/Chicago")
    wd, hm = ct.weekday(), ct.hour + ct.minute / 60
    if wd == 5:
        return False
    if wd == 6:
        return hm >= 17
    if wd == 4:
        return hm < 16
    return not (16 <= hm < 17)


def next_open(ts: pd.Timestamp) -> pd.Timestamp:
    t = ts
    while not cme_open(t):
        t += pd.Timedelta(hours=1)
    return t


def stats_block(name: str, d: pd.Series, extra: dict | None = None) -> list[dict]:
    rows = []
    for per, dd in (("ALL", d), ("IS", d.loc[:L.IS_END.normalize()]), ("HO", d.loc["2024-01-01":L.HO_END.normalize()]),
                    ("FWD", d.loc[L.HO_END.normalize() + pd.Timedelta(days=1):])):
        if len(dd) < 5:
            continue
        s = L.summary(dd)
        s.update({"vehicle": name, "period": per})
        if extra:
            s.update(extra)
        rows.append(s)
        count("V1_vehicle_x_period")
    folds = [L.sharpe(d.loc[f"{y}-01-01":f"{y}-12-31"]) for y in range(2019, 2027)]
    for r in rows:
        r["wf_share_pos_2019_2026"] = float(np.mean([f > 0 for f in folds if np.isfinite(f)]))
    return rows


def breakeven(pn, tr, first, last, extra=None) -> dict:
    out = {}
    for per, lo, hi in (("ALL", first, last), ("HO", pd.Timestamp("2024-01-01"), L.HO_END.normalize())):
        def sr(c):
            return L.sharpe(L.daily_pnl(pn, tr, cost_rt=c, extra_cost=extra, start=first, end=last).loc[lo:hi])
        for target in (1.0, 0.0):
            a, b = 0.0, 0.02
            if sr(a) < target:
                out[f"{per}_cost_rt_bps_at_sr{target:g}"] = 0.0
                continue
            for _ in range(30):
                m = (a + b) / 2
                if sr(m) > target:
                    a = m
                else:
                    b = m
            out[f"{per}_cost_rt_bps_at_sr{target:g}"] = a * 1e4
    return out


pn = L.build_panel()
first = pn.z.first_valid_index().normalize()
last = pn.idx[-1].normalize()
tr = L.run_strategy(pn, h=24)
gross = L.daily_pnl(pn, tr, start=first, end=last)
rows: list[dict] = []
rows += stats_block("brut (Binance spot, sans coût)", gross)

# ---------- (a) perp HL ----------
fund, src = funding_per_trade(pn, tr)
tr["funding"] = fund.values
tr["funding_src"] = src.values
fsum = tr.groupby("funding_src")["funding"].agg(["count", "mean", "sum"])
fsum["mean_bps"] = fsum["mean"] * 1e4
hl_taker = L.daily_pnl(pn, tr, cost_rt=HL_TAKER_RT, extra_cost=tr["funding"], start=first, end=last)
hl_maker = L.daily_pnl(pn, tr, cost_rt=HL_MAKER_RT, extra_cost=tr["funding"], start=first, end=last)
rows += stats_block("perp HL taker + funding", hl_taker, {"cost_rt_bps": HL_TAKER_RT * 1e4})
rows += stats_block("perp HL maker + funding", hl_maker, {"cost_rt_bps": HL_MAKER_RT * 1e4})
be_hl = breakeven(pn, tr, first, last, extra=tr["funding"])
# perp HL vs spot Binance sur les ~200 derniers jours (bougies HL 1 h)
hlc = hl_candles().reindex(pn.idx)
sub = tr[(tr["entry"] >= hlc.first_valid_index()) & tr["exit"].le(hlc.last_valid_index())].copy()
sub["ret_hl"] = sub["side"] * (hlc.reindex(sub["exit"]).values / hlc.reindex(sub["entry"]).values - 1)
perp_vs_spot = {"n": len(sub), "mean_ret_spot_bps": float(sub["ret"].mean() * 1e4),
                "mean_ret_hlperp_bps": float(sub["ret_hl"].mean() * 1e4),
                "corr": float(sub[["ret", "ret_hl"]].corr().iloc[0, 1]) if len(sub) > 2 else np.nan,
                "mean_abs_diff_bps": float((sub["ret"] - sub["ret_hl"]).abs().mean() * 1e4)}
count("V1_perp_vs_spot")

# ---------- (b) MBT CME via IBKR ----------
rf = L.load_rf_daily()
fx = fred("DEXUSEU").reindex(pd.date_range("2015-01-01", last, freq="D")).ffill()
yfp = L.RAW / "yf_BTC=F.csv"
if not yfp.exists():
    import yfinance as yf
    yf.download("BTC=F", start="2017-12-01", progress=False, auto_adjust=False)["Close"].to_csv(yfp)
fut = pd.read_csv(yfp, index_col=0, parse_dates=True).iloc[:, 0].dropna()
cb = pn.cb_btc
basis_rows = []
for dte_day, F in fut.items():
    # règlement CME 15:00 CT ; on prend la clôture Coinbase de la bougie qui se termine à cet instant
    ct = pd.Timestamp(dte_day.date()).tz_localize("America/Chicago") + pd.Timedelta(hours=15)
    utc_close = ct.tz_convert("UTC").tz_localize(None) - pd.Timedelta(hours=1)
    S = cb.get(utc_close, np.nan)
    if not np.isfinite(S):
        continue
    d0 = pd.Timestamp(dte_day.date())
    lastfri = (d0 + pd.offsets.MonthEnd(0))
    while lastfri.weekday() != 4:
        lastfri -= pd.Timedelta(days=1)
    if lastfri < d0:
        nxt = d0 + pd.offsets.MonthEnd(1)
        lastfri = nxt
        while lastfri.weekday() != 4:
            lastfri -= pd.Timedelta(days=1)
    dte = max((lastfri - d0).days, 1)
    basis_rows.append({"date": d0, "F": float(F), "S": float(S), "dte": dte,
                       "basis_ann": (float(F) / float(S) - 1) * 365 / dte})
basis = pd.DataFrame(basis_rows).set_index("date")
basis = basis[basis["dte"] >= 3]
basis_y = basis["basis_ann"].groupby(basis.index.year).median()
rf_y = rf.groupby(rf.index.year).mean()
excess_basis_y = (basis_y - rf_y.reindex(basis_y.index)).rename("basis_minus_rf")
pd.DataFrame({"basis_ann_median": basis_y, "rf_mean": rf_y.reindex(basis_y.index), "basis_minus_rf": excess_basis_y,
              "n_days": basis["basis_ann"].groupby(basis.index.year).size()}).to_csv(OUT / "cme_basis_by_year.csv", float_format="%.4f")
count("V1_basis")


def basis_cost(entry: pd.Timestamp, side: int) -> float:
    y = entry.year
    b = excess_basis_y.get(y, excess_basis_y.iloc[0] if y < excess_basis_y.index[0] else excess_basis_y.iloc[-1])
    return side * b / 365.0  # coût d'un jour de tenue : le long paie la base au-delà du cash


tr["basis_cost"] = [basis_cost(e, s) for e, s in zip(tr["entry"], tr["side"])]
# Coûts en bps au prix courant (le MBT n'existe que depuis 2021-05 et le nano depuis 2022-06 : appliquer les
# frais fixes en dollars aux prix de 2017-2019 serait un anachronisme). Ancrage : dernier prix et dernier EURUSD.
P_LAST = float(pn.bn_btc.dropna().iloc[-1])
FX_LAST = float(fred("DEXUSEU").iloc[-1])
EQ_USD = EQUITY_EUR * FX_LAST
tr["mbt_cost_rt"] = MBT_RT_USD / (0.1 * P_LAST)
tr["nano_cost_rt"] = NANO_RT_USD / (0.01 * P_LAST)

# horaires : décaler l'entrée et la sortie à la prochaine heure ouverte (variante "décaler") ou sauter
sched = []
idx_pos = {t: i for i, t in enumerate(pn.idx)}
for k, r in tr.iterrows():
    t_in = r["entry"] + pd.Timedelta(hours=1)
    t_out = r["exit"] + pd.Timedelta(hours=1)
    o_in, o_out = cme_open(t_in), cme_open(t_out)
    n_in, n_out = next_open(t_in), next_open(t_out)
    sched.append({"k": k, "entry_open": o_in, "exit_open": o_out,
                  "e_shift": idx_pos.get(n_in - pd.Timedelta(hours=1), np.nan),
                  "x_shift": idx_pos.get(max(n_out, n_in + pd.Timedelta(hours=1)) - pd.Timedelta(hours=1), np.nan)})
sched = pd.DataFrame(sched).set_index("k")
tr = tr.join(sched)
pre = tr["entry"] < CME_247
closed_share = {"share_entry_closed_pre_247": float((~tr.loc[pre, "entry_open"]).mean()),
                "share_exit_closed_pre_247": float((~tr.loc[pre, "exit_open"]).mean()),
                "share_either_closed_pre_247": float((~(tr.loc[pre, "entry_open"] & tr.loc[pre, "exit_open"])).mean()),
                "n_trades_pre_247": int(pre.sum()), "n_trades_post_247": int((~pre).sum())}


def mbt_trades(mode: str) -> pd.DataFrame:
    t = tr.copy()
    if mode == "sauter":
        t = t[t["entry_open"]].copy()
        t["x"] = t["x_shift"].astype(int)
    elif mode == "decaler":
        t = t.dropna(subset=["e_shift", "x_shift"]).copy()
        t["e"] = t["e_shift"].astype(int)
        t["x"] = t["x_shift"].astype(int)
    return t


variants = {}
for mode in ("24/7 (référence)", "sauter", "decaler"):
    t = mbt_trades(mode) if mode != "24/7 (référence)" else tr.copy()
    d = L.daily_pnl(pn, t, cost_rt=0.0, extra_cost=t["mbt_cost_rt"] + t["basis_cost"], start=first, end=last)
    variants[mode] = d
    rows += stats_block(f"MBT fractionnaire, horaires {mode}", d, {"n_trades": len(t)})
gross_skip = L.daily_pnl(pn, mbt_trades("sauter"), start=first, end=last)
gross_shift = L.daily_pnl(pn, mbt_trades("decaler"), start=first, end=last)
closed_share.update({"gross_sr_all_247": L.sharpe(gross), "gross_sr_all_sauter": L.sharpe(gross_skip),
                     "gross_sr_all_decaler": L.sharpe(gross_shift),
                     "gross_pnl_lost_sauter_share": float(1 - gross_skip.sum() / gross.sum()),
                     "gross_pnl_lost_decaler_share": float(1 - gross_shift.sum() / gross.sum())})


def lot_series(t: pd.DataFrame, contract_btc: float, cost_rt: float, mode: str) -> tuple[pd.Series, dict]:
    """Lots entiers sur un compte de 12 000 €, au prix et au change courants : un lot = une fraction fixe g du compte.

    "1 lot" : exposition ±g à chaque trade ; "arrondi au lot" : round(w / g) · g (souvent zéro pour le MBT).
    """
    g = contract_btc * P_LAST / EQ_USD
    tt = t.copy()
    n = np.ones(len(tt)) if mode == "1 lot" else np.round(tt["w"].values / g)
    tt["w"] = n * g
    tt = tt[tt["w"] > 0]
    d = L.daily_pnl(pn, tt, cost_rt=0.0, extra_cost=pd.Series(cost_rt, index=tt.index) + tt["basis_cost"],
                    start=first, end=last)
    info = {"lot_fraction_of_equity": float(g), "share_trades_with_ge1_lot": float(np.mean(n >= 1)),
            "median_lots": float(np.median(n)), "max_lots": int(np.max(n))}
    return d, info


lot_info = {}
t247 = tr.copy()
for label, cb_, rt_ in (("MBT", 0.1, MBT_RT_USD / (0.1 * P_LAST)), ("Nano BIT", 0.01, NANO_RT_USD / (0.01 * P_LAST))):
    for mode in ("1 lot", "arrondi au lot"):
        d, info = lot_series(t247, cb_, rt_, mode)
        lot_info[f"{label} {mode}"] = info
        rows += stats_block(f"{label} {mode}, compte 12 k€", d, info)
    if label == "MBT":
        d, info = lot_series(mbt_trades("decaler"), cb_, rt_, "1 lot")
        lot_info["MBT 1 lot horaires decaler"] = info
        rows += stats_block("MBT 1 lot, horaires décaler, compte 12 k€", d, info)
d_nano_frac = L.daily_pnl(pn, tr, cost_rt=0.0, extra_cost=tr["nano_cost_rt"] + tr["basis_cost"], start=first, end=last)
rows += stats_block("Nano BIT fractionnaire (24/7)", d_nano_frac)

# ---------- (c) spot long seul ----------
longs = tr[tr["side"] == 1].copy()
d_spot = L.daily_pnl(pn, longs, cost_rt=SPOT_RT, start=first, end=last)
rows += stats_block("spot long seul Binance (20 bps RT)", d_spot, {"n_trades": len(longs)})
d_spot_cb = L.daily_pnl(pn, longs, px=pn.cb_btc, cost_rt=2 * 50e-4, start=first, end=last)
rows += stats_block("spot long seul Coinbase UE taker (100 bps RT)", d_spot_cb, {"n_trades": len(longs)})

veh = pd.DataFrame(rows)
cols = ["vehicle", "period", "sharpe", "t_hac", "ann_ret", "ann_vol", "maxdd", "worst_day", "skew", "days",
        "wf_share_pos_2019_2026", "n_trades", "share_trades_with_ge1_lot", "median_lots", "cost_rt_bps"]
veh[[c for c in cols if c in veh.columns]].to_csv(OUT / "vehicles.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 250)
print(veh[["vehicle", "period", "sharpe", "t_hac", "maxdd", "worst_day", "skew", "ann_vol", "wf_share_pos_2019_2026"]].to_string())

be = {"perp_HL_funding_inclus": be_hl,
      "MBT_cost_rt_bps_median": float(tr["mbt_cost_rt"].median() * 1e4),
      "MBT_cost_rt_bps_last_price": float(MBT_RT_USD / (0.1 * pn.bn_btc.dropna().iloc[-1]) * 1e4),
      "nano_cost_rt_bps_last_price": float(NANO_RT_USD / (0.01 * pn.bn_btc.dropna().iloc[-1]) * 1e4),
      "basis_cost_bps_per_trade_mean_abs": float(tr["basis_cost"].abs().mean() * 1e4),
      "basis_cost_bps_per_trade_mean_signed": float(tr["basis_cost"].mean() * 1e4),
      "funding_by_source": fsum.reset_index().to_dict(orient="records"),
      "funding_bps_per_trade_mean_signed": float(tr["funding"].mean() * 1e4),
      "funding_bps_per_trade_p95_abs": float(tr["funding"].abs().quantile(0.95) * 1e4),
      "perp_vs_spot_last_200d": perp_vs_spot, "cme_schedule": closed_share, "lots": lot_info,
      "btc_last_price": P_LAST, "eurusd_last": FX_LAST, "equity_usd": EQ_USD}
count("V1_breakeven", 4)

# ---------- §6 corrélations ----------
p = pn.bn_btc.ffill()
btc_d = p.groupby(pn.idx.normalize()).last().pct_change()
vol_d = btc_d.rolling(30).std().shift(1) * np.sqrt(365)
bh = (0.10 / vol_d).clip(upper=3) * btc_d
rfd = L.load_rf_daily().reindex(btc_d.index).fillna(0) / 365
bh_ex = (bh - (0.10 / vol_d).clip(upper=3) * rfd).loc[first:last].dropna()
import statsmodels.api as sm  # noqa: E402
y = gross.reindex(bh_ex.index)
res = sm.OLS(y.values, sm.add_constant(bh_ex.values)).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
l38 = {"beta": float(res.params[1]), "alpha_ann": float(res.params[0] * 365), "alpha_t_hac": float(res.tvalues[0]),
       "r2": float(res.rsquared), "corr": float(np.corrcoef(y.values, bh_ex.values)[0, 1])}
count("L38", 1)
closes = {}
for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
    df = L.load_binance(s, "1d")
    closes[s] = df["close"]
px_d = pd.DataFrame(closes)
lr = np.log(px_d / px_d.shift(1))
cum = lr.rolling(28).sum().shift(1)
volL = lr.rolling(28).std().shift(1)
sig = np.tanh(cum / (volL * np.sqrt(28) + 1e-8)).clip(lower=0)
w_a = sig * (0.15 / (volL * np.sqrt(365))).clip(upper=3)
ra = px_d.pct_change()
A = (w_a * ra).mean(axis=1, skipna=True)
A = A.loc[first:last].dropna()
common = A.index.intersection(gross.index)
corrA = {"corr_daily_all": float(np.corrcoef(gross.reindex(common), A.reindex(common))[0, 1]),
         "corr_daily_HO": float(gross.reindex(common).loc["2024-01-01":].corr(A.reindex(common).loc["2024-01-01":])),
         "corr_weekly": float(gross.reindex(common).resample("W").sum().corr(A.reindex(common).resample("W").sum())),
         "A_sharpe_same_window_gross_of_rf": L.sharpe(A.reindex(common)),
         "corr_on_days_c9_active": float(gross.reindex(common)[gross.reindex(common) != 0].corr(A.reindex(common)[gross.reindex(common) != 0]))}
count("A1_corr", 3)
(OUT / "vehicles_detail.json").write_text(json.dumps({"breakeven_and_costs": be, "L38": l38, "strategy_A": corrA},
                                                      indent=1, default=str))
print(json.dumps({"be": be, "L38": l38, "A": corrA}, indent=1, default=str))
tr[["signal", "entry", "side", "w", "ret", "funding", "funding_src", "basis_cost", "mbt_cost_rt", "entry_open", "exit_open"]].to_csv(
    OUT / "trades_h24_costs.csv", index=False, float_format="%.6f")
for name, d in (("perp_hl_taker", hl_taker),):
    d.rename("pnl").to_csv(OUT / f"daily_h24_{name}.csv", float_format="%.7f")
(OUT / "_nt_vehicles.json").write_text(json.dumps(NT, indent=1))

# ---------- quantiles de référence du forward (FORWARD_SPEC.md) ----------
ref = {}
for n in (91, 182):
    r = hl_taker.rolling(n).sum().dropna()
    ref[str(n)] = {"p5": r.quantile(.05), "p10": r.quantile(.10), "p50": r.median(), "p_neg": (r < 0).mean(), "min": r.min()}
    r2 = hl_taker.loc["2023-01-01":].rolling(n).sum().dropna()
    ref[f"{n}_since2023"] = {"p5": r2.quantile(.05), "p50": r2.median(), "p_neg": (r2 < 0).mean()}
ref["trades_per_91d_median"] = float(tr.set_index("signal").resample("91D").size().median())
(OUT / "forward_reference_quantiles.json").write_text(json.dumps(ref, indent=1, default=float))
