"""FBL-10b — l'envers de FBL-10 (PREREG_ENVERS.md) : réplication avant Stock Connect (1997-2014), puis, si elle tient,
espérance, plis et admission funded. Lecture unique, décision.

Réutilise `fbl10.py` (calendrier, jambes, fête). À lancer avec `python3 -I` : les CSV lus sont téléchargés.

Usage : /usr/bin/python3 -I fbl10b.py                  (à ne lancer qu'une fois)
        /usr/bin/python3 -I fbl10b.py --dry <dossier>   (essai à blanc : rendements synthétiques)
Sorties : ../out/fbl10b.txt, ../out/fbl10b.json, ../out/fbl10b_jours.csv
"""
from __future__ import annotations

import site
import sys

sys.path.append(site.getusersitepackages())
sys.dont_write_bytecode = True

import io  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fbl10 as F  # noqa: E402

PRE = (pd.Timestamp("1997-07-02"), pd.Timestamp("2014-11-14"))
HAIRCUT = 0.564


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def kinds(hk: pd.DataFrame, ss: pd.DataFrame, start, end) -> pd.Series:
    days = hk.index[(hk.index >= start) & (hk.index <= end)]
    closed = ~days.isin(ss.index)
    prev = np.r_[False, closed[:-1]]
    return pd.Series(np.where(closed, "fermé", np.where(prev, "réouverture", "ordinaire")), index=days)


def trades(hk: pd.DataFrame, kind: pd.Series, r: pd.Series) -> pd.Series:
    """Achat les jours fermés, vente les réouvertures, ouverture → clôture, stop 2 % approché par le plus haut / bas."""
    ev = kind[kind != "ordinaire"]
    h = hk.reindex(ev.index)
    long = (ev == "fermé").to_numpy()
    raw = r.reindex(ev.index).to_numpy()
    pnl = np.where(long, raw, -raw)
    stopped = np.where(long, h["Low"] <= h["Open"] * (1 - F.STOP), h["High"] >= h["Open"] * (1 + F.STOP))
    return pd.Series(np.where(stopped, -F.STOP * 1e4, pnl) - F.K0, index=ev.index)


