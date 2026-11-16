"""FBL-10b : récupère ^HSI et 000001.SS avant Stock Connect (jusqu'au 2014-11-14) par yfinance.

Écrit les CSV bruts dans ../_data/ (gitignoré) et n'affiche que les comptes de lignes et les bornes : aucun rendement.

Usage : /usr/bin/python3 fetch_pre.py
"""
from __future__ import annotations

from pathlib import Path

import yfinance as yf

OUT = Path(__file__).resolve().parents[1] / "_data"
for t in ("^HSI", "000001.SS"):
    df = yf.download(t, start="1990-01-01", end="2014-11-15", auto_adjust=False, progress=False, multi_level_index=False)
    df.to_csv(OUT / f"pre_{t.replace('^', '').replace('.', '_')}.csv")
    print(t, len(df), df.index.min().date() if len(df) else None, "→", df.index.max().date() if len(df) else None)
