"""S2 — gotobi USDJPY dosé par le calendrier des règlements : lecture unique du holdout.

Pré-enregistrement : ../PREREG.md, commité avant tout lancement. Le script vérifie d'abord qu'il
retrouve l'agrégat G1 publié sur la découverte, puis lit le holdout une seule fois, pour S2 et
pour les statistiques gelées de PR-C. `gotobi_days`, `leg` et `jp_holidays` sont copiés de
`alpha_hunt_2026-10/flows/code/` (f6_gotobi, f6d_gotobi_stop, f6f_jp_holiday).

Usage : /usr/bin/python3 s2_holdout.py      (à ne lancer qu'une fois)
        /usr/bin/python3 s2_holdout.py --dry <dossier>   (essai à blanc : prix remplacés par une
        marche aléatoire avant tout calcul, sorties dans <dossier> ; ne lit aucun rendement réel)
Sorties : ../out/s2_holdout.txt, ../out/s2_holdout.json, ../out/s2_holdout_events.csv
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
SRC = Path(os.environ.get("RESEARCH_DATA_ROOT", "data") + "/deep_history_utc/USDJPY_M1.csv")
HOLDOUT_START = pd.Timestamp("2024-07-01")
LAST_EVENT = pd.Timestamp("2026-05-31")
STOP_BPS = 25.0
COST_EVENT = 1.87
GATE = 3 * COST_EVENT
NOTIONAL_X = 2.5
EQUITY = 9914.0
PUBLISHED_G1 = dict(mean=4.05, t=6.87)
SHIFTS = (-4, -3, -2, -1, 1, 2, 3, 4)


def hac_t(x, lags: int = 6) -> float:
    """t de Newey-West de la moyenne (copie de flows/code/common.py)."""
    x = np.asarray(pd.Series(x).dropna(), dtype=float)
    n = len(x)
    if n < 5:
        return np.nan
    e = x - x.mean()
    s = e @ e / n
    for L in range(1, lags + 1):
        s += 2 * (1 - L / (lags + 1)) * (e[L:] @ e[:-L]) / n
    return float(x.mean() / np.sqrt(s / n))


def gotobi_days(days: pd.DatetimeIndex):
    """Calendrier gotobi ouvré (week-ends reportés au jour précédent ; fériés JP ignorés)."""
    bd = pd.Series(days, index=days)
    out, me = set(), set()
    for _, g in bd.groupby([days.year, days.month]):
        me.add(g.index.max())
        out.add(g.index.max())
        for dom in (5, 10, 15, 20, 25):
            cand = g.index[g.index.day <= dom]
            if len(cand):
                out.add(cand.max())
    return out, me


def categories(days: pd.DatetimeIndex) -> pd.Series:
    """DME, D25 ou AUTRES par jour gotobi ; la catégorie la plus dosée l'emporte."""
    cat: dict = {}
    bd = pd.Series(days, index=days)
    for _, g in bd.groupby([days.year, days.month]):
        for dom in (5, 10, 15, 20):
            c = g.index[g.index.day <= dom]
            if len(c):
                cat.setdefault(c.max(), "AUTRES")
        c = g.index[g.index.day <= 25]
        if len(c):
            cat[c.max()] = "D25"
        cat[g.index.max()] = "DME"
    return pd.Series(cat).sort_index()


def leg(d: pd.DataFrame, day, a: int, b: int, side: int, stop):
    """Une jambe, en bps (copie de f6d_gotobi_stop.leg)."""
    w = d.loc[day + pd.Timedelta(minutes=a): day + pd.Timedelta(minutes=b - 1)]
    if len(w) < 0.8 * (b - a) or w.index[0] != day + pd.Timedelta(minutes=a):
        return np.nan
    e = w["open"].iloc[0]
    xe = d["open"].get(day + pd.Timedelta(minutes=b), np.nan)
    if np.isnan(xe):
        return np.nan
    if stop is not None:
        lvl = e * (1 - side * stop / 1e4)
        for o, h, l in zip(w["open"].values, w["high"].values, w["low"].values):
            if side > 0 and (o <= lvl or l <= lvl):
                return side * (min(o, lvl) / e - 1) * 1e4
            if side < 0 and (o >= lvl or h >= lvl):
                return side * (max(o, lvl) / e - 1) * 1e4
    return side * (xe / e - 1) * 1e4


