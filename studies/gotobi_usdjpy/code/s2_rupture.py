"""S2 — test de rupture du gotobi dosé (PREREG_RUPTURE.md) : balayage sup|t| corrigé par bootstrap.

`break_scan` vient de `overnight_hourly/code/analysis.py`, appelé tel quel. Les événements viennent
de `s2_validation.py`, l'admission aussi.

Usage : /usr/bin/python3 s2_rupture.py                  (à ne lancer qu'une fois)
        /usr/bin/python3 s2_rupture.py --dry <dossier>   (essai à blanc : prix USDJPY synthétiques)
Sorties : ../out/s2_rupture.txt, ../out/s2_rupture.json
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "overnight_hourly" / "code"))
import analysis as OH  # noqa: E402
import s2_validation as V  # noqa: E402

P_MAX = 0.05


def main(out: Path, dry: bool) -> None:
    out.mkdir(parents=True, exist_ok=True)
    df = V.load(dry)
    days = pd.DatetimeIndex(sorted(set(df.index.normalize())))
    days = days[(days.weekday < 5) & (days <= V.H.LAST_EVENT)]
    ev = V.events(df, days).dropna(subset=["both"]).sort_index()
    ev["D"] = ev["cat"].isin(V.D_CATS)
    D = ev.loc[ev["D"], "both"]
    lines = ["ESSAI À BLANC (prix synthétiques)"] if dry else []

    scan = OH.break_scan(pd.Series(D.index), D.reset_index(drop=True))
    sig = scan["p_boot"] < P_MAX
    res: dict = {"D": scan, "significatif": bool(sig)}
    if dry:
        sig = True   # essai à blanc : exercer aussi la branche « rupture significative »
    lines += [f"D (le 25 + fin de mois), {len(D)} événements, {D.index.min().date()} → {D.index.max().date()}",
              f"  rupture estimée {scan['break_date']} : avant {scan['mean_pre']:+.2f} bps, après {scan['mean_post']:+.2f} ; "
              f"sup|t| {scan['sup_t']:.2f} (seuil 95 % du bootstrap {scan['boot_p95']:.2f}) ; p {scan['p_boot']:.3f} → "
              f"{'significative' if sig else 'non significative'}"]

    m = ev.assign(mois=ev.index.to_period("M"))
    g = m.groupby(["mois", "D"])["both"].mean().unstack()
    contrast = (g[True] - g[False]).dropna()
    cs = OH.break_scan(pd.Series(contrast.index.to_timestamp()), contrast.reset_index(drop=True))
    res["contraste_mensuel"] = cs
    lines.append(f"  rapporté : contraste mensuel D − AUTRES ({cs['n']} mois) — rupture {cs['break_date']}, avant "
                 f"{cs['mean_pre']:+.2f}, après {cs['mean_post']:+.2f}, sup|t| {cs['sup_t']:.2f}, p {cs['p_boot']:.3f}")

    if not sig:
        res["decision"], res["manque"] = "ARCHIVER", ["rupture non significative"]
        lines.append("→ S2 : l'archive reste (rupture non significative)")
    else:
        tau = pd.Timestamp(scan["break_date"])
        post = D[D.index > tau]
        gate_ok = float(post.mean()) >= V.H.GATE
        sleeve_ev = (post - V.H.COST_EVENT) * V.NOTIONAL / 1e4
        book = pd.read_csv(io.StringIO(V.A.git_show(V.A.BR_COMMIT, V.A.BR_CSV)), index_col=0, parse_dates=True)
        idx = book.index.union(sleeve_ev.index)
        idx = idx[(idx > tau) & (idx <= V.WIN_END)]
        book = book.reindex(idx).fillna(0.0)
        base = book["Livre complet"] - book["ORB seul"]
        adm = V.admission(base, sleeve_ev.reindex(idx).fillna(0.0), f"après {tau.date()}")
        res.update(gate_ok=bool(gate_ok), post_mean=float(post.mean()), post_n=int(len(post)), admission=adm)
        lines.append(f"  après la rupture : D {post.mean():+.2f} bps (n {len(post)}), porte 5,61 {'tenue' if gate_ok else 'manquée'}")
        lines += V.fmt_adm(adm)
        launch = gate_ok and adm["verdict"] == "ADMIS"
        res["decision"] = "LANCER" if launch else "ARCHIVER"
        res["manque"] = [k for k, bad in (("porte de coût", not gate_ok),
                                          ("admission ADMIS", adm["verdict"] != "ADMIS")) if bad]
        lines.append(f"→ S2 : {res['decision']}" + ("" if launch else f" (manque : {', '.join(res['manque'])})"))
    (out / "s2_rupture.json").write_text(json.dumps(res, indent=1, default=float))
    (out / "s2_rupture.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--dry":
        main(Path(sys.argv[2]), dry=True)
    else:
        main(V.OUT, dry=False)
