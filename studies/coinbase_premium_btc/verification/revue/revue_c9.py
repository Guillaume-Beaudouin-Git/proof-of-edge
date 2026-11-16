"""Relecture indépendante de la vérification locale de C9 (code propre, écrit sans réutiliser c9lib.py).

Usage : /usr/bin/python3 -I -B revue_c9.py <out_dir>
Données : caches publics du chercheur dans scratchpad/c9_verif/raw (Coinbase REST, Binance Vision, FRED, funding HL/Binance),
relus et re-parsés ici ; aucune fonction de code/ n'est importée.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.api as sm  # noqa: E402
from scipy.stats import norm  # noqa: E402

RAW = Path("c9_verif/raw")
DOSSIER = Path(__file__).resolve().parents[1]
CLOUD = DOSSIER.parent / "new_sleeve_search_2026-11" / "c9_coinbase_premium" / "out"
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
IS_END = pd.Timestamp("2023-12-31")
HO0, HO1 = pd.Timestamp("2024-01-01"), pd.Timestamp("2026-09-30")
FWD0 = pd.Timestamp("2026-10-01")
ANN = 365.0
NT: dict[str, int] = {}


def count(k: str, n: int = 1) -> None:
    NT[k] = NT.get(k, 0) + n


# ------------------------------------------------------------------ données
def read_vision(symbol: str) -> pd.DataFrame:
    frames = []
    for p in sorted((RAW / "binance_spot_1h" / symbol).glob("*.csv")):
        d = pd.read_csv(p, header=None, usecols=[0, 1, 4])
        if isinstance(d.iloc[0, 0], str) and not d.iloc[0, 0].lstrip("-").isdigit():
            d = d.iloc[1:]
        t = pd.to_numeric(d[0]).astype("int64")
        t = np.where(t > 10**14, t // 1000, t)  # µs → ms (fichiers 2025+)
        frames.append(pd.DataFrame({"open": pd.to_numeric(d[1]).values, "close": pd.to_numeric(d[4]).values},
                                   index=pd.to_datetime(t, unit="ms")))
    tail = RAW / "binance_tail" / f"{symbol}.json"
    if tail.exists():
        rows = json.loads(tail.read_text())
        frames.append(pd.DataFrame({"open": [float(r[1]) for r in rows], "close": [float(r[4]) for r in rows]},
                                   index=pd.to_datetime([int(r[0]) for r in rows], unit="ms")))
    df = pd.concat(frames)
    df = df[~df.index.duplicated()].sort_index()
    return df


def read_coinbase(product: str) -> pd.DataFrame:
    d = pd.read_csv(RAW / "coinbase" / f"{product}_1h.csv")
    d.index = pd.to_datetime(d["time"], unit="s")
    return d[["open", "close"]].sort_index()


def read_rf() -> pd.Series:
    d = pd.read_csv(RAW / "fred" / "DTB3.csv")
    s = pd.to_numeric(d.iloc[:, 1], errors="coerce") / 100.0
    s.index = pd.to_datetime(d.iloc[:, 0])
    return s.dropna()


bn_btc, bn_eth = read_vision("BTCUSDT"), read_vision("ETHUSDT")
cb_btc, cb_eth = read_coinbase("BTC-USD"), read_coinbase("ETH-USD")
last_closed = pd.Timestamp("2026-10-30 13:00")  # dernière bougie close commune au moment du run du chercheur
idx = pd.date_range(max(bn_btc.index[0], cb_btc.index[0]), last_closed, freq="h")
BN = bn_btc["close"].reindex(idx)
BN_OPEN_NEXT = bn_btc["open"].reindex(idx).shift(-1)  # open de la bougie suivante = premier prix après le signal
CB = cb_btc["close"].reindex(idx)
prime = np.log(CB / BN)
prime_eth = np.log(cb_eth["close"].reindex(idx) / bn_eth["close"].reindex(idx))
depeg = (prime.abs() > 0.01) & (prime_eth.abs() > 0.01) & (np.sign(prime) == np.sign(prime_eth))
valid = prime.notna() & ~depeg
pv = prime[valid]
z = ((pv - pv.rolling(720, min_periods=720).mean()) / pv.rolling(720, min_periods=720).std()).reindex(idx)
r_h = BN.ffill().pct_change()
r_h[BN.isna()] = np.nan
rv = r_h.dropna()
vol = (rv.rolling(720, min_periods=720).std() * np.sqrt(8760)).reindex(idx)  # 720 derniers rendements VALIDES (PREREG)
BNV = BN.values
rf_d = read_rf().reindex(pd.date_range("2017-01-01", "2026-12-31", freq="D")).ffill()
rf_h = pd.Series(rf_d.reindex(idx.normalize()).values / 8760.0, index=idx).fillna(0.0)

data_check = {
    "hours": len(idx), "binance_missing_hours": int(BN.isna().sum()), "coinbase_missing_hours": int(CB.isna().sum()),
    "prime_hours": int(prime.notna().sum()), "depeg_hours": int(depeg.sum()),
    "first_z": str(z.first_valid_index()), "z_gt2": int((z > 2).sum()), "z_lt_m2": int((z < -2).sum()),
    "prime_sd_bps_by_year": {int(y): round(float(v * 1e4), 2) for y, v in prime[valid].groupby(idx[valid].year).std().items()},
    "binance_missing_by_year": {int(y): int(v) for y, v in BN.isna().groupby(idx.year).sum().items()},
}


# ------------------------------------------------------------------ stratégie
def trades(h: int, delay: int = 0, zs: pd.Series | None = None, sides=(1, -1)) -> pd.DataFrame:
    zz = (zs if zs is not None else z).values
    volv = vol.values
    n = len(idx)
    out, nxt = [], -1
    for i in np.flatnonzero(np.abs(np.nan_to_num(zz)) > 2.0):
        if i < nxt:
            continue
        s = 1 if zz[i] > 0 else -1
        if s not in sides:
            continue
        e, x = i + delay, i + delay + h
        if x >= n:
            break
        if not (np.isfinite(volv[i]) and volv[i] > 0 and np.isfinite(BNV[e]) and np.isfinite(BNV[x])):
            continue  # pas de prix Binance à l'entrée ou à la sortie : trade impossible
        out.append((i, e, x, s, min(0.10 / volv[i], 3.0), zz[i]))
        nxt = i + h
    return pd.DataFrame(out, columns=["i", "e", "x", "side", "w", "z"])


def daily(tr: pd.DataFrame, px: pd.Series = BN, cost_rt: float = 0.0, extra: np.ndarray | None = None,
          short_rf_sign: float = 1.0) -> pd.Series:
    """P&L quotidien en excès du cash, zéros à plat. Rendement de la bougie k = px[k]/px[k-1] − 1.

    short_rf_sign = +1 : le short ENCAISSE rf (future CME, cash gagé rémunéré) ; −1 : le short PAIE rf (perp HL,
    collatéral USDC non rémunéré, benchmark cash rf).
    """
    p = px.ffill().values
    r = np.concatenate([[0.0], p[1:] / p[:-1] - 1.0])
    r = np.nan_to_num(r)
    pos = np.zeros(len(idx))
    rfpos = np.zeros(len(idx))
    for e, x, s, w in zip(tr["e"].values, tr["x"].values, tr["side"].values, tr["w"].values):
        pos[e + 1:x + 1] = s * w
        rfpos[e + 1:x + 1] = w * (1.0 if s > 0 else -short_rf_sign)
    hourly = pos * r - rfpos * rf_h.values
    cost = np.zeros(len(idx))
    c = tr["w"].values * cost_rt
    if extra is not None:
        c = c + tr["w"].values * extra
    np.add.at(cost, tr["e"].values, c)
    d = pd.Series(hourly - cost, index=idx).groupby(idx.normalize()).sum()
    return d.loc[z.first_valid_index().normalize():]


def trade_ret(tr: pd.DataFrame, px: pd.Series = BN) -> np.ndarray:
    p = px.ffill().values
    return tr["side"].values * (p[tr["x"].values] / p[tr["e"].values] - 1.0)


# ------------------------------------------------------------------ statistiques
def sharpe(d: pd.Series) -> float:
    return float(d.mean() / d.std() * np.sqrt(ANN)) if d.std() > 0 else np.nan


def hac_t(x) -> float:
    x = np.asarray(x, float)
    return float(sm.OLS(x, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": 6}).tvalues[0])


def stat_boot(d: pd.Series, B: int = 2000, mean_block: float = 10.0, seed: int = 11) -> np.ndarray:
    """Bootstrap stationnaire : indices construits bloc par bloc (longueurs géométriques)."""
    rng = np.random.default_rng(seed)
    x = d.values
    n = len(x)
    out = np.empty(B)
    for b in range(B):
        pos = []
        while len(pos) < n:
            start = rng.integers(0, n)
            length = rng.geometric(1.0 / mean_block)
            pos.extend(((start + np.arange(length)) % n).tolist())
        y = x[np.array(pos[:n])]
        out[b] = y.mean() / y.std() * np.sqrt(ANN) if y.std() > 0 else 0.0
    return out


def mdd(d: pd.Series) -> float:
    c = d.cumsum()
    return float((c - c.cummax()).min())


def block(d: pd.Series, ci: bool = False) -> dict:
    o = {"days": len(d), "sharpe": sharpe(d), "t_hac": hac_t(d), "ann_ret": float(d.mean() * ANN),
         "ann_vol": float(d.std() * np.sqrt(ANN)), "maxdd": mdd(d), "worst_day": float(d.min()), "skew": float(d.skew())}
    if ci:
        bs = stat_boot(d)
        o["ci_lo"], o["ci_hi"] = float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
    return o


def per(d: pd.Series) -> dict[str, pd.Series]:
    return {"IS": d.loc[:IS_END], "HO": d.loc[HO0:HO1], "FWD": d.loc[FWD0:], "ALL": d.loc[:HO1]}


def mde(n_days: float) -> float:
    return float((norm.ppf(0.95) + norm.ppf(0.80)) / np.sqrt(n_days / ANN))


# ================================================================== 1. reproduction
rows = []
series = {}
for h in (1, 4, 24):
    for dl in (0, 1):
        tr = trades(h, dl)
        d = daily(tr)
        series[(h, dl)] = (tr, d)
        for pn, dd in per(d).items():
            if len(dd) < 5:
                continue
            b = block(dd, ci=(dl == 0 and pn in ("IS", "HO") and h == 24))
            ent = idx[tr["e"].values]
            m = (ent >= dd.index[0]) & (ent <= dd.index[-1] + pd.Timedelta(hours=23))
            b.update({"h": h, "delay": dl, "period": pn, "n_trades": int(m.sum()),
                      "gross_bps_trade": float(trade_ret(tr[m]).mean() * 1e4) if m.sum() else np.nan})
            rows.append(b)
            count("R_reproduction_h_delay_periode")
rep = pd.DataFrame(rows)
rep.to_csv(OUT / "repro.csv", index=False, float_format="%.4f")
print(rep[["h", "delay", "period", "sharpe", "t_hac", "n_trades", "gross_bps_trade", "maxdd", "skew"]].to_string())

tr24, d24 = series[(24, 0)]
tr24 = tr24.copy()
tr24["entry"] = idx[tr24["e"].values]
tr24["ret"] = trade_ret(tr24)
tr24["pnl"] = tr24["w"] * tr24["ret"]
d24.rename("pnl").to_csv(OUT / "daily_h24_revue.csv", float_format="%.7f")

# comparaison aux séries du cloud et du chercheur
cloud = pd.read_csv(CLOUD / "daily_pnl_h24.csv", index_col=0, parse_dates=True)["pnl"]
cher = pd.read_csv(DOSSIER / "out" / "daily_h24_gross.csv", index_col=0, parse_dates=True)["pnl"]
common = d24.index.intersection(cloud.index)
act_cloud = cloud.loc[common] != 0
act_me = d24.loc[common] != 0
comp = {"corr_vs_cloud": float(np.corrcoef(d24.loc[common], cloud.loc[common])[0, 1]),
        "corr_vs_chercheur": float(d24.corr(cher.reindex(d24.index))),
        "active_days_cloud": int(act_cloud.sum()), "active_days_me": int(act_me.sum()),
        "active_days_both": int((act_cloud & act_me).sum()),
        "cloud_sharpe_IS_recalc": sharpe(cloud.loc["2017-09-26":IS_END]), "cloud_sharpe_HO_recalc": sharpe(cloud.loc[HO0:HO1]),
        "cloud_ratio_log_vs_simple_note": "cloud : log-rendements, pas de cash retiré, cap 10, min_periods 360"}
count("R_comparaison_series", 2)
print(comp)

# ================================================================== 2. variantes d'exécution et de devise
var = []
for name, px, dl in (("Binance close (réf.)", BN, 0), ("Binance open bougie suivante", BN_OPEN_NEXT, 0),
                     ("Coinbase USD close", CB, 0), ("mi-prix (CB+BN)/2", (CB + BN) / 2, 0),
                     ("Binance close, délai +1 h", BN, 1)):
    tr = trades(24, dl)
    d = daily(tr, px=px)
    for pn, dd in per(d).items():
        if pn == "FWD":
            continue
        var.append({"variante": name, "period": pn, "sharpe": sharpe(dd), "t_hac": hac_t(dd),
                    "bps_trade": float(trade_ret(tr[(idx[tr["e"].values] >= dd.index[0]) & (idx[tr["e"].values] <= dd.index[-1] + pd.Timedelta(hours=23))], px).mean() * 1e4)})
        count("V_variante_prix_x_periode")
var = pd.DataFrame(var)
var.to_csv(OUT / "variantes_prix.csv", index=False, float_format="%.4f")
print(var.to_string())

# ================================================================== 3. dose-réponse |z| (tous les trades h24 non chevauchants)
dr = []
bins = [(2, 2.5), (2.5, 3), (3, 4), (4, 99)]
for pn, lo, hi in (("IS", idx[0], IS_END + pd.Timedelta(hours=23)), ("HO", HO0, HO1 + pd.Timedelta(hours=23))):
    sub = tr24[(tr24["entry"] >= lo) & (tr24["entry"] <= hi)]
    for a, b in bins:
        m = (sub["z"].abs() >= a) & (sub["z"].abs() < b)
        if m.sum() >= 5:
            dr.append({"period": pn, "abs_z": f"[{a},{b})", "n": int(m.sum()), "bps_trade": float(sub.loc[m, "ret"].mean() * 1e4),
                       "t_hac": hac_t(sub.loc[m, "ret"]), "share_pnl": float(sub.loc[m, "pnl"].sum() / sub["pnl"].sum())})
            count("D_dose_reponse")
# bande 1-2 non tradée : signal plus faible, mêmes règles de non-chevauchement
z12 = z.where(z.abs().between(1, 2))
z12 = z12.where(z12.abs() > 0) * 2.5 / z12.abs()  # forcé à |2,5| pour passer le seuil de trades()
tr12 = trades(24, 0, zs=z12.fillna(0))
tr12["entry"] = idx[tr12["e"].values]
tr12["ret"] = trade_ret(tr12)
for pn, lo, hi in (("IS", idx[0], IS_END + pd.Timedelta(hours=23)), ("HO", HO0, HO1 + pd.Timedelta(hours=23))):
    sub = tr12[(tr12["entry"] >= lo) & (tr12["entry"] <= hi)]
    dr.append({"period": pn, "abs_z": "[1,2) non tradée", "n": len(sub), "bps_trade": float(sub["ret"].mean() * 1e4),
               "t_hac": hac_t(sub["ret"]), "share_pnl": np.nan})
    count("D_dose_reponse")
dr = pd.DataFrame(dr)
dr.to_csv(OUT / "dose_reponse_h24.csv", index=False, float_format="%.4f")
print(dr.to_string())

# ================================================================== 4. concentration par trade et par épisode (grappes de 7 jours)
conc = []
for pn, lo, hi in (("ALL", idx[0], HO1 + pd.Timedelta(hours=23)), ("HO", HO0, HO1 + pd.Timedelta(hours=23))):
    sub = tr24[(tr24["entry"] >= lo) & (tr24["entry"] <= hi)].copy()
    dd_full = daily(sub).loc[lo.normalize():hi.normalize()]
    tot = sub["pnl"].sum()
    # épisodes : trades séparés de moins de 7 jours
    gap = sub["entry"].diff() > pd.Timedelta(days=7)
    sub["episode"] = gap.cumsum()
    ep = sub.groupby("episode")["pnl"].sum().sort_values(ascending=False)
    for k in (1, 3, 5, 10):
        top_tr = sub["pnl"].sort_values(ascending=False).index[:k]
        d_wo = daily(sub.drop(index=top_tr)).loc[lo.normalize():hi.normalize()]
        top_ep = ep.index[:k]
        d_wo_ep = daily(sub[~sub["episode"].isin(top_ep)]).loc[lo.normalize():hi.normalize()]
        conc.append({"period": pn, "k": k, "share_top_trades": float(sub.loc[top_tr, "pnl"].sum() / tot), "sharpe_sans_top_trades": sharpe(d_wo),
                     "share_top_episodes": float(ep.iloc[:k].sum() / tot), "n_trades_in_top_episodes": int(sub["episode"].isin(top_ep).sum()),
                     "sharpe_sans_top_episodes": sharpe(d_wo_ep), "n_episodes": int(sub["episode"].nunique()), "n_trades": len(sub)})
        count("C_concentration", 2)
conc = pd.DataFrame(conc)
conc.to_csv(OUT / "concentration_episodes.csv", index=False, float_format="%.4f")
print(conc.to_string())
# part des pertes : pires trades et pire épisode
worst = tr24.sort_values("pnl").head(5)
worst_rows = [{"entry": str(e), "side": int(s), "z": float(zz), "w": float(w), "ret_bps": float(r * 1e4), "pnl": float(p)}
              for e, s, zz, w, r, p in zip(worst["entry"], worst["side"], worst["z"], worst["w"], worst["ret"], worst["pnl"])]

# ================================================================== 5. sélection d'horizon : inflation du max de 3 lectures (bootstrap joint)
ho3 = pd.DataFrame({h: per(series[(h, 0)][1])["HO"] for h in (1, 4, 24)})
rng = np.random.default_rng(3)
n = len(ho3)
B = 2000
mx, mn, s24 = np.empty(B), np.empty(B), np.empty(B)
X = ho3.values
for b in range(B):
    pos = []
    while len(pos) < n:
        st, ln = rng.integers(0, n), rng.geometric(0.1)
        pos.extend(((st + np.arange(ln)) % n).tolist())
    Y = X[np.array(pos[:n])]
    sr = Y.mean(0) / Y.std(0) * np.sqrt(ANN)
    mx[b], mn[b], s24[b] = sr.max(), sr.mean(), sr[2]
ho_sr = {int(h): sharpe(ho3[h]) for h in ho3.columns}
sel = {"holdout_sr": ho_sr, "mean_of_three": float(np.mean(list(ho_sr.values()))),
       "boot_E_max_minus_E_mean": float(mx.mean() - mn.mean()),
       "boot_E_max_minus_E_h24": float(mx.mean() - s24.mean()),
       "boot_sd_h24_holdout": float(s24.std()),
       "p_one_sided_HO_h24": float(1 - norm.cdf(hac_t(ho3[24]))),
       "sidak_k3": float(1 - (1 - (1 - norm.cdf(hac_t(ho3[24])))) ** 3),
       "sidak_k42_module1": float(1 - (1 - (1 - norm.cdf(hac_t(ho3[24])))) ** 42),
       "p_one_sided_IS_h24": float(1 - norm.cdf(hac_t(per(series[(24, 0)][1])["IS"]))),
       "sidak_k42_IS_h24": float(1 - (1 - (1 - norm.cdf(hac_t(per(series[(24, 0)][1])["IS"])))) ** 42),
       "mde_holdout": mde(n), "mde_6m": mde(182), "mde_1y": mde(365), "mde_3y": mde(3 * 365),
       "corr_daily_HO_h4_h24": float(ho3[4].corr(ho3[24])), "corr_daily_HO_h1_h24": float(ho3[1].corr(ho3[24]))}
# walk-forward annuel : horizon au meilleur Sharpe passé (fenêtre croissante), lecture de contrôle
wf = []
pieces = []
for y in range(2019, 2027):
    past = {h: sharpe(series[(h, 0)][1].loc[:f"{y - 1}-12-31"]) for h in (1, 4, 24)}
    pick = max(past, key=past.get)
    seg = series[(pick, 0)][1].loc[f"{y}-01-01":min(pd.Timestamp(f"{y}-12-31"), HO1)]
    pieces.append(seg)
    wf.append({"year": y, "pick": pick, "oos_sr_pick": sharpe(seg), "oos_sr_h24": sharpe(series[(24, 0)][1].loc[f"{y}-01-01":min(pd.Timestamp(f"{y}-12-31"), HO1)])})
wfs = pd.concat(pieces)
sel["wf_pick_sr_2019_HOend"] = sharpe(wfs)
sel["wf_pick_sr_2024_HOend"] = sharpe(wfs.loc[HO0:HO1])
sel["h24_sr_2019_HOend"] = sharpe(series[(24, 0)][1].loc["2019-01-01":HO1])
count("S_selection_horizon", 6)
(OUT / "selection_horizon.json").write_text(json.dumps(sel, indent=1))
pd.DataFrame(wf).to_csv(OUT / "wf_horizon.csv", index=False, float_format="%.4f")
print(json.dumps(sel, indent=1))

# ================================================================== 6. jambes et années
legs = []
for pn, lo, hi in (("IS", idx[0], IS_END + pd.Timedelta(hours=23)), ("HO", HO0, HO1 + pd.Timedelta(hours=23))):
    for s in (1, -1):
        sub = tr24[(tr24["side"] == s) & (tr24["entry"] >= lo) & (tr24["entry"] <= hi)]
        legs.append({"period": pn, "side": s, "n": len(sub), "bps_trade": float(sub["ret"].mean() * 1e4), "t_hac": hac_t(sub["ret"]),
                     "sharpe_leg": sharpe(daily(sub).loc[lo.normalize():hi.normalize()])})
        count("L_jambes")
legs = pd.DataFrame(legs)
legs.to_csv(OUT / "jambes_h24.csv", index=False, float_format="%.4f")
years = d24.loc[:HO1].groupby(d24.loc[:HO1].index.year).apply(sharpe)
count("A_annees", len(years))
print(legs.to_string()); print(years.round(2).to_dict())

# ================================================================== 7. funding HL / Binance (reparsé) et net perp HL
hl = pd.DataFrame(json.loads((RAW / "funding" / "hl_btc.json").read_text()))
hl_s = pd.Series(hl["fundingRate"].astype(float).values, index=pd.to_datetime(hl["time"].astype("int64"), unit="ms"))
hl_s = hl_s[~hl_s.index.duplicated()].sort_index()
bnf = pd.DataFrame(json.loads((RAW / "funding" / "binance_btcusdt.json").read_text()))
bn_s = pd.Series(bnf["fundingRate"].astype(float).values, index=pd.to_datetime(bnf["fundingTime"].astype("int64"), unit="ms"))
bn_s = bn_s[~bn_s.index.duplicated()].sort_index()
fund, src = np.zeros(len(tr24)), []
for k, (e, x, s) in enumerate(zip(tr24["e"].values, tr24["x"].values, tr24["side"].values)):
    t0, t1 = idx[e] + pd.Timedelta(hours=1), idx[x] + pd.Timedelta(hours=1)
    if t0 >= hl_s.index[0]:
        f = hl_s.loc[t0 + pd.Timedelta(seconds=1):t1].sum(); src.append("HL")
    elif t0 >= bn_s.index[0]:
        f = bn_s.loc[t0 + pd.Timedelta(seconds=1):t1].sum(); src.append("Binance")
    else:
        f = 0.0; src.append("aucun")
    fund[k] = s * f
tr24["funding_cost"] = fund
tr24["funding_src"] = src
fstat = {"hl_rates_n": len(hl_s), "hl_first": str(hl_s.index[0]), "hl_mean_rate_hourly_bps": float(hl_s.mean() * 1e4),
         "hl_ann_mean_pct": float(hl_s.mean() * 24 * 365 * 100),
         "funding_cost_bps_trade_mean": float(fund.mean() * 1e4), "funding_cost_bps_trade_mean_HL_only": float(fund[np.array(src) == "HL"].mean() * 1e4),
         "funding_p95_abs_bps": float(np.quantile(np.abs(fund), 0.95) * 1e4), "n_by_src": {k: int(v) for k, v in pd.Series(src).value_counts().items()},
         "funding_cost_bps_trade_long_HL": float(fund[(np.array(src) == "HL") & (tr24["side"].values == 1)].mean() * 1e4),
         "funding_cost_bps_trade_short_HL": float(fund[(np.array(src) == "HL") & (tr24["side"].values == -1)].mean() * 1e4)}
count("F_funding", 3)
HL_TAKER = 2 * 4.5e-4 + 0.13e-4
HL_MAKER = 2 * 1.5e-4
veh = []
for name, cost, sign, px in (("brut", 0.0, 1.0, BN), ("perp HL taker + funding (short encaisse rf, comme le chercheur)", HL_TAKER, 1.0, BN),
                             ("perp HL taker + funding, short paie rf (collatéral USDC non rémunéré)", HL_TAKER, -1.0, BN),
                             ("perp HL maker + funding, short paie rf", HL_MAKER, -1.0, BN),
                             ("perp HL taker + funding, short paie rf, prix Coinbase USD (borne basse)", HL_TAKER, -1.0, CB),
                             ("perp HL taker + funding, short paie rf, mi-prix", HL_TAKER, -1.0, (CB + BN) / 2)):
    d = daily(tr24, px=px, cost_rt=cost, extra=(fund if cost > 0 else None), short_rf_sign=sign)
    for pn, dd in per(d).items():
        if pn == "FWD":
            continue
        b = block(dd)
        b.update({"vehicule": name, "period": pn})
        folds = [sharpe(d.loc[f"{y}-01-01":min(pd.Timestamp(f"{y}-12-31"), HO1)]) for y in range(2019, 2027)]
        b["plis_pos_2019_2026"] = f"{int(sum(f > 0 for f in folds))}/8"
        veh.append(b)
        count("V_vehicule_x_periode")
veh = pd.DataFrame(veh)
veh.to_csv(OUT / "vehicules_revue.csv", index=False, float_format="%.4f")
print(veh[["vehicule", "period", "sharpe", "t_hac", "maxdd", "worst_day", "skew", "plis_pos_2019_2026"]].to_string())

# point mort (brut Binance, funding inclus, short paie rf)
def sr_at(c: float, lo, hi) -> float:
    return sharpe(daily(tr24, cost_rt=c, extra=fund, short_rf_sign=-1.0).loc[lo:hi])
be = {}
for pn, lo, hi in (("ALL", d24.index[0], HO1), ("HO", HO0, HO1)):
    for tgt in (1.0, 0.7, 0.0):
        a, b_ = 0.0, 0.02
        for _ in range(25):
            m = (a + b_) / 2
            if sr_at(m, lo, hi) > tgt:
                a = m
            else:
                b_ = m
        be[f"{pn}_bps_RT_at_SR{tgt:g}"] = round(a * 1e4, 1)
        count("B_point_mort")
# traînée de Sharpe par bp de coût (pente locale autour de 0-10 bps)
be["sharpe_per_bp_RT_ALL"] = float((sr_at(10e-4, d24.index[0], HO1) - sr_at(0.0, d24.index[0], HO1)) / 10)
print(be, fstat)

# ================================================================== 8. granularité MBT / nano sur 12 000 €
P = float(BN.dropna().iloc[-1])
fx = pd.read_csv(RAW / "fred" / "DEXUSEU.csv")
fxv = float(pd.to_numeric(fx.iloc[:, 1], errors="coerce").dropna().iloc[-1])
eq = 12_000 * fxv
lot = {"btc_last": P, "eurusd": fxv, "equity_usd": eq, "mbt_lot_usd": 0.1 * P, "mbt_lot_share_equity": 0.1 * P / eq,
       "nano_lot_share_equity": 0.01 * P / eq, "w_median_recent_2y": float(tr24.loc[tr24["entry"] >= "2024-10-01", "w"].median()),
       "w_p90_recent_2y": float(tr24.loc[tr24["entry"] >= "2024-10-01", "w"].quantile(0.9)),
       "share_trades_w_ge_1mbt_recent_2y": float((tr24.loc[tr24["entry"] >= "2024-10-01", "w"] >= 0.1 * P / eq).mean()),
       "mbt_fee_rt_usd": 2 * (0.85 + 1.15 + 0.02) + 0.50, "mbt_fee_rt_bps": (2 * (0.85 + 1.15 + 0.02) + 0.50) / (0.1 * P) * 1e4}
# série à 1 lot fixe (w = part du compte d'un lot), coût MBT, sans base
tr1 = tr24.copy()
tr1["w"] = 0.1 * P / eq
d1 = daily(tr1, cost_rt=lot["mbt_fee_rt_bps"] / 1e4)
b1 = block(d1.loc[:HO1])
lot.update({f"mbt_1lot_{k}": v for k, v in b1.items()})
count("G_granularite", 1)
print(lot)

# ================================================================== sorties
summary = {"data_check": data_check, "comparaison": comp, "worst_trades": worst_rows, "funding": fstat, "breakeven": be, "lots": lot,
           "years_sharpe_h24": {int(k): float(v) for k, v in years.items()}}
(OUT / "revue_summary.json").write_text(json.dumps(summary, indent=1, default=str))
(OUT / "n_tests_revue.json").write_text(json.dumps({"familles": NT, "total": int(sum(NT.values()))}, indent=1))
print("n_tests", NT, sum(NT.values()))