class Events:
    """Cache des deux jambes G1 par jour (avec stop), et des variantes sans stop."""

    def __init__(self, d: pd.DataFrame):
        self.d, self.cache = d, {}

    def g1(self, day) -> tuple[float, float]:
        if day not in self.cache:
            self.cache[day] = (leg(self.d, day, -60, 54, 1, STOP_BPS), leg(self.d, day, 56, 120, -1, STOP_BPS))
        return self.cache[day]

    def frame(self, days) -> pd.DataFrame:
        f = pd.DataFrame([self.g1(x) for x in days], index=pd.DatetimeIndex(days), columns=["pre", "post"])
        f["both"] = f["pre"] + f["post"]
        return f


def jp_holidays(y0: int, y1: int) -> set:
    """Fériés japonais approchés (copie de f6f_jp_holiday.py, équinoxes étendues à 2025-2026)."""
    vernal = {2024: 20, 2025: 20, 2026: 20}
    autumnal = {2024: 22, 2025: 23, 2026: 23}

    def nth_monday(y, m, n):
        d = pd.date_range(f"{y}-{m:02d}-01", periods=31, freq="D")
        return d[(d.month == m) & (d.weekday == 0)][n - 1]

    h = set()
    for y in range(y0, y1 + 1):
        fixed = [(1, 1), (1, 2), (1, 3), (2, 11), (2, 23), (4, 29), (5, 3), (5, 4), (5, 5), (8, 11),
                 (11, 3), (11, 23), (12, 31), (3, vernal[y]), (9, autumnal[y])]
        for m, dd in fixed:
            x = pd.Timestamp(y, m, dd)
            h.add(x)
            if x.weekday() == 6:
                h.add(x + pd.Timedelta(days=1))
        for m, n in ((1, 2), (7, 3), (9, 3), (10, 2)):
            h.add(nth_monday(y, m, n))
        if any(pd.Timestamp(y, 5, k).weekday() == 6 for k in (3, 4, 5)):
            h.add(pd.Timestamp(y, 5, 6))
    return h


def stats(x: pd.Series) -> dict:
    x = x.dropna()
    n = len(x)
    sd = float(x.std()) if n > 1 else np.nan
    return dict(n=n, mean=float(x.mean()) if n else np.nan, sd=sd, t_hac=hac_t(x),
                mde80=2.8 * sd / np.sqrt(n) if n > 1 else np.nan,
                worst=float(x.min()) if n else np.nan)


def shifted_anchor_days(days_all: pd.DatetimeIndex, months, anchors, k: int) -> set:
    """Dernier jour ouvré ≤ ancre + k, pour chaque mois de `months` (construction de f6b)."""
    out = set()
    bd = pd.Series(days_all, index=days_all)
    for (y, m), g in bd.groupby([days_all.year, days_all.month]):
        if (y, m) not in months:
            continue
        for dom in anchors:
            cand = g.index[g.index.day <= dom + k]
            if len(cand):
                out.add(cand.max())
    return out


