"""Téléchargement des données publiques sans clé pour la vérification locale de C9.

Usage : /usr/bin/python3 -I -B download.py <scratch_raw_dir>
Sources : Coinbase Exchange REST (bougies 1 h), Binance Vision (klines spot 1 h et 1 j, funding USD-M),
Binance REST public (dernières heures), Hyperliquid info (fundingHistory BTC), FRED DTB3 (csv public).
"""
from __future__ import annotations

import io
import json
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

UA = {"User-Agent": "c9-verif-research/1.0"}


def get(url: str, data: bytes | None = None, headers: dict | None = None, tries: int = 5) -> bytes:
    h = dict(UA)
    if headers:
        h.update(headers)
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise
            time.sleep(2 * (k + 1))
        except Exception:
            time.sleep(2 * (k + 1))
    raise RuntimeError(url)


def coinbase(product: str, start: datetime, end: datetime, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    rows: dict[int, list] = {}
    if out.exists():
        for line in out.read_text().splitlines()[1:]:
            p = line.split(",")
            rows[int(p[0])] = p
        start = max(start, datetime.fromtimestamp(max(rows), tz=timezone.utc) - timedelta(hours=2))
    t = start
    while t < end:
        t2 = min(t + timedelta(hours=300), end)
        url = (f"https://api.exchange.coinbase.com/products/{product}/candles?granularity=3600"
               f"&start={t.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={t2.strftime('%Y-%m-%dT%H:%M:%SZ')}")
        for c in json.loads(get(url)):
            rows[int(c[0])] = [str(x) for x in c]
        t = t2
        time.sleep(0.35)
    with out.open("w") as f:
        f.write("time,low,high,open,close,volume\n")
        for k in sorted(rows):
            f.write(",".join(rows[k]) + "\n")
    print(product, len(rows))


def vision_klines(symbol: str, interval: str, first: str, outdir: Path, market: str = "spot") -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    y, m = map(int, first.split("-"))
    now = datetime.now(timezone.utc)
    base = f"https://data.binance.vision/data/{market}"
    while (y, m) < (now.year, now.month):
        name = f"{symbol}-{interval}-{y:04d}-{m:02d}"
        dest = outdir / f"{name}.csv"
        if not dest.exists():
            try:
                z = get(f"{base}/monthly/klines/{symbol}/{interval}/{name}.zip")
                with zipfile.ZipFile(io.BytesIO(z)) as zf:
                    dest.write_bytes(zf.read(zf.namelist()[0]))
            except urllib.error.HTTPError:
                print("absent", name)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    d = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    while d.date() < now.date():
        name = f"{symbol}-{interval}-{d:%Y-%m-%d}"
        dest = outdir / f"{name}.csv"
        if not dest.exists():
            try:
                z = get(f"{base}/daily/klines/{symbol}/{interval}/{name}.zip")
                with zipfile.ZipFile(io.BytesIO(z)) as zf:
                    dest.write_bytes(zf.read(zf.namelist()[0]))
            except urllib.error.HTTPError:
                print("absent", name)
        d += timedelta(days=1)
    print(symbol, interval, len(list(outdir.glob("*.csv"))))


def binance_rest_tail(symbol: str, out: Path) -> None:
    now = datetime.now(timezone.utc)
    start = int(datetime(now.year, now.month, now.day, tzinfo=timezone.utc).timestamp() * 1000) - 2 * 86400000
    raw = get(f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&startTime={start}&limit=1000")
    out.write_bytes(raw)
    print(symbol, "tail", len(json.loads(raw)))


def binance_funding(out: Path) -> None:
    rows = []
    t = int(datetime(2019, 9, 1, tzinfo=timezone.utc).timestamp() * 1000)
    while True:
        raw = json.loads(get(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime={t}&limit=1000"))
        if not raw:
            break
        rows += raw
        t = raw[-1]["fundingTime"] + 1
        if len(raw) < 1000:
            break
        time.sleep(0.3)
    out.write_text(json.dumps(rows))
    print("binance funding", len(rows))


def hl_funding(out: Path) -> None:
    rows = []
    t = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    while True:
        body = json.dumps({"type": "fundingHistory", "coin": "BTC", "startTime": t}).encode()
        raw = json.loads(get("https://api.hyperliquid.xyz/info", data=body, headers={"Content-Type": "application/json"}))
        if not raw:
            break
        rows += raw
        nt = raw[-1]["time"] + 1
        if nt <= t or len(raw) < 2:
            break
        t = nt
        time.sleep(0.3)
    out.write_text(json.dumps(rows))
    print("hl funding", len(rows))


def main(root: Path) -> None:
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = datetime(2017, 7, 1, tzinfo=timezone.utc)
    coinbase("BTC-USD", start, end, root / "coinbase" / "BTC-USD_1h.csv")
    coinbase("ETH-USD", start, end, root / "coinbase" / "ETH-USD_1h.csv")
    vision_klines("BTCUSDT", "1h", "2017-08", root / "binance_spot_1h" / "BTCUSDT")
    vision_klines("ETHUSDT", "1h", "2017-08", root / "binance_spot_1h" / "ETHUSDT")
    for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        vision_klines(s, "1d", "2017-08" if s != "SOLUSDT" else "2020-08", root / "binance_spot_1d" / s)
    (root / "binance_tail").mkdir(parents=True, exist_ok=True)
    for s in ("BTCUSDT", "ETHUSDT"):
        binance_rest_tail(s, root / "binance_tail" / f"{s}.json")
    (root / "funding").mkdir(parents=True, exist_ok=True)
    binance_funding(root / "funding" / "binance_btcusdt.json")
    hl_funding(root / "funding" / "hl_btc.json")
    (root / "fred").mkdir(parents=True, exist_ok=True)
    (root / "fred" / "DTB3.csv").write_bytes(get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3"))
    print("done")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