def main(out: Path, dry: bool) -> None:
    out.mkdir(parents=True, exist_ok=True)
    lines = ["ESSAI À BLANC (rendements synthétiques)"] if dry else []
    hk_pre, ss_pre = F.read("pre_HSI"), F.read("pre_000001_SS")
    hk_post, ss_post = F.read("HSI"), F.read("000001_SS")
    k_pre = kinds(hk_pre, ss_pre, *PRE)
    if dry:
        rng = np.random.default_rng(4)
        eff = k_pre.reindex(hk_pre.index).map({"fermé": 0.003, "réouverture": -0.004}).fillna(0.0).to_numpy()
        hk_pre = hk_pre.assign(Close=hk_pre["Open"] * np.exp(rng.normal(0.0, 0.013, len(hk_pre)) + eff))
    r_pre = ((hk_pre["Close"] / hk_pre["Open"] - 1) * 1e4).reindex(k_pre.index)
    L = F.legs(r_pre, k_pre)
    r1 = L["fermé"]["diff"] >= 10.0
    r2 = L["réouverture"]["diff"] <= -15.0
    res: dict = dict(counts=k_pre.value_counts().to_dict(), legs_pre=L, R1=bool(r1), R2=bool(r2))
    replicated = r1 and r2
    sub = {nm: F.legs(r_pre[sel], k_pre[sel]) for nm, sel in
           (("1997-2007", k_pre.index < pd.Timestamp("2008-01-01")), ("2008-2014", k_pre.index >= pd.Timestamp("2008-01-01")))}
    hol = {k: {nm: dict(n=int(len(v)), diff=float(v.mean() - L["ordinaire"]["mean"]))
               for nm, v in r_pre[k_pre == k].groupby([F.holiday(d) for d in r_pre[k_pre == k].index])}
           for k in ("fermé", "réouverture")}
    yrs = {k: {str(y): float(v.mean()) for y, v in (r_pre[k_pre == k] - L["ordinaire"]["mean"]).groupby(r_pre[k_pre == k].index.year)}
           for k in ("fermé", "réouverture")}
    res["reported"] = dict(subperiods=sub, by_holiday=hol, by_year=yrs)

    if replicated:
        k_post = F.calendar(hk_post, ss_post)
        r_post = ((hk_post["Close"] / hk_post["Open"] - 1) * 1e4).reindex(k_post.index)
        t_pre, t_post = trades(hk_pre, k_pre, r_pre), trades(hk_post, k_post, r_post)
        se_post = float(t_post.std() / math.sqrt(len(t_post)))
        se_pre = float(t_pre.std() / math.sqrt(len(t_pre)))
        est = [(float(t_post.mean()) - HAIRCUT * se_post, se_post), (float(t_pre.mean()), se_pre)]
        w = [1 / s ** 2 for _, s in est]
        comb = sum(x * wi for (x, _), wi in zip(est, w)) / sum(w)
        se_c = 1 / math.sqrt(sum(w))
        p_pos = phi(comb / se_c)
        l1, l2 = bool(comb >= 1.5 and p_pos >= 0.80), bool(comb - F.K0 >= 0)
        allt = pd.concat([t_pre, t_post]).sort_index()
        folds = []
        for c in np.array_split(np.arange(len(allt)), 5):
            y = allt.iloc[c]
            folds.append(dict(debut=str(y.index.min().date()), fin=str(y.index.max().date()), n=int(len(y)), net=float(y.mean())))
        e1 = sum(f["net"] > 0 for f in folds) >= 4
        sleeve = allt * F.NOTIONAL / 1e4
        book = pd.read_csv(io.StringIO(F.V.A.git_show(F.V.A.BR_COMMIT, F.V.A.BR_CSV)), index_col=0, parse_dates=True)
        idx = book.index.union(sleeve.index)
        idx = idx[(idx >= pd.Timestamp("2013-10-01")) & (idx <= F.WIN_END)]
        book = book.reindex(idx).fillna(0.0)
        adm = F.V.admission(book["Livre complet"] - book["ORB seul"], sleeve.reindex(idx).fillna(0.0), "3 000 $")
        launch = bool(l1 and l2 and e1 and adm["verdict"] == "ADMIS")
        res.update(E3=dict(post=est[0], pre=est[1], combined=comb, se=se_c, p_pos=p_pos, L1=l1, L2=l2),
                   folds=folds, E1=bool(e1), admission=adm, E4=adm["verdict"] == "ADMIS",
                   trades=dict(n_pre=int(len(t_pre)), net_pre=float(t_pre.mean()), n_post=int(len(t_post)), net_post=float(t_post.mean())))
    else:
        launch = False
    res["decision"] = "LANCER (sous réserve de la fourchette HK50.cash)" if launch else "ARCHIVER"
    res["nature"] = None if launch else "de puissance"

    fmt = lambda x: f"{x['diff']:+.2f} bps (n {x['n']}, t {x['t_hac']:+.2f})"  # noqa: E731
    lines += [f"Avant Stock Connect (1997-07 → 2014-11) : {res['counts']} ; moyenne ordinaire {L['ordinaire']['mean']:+.2f}",
              f"  R1 jours fermés {fmt(L['fermé'])} → {r1} (seuil ≥ +10)",
              f"  R2 réouvertures {fmt(L['réouverture'])} → {r2} (seuil ≤ −15)"]
    if replicated:
        e = res["E3"]
        lines += [f"  E3 : 2014-2026 corrigé {e['post'][0]:+.2f} (e.-t. {e['post'][1]:.2f}) ; 1997-2014 {e['pre'][0]:+.2f} "
                  f"(e.-t. {e['pre'][1]:.2f}) → combiné net {e['combined']:+.2f} (e.-t. {e['se']:.2f}), P(net > 0) {e['p_pos']:.2f} → "
                  f"L1 {e['L1']}, L2 {e['L2']}",
                  "  E1 plis : " + " ; ".join(f"{f['debut'][:7]}→{f['fin'][:7]} {f['net']:+.1f}" for f in res["folds"]) + f" → {res['E1']}",
                  "  E4 :"] + ["  " + s for s in F.V.fmt_adm(res["admission"])]
    lines += [f"→ FBL-10b : {res['decision']}" + (f" (mort {res['nature']})" if res["nature"] else ""), "Rapporté :"]
    for nm, v in sub.items():
        lines.append(f"  {nm} : fermés {v['fermé']['diff']:+.2f} (n {v['fermé']['n']}), réouvertures {v['réouverture']['diff']:+.2f} (n {v['réouverture']['n']})")
    for k, v in hol.items():
        lines.append(f"  {k} par fête : " + " ; ".join(f"{nm} {x['diff']:+.1f} (n {x['n']})" for nm, x in v.items()))
    for k, v in yrs.items():
        lines.append(f"  {k} par année : " + " ".join(f"{y}:{m:+.0f}" for y, m in v.items()))
    pd.DataFrame({"kind": k_pre, "r_hsi": r_pre}).to_csv(out / "fbl10b_jours.csv")
    (out / "fbl10b.json").write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    (out / "fbl10b.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--dry":
        main(Path(sys.argv[2]), dry=True)
    else:
        main(F.OUT, dry=False)