def main(out: Path, dry: bool) -> None:
    out.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SRC, usecols=["timestamp_utc", "open", "high", "low", "close"])
    df.index = pd.to_datetime(df.pop("timestamp_utc"), format="%Y.%m.%d %H:%M:%S")
    df = df[~df.index.duplicated()]
    assert df.index.is_monotonic_increasing
    if dry:
        p = 150.0 * np.exp(np.cumsum(np.random.default_rng(0).normal(0.0, 2e-4, len(df))))
        df = pd.DataFrame({"open": p, "high": p * (1 + 1e-4), "low": p * (1 - 1e-4), "close": p}, index=df.index)
    lines = ["ESSAI À BLANC (prix synthétiques)"] if dry else []

    # --- 1. Contrôle d'implémentation sur la découverte : agrégat G1 seulement ---
    disc = df[df.index < HOLDOUT_START]
    ddays = pd.DatetimeIndex(sorted(set(disc.index.normalize())))
    ddays = ddays[ddays.weekday < 5]
    dset, _ = gotobi_days(ddays)
    dev = Events(disc).frame([x for x in ddays if x in dset])
    dchk = stats(dev["both"])
    ok = abs(dchk["mean"] - PUBLISHED_G1["mean"]) < 0.01 and abs(dchk["t_hac"] - PUBLISHED_G1["t"]) < 0.01
    lines.append(f"Contrôle découverte (G1 agrégé) : n {dchk['n']}, brut {dchk['mean']:.3f} bps, "
                 f"t HAC {dchk['t_hac']:.3f} — publié 4,05 / 6,87 → {'OK' if ok else 'ÉCHEC'}")
    if not ok and not dry:
        (out / "s2_holdout.txt").write_text("\n".join(lines) + "\nArrêt : le holdout n'est pas lu.\n")
        print("\n".join(lines))
        sys.exit(1)

    # --- 2. Holdout ---
    hold = df[df.index >= HOLDOUT_START - pd.Timedelta(hours=2)]
    days_all = pd.DatetimeIndex(sorted(set(hold.index.normalize())))
    days_all = days_all[(days_all.weekday < 5) & (days_all >= HOLDOUT_START)]
    hdays = days_all[days_all <= LAST_EVENT]
    gset, meset = gotobi_days(hdays)
    gset_all, _ = gotobi_days(days_all)
    true_g = gset | gset_all
    cat = categories(hdays)
    assert set(cat.index) == gset and set(cat[cat == "DME"].index) == meset
    E = Events(hold)
    ev = E.frame(cat.index)
    ev["cat"] = cat
    ev.to_csv(out / "s2_holdout_events.csv")
    months = {(x.year, x.month) for x in hdays}
    res: dict = {"window": [str(hdays.min().date()), str(hdays.max().date())],
                 "discovery_check": dchk, "gate_bps": GATE}

    # --- 3. S2 : décision ---
    isD = ev["cat"].isin(["D25", "DME"])
    D, oth = ev[isD], ev[ev["cat"] == "AUTRES"]
    sD, sO = stats(D["both"]), stats(oth["both"])
    legs = {"pre": float(D["pre"].mean()), "post": float(D["post"].mean())}
    k1, k2, k3 = sD["mean"] < GATE, sD["mean"] <= sO["mean"], min(legs.values()) < 0
    verdict = "TUÉE" if (k1 or k2 or k3) else "NON TUÉE"
    res["S2"] = dict(D=sD, AUTRES=sO, D_legs=legs, D25=stats(ev.loc[ev["cat"] == "D25", "both"]),
                     DME=stats(ev.loc[ev["cat"] == "DME", "both"]), K1=bool(k1), K2=bool(k2),
                     K3=bool(k3), verdict=verdict)
    lines += ["", f"Holdout : {hdays.min().date()} → {hdays.max().date()}, {len(ev)} jours gotobi, "
                  f"{int(ev['both'].notna().sum())} événements complets",
              "", "S2 — décision (porte 3 × 1,87 = 5,61 bps)"]
    for nm, s in (("D = D25 ∪ DME", sD), ("  D25", res["S2"]["D25"]), ("  DME", res["S2"]["DME"]),
                  ("AUTRES (5, 10, 15, 20)", sO)):
        lines.append(f"  {nm:24s} n {s['n']:3d}  brut {s['mean']:+6.2f} bps  σ {s['sd']:5.1f}  "
                     f"t HAC {s['t_hac']:+5.2f}  MDE80 {s['mde80']:5.2f}  pire {s['worst']:+6.1f}")
    lines += [f"  jambes sur D : achat {legs['pre']:+.2f}, vente {legs['post']:+.2f}",
              f"  K1 (D < 5,61) {k1} ; K2 (D ≤ AUTRES) {k2} ; K3 (une jambe < 0) {k3}",
              f"  → S2 {verdict}"]

    # --- 4. S2 : à rapporter sans décider ---
    by_year = {str(y): stats(g["both"]) for y, g in D.groupby(D.index.year)}
    res["S2"]["D_by_year"] = by_year
    lines.append("  D par année : " + " ; ".join(f"{y} {s['mean']:+.2f} (n {s['n']})" for y, s in by_year.items()))
    uncond = E.frame(hdays)["both"]
    pos = {x: i for i, x in enumerate(days_all)}
    me_list = sorted(meset)
    plac = []
    for k in SHIFTS:
        d25 = shifted_anchor_days(days_all, months, (25,), k)
        dme = {days_all[pos[x] + k] for x in me_list if 0 <= pos[x] + k < len(days_all)}
        pdays = sorted((d25 | dme) - true_g)
        m = float(E.frame(pdays)["both"].mean())
        plac.append(dict(k=k, n=len(pdays), mean=m))
    pool = float(np.mean([p["mean"] for p in plac]))
    rank = 1 + sum(p["mean"] > sD["mean"] for p in plac)
    res["S2"]["placebo"] = dict(shifts=plac, pool_mean=pool, uncond_mean=float(uncond.mean()), rank_of_9=rank)
    lines.append("  placebos D décalés : " + " ; ".join(f"k{p['k']:+d} {p['mean']:+.2f} (n {p['n']})" for p in plac))
    lines.append(f"  vrai D au rang {rank}/9 ; pool {pool:+.2f} contre inconditionnel {uncond.mean():+.2f} "
                 f"(n {int(uncond.notna().sum())}, contrôle L58)")
    worst = sD["worst"]
    lines.append(f"  pire événement D {worst:+.1f} bps → à {NOTIONAL_X}× l'équité : {worst * NOTIONAL_X / 100:+.2f} % "
                 f"({worst * NOTIONAL_X / 1e4 * EQUITY:+.0f} $)")
    w = hold[(hold.index.hour == 23) | (hold.index.hour <= 1)]
    w = w[w.index <= LAST_EVENT + pd.Timedelta(days=1)]
    z = (w["high"] == w["low"]).groupby(w.index.year).mean()
    res["L60_zero_range_23_02"] = {str(y): float(v) for y, v in z.items()}
    lines.append("  L60, part de barres à fourchette nulle 23:00-02:00 UTC : "
                 + " ".join(f"{y} {v:.3f}" for y, v in z.items()))

    # --- 5. Statistiques gelées de PR-C (rapportées, hors verdict S2) ---
    allg = stats(ev["both"])
    glegs = {"pre": float(ev["pre"].mean()), "post": float(ev["post"].mean())}
    pc = []
    for k in SHIFTS:
        pdays = sorted(shifted_anchor_days(days_all, months, (5, 10, 15, 20, 25), k) - true_g)
        pc.append(dict(k=k, n=len(pdays), mean=float(E.frame(pdays)["both"].mean())))
    pmeans = [p["mean"] for p in pc]
    rank_g = 1 + sum(m > allg["mean"] for m in pmeans)
    K1, K2, K3 = allg["mean"] <= 0, max(glegs.values()) < 0, allg["mean"] < float(np.median(pmeans))
    survie = allg["mean"] >= 2.0 and min(glegs.values()) >= 0 and rank_g <= 3
    confirm = allg["t_hac"] >= 2.0
    hol = jp_holidays(2024, 2026)
    on_h = ev.index.isin(list(hol))
    nofix = pd.Series({x: leg(hold, x, -60, 54, 1, None) + leg(hold, x, 56, 120, -1, None) for x in ev.index})
    withfix = pd.Series({x: leg(hold, x, -60, 55, 1, None) + leg(hold, x, 55, 120, -1, None) for x in ev.index})
    share_fix = float(1 - nofix.mean() / withfix.mean()) if withfix.mean() != 0 else np.nan
    res["PR_C"] = dict(all=allg, legs=glegs, placebo=pc, placebo_pool=float(np.mean(pmeans)),
                       rank_of_9=rank_g, K1=bool(K1), K2=bool(K2), K3=bool(K3), survie=bool(survie),
                       confirmation=bool(confirm), jp_holiday=stats(ev.loc[on_h, "both"]),
                       not_holiday=stats(ev.loc[~on_h, "both"]), no_stop_g1=float(nofix.mean()),
                       no_stop_with_fix_minute=float(withfix.mean()), fix_minute_share=share_fix)
    lines += ["", "PR-C (G1, tous les gotobi du holdout) — rapporté, hors verdict S2",
              f"  n {allg['n']}  brut {allg['mean']:+.2f} bps  t HAC {allg['t_hac']:+.2f}  MDE80 {allg['mde80']:.2f}  "
              f"pire {allg['worst']:+.1f} ; jambes achat {glegs['pre']:+.2f}, vente {glegs['post']:+.2f}",
              "  placebos décalés : " + " ; ".join(f"k{p['k']:+d} {p['mean']:+.2f} (n {p['n']})" for p in pc),
              f"  vrai calendrier au rang {rank_g}/9 ; pool {np.mean(pmeans):+.2f} contre inconditionnel {uncond.mean():+.2f}",
              f"  K1 {K1} ; K2 {K2} ; K3 {K3} ; SURVIE {survie} ; CONFIRMATION (t ≥ 2) {confirm}",
              f"  fériés japonais : {res['PR_C']['jp_holiday']['mean']:+.2f} (n {res['PR_C']['jp_holiday']['n']}) ; "
              f"autres {res['PR_C']['not_holiday']['mean']:+.2f} (n {res['PR_C']['not_holiday']['n']})",
              f"  sans stop : G1 {nofix.mean():+.2f}, avec la minute du fixing {withfix.mean():+.2f} "
              f"(part de la minute {share_fix:.0%})"]
    (out / "s2_holdout.json").write_text(json.dumps(res, indent=1, default=float))
    (out / "s2_holdout.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--dry":
        main(Path(sys.argv[2]), dry=True)
    else:
        main(OUT, dry=False)
