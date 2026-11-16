"""S2 — historique descriptif, année par année, du gotobi dosé tel qu'il aurait été tradé.

Aucun essai : découverte et holdout ont déjà été lus (`RAPPORT.md`, `RAPPORT_VALIDATION.md`).
Coût d'aujourd'hui (1,87 bp par événement) appliqué à toute la période ; notionnel 2,5 × 9 914 $.

Usage : /usr/bin/python3 s2_historique.py
Sorties : ../out/s2_historique.csv, ../out/s2_historique.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s2_validation as V  # noqa: E402

USD_PER_BP = V.NOTIONAL / 1e4


def main() -> None:
    df = V.load(dry=False)
    days = pd.DatetimeIndex(sorted(set(df.index.normalize())))
    days = days[(days.weekday < 5) & (days <= V.H.LAST_EVENT)]
    ev = V.events(df, days).dropna(subset=["both"])
    ev["D"] = ev["cat"].isin(V.D_CATS)
    ev["net"] = ev["both"] - V.H.COST_EVENT
    rows = []
    for y, g in ev.groupby(ev.index.year):
        d, o = g[g["D"]], g[~g["D"]]
        rows.append(dict(annee=y, n_D=len(d), brut_D=d["both"].mean(), net_D=d["net"].mean(),
                         pnl_usd=d["net"].sum() * USD_PER_BP, gagnants=(d["net"] > 0).mean(),
                         pire_usd=d["net"].min() * USD_PER_BP, n_autres=len(o), brut_autres=o["both"].mean(),
                         brut_tous=g["both"].mean()))
    t = pd.DataFrame(rows).set_index("annee")
    t["cumul_usd"] = t["pnl_usd"].cumsum()
    t.to_csv(V.OUT / "s2_historique.csv")
    lines = [f"Gotobi dosé (le 25 + fin de mois), USDJPY, {ev.index.min().date()} → {ev.index.max().date()} ; "
             f"coût 1,87 bp par événement ; notionnel {V.NOTIONAL:,.0f} $ ({USD_PER_BP:.2f} $ par bp)",
             f"{'année':>6} {'trades':>6} {'brut':>7} {'net':>7} {'P&L $':>7} {'cumul $':>8} {'gagnants':>8} "
             f"{'pire $':>7} | {'autres gotobi, brut':>20}"]
    for y, r in t.iterrows():
        lines.append(f"{y:>6} {r.n_D:>6.0f} {r.brut_D:>+7.2f} {r.net_D:>+7.2f} {r.pnl_usd:>+7.0f} {r.cumul_usd:>+8.0f} "
                     f"{r.gagnants:>8.0%} {r.pire_usd:>+7.0f} | {r.brut_autres:>+12.2f} (n {r.n_autres:.0f})")
    for a, b in ((2007, 2015), (2016, 2026)):
        s = ev[(ev.index.year >= a) & (ev.index.year <= b)]
        d = s[s["D"]]
        lines.append(f"{a}-{b} : {len(d)} trades, brut {d['both'].mean():+.2f}, net {d['net'].mean():+.2f} bps, "
                     f"P&L {d['net'].sum() * USD_PER_BP:+.0f} $ ({d['net'].sum() * USD_PER_BP / (b - a + 1):+.0f} $/an) ; "
                     f"autres gotobi brut {s.loc[~s['D'], 'both'].mean():+.2f}")
    (V.OUT / "s2_historique.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
