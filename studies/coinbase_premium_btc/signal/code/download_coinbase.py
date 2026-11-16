"""Bougies horaires Coinbase Exchange (API publique, sans clé) pour BTC-USD et ETH-USD, 2015→.
Usage : python3 download_coinbase.py <cache_dir>
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import requests

UA = {"User-Agent": "Mozilla/5.0 (research)"}


def fetch(product: str, start: pd.Timestamp, end: pd.Timestamp, gran: int = 3600) -> list:
    url = f"https://api.exchange.coinbase.com/products/{product}/candles"
    for i in range(6):
        try:
            r = requests.get(url, params={"granularity": gran, "start": start.isoformat() + "Z", "end": end.isoformat() + "Z"}, headers=UA, timeout=60)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                time.sleep(2 + i)
                continue
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1 + i)
    return []


def main(cache: str) -> None:
    out_dir = Path(cache) / "coinbase"
    out_dir.mkdir(parents=True, exist_ok=True)
    for product in ["BTC-USD", "ETH-USD"]:
        out = out_dir / f"{product}_1h.parquet"
        rows = []
        t = pd.Timestamp("2015-01-01")
        end_all = pd.Timestamp.now("UTC").tz_localize(None)
        while t < end_all:
            e = min(t + pd.Timedelta(hours=299), end_all)
            rows.extend(fetch(product, t, e))
            t = e + pd.Timedelta(hours=1)
            time.sleep(0.15)
        df = pd.DataFrame(rows, columns=["time", "low", "high", "open", "close", "volume"])
        df["ts"] = pd.to_datetime(df["time"], unit="s")
        df = df.drop_duplicates("ts").sort_values("ts").reset_index(drop=True)
        df.to_parquet(out)
        print(product, len(df), df.ts.min(), df.ts.max(), flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
