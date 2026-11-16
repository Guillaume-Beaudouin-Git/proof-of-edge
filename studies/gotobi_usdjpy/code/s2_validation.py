"""S2 — validation : la dose sur la découverte (walk-forward, 6 plis) et l'admission au funded.

Pré-enregistrement : ../PREREG_VALIDATION.md, commité avant le lancement. Les règles de trade et
le calendrier viennent de `s2_holdout.py`. Les fonctions d'admission viennent de
`p2_funded/code/admission.py`, importées telles quelles.

Usage : /usr/bin/python3 s2_validation.py                  (à ne lancer qu'une fois)
        /usr/bin/python3 s2_validation.py --dry <dossier>   (essai à blanc : prix USDJPY synthétiques)
Sorties : ../out/s2_validation.txt, ../out/s2_validation.json
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "p2_funded" / "code"))
import admission as A  # noqa: E402
import s2_holdout as H  # noqa: E402

OUT = HERE.parent / "out"
FOLDS = [("2007-09", "2007", "2009"), ("2010-12", "2010", "2012"), ("2013-15", "2013", "2015"),
         ("2016-18", "2016", "2018"), ("2019-21", "2019", "2021"), ("2022-24 S1", "2022", "2024")]
NOTIONAL = 2.5 * 9914.0
WIN_START, WIN_END = pd.Timestamp("2013-10-01"), pd.Timestamp("2026-05-29")
WORST_CAP = -0.015 * 9914.0
D_CATS = ("D25", "DME")


def load(dry: bool) -> pd.DataFrame:
    df = pd.read_csv(H.SRC, usecols=["timestamp_utc", "open", "high", "low", "close"])
    df.index = pd.to_datetime(df.pop("timestamp_utc"), format="%Y.%m.%d %H:%M:%S")
    df = df[~df.index.duplicated()]
    assert df.index.is_monotonic_increasing
    if dry:
        p = 150.0 * np.exp(np.cumsum(np.random.default_rng(1).normal(0.0, 2e-4, len(df))))
        df = pd.DataFrame({"open": p, "high": p * (1 + 1e-4), "low": p * (1 - 1e-4), "close": p}, index=df.index)
    return df


def events(d: pd.DataFrame, days: pd.DatetimeIndex) -> pd.DataFrame:
    cat = H.categories(days)
    assert set(cat.index) == H.gotobi_days(days)[0]
    ev = H.Events(d).frame(cat.index)
    ev["cat"] = cat
    return ev


def admission(base: pd.Series, sleeve: pd.Series, label: str) -> dict:
    b, a = base.to_numpy(), sleeve.to_numpy()
    idx = A.block_idx(len(b), A.HORIZON, A.N_MC)
    d = A.delta_sr(b, a)
    mb, mc = A.floor_mc(b, idx), A.floor_mc(b + a, idx)
    worst = float(a.min())
    if d["delta"] <= 0 or mc["p_loss"] - mb["p_loss"] > 0.01 or worst < WORST_CAP:
        verdict = "REJET"
    else:
        verdict = "ADMIS" if d["p_le_0"] < 0.05 else "UNDERPOWERED"
    return dict(label=label, n_days=int(len(b)), sr_sleeve=A.sharpe(a), dsr=d, mc_base=mb, mc_combined=mc,
                worst_sleeve_usd=worst, worst_combined_usd=float((b + a).min()), verdict=verdict)


def fmt_adm(r: dict) -> list[str]:
    d, mb, mc = r["dsr"], r["mc_base"], r["mc_combined"]
    return [f"  [{r['label']}] {r['verdict']} — {r['n_days']} jours ; Sharpe sleeve seule {r['sr_sleeve']:.2f}",
            f"    Sharpe base {d['sr_base']:.3f} → combiné {d['sr_combined']:.3f} : ΔSR {d['delta']:+.3f} "
            f"(p(≤0) {d['p_le_0']:.3f}, erreur-type {d['se']:.3f}, MDE80 {d['mde80']:.3f})",
            f"    P(perte du compte, 2 ans, sans gouverneur) {mb['p_loss']:.2%} → {mc['p_loss']:.2%} "
            f"(Δ {100 * (mc['p_loss'] - mb['p_loss']):+.2f} pt) ; trader {mb['trader_usd_month']:.1f} → "
            f"{mc['trader_usd_month']:.1f} $/mois",
            f"    pire séance sleeve {r['worst_sleeve_usd']:+.0f} $ (plafond {WORST_CAP:.0f}) ; "
            f"pire jour combiné {r['worst_combined_usd']:+.0f} $"]


def main(out: Path, dry: bool) -> None:
    out.mkdir(parents=True, exist_ok=True)
    df = load(dry)
    lines = ["ESSAI À BLANC (prix synthétiques)"] if dry else []
    res: dict = {}

    # --- Étape 1 : la dose sur la découverte ---
    disc = df[df.index < H.HOLDOUT_START]
    ddays = pd.DatetimeIndex(sorted(set(disc.index.normalize())))
    ev_d = events(disc, ddays[ddays.weekday < 5])
    hold = df[df.index >= H.HOLDOUT_START - pd.Timedelta(hours=2)]
    hdays = pd.DatetimeIndex(sorted(set(hold.index.normalize())))
    hdays = hdays[(hdays.weekday < 5) & (hdays >= H.HOLDOUT_START) & (hdays <= H.LAST_EVENT)]
    ev_h = events(hold, hdays)
    g1, dh = float(ev_d["both"].mean()), float(ev_h.loc[ev_h["cat"].isin(D_CATS), "both"].mean())
    published = json.loads((OUT / "s2_holdout.json").read_text())["S2"]["D"]["mean"]
    ok = abs(g1 - H.PUBLISHED_G1["mean"]) < 0.01 and abs(dh - published) < 0.01
    lines.append(f"Contrôle : G1 découverte {g1:.3f} (publié 4,05) ; D holdout {dh:.3f} (publié {published:.3f}) → "
                 f"{'OK' if ok else 'ÉCHEC'}")
    if not ok and not dry:
        (out / "s2_validation.txt").write_text("\n".join(lines) + "\nArrêt.\n")
        print("\n".join(lines))
        sys.exit(1)

    e = ev_d.dropna(subset=["both"]).sort_index()
    isD = e["cat"].isin(D_CATS)
    X = sm.add_constant(isD.astype(float).to_numpy())
    m = sm.OLS(e["both"].to_numpy(), X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    contrast, t_contrast = float(m.params[1]), float(m.tvalues[1])
    sD, sO = H.stats(e.loc[isD, "both"]), H.stats(e.loc[~isD, "both"])
    folds = []
    for name, a, b in FOLDS:
        x = e.loc[a:b]
        xd, xo = x.loc[x["cat"].isin(D_CATS), "both"], x.loc[~x["cat"].isin(D_CATS), "both"]
        folds.append(dict(fold=name, n_D=int(len(xd)), D=float(xd.mean()), n_O=int(len(xo)), AUTRES=float(xo.mean()),
                          D_gt=bool(xd.mean() > xo.mean())))
    n_gt = sum(f["D_gt"] for f in folds)
    v1, v2, v3 = contrast > 0 and t_contrast >= 2, n_gt >= 5, sD["mean"] >= H.GATE
    res["etape1"] = dict(contrast=contrast, t_contrast=t_contrast, D=sD, AUTRES=sO, folds=folds, n_folds_D_gt=n_gt,
                         D25=H.stats(e.loc[e["cat"] == "D25", "both"]), DME=H.stats(e.loc[e["cat"] == "DME", "both"]),
                         D_legs={"pre": float(e.loc[isD, "pre"].mean()), "post": float(e.loc[isD, "post"].mean())},
                         V1=bool(v1), V2=bool(v2), V3=bool(v3))
    r1 = res["etape1"]
    lines += ["", "Étape 1 — la dose sur la découverte (2007-01 → 2024-06)",
              f"  D (25 + fin de mois) n {sD['n']}  brut {sD['mean']:+.2f} bps  t HAC {sD['t_hac']:+.2f} ; "
              f"AUTRES n {sO['n']}  brut {sO['mean']:+.2f}  t HAC {sO['t_hac']:+.2f}",
              f"  contraste D − AUTRES {contrast:+.2f} bps, t HAC6 {t_contrast:+.2f}",
              f"  D25 {r1['D25']['mean']:+.2f} (n {r1['D25']['n']}) ; DME {r1['DME']['mean']:+.2f} (n {r1['DME']['n']}) ; "
              f"jambes de D : achat {r1['D_legs']['pre']:+.2f}, vente {r1['D_legs']['post']:+.2f}",
              "  plis : " + " ; ".join(f"{f['fold']} D {f['D']:+.2f} (n {f['n_D']}) / AUTRES {f['AUTRES']:+.2f}"
                                       for f in folds),
              f"  V1 (contraste > 0, t ≥ 2) {v1} ; V2 (D > AUTRES dans ≥ 5 plis sur 6 : {n_gt}) {v2} ; "
              f"V3 (D ≥ {H.GATE:.2f}) {v3}"]

    # --- Étape 2 : admission au funded ---
    allD = pd.concat([e.loc[isD, "both"], ev_h.loc[ev_h["cat"].isin(D_CATS), "both"].dropna()]).sort_index()
    sleeve_ev = (allD - H.COST_EVENT) * NOTIONAL / 1e4
    book = pd.read_csv(io.StringIO(A.git_show(A.BR_COMMIT, A.BR_CSV)), index_col=0, parse_dates=True)
    idx = book.index.union(sleeve_ev.index)
    idx = idx[(idx >= WIN_START) & (idx <= WIN_END)]
    book = book.reindex(idx).fillna(0.0)
    base = book["Livre complet"] - book["ORB seul"]
    sleeve = sleeve_ev.reindex(idx).fillna(0.0)
    adm = admission(base, sleeve, "décisif : 2,5× l'équité, 2013-10 → 2026-05")
    erc = admission(base, sleeve * (base.std() / sleeve.std()), "indicatif : ERC")
    hmask = idx >= H.HOLDOUT_START
    adm_h = admission(base[hmask], sleeve[hmask], "indicatif : holdout seul, 2024-07 → 2026-05")
    corr = {c: float(np.corrcoef(sleeve, book[c])[0, 1]) for c in book.columns}
    corr["base (complet − ORB)"] = float(np.corrcoef(sleeve, base)[0, 1])
    res["etape2"] = dict(decisif=adm, erc=erc, holdout=adm_h, corr=corr, n_events=int((sleeve != 0).sum()),
                         erc_notional_x_equity=float(NOTIONAL * base.std() / sleeve.std() / 9914.0))
    lines += ["", f"Étape 2 — admission au funded ({int((sleeve != 0).sum())} événements dans la fenêtre)"]
    lines += fmt_adm(adm) + fmt_adm(erc) + fmt_adm(adm_h)
    lines.append(f"  notionnel ERC : {res['etape2']['erc_notional_x_equity']:.1f}× l'équité")
    lines.append("  corrélations quotidiennes : " + " ; ".join(f"{k} {v:+.3f}" for k, v in corr.items()))

    # --- Décision ---
    launch = v1 and v2 and v3 and adm["verdict"] == "ADMIS"
    missing = [n for n, ok_ in (("V1", v1), ("V2", v2), ("V3", v3), ("admission ADMIS", adm["verdict"] == "ADMIS"))
               if not ok_]
    res["decision"] = "LANCER" if launch else "ARCHIVER"
    res["manque"] = missing
    lines += ["", f"→ S2 : {res['decision']}" + ("" if launch else f" (manque : {', '.join(missing)})")]
    (out / "s2_validation.json").write_text(json.dumps(res, indent=1, default=float))
    (out / "s2_validation.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--dry":
        main(Path(sys.argv[2]), dry=True)
    else:
        main(OUT, dry=False)
