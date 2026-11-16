"""Re-pricing de la liste de trades C9 h24 (inchangée) aux coûts et aux prix de chaque véhicule accessible depuis la France.

Usage : /usr/bin/python3 -I -B run_vehicules_fr.py <dl_dir> <out_dir>
  <dl_dir> : dossier des téléchargements publics (kraken_hist/, cb_api/) ; <out_dir> : sorties.
Aucune nouvelle configuration de signal : mêmes trades que run_vehicles.py (h = 24, |z| > 2, 10 % de vol, plafond 3).
Conventions identiques à revue/revue_c9.py : série quotidienne avec zéros, excès du cash, le short PAIE rf (collatéral
non rémunéré) sur tous les véhicules dérivés, coût aller-retour × w au jour d'entrée, √365.
Frais (sources et dates dans VEHICULES_FR.md, lus le 2026-10-30) :
  HL palier 0 : 4,5 / 1,5 bps par côté ; Kraken EU (PF_XBTUSD) palier 1 : 5 / 2 bps ; fourchettes mesurées 0,13 bp.
  Coinbase UE nano perp-style 0,01 BTC : 0,02 % annoncé + frais bourse/compensation/NFA ≈ 0,21 $ par contrat et par côté
  (JUGÉ, repris des frais CDE de run_vehicles.py) ; IG CFD : fourchette minimale 150 $ par BTC, financement long 25 %/an,
  short crédité 5 %/an (une nuit par trade de 24 h) ; eToro CFD : 1 % à l'ouverture et à la clôture.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c9lib as L  # noqa: E402
from c9lib import np, pd  # noqa: E402

DL = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
NT: dict[str, int] = {}


def count(f: str, k: int = 1) -> None:
    NT[f] = NT.get(f, 0) + k


pn = L.build_panel()
idx = pn.idx
first = pn.z.first_valid_index().normalize()
last = idx[-1].normalize()
tr = L.run_strategy(pn, h=24)
P_LAST = float(pn.bn_btc.dropna().iloc[-1])
EQ_EUR = 12_000.0
FX_LAST = 1.1199  # EURUSD de vehicles_detail.json

# ---------------------------------------------------------------- séries de prix des véhicules
def load_kraken(kind: str) -> pd.Series:
    rows = []
    for p in sorted((DL / "kraken_hist").glob(f"{kind}_*.json")):
        rows += json.loads(p.read_text()).get("candles", [])
    s = pd.Series({pd.Timestamp(int(c["time"]), unit="ms"): float(c["close"]) for c in rows})
    return s[~s.index.duplicated()].sort_index()


def load_bip() -> pd.Series:
    rows = []
    for p in sorted((DL / "cb_api").glob("bip_*.json")):
        rows += json.loads(p.read_text()).get("candles", [])
    s = pd.Series({pd.Timestamp(int(c["start"]), unit="s"): float(c["close"]) for c in rows})
    return s[~s.index.duplicated()].sort_index()


def load_hl() -> pd.Series:
    c = json.loads((L.RAW / "hl_candles_btc_1h.json").read_text())
    s = pd.Series([float(x["c"]) for x in c], index=pd.to_datetime([x["t"] for x in c], unit="ms"))
    return s[~s.index.duplicated()].sort_index()


KR = load_kraken("trade").reindex(idx)
BIP = load_bip().reindex(idx)
HLP = load_hl().reindex(idx)
BN, CB = pn.bn_btc, pn.cb_btc

# ---------------------------------------------------------------- funding
hl = pd.DataFrame(json.loads((L.RAW / "funding" / "hl_btc.json").read_text()))
hl_s = pd.Series(hl["fundingRate"].astype(float).values, index=pd.to_datetime(hl["time"], unit="ms").round("min"))
bn = pd.DataFrame(json.loads((L.RAW / "funding" / "binance_btcusdt.json").read_text()))
bn_s = pd.Series(bn["fundingRate"].astype(float).values, index=pd.to_datetime(bn["fundingTime"], unit="ms").round("min"))
kr = json.loads((DL / "kraken_hist" / "funding_since2022.json").read_text())["rates"]
kr_s = pd.Series([float(r["relativeFundingRate"]) for r in kr],
                 index=pd.to_datetime([r["timestamp"] for r in kr]).tz_localize(None))
for s_ in (hl_s, bn_s, kr_s):
    s_.sort_index(inplace=True)


def funding(series_order: list[pd.Series]) -> tuple[np.ndarray, list[str]]:
    """Funding payé (fraction du notionnel, >0 = coût) sur la fenêtre tenue ; première source disponible."""
    names = {id(hl_s): "HL", id(bn_s): "Binance", id(kr_s): "Kraken"}
    out, src = np.zeros(len(tr)), []
    for k, (e, x, s) in enumerate(zip(tr["e"].values, tr["x"].values, tr["side"].values)):
        t0, t1 = idx[e] + pd.Timedelta(hours=1), idx[x] + pd.Timedelta(hours=1)
        for ser in series_order:
            if t0 >= ser.index[0]:
                out[k] = s * ser.loc[t0 + pd.Timedelta(seconds=1):t1].sum()
                src.append(names[id(ser)])
                break
        else:
            src.append("aucun")
    return out, src


f_hl, src_hl = funding([hl_s, bn_s])
f_kr, src_kr = funding([kr_s, hl_s, bn_s])
count("F_funding", 2)


# ---------------------------------------------------------------- P&L quotidien
def daily(t: pd.DataFrame, px: pd.Series, cost: np.ndarray | float, short_rf_sign: float = -1.0) -> pd.Series:
    p = px.ffill().values
    r = np.nan_to_num(np.concatenate([[0.0], p[1:] / p[:-1] - 1.0]))
    pos, rfpos = np.zeros(len(idx)), np.zeros(len(idx))
    for e, x, s, w in zip(t["e"].values, t["x"].values, t["side"].values, t["w"].values):
        pos[e + 1:x + 1] = s * w
        rfpos[e + 1:x + 1] = w * (1.0 if s > 0 else -short_rf_sign)
    hourly = pos * r - rfpos * pn.rf_h.values
    c = np.zeros(len(idx))
    np.add.at(c, t["e"].values, t["w"].values * (np.asarray(cost) if np.ndim(cost) else cost))
    d = pd.Series(hourly - c, index=idx).groupby(idx.normalize()).sum()
    return d.loc[first:last]


PERIODS = {"ALL": (first, last), "IS": (first, L.IS_END.normalize()),
           "HO": (pd.Timestamp("2024-01-01"), L.HO_END.normalize()),
           "KR_2022-04+": (pd.Timestamp("2022-04-01"), last)}


def block(name: str, d: pd.Series, t: pd.DataFrame, cost_bps: np.ndarray | float, note: str = "") -> list[dict]:
    rows = []
    for per, (lo, hi) in PERIODS.items():
        dd = d.loc[lo:hi]
        tt = t[(idx[t["e"].values] >= lo) & (idx[t["e"].values] <= hi + pd.Timedelta(hours=23))]
        cb = np.asarray(cost_bps) if np.ndim(cost_bps) else np.full(len(t), cost_bps)
        cb = pd.Series(cb, index=t.index).loc[tt.index]
        rows.append({"vehicule": name, "periode": per, "sharpe": L.sharpe(dd), "t_hac": L.hac_t(dd),
                     "ann_ret": float(dd.mean() * 365), "maxdd": L.maxdd(dd), "n_trades": len(tt),
                     "cout_moyen_bps_AR": float(cb.mean()), "note": note})
        count("V_fr_vehicule_x_periode")
    return rows


rows: list[dict] = []
rows += block("brut, prix Binance (référence)", daily(tr, BN, 0.0, short_rf_sign=1.0), tr, 0.0)

HL_T, HL_M = 2 * 4.5e-4 + 0.13e-4, 2 * 1.5e-4
KR_T, KR_M = 2 * 5e-4 + 0.13e-4, 2 * 2e-4
for px_name, px in (("Binance", BN), ("Coinbase USD", CB)):
    rows += block(f"HL perp taker, prix {px_name}", daily(tr, px, HL_T + f_hl), tr, HL_T * 1e4 + f_hl * 1e4)
    rows += block(f"Kraken UE PF_XBTUSD taker, prix {px_name}", daily(tr, px, KR_T + f_kr), tr, KR_T * 1e4 + f_kr * 1e4)
    rows += block(f"Kraken UE PF_XBTUSD maker, prix {px_name}", daily(tr, px, KR_M + f_kr), tr, KR_M * 1e4 + f_kr * 1e4)

# Kraken au PRIX RÉEL du perp PF_XBTUSD (bougies 1 h publiques, depuis 2022-03-22) : mêmes trades, trois prix
ok_kr = np.isfinite(KR.values[tr["e"].values]) & np.isfinite(KR.values[tr["x"].values])
t_kr = tr[ok_kr]
fk = pd.Series(f_kr, index=tr.index).loc[t_kr.index].values
for px_name, px in (("réel PF_XBTUSD", KR), ("Binance", BN), ("Coinbase USD", CB)):
    d = daily(t_kr, px, KR_T + fk).loc["2022-04-01":]
    for per, (lo, hi) in (("KR_2022-04+", (pd.Timestamp("2022-04-01"), last)), ("KR_HO", (pd.Timestamp("2024-01-01"), L.HO_END.normalize()))):
        dd = d.loc[lo:hi]
        rows.append({"vehicule": f"Kraken UE taker, trades à prix Kraken connu, prix {px_name}", "periode": per,
                     "sharpe": L.sharpe(dd), "t_hac": L.hac_t(dd), "ann_ret": float(dd.mean() * 365), "maxdd": L.maxdd(dd),
                     "n_trades": int(((idx[t_kr['e'].values] >= lo) & (idx[t_kr['e'].values] <= hi)).sum()),
                     "cout_moyen_bps_AR": float((KR_T + fk).mean() * 1e4), "note": "L77 direct"})
        count("V_fr_kraken_prix_reel")

# Coinbase UE nano perp-style 0,01 BTC : frais fixes en $ au prix courant (même ancrage que run_vehicles.py)
NANO_FIX = 0.21 / (0.01 * P_LAST)
CB_T = 2 * (5e-4 + NANO_FIX) + 1e-4
CB_M = 2 * (2e-4 + NANO_FIX)
rows += block("Coinbase UE nano perp-style taker (JUGÉ 5 bps + fixe), prix Coinbase USD",
              daily(tr, CB, CB_T + f_hl), tr, CB_T * 1e4 + f_hl * 1e4, "funding proxy HL/Binance")
rows += block("Coinbase UE nano perp-style 0,02 % (annoncé), prix Coinbase USD",
              daily(tr, CB, CB_M + f_hl), tr, CB_M * 1e4 + f_hl * 1e4, "funding proxy HL/Binance")
# lots entiers de 0,01 BTC
g = 0.01 * P_LAST / (EQ_EUR * FX_LAST)
tl = tr.copy()
tl["w"] = np.round(tl["w"].values / g) * g
tl = tl[tl["w"] > 0]
rows += block("Coinbase UE nano, arrondi au lot 0,01 BTC, taker", daily(tl, CB, CB_T + pd.Series(f_hl, index=tr.index).loc[tl.index].values),
              tl, CB_T * 1e4 + pd.Series(f_hl, index=tr.index).loc[tl.index].values * 1e4)

# IG CFD : fourchette fixe 150 $ (minimale) au prix courant + une nuit de financement (long 25 %/an débité, short 5 %/an crédité)
IG_SPREAD = 150.0 / P_LAST
ig_fin = np.where(tr["side"].values > 0, 0.25 / 360, -0.05 / 360)  # IG : taux annuel / 360 (0,0694 %/j = 25 %/360)
rows += block("IG CFD (fourchette min 150 $ + 1 nuit), prix Coinbase USD", daily(tr, CB, IG_SPREAD + ig_fin), tr,
              (IG_SPREAD + ig_fin) * 1e4, "fourchette MINIMALE ; 2:1")
rows += block("eToro CFD (1 % par côté)", daily(tr, CB, 0.02), tr, 200.0)
rows += block("spot long seul Kraken UE taker 0,40 %/côté (réf.)", daily(tr[tr["side"] > 0], CB, 2 * 40e-4, 1.0),
              tr[tr["side"] > 0], 80.0)


# ---------------------------------------------------------------- horaires restreints (turbos, Saxo 24×5)
def paris_open(ts_utc: pd.Timestamp) -> bool:
    t = ts_utc.tz_localize("UTC").tz_convert("Europe/Paris")
    return t.weekday() < 5 and 8 <= t.hour < 22


def ny_24x5(ts_utc: pd.Timestamp) -> bool:
    """Dimanche 17:00 → vendredi 17:00 heure de New York (horaire 24×5½ type Saxo crypto FX / ancien CME)."""
    t = ts_utc.tz_localize("UTC").tz_convert("America/New_York")
    wd, h = t.weekday(), t.hour
    if wd == 5:
        return False
    if wd == 6:
        return h >= 17
    if wd == 4:
        return h < 17
    return True


def restrict(is_open) -> tuple[pd.DataFrame, dict]:
    keep, ex = [], []
    for k, r in tr.iterrows():
        t_in = idx[r["e"]] + pd.Timedelta(hours=1)
        if not is_open(t_in):
            continue
        t_out = idx[r["x"]] + pd.Timedelta(hours=1)
        x = int(r["x"])
        while not is_open(t_out) and x + 1 < len(idx):
            x += 1
            t_out += pd.Timedelta(hours=1)
        keep.append(k)
        ex.append(x)
    t = tr.loc[keep].copy()
    t["x"] = ex
    g_all = daily(tr, BN, 0.0, 1.0)
    g_r = daily(t, BN, 0.0, 1.0)
    pre = tr.loc[[k for k in tr.index]]
    info = {"part_trades_perdus": float(1 - len(t) / len(tr)),
            "part_pnl_brut_perdu": float(1 - g_r.sum() / g_all.sum()),
            "sharpe_brut_restreint_ALL": L.sharpe(g_r), "sharpe_brut_247_ALL": L.sharpe(g_all),
            "sharpe_brut_restreint_HO": L.sharpe(g_r.loc["2024-01-01":L.HO_END.normalize()]),
            "part_entrees_weekend": float(np.mean([idx[e].weekday() >= 5 for e in pre["e"]]))}
    count("H_horaires", 4)
    return t, info


t_turbo, info_turbo = restrict(paris_open)
t_saxo, info_saxo = restrict(ny_24x5)
rows += block("turbo/KO 8 h-22 h Paris lun-ven (sauter/décaler), 50 bps AR JUGÉ", daily(t_turbo, CB, 50e-4), t_turbo, 50.0)

veh = pd.DataFrame(rows)
veh.to_csv(OUT / "vehicules_fr.csv", index=False, float_format="%.4f")


# ---------------------------------------------------------------- L77 : quel prix le perp suit-il ?
def tracking(px: pd.Series, name: str) -> dict:
    ok = np.isfinite(px.values[tr["e"].values]) & np.isfinite(px.values[tr["x"].values])
    t = tr[ok]
    if len(t) < 5:
        return {"venue": name, "n": int(len(t))}
    def ret(p):
        pv = p.ffill().values
        return t["side"].values * (pv[t["x"].values] / pv[t["e"].values] - 1)
    rv, rb, rc = ret(px), ret(BN), ret(CB)
    d_bc = rb - rc
    beta = float(np.polyfit(d_bc, rv - rc, 1)[0]) if np.std(d_bc) > 0 else np.nan
    count("L77_tracking", 4)
    return {"venue": name, "n": int(len(t)), "debut": str(idx[t["e"].values[0]]),
            "ret_moy_venue_bps": float(rv.mean() * 1e4), "ret_moy_binance_bps": float(rb.mean() * 1e4),
            "ret_moy_coinbase_bps": float(rc.mean() * 1e4),
            "ecart_abs_moy_vs_binance_bps": float(np.abs(rv - rb).mean() * 1e4),
            "ecart_abs_moy_vs_coinbase_bps": float(np.abs(rv - rc).mean() * 1e4),
            "beta_vers_binance_(0=Coinbase,1=Binance)": beta,
            "ecart_type_binance_moins_coinbase_bps": float(np.std(d_bc) * 1e4)}


trk = [tracking(KR, "Kraken PF_XBTUSD (trade, 1 h)"), tracking(BIP, "Coinbase CDE BIP perp-style (1 h)"),
       tracking(HLP, "Hyperliquid BTC perp (1 h)")]

# ---------------------------------------------------------------- taille des positions
notional_eur = tr["w"] * EQ_EUR
size = {"w_median": float(tr["w"].median()), "w_p10": float(tr["w"].quantile(.1)), "w_p90": float(tr["w"].quantile(.9)),
        "w_max": float(tr["w"].max()), "part_w_sup_2_(levier_ESMA_2:1)": float((tr["w"] > 2).mean()),
        "part_w_sup_1": float((tr["w"] > 1).mean()),
        "notionnel_eur_median": float(notional_eur.median()),
        "notionnel_eur_median_depuis_2024": float(notional_eur[tr["entry"] >= "2024-01-01"].median()),
        "notionnel_eur_p10_p90_depuis_2024": [float(notional_eur[tr["entry"] >= "2024-01-01"].quantile(q)) for q in (.1, .9)],
        "nano_lots_median": float(np.median(np.round(tr["w"].values / g))), "nano_lot_fraction_equity": float(g)}
count("S_taille", 3)

fund_stats = {"kraken_funding_bps_trade_mean_(trades depuis 2025-10-30)":
              float(np.mean([f for f, s in zip(f_kr, src_kr) if s == "Kraken"]) * 1e4) if "Kraken" in src_kr else None,
              "hl_funding_bps_trade_mean_memes_trades":
              float(np.mean([f for f, s in zip(f_hl, src_kr) if s == "Kraken"]) * 1e4) if "Kraken" in src_kr else None,
              "n_trades_funding_kraken": int(sum(s == "Kraken" for s in src_kr))}
count("F_funding_compare", 2)
detail = {"tracking_L77": trk, "taille": size, "horaires_turbo_8-22_paris": info_turbo, "horaires_24x5_NY": info_saxo,
          "funding": fund_stats, "couts_bps_AR": {"HL_taker": HL_T * 1e4, "HL_maker": HL_M * 1e4, "Kraken_taker": KR_T * 1e4,
                                                 "Kraken_maker": KR_M * 1e4, "Coinbase_nano_taker_juge": CB_T * 1e4,
                                                 "Coinbase_nano_002": CB_M * 1e4, "IG_fourchette_min": IG_SPREAD * 1e4,
                                                 "IG_nuit_long": 0.25 / 360 * 1e4, "IG_nuit_short": -0.05 / 360 * 1e4},
          "btc_last": P_LAST}
(OUT / "vehicules_fr_detail.json").write_text(json.dumps(detail, indent=1, default=str))
(OUT / "_nt_vehicules_fr.json").write_text(json.dumps(NT, indent=1))
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 80)
print(veh[["vehicule", "periode", "sharpe", "t_hac", "maxdd", "n_trades", "cout_moyen_bps_AR"]].to_string())
print(json.dumps(detail, indent=1, default=str))
