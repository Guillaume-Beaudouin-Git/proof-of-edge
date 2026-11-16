"""FBL-10 : récupère les séries quotidiennes ^HSI, 2800.HK (Tracker Fund) et 000001.SS (Shanghai) par yfinance.

Écrit les CSV bruts dans ../_data/ (gitignoré) et n'affiche que les comptes de lignes et les bornes de dates : aucun
rendement n'est calculé ici.

Usage : /usr/bin/python3 fetch.py
"""
from __future__ import annotations

from pathlib import Path

import yfinance as yf

OUT = Path(__file__).resolve().parents[1] / "_data"
for t in ("^HSI", "2800.HK", "000001.SS"):
    df = yf.download(t, start="2014-01-01", end="2026-10-18", auto_adjust=False, progress=False, multi_level_index=False)
    df.to_csv(OUT / f"{t.replace('^', '').replace('.', '_')}.csv")
    print(t, len(df), df.index.min().date() if len(df) else None, "→", df.index.max().date() if len(df) else None)
