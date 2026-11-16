"""Hors pré-enregistrement, rapporté après la décision de FBL-10b : l'effet des jours fermés n'est-il qu'un effet
d'après-fête propre à Hong Kong ? Témoin : premiers jours HK après une fermeture de Hong Kong seul (Shanghai ouvert),
et veilles de ces fermetures, avant et après Stock Connect. Ne change aucune décision.

Usage : /usr/bin/python3 -I temoin_hk.py
Sortie : ../out/temoin_hk.txt
"""
from __future__ import annotations

import site
import sys

sys.path.append(site.getusersitepackages())
sys.dont_write_bytecode = True

from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fbl10 as F  # noqa: E402
import fbl10b as B  # noqa: E402


def main() -> None:
    lines = []
    for nm, (hk, ss, start, end) in {"1997-2014": (F.read("pre_HSI"), F.read("pre_000001_SS"), *B.PRE),
                                     "2014-2026": (F.read("HSI"), F.read("000001_SS"), F.LAUNCH, pd.Timestamp("2026-10-16"))}.items():
        kind = B.kinds(hk, ss, start, end)
        r = ((hk["Close"] / hk["Open"] - 1) * 1e4).reindex(kind.index)
        ordinary = r[kind == "ordinaire"]
        hk_days = kind.index
        ss_days = ss.index[(ss.index >= start) & (ss.index <= end)]
        hk_only_closed = ss_days[~ss_days.isin(hk_days)]
        nxt = hk_days[np.searchsorted(hk_days, hk_only_closed, side="right").clip(0, len(hk_days) - 1)]
        prv = hk_days[(np.searchsorted(hk_days, hk_only_closed, side="left") - 1).clip(0, None)]
        after, before = pd.DatetimeIndex(nxt).unique(), pd.DatetimeIndex(prv).unique()
        after = after[kind.reindex(after).to_numpy() == "ordinaire"]
        before = before[kind.reindex(before).to_numpy() == "ordinaire"]
        a, b = r.reindex(after).dropna(), r.reindex(before).dropna()
        lines.append(f"{nm} : jours ordinaires {ordinary.mean():+.2f} (n {len(ordinary)}) ; "
                     f"lendemain d'une fermeture de HK seul {a.mean() - ordinary.mean():+.2f} (n {len(a)}, t {F.AH.hac_t(a - ordinary.mean()):+.2f}) ; "
                     f"veille {b.mean() - ordinary.mean():+.2f} (n {len(b)}, t {F.AH.hac_t(b - ordinary.mean()):+.2f})")
    out = HERE.parent / "out"
    (out / "temoin_hk.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
