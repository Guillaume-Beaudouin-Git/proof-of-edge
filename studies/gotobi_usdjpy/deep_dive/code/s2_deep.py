"""S2 — revue indépendante : descriptif 2007-2026, estimation prospective, recouvrement des annonces.

Pré-enregistrement : ../PREREG_DEEP.md (commité avant le lancement). Les rendements USDJPY
2007-01 → 2026-05 sont déjà lus : tout est descriptif ou d'estimation, sauf le décompte L4
(annonces), qui ne lit aucun rendement. Règle de trade, calendrier et jambes : `../../code/`.

Usage : /usr/bin/python3 s2_deep.py
Sorties : ../out/s2_deep.txt, ../out/s2_deep.json, ../out/s2_deep_events.csv
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, norm, skew

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "code"))
import s2_validation as V  # noqa: E402

H = V.H
OUT = HERE.parent / "out"
CAL = Path(os.environ.get("RESEARCH_DATA_ROOT", "data") + "/deep_history_utc/calendar/"
           "economic_calendar_2018_2026_full.csv")
COSTS = (1.87, 2.5, 3.0)
USD_PER_BP = V.NOTIONAL / 1e4
EV_YEAR = 24
H_SEL = 0.5
G1_HOLDOUT = 2.38
MT5_START, MT5_END = pd.Timestamp("2018-01-02"), pd.Timestamp("2025-05-30")
PERIODS = [(n, pd.Timestamp(f"{a}-01-01"), pd.Timestamp(f"{b}-12-31")) for n, a, b in V.FOLDS]
PERIODS[-1] = ("2022-24 S1", pd.Timestamp("2022-01-01"), pd.Timestamp("2024-06-30"))
PERIODS.append(("holdout", H.HOLDOUT_START, H.LAST_EVENT))
INTERVENTIONS = ["2010-09-15", "2011-03-18", "2011-08-04", "2011-10-31", "2011-11-01", "2011-11-02",
                 "2011-11-03", "2011-11-04", "2022-09-22", "2022-10-21", "2022-10-24", "2024-04-29",
                 "2024-05-01", "2024-07-11", "2024-07-12"]
VERNAL = {2007: 21, 2008: 20, 2009: 20, 2010: 21, 2011: 21, 2012: 20, 2013: 20, 2014: 21, 2015: 21,
          2016: 20, 2017: 20, 2018: 21, 2019: 21, 2020: 20, 2021: 20, 2022: 21, 2023: 21, 2024: 20,
          2025: 20, 2026: 20}
AUTUMNAL = {2007: 23, 2008: 23, 2009: 23, 2010: 23, 2011: 23, 2012: 22, 2013: 23, 2014: 23, 2015: 23,
            2016: 22, 2017: 23, 2018: 23, 2019: 23, 2020: 22, 2021: 23, 2022: 23, 2023: 23, 2024: 22,
            2025: 23, 2026: 23}
N_BOOT, BLOCK = 20_000, 6
RNG = np.random.default_rng(20261019)


def hac_se(x, lags: int = 6) -> float:
    """Erreur-type de Newey-West de la moyenne (même noyau que `s2_holdout.hac_t`)."""
    x = np.asarray(pd.Series(x).dropna(), dtype=float)
    n = len(x)
    e = x - x.mean()
    s = e @ e / n
    for L in range(1, lags + 1):
        s += 2 * (1 - L / (lags + 1)) * (e[L:] @ e[:-L]) / n
    return float(np.sqrt(s / n))


def jp_holidays(y0: int = 2007, y1: int = 2026) -> set:
    """Fériés japonais approchés : `flows/code/f6f_jp_holiday.py`, équinoxes étendues à 2025-2026."""
    def nth_monday(y, m, n):
        d = pd.date_range(f"{y}-{m:02d}-01", periods=31, freq="D")
        return d[(d.month == m) & (d.weekday == 0)][n - 1]

    h = set()
    for y in range(y0, y1 + 1):
        fixed = [(1, 1), (1, 2), (1, 3), (2, 11), (4, 29), (5, 3), (5, 4), (5, 5), (11, 3), (11, 23), (12, 31),
                 (3, VERNAL[y]), (9, AUTUMNAL[y])]
        if y == 2019:
            fixed += [(4, 30), (5, 1), (5, 2), (10, 22)]
        if y in (2009, 2015, 2026):
            fixed.append((9, 22))
        if y <= 2018:
            fixed.append((12, 23))
        if y >= 2020:
            fixed.append((2, 23))
        if y >= 2016:
            fixed.append((8, 11))
        for m, dd in fixed:
            x = pd.Timestamp(y, m, dd)
            h.add(x)
            if x.weekday() == 6:
                h.add(x + pd.Timedelta(days=1))
        for m, n in ((1, 2), (7, 3), (9, 3), (10, 2)):
            if y in (2020, 2021) and m in (7, 10):
                continue
            h.add(nth_monday(y, m, n))
        if y == 2020:
            h |= {pd.Timestamp("2020-07-23"), pd.Timestamp("2020-07-24"), pd.Timestamp("2020-08-10")}
        if y == 2021:
            h |= {pd.Timestamp("2021-07-22"), pd.Timestamp("2021-07-23"), pd.Timestamp("2021-08-09")}
        if any(pd.Timestamp(y, 5, k).weekday() == 6 for k in (3, 4, 5)):
            h.add(pd.Timestamp(y, 5, 6))
    return h


def build_events(df: pd.DataFrame) -> pd.DataFrame:
    days = pd.DatetimeIndex(sorted(set(df.index.normalize())))
    days = days[(days.weekday < 5) & (days <= H.LAST_EVENT)]
    ev = V.events(df, days)
    ns = pd.DataFrame({x: (H.leg(df, x, -60, 54, 1, None), H.leg(df, x, 56, 120, -1, None)) for x in ev.index},
                      index=["pre_ns", "post_ns"]).T
    ev = ev.join(ns)
    ev["both_ns"] = ev["pre_ns"] + ev["post_ns"]
    ev = ev.dropna(subset=["both"])
    ev["isD"] = ev["cat"].isin(V.D_CATS)
    ev["stopA"] = (ev["pre"] - ev["pre_ns"]).abs() > 1e-9
    ev["stopB"] = (ev["post"] - ev["post_ns"]).abs() > 1e-9
    ev["gapA"] = ev["pre"] < -H.STOP_BPS - 1e-6
    ev["gapB"] = ev["post"] < -H.STOP_BPS - 1e-6
    ev["wd"] = ev.index.weekday
    hol = jp_holidays()
    ev["jp_hol"] = [x in hol for x in ev.index]
    ev["seg"] = np.where(ev.index < MT5_START, "Duka 2007-17", np.where(ev.index <= MT5_END, "MT5 2018-25", "Duka 2025-26"))
    ev["period"] = None
    for name, a, b in PERIODS:
        ev.loc[(ev.index >= a) & (ev.index <= b), "period"] = name
    return ev, days


def stats(x) -> dict:
    x = pd.Series(x).dropna()
    return dict(n=int(len(x)), mean=float(x.mean()), se=hac_se(x) if len(x) > 7 else np.nan)


def dersimonian_laird(m: np.ndarray, se: np.ndarray) -> dict:
    w = 1 / se ** 2
    fe = float((w * m).sum() / w.sum())
    q = float((w * (m - fe) ** 2).sum())
    k = len(m)
    tau2 = max(0.0, (q - (k - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
    ws = 1 / (se ** 2 + tau2)
    mu = float((ws * m).sum() / ws.sum())
    se_mu = float(np.sqrt(1 / ws.sum()))
    return dict(fe=fe, Q=q, df=k - 1, tau2=tau2, tau=float(np.sqrt(tau2)), mu=mu, se=se_mu,
                pred_sd=float(np.sqrt(se_mu ** 2 + tau2)))


def block_sums(x: np.ndarray, n_ev: int) -> np.ndarray:
    """Sommes de n_ev événements tirés par blocs circulaires de BLOCK (bootstrap de Politis-Romano)."""
    n = len(x)
    nb = int(np.ceil(n_ev / BLOCK))
    starts = RNG.integers(0, n, size=(N_BOOT, nb))
    idx = (starts[:, :, None] + np.arange(BLOCK)[None, None, :]) % n
    return x[idx.reshape(N_BOOT, -1)[:, :n_ev]].sum(axis=1)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = V.load(dry=False)
    ev, days = build_events(df)
    ev.to_csv(OUT / "s2_deep_events.csv")
    D = ev[ev["isD"]]
    res: dict = {}
    L: list[str] = []

    # --- 0. Contrôle : on retrouve les chiffres publiés ---
    pub = json.loads((V.OUT / "s2_validation.json").read_text())["etape1"]
    disc_D = D.loc[D.index < H.HOLDOUT_START, "both"]
    hold_D = D.loc[D.index >= H.HOLDOUT_START, "both"]
    fold_ok = all(abs(D.loc[D["period"] == f["fold"], "both"].mean() - f["D"]) < 1e-6 for f in pub["folds"])
    ok = abs(disc_D.mean() - pub["D"]["mean"]) < 1e-6 and abs(hold_D.mean() - 6.195) < 0.001 and fold_ok \
        and len(D) == 462
    L.append(f"Contrôle : D découverte {disc_D.mean():.3f} (publié {pub['D']['mean']:.3f}), holdout {hold_D.mean():.3f} "
             f"(publié 6.195), 6 plis identiques {fold_ok}, n D {len(D)} (publié 462) → {'OK' if ok else 'ÉCHEC'}")
    if not ok:
        (OUT / "s2_deep.txt").write_text("\n".join(L) + "\nArrêt.\n")
        sys.exit(1)

    # --- 1. Sensibilité au coût ---
    per = [("2007-2015", "2007-01-01", "2015-12-31"), ("2016-2024 S1", "2016-01-01", "2024-06-30"),
           ("holdout 2024-07 → 2026-05", "2024-07-01", "2026-05-31"), ("tout 2007-2026", "2007-01-01", "2026-05-31")]
    L += ["", "1. Coût — D, net par événement (bps) et $/an (24 événements, 2,5× l'équité, avant partage)"]
    L.append(f"  {'période':27s} {'n':>4s} {'brut':>6s} | " + " | ".join(f"coût {c:.2f} : net, $/an, ratio" for c in COSTS))
    res["cost"] = []
    for name, a, b in per:
        x = D.loc[a:b, "both"]
        row = dict(period=name, n=len(x), gross=float(x.mean()))
        cells = []
        for c in COSTS:
            net = x.mean() - c
            row[f"net_{c}"] = float(net)
            row[f"usd_year_{c}"] = float(net * EV_YEAR * USD_PER_BP)
            cells.append(f"{net:+5.2f}, {net * EV_YEAR * USD_PER_BP:+5.0f} $, {x.mean() / c:4.2f}×")
        res["cost"].append(row)
        L.append(f"  {name:27s} {len(x):4d} {x.mean():+6.2f} | " + " | ".join(cells))

    # --- 2. Jambes par période et par source ---
    L += ["", "2. Jambes de D par période (bps) : achat avant le fixing / vente après / total"]
    res["legs"] = {}
    for name, a, b in PERIODS:
        x = D[(D.index >= a) & (D.index <= b)]
        res["legs"][name] = dict(n=len(x), pre=float(x["pre"].mean()), post=float(x["post"].mean()),
                                 both=float(x["both"].mean()))
        L.append(f"  {name:11s} n {len(x):3d}  achat {x['pre'].mean():+5.2f}  vente {x['post'].mean():+5.2f}  "
                 f"total {x['both'].mean():+5.2f}")
    L.append("  par source de données :")
    for s, g in D.groupby("seg", sort=False):
        L.append(f"    {s:13s} n {len(g):3d}  achat {g['pre'].mean():+5.2f}  vente {g['post'].mean():+5.2f}  "
                 f"total {g['both'].mean():+5.2f}")
    res["legs_by_source"] = {s: dict(n=len(g), pre=float(g["pre"].mean()), post=float(g["post"].mean()))
                             for s, g in D.groupby("seg")}

    # --- 3. Stop ---
    L += ["", "3. Stop 25 bps — D avec et sans stop (bps), stops touchés, remplis au-delà du niveau (gap)"]
    res["stop"] = {}
    for name, a, b in PERIODS + [("tout", pd.Timestamp("2007-01-01"), H.LAST_EVENT)]:
        x = D[(D.index >= a) & (D.index <= b)]
        r = dict(n=len(x), with_stop=float(x["both"].mean()), no_stop=float(x["both_ns"].mean()),
                 stopA=int(x["stopA"].sum()), stopB=int(x["stopB"].sum()), gaps=int((x["gapA"] | x["gapB"]).sum()))
        res["stop"][name] = r
        L.append(f"  {name:11s} avec {r['with_stop']:+5.2f}  sans {r['no_stop']:+5.2f}  stops achat {r['stopA']:2d}, "
                 f"vente {r['stopB']:2d}  gaps {r['gaps']}")
    sa, sb = D.loc[D["stopA"], "pre"], D.loc[D["stopB"], "post"]
    L.append(f"  jambes stoppées : achat n {len(sa)}, moyenne {sa.mean():+.2f} ; vente n {len(sb)}, moyenne {sb.mean():+.2f} ; "
             f"pire sans stop {D['both_ns'].min():+.1f} bps ({D['both_ns'].idxmin().date()})")

    # --- 4. Distribution et queues ---
    x = D["both"]
    q = x.quantile([.01, .05, .10, .25, .5, .75, .90, .95, .99])
    srt = x.sort_values()
    k10 = int(round(0.1 * len(x)))
    res["dist"] = dict(quantiles={f"{k:.2f}": float(v) for k, v in q.items()}, skew=float(skew(x)),
                       exkurt=float(kurtosis(x)), hit=float((x > 0).mean()), sd=float(x.std()),
                       share_top10=float(srt.iloc[-k10:].sum() / x.sum()),
                       share_bottom10=float(srt.iloc[:k10].sum() / x.sum()))
    L += ["", "4. Distribution de D, brut avec stop (462 événements)",
          "  quantiles 1/5/10/25/50/75/90/95/99 % : " + " / ".join(f"{v:+.1f}" for v in q.values),
          f"  σ {x.std():.1f}  asymétrie {skew(x):+.2f}  kurtosis en excès {kurtosis(x):+.2f}  gagnants {(x > 0).mean():.0%}",
          f"  part du brut total : 10 % meilleurs {res['dist']['share_top10']:+.0%}, 10 % pires {res['dist']['share_bottom10']:+.0%}",
          "  10 pires événements (date, catégorie, jour, achat, vente, total ; sans stop) :"]
    wd = "lun mar mer jeu ven".split()
    for d, r in D.nsmallest(10, "both").iterrows():
        L.append(f"    {d.date()} {r['cat']:4s} {wd[r['wd']]}  {r['pre']:+6.1f} {r['post']:+6.1f} {r['both']:+6.1f} ; "
                 f"sans stop {r['both_ns']:+7.1f}" + ("  [férié JP]" if r["jp_hol"] else ""))
    res["worst10"] = [dict(date=str(d.date()), cat=r["cat"], both=float(r["both"]), both_ns=float(r["both_ns"]))
                      for d, r in D.nsmallest(10, "both").iterrows()]

    # --- 5. Interventions du MoF ---
    pos = {x: i for i, x in enumerate(days)}
    near = set()
    for s in INTERVENTIONS:
        t = pd.Timestamp(s)
        if t in pos:
            near |= {days[j] for j in range(max(0, pos[t] - 1), min(len(days), pos[t] + 2))}
    hit = D[D.index.isin(list(near))]
    res["mof"] = [dict(date=str(d.date()), cat=r["cat"], pre=float(r["pre"]), post=float(r["post"]),
                       both=float(r["both"]), both_ns=float(r["both_ns"])) for d, r in hit.iterrows()]
    L += ["", f"5. Interventions du MoF ({len(INTERVENTIONS)} dates publiques 2010-2024) : événements D à ±1 jour ouvré"]
    for d, r in hit.iterrows():
        L.append(f"    {d.date()} {r['cat']:4s} achat {r['pre']:+6.1f} vente {r['post']:+6.1f} total {r['both']:+6.1f} "
                 f"(sans stop {r['both_ns']:+7.1f})")

    # --- 6. Fériés japonais ---
    jh = D[D["jp_hol"]]
    res["jp_holiday"] = dict(n=len(jh), mean=float(jh["both"].mean()), dates=[str(d.date()) for d in jh.index],
                             other=float(D.loc[~D["jp_hol"], "both"].mean()))
    L += ["", f"6. Fériés japonais (pas de fixing) parmi D : n {len(jh)}, brut {jh['both'].mean():+.2f} "
              f"contre {D.loc[~D['jp_hol'], 'both'].mean():+.2f} les autres jours",
          "    dates : " + ", ".join(f"{d.date()} ({r['both']:+.0f})" for d, r in jh.iterrows())]

    # --- 7. Jour de semaine ---
    L += ["", "7. Jour de semaine de D (brut, bps ; n)"]
    res["weekday"] = {}
    for lab, sub in (("tout", D), ("depuis 2016", D[D.index >= "2016-01-01"])):
        g = sub.groupby("wd")["both"].agg(["mean", "size"])
        res["weekday"][lab] = {wd[i]: dict(mean=float(m), n=int(n)) for i, (m, n) in g.iterrows()}
        L.append(f"  {lab:12s} " + "  ".join(f"{wd[i]} {m:+5.2f} ({n})" for i, (m, n) in g.iterrows()))

    # --- 8. 2026 S1 ---
    s26 = D[D.index >= "2026-01-01"]
    L += ["", f"8. 2026 S1 : {len(s26)} événements D, brut {s26['both'].mean():+.2f} (achat {s26['pre'].mean():+.2f}, "
              f"vente {s26['post'].mean():+.2f})"]
    for d, r in s26.iterrows():
        L.append(f"    {d.date()} {r['cat']:4s} {wd[r['wd']]}  achat {r['pre']:+6.1f}  vente {r['post']:+6.1f}  "
                 f"total {r['both']:+6.1f}" + ("  [stop]" if r["stopA"] or r["stopB"] else ""))
    res["s2026"] = dict(n=len(s26), mean=float(s26["both"].mean()), pre=float(s26["pre"].mean()),
                        post=float(s26["post"].mean()))

    # --- 9. Années perdantes (net à 1,87) ---
    yr = (D["both"] - H.COST_EVENT).groupby(D.index.year).sum() * USD_PER_BP
    full = yr[yr.index <= 2025]
    res["years"] = dict(usd={int(k): float(v) for k, v in yr.items()}, losing_full=int((full < 0).sum()),
                        n_full=int(len(full)), losing_since_2016=int((full[full.index >= 2016] < 0).sum()))
    L += ["", f"9. Années perdantes (net à 1,87 bp, 2,5×) : {res['years']['losing_full']} sur {len(full)} années pleines "
              f"(2007-2025) ; depuis 2016 : {res['years']['losing_since_2016']} sur {int((full.index >= 2016).sum())}"]

    # --- 10. Annonces (L4) ---
    cal = pd.read_csv(CAL, parse_dates=["datetime_utc"])
    hi = cal[(cal["impact"] == "HIGH") & cal["currency"].isin(["JPY", "USD"])]
    D18 = D[D.index >= "2018-01-01"]
    flags, names = [], []
    for d in D18.index:
        w = hi[(hi["datetime_utc"] >= d - pd.Timedelta(days=1) + pd.Timedelta(hours=22, minutes=58)) &
               (hi["datetime_utc"] <= d + pd.Timedelta(hours=2, minutes=2))]
        flags.append(len(w) > 0)
        names.append("; ".join(f"{a} {b} {t:%H:%M}" for a, b, t in zip(w["currency"], w["event"], w["datetime_utc"])))
    D18 = D18.assign(news=flags, news_what=names)
    frac = float(D18["news"].mean())
    res["L4"] = dict(n_D_2018_2026=len(D18), n_skip=int(D18["news"].sum()), frac=frac, pass_=bool(frac <= 0.20),
                     mean_skip=float(D18.loc[D18["news"], "both"].mean()),
                     mean_keep=float(D18.loc[~D18["news"], "both"].mean()),
                     what=D18.loc[D18["news"], "news_what"].value_counts().to_dict())
    L += ["", f"10. Annonces (L4) : D 2018-01 → 2026-05, {len(D18)} événements ; exclus (HIGH JPY/USD entre 22:58 la veille "
              f"et 02:02 UTC) {int(D18['news'].sum())}, soit {frac:.1%} → L4 {'TIENT' if frac <= 0.20 else 'ÉCHOUE'} (≤ 20 %)",
          f"    rapporté sans décider : brut des jours exclus {res['L4']['mean_skip']:+.2f} (n {int(D18['news'].sum())}), "
          f"des jours gardés {res['L4']['mean_keep']:+.2f}",
          "    annonces en cause : " + " | ".join(f"{k} ×{v}" for k, v in res["L4"]["what"].items())]
    by_cat = D18[D18["news"]].groupby("cat").size().to_dict()
    L.append(f"    exclus par catégorie : {by_cat}")

    # --- 11. Méta-analyse à effets aléatoires sur 7 périodes ---
    L += ["", "11. Méta-analyse à effets aléatoires (DerSimonian-Laird), 6 plis + holdout, erreurs-types HAC lag 6"]
    res["re"] = {}
    series = {"D": ev[ev["isD"]], "AUTRES": ev[~ev["isD"]], "G1 (tous)": ev}
    tab = {}
    for nm, sub in series.items():
        ms, ses = [], []
        for name, a, b in PERIODS:
            x = sub.loc[(sub.index >= a) & (sub.index <= b), "both"]
            ms.append(x.mean())
            ses.append(hac_se(x))
        tab[nm] = (np.array(ms), np.array(ses))
    tab["contraste D − AUTRES"] = (tab["D"][0] - tab["AUTRES"][0], np.sqrt(tab["D"][1] ** 2 + tab["AUTRES"][1] ** 2))
    is_disc = np.array([p[0] != "holdout" for p in PERIODS])
    for nm, (m, se) in tab.items():
        L.append(f"  {nm:20s} périodes : " + " ".join(f"{v:+5.2f}" for v in m) + "   (SE " +
                 " ".join(f"{v:.2f}" for v in se) + ")")
        for h in ((0.0, H_SEL, 1.0) if nm != "contraste D − AUTRES" else (0.0,)):
            r = dersimonian_laird(m - h * is_disc, se)
            res["re"][f"{nm} | h={h}"] = r
            L.append(f"      h {h:.1f} : μ_RE {r['mu']:+5.2f} (SE {r['se']:.2f}) ; Q {r['Q']:.1f} sur {r['df']} ddl ; "
                     f"τ {r['tau']:.2f} ; écart-type prédictif {r['pred_sd']:.2f}")

    # --- 12. Scénarios prospectifs ---
    reD = res["re"][f"D | h={H_SEL}"]
    recent = float(D.loc["2016-01-01":, "both"].mean()) - H_SEL
    scen = {"érosion": G1_HOLDOUT, "central": reD["mu"], "régime récent": recent}
    xnet0 = D["both"].to_numpy()
    L += ["", "12. Scénarios prospectifs (brut par événement ; net ; $/an avant partage ; P(année perdante) ; "
              "P(perte sur 2 ans)) — bootstrap par blocs de 6 événements, 20 000 tirages"]
    res["scenarios"] = {}
    for sn, g in scen.items():
        for c in COSTS:
            target = g - c
            xc = xnet0 - xnet0.mean() + target
            s1, s2 = block_sums(xc, EV_YEAR), block_sums(xc, 2 * EV_YEAR)
            r = dict(gross=float(g), cost=c, net=float(target), usd_year=float(target * EV_YEAR * USD_PER_BP),
                     sd_year_usd=float(s1.std() * USD_PER_BP), p_lose_1y=float((s1 < 0).mean()),
                     p_lose_2y=float((s2 < 0).mean()))
            res["scenarios"][f"{sn} | {c}"] = r
            L.append(f"  {sn:14s} coût {c:.2f} : brut {g:+5.2f}  net {target:+5.2f}  {r['usd_year']:+5.0f} $/an "
                     f"(σ {r['sd_year_usd']:.0f})  P(an perdant) {r['p_lose_1y']:.0%}  P(2 ans perdants) {r['p_lose_2y']:.0%}")

    # --- 13. Règle de décision L1-L5 (L5 : voir s2_ea_logs.py) ---
    net_c = reD["mu"] - 1.87
    p_pos = float(norm.cdf(net_c / reD["pred_sd"]))
    l1 = net_c >= 1.5 and p_pos >= 0.80
    l2 = reD["mu"] - 2.5 >= 0
    loss_eros = -min(0.0, (G1_HOLDOUT - 2.5) * EV_YEAR * USD_PER_BP)
    l3 = loss_eros <= 60
    l4 = res["L4"]["pass_"]
    res["decision"] = dict(L1=dict(net_central=net_c, p_net_pos=p_pos, ok=bool(l1)),
                           L2=dict(net_at_2_5=reD["mu"] - 2.5, ok=bool(l2)),
                           L3=dict(expected_loss_usd_year=loss_eros, ok=bool(l3)), L4=dict(ok=bool(l4)))
    L += ["", "13. Règle de décision (PREREG_DEEP §5 ; L5 dans s2_ea_logs.txt)",
          f"  L1 net central {net_c:+.2f} bp (≥ 1,5) et P(net > 0) {p_pos:.3f} (≥ 0,80) → {'TIENT' if l1 else 'ÉCHOUE'}",
          f"  L2 net central au coût 2,5 : {reD['mu'] - 2.5:+.2f} (≥ 0) → {'TIENT' if l2 else 'ÉCHOUE'}",
          f"  L3 perte attendue, érosion au coût 2,5 : {loss_eros:.0f} $/an (≤ 60) → {'TIENT' if l3 else 'ÉCHOUE'}",
          f"  L4 part des événements exclus {frac:.1%} (≤ 20 %) → {'TIENT' if l4 else 'ÉCHOUE'}"]

    # --- 14. Caractéristiques de la règle d'arrêt live (descriptif, pour la spécification) ---
    L += ["", "14. Règle d'arrêt live — probabilité d'arrêt selon le vrai net (bootstrap par blocs, nets recentrés)",
          "  règle : arrêt si net moyen live < −4 bps à 24 événements, ou < 0 à 48 événements"]
    res["stop_rule"] = {}
    for true_net in (4.3, round(net_c, 2), 0.5, 0.0, -2.0):
        xc = xnet0 - xnet0.mean() + true_net
        n = len(xc)
        starts = RNG.integers(0, n, size=(N_BOOT, 8))
        idx = ((starts[:, :, None] + np.arange(BLOCK)[None, None, :]) % n).reshape(N_BOOT, -1)
        path = xc[idx]
        m24, m48 = path[:, :24].mean(axis=1), path[:, :48].mean(axis=1)
        p24 = float((m24 < -4).mean())
        p48 = float(((m24 < -4) | (m48 < 0)).mean())
        res["stop_rule"][str(true_net)] = dict(p_stop_24=p24, p_stop_by_48=p48)
        L.append(f"  vrai net {true_net:+5.2f} bps : arrêt à 24 {p24:.0%} ; arrêt d'ici 48 {p48:.0%}")

    # --- 15. Queue à la taille déployée ---
    w = float(D["both"].min())
    res["tail"] = dict(worst_bps=w, worst_usd=w * USD_PER_BP, worst_usd_slip2=2 * w * USD_PER_BP)
    L += ["", f"15. Queue : pire événement D {w:+.1f} bps → {w * USD_PER_BP:+.0f} $ à 2,5× ; "
              f"glissement du stop ×2 : {2 * w * USD_PER_BP:+.0f} $ (perte journalière max 500 $)"]

    (OUT / "s2_deep.json").write_text(json.dumps(res, indent=1, default=float, ensure_ascii=False))
    (OUT / "s2_deep.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
