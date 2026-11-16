"""S2 — descriptif ajouté après le pré-enregistrement : le flux MT5/FTMO-Demo contre Dukascopy, mêmes dates.

Motif : sur la série assemblée, D fait +6,15 bps sur le segment MT5 (2018-01 → 2025-05) contre +3,41
et +4,51 sur les segments Dukascopy (`../out/s2_deep.txt` §2). Effet de période ou effet de flux ?
Le cache Dukascopy recouvre le segment MT5 en 2018 et de 2024-01 à 2025-05 : on recalcule les mêmes
événements sur les deux flux. Aucun paramètre n'est choisi ; la règle de décision n'est pas touchée.

Usage : /usr/bin/python3 s2_feed.py
Sortie : ../out/s2_feed.txt
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "code"))
import s2_holdout as H  # noqa: E402

OUT = HERE.parent / "out"
CACHE = Path(os.environ.get("RESEARCH_DATA_ROOT", "data") + "/deep_history_m1/_cache_duka")
WINDOWS = [(pd.Timestamp("2018-01-02"), pd.Timestamp("2018-12-31")), (pd.Timestamp("2024-01-01"), pd.Timestamp("2025-05-30"))]


def main() -> None:
    duka = pd.concat([pd.read_parquet(CACHE / f"USDJPY_{y}.parquet") for y in (2018, 2024, 2025)])
    duka.index = pd.DatetimeIndex(duka.pop("ts_utc"))
    duka = duka[~duka.index.duplicated()].sort_index()[["open", "high", "low", "close"]]
    mt5 = pd.read_csv(OUT / "s2_deep_events.csv", index_col=0, parse_dates=True)
    sel = mt5[np.any([(mt5.index >= a) & (mt5.index <= b) for a, b in WINDOWS], axis=0)].copy()
    E = H.Events(duka)
    f = E.frame(sel.index)
    sel["duka_pre"], sel["duka_post"], sel["duka_both"] = f["pre"], f["post"], f["both"]
    sel = sel.dropna(subset=["duka_both"])
    L = ["Mêmes événements gotobi, deux flux (bps, brut avec stop) : MT5/FTMO-Demo (série assemblée) contre Dukascopy",
         f"Fenêtres : 2018-01-02 → 2018-12-31 et 2024-01-01 → 2025-05-30 ; {len(sel)} événements"]
    for lab, sub in (("D", sel[sel["isD"]]), ("AUTRES", sel[~sel["isD"]]), ("tous", sel)):
        c = np.corrcoef(sub["both"], sub["duka_both"])[0, 1]
        dlt = sub["both"] - sub["duka_both"]
        L.append(f"  {lab:7s} n {len(sub):3d} : MT5 {sub['both'].mean():+6.2f} (achat {sub['pre'].mean():+5.2f}, vente "
                 f"{sub['post'].mean():+5.2f}) ; Dukascopy {sub['duka_both'].mean():+6.2f} (achat {sub['duka_pre'].mean():+5.2f}, "
                 f"vente {sub['duka_post'].mean():+5.2f}) ; écart {dlt.mean():+5.2f} (t HAC {H.hac_t(dlt):+.2f}) ; corrélation {c:.3f}")
    (OUT / "s2_feed.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
