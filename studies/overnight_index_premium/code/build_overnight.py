"""Independent reconstruction of the US100/GER40 overnight leg, anchored in
exchange time WITH daylight saving (America/New_York for US100, Europe/Berlin
for GER40); each night is labelled by its ENTRY day (the day of the close being
held), NOT the open day -- the trap flagged by the coordinating note (a night
labelled by its open passes the weekend gap off as "Monday" and artificially
inflates Wednesday).

Source: true-UTC M1 OHLC, local cache
`$RESEARCH_DATA_ROOT/m1_cache/{US100,GER40}_M1.parquet`
(identical to the deep_history_utc {sym}_M1.csv files, checked below).

Cash sessions used (consistent with the LIVE sleeve's build_series.py):
  US100: 09:30-16:00 America/New_York (NASDAQ-100 cash)
  GER40: 09:00-17:30 Europe/Berlin   (Xetra)
The deployed sleeve enters at the close (+5 min) and exits at the next open
(US100 22:05 -> 15:30 Paris, GER40 17:35 -> 09:00 Paris -- exactly these two
sessions in native exchange time, +5 min).
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(os.environ.get("RESEARCH_DATA_ROOT", "data")) / "m1_cache"
OUT = Path(__file__).resolve().parent.parent / "results"

SESSIONS = {
    "US100": dict(tz="America/New_York", open="09:30", close="16:00"),
    "GER40": dict(tz="Europe/Berlin", open="09:00", close="17:30"),
}


def load_m1(sym: str) -> pd.DataFrame:
    df = pd.read_parquet(CACHE / f"{sym}_M1.parquet")
    return df.sort_index()


def to_local(df: pd.DataFrame, tz: str) -> pd.DataFrame:
    out = df.copy()
    out.index = out.index.tz_convert(tz)
    return out


def session_prices(df_local: pd.DataFrame, open_hm: str, close_hm: str) -> pd.DataFrame:
    """One record per local calendar day: first price at/after `open_hm`, last
    price at/before `close_hm`, plus the range and TWAP of the last half-hour
    (Part C proxy)."""
    idx = df_local.index
    hm = idx.hour * 60 + idx.minute
    oh, om = map(int, open_hm.split(":"))
    ch, cm = map(int, close_hm.split(":"))
    o_min, c_min = oh * 60 + om, ch * 60 + cm

    day = pd.Series(idx.date, index=idx)
    rows = []
    for d, g in df_local.groupby(day):
        ghm = (g.index.hour * 60 + g.index.minute).to_numpy()
        # open: first bar >= o_min (15-min tolerance for shortened days)
        j_open = np.searchsorted(ghm, o_min, side="left")
        # close: last bar <= c_min
        j_close = np.searchsorted(ghm, c_min, side="right") - 1
        if j_open >= len(ghm) or j_close < 0 or j_open > j_close:
            continue
        if abs(ghm[j_open] - o_min) > 20 or abs(ghm[j_close] - c_min) > 20:
            # truncated/shifted session (partial holiday, data gap) -> skip
            continue
        px_open = float(g["open"].to_numpy()[j_open])
        px_close = float(g["close"].to_numpy()[j_close])
        # last half-hour before the close: dispersion proxy (Part C)
        last30_mask = (ghm > c_min - 30) & (ghm <= c_min)
        seg = g.iloc[last30_mask] if last30_mask.any() else g.iloc[[j_close]]
        hi30 = float(seg["high"].max())
        lo30 = float(seg["low"].min())
        twap30 = float(seg["close"].mean())
        rows.append(dict(date=pd.Timestamp(d), px_open=px_open, px_close=px_close,
                          range30_bps=(hi30 - lo30) / px_close * 1e4,
                          twap_dev_bps=(px_close - twap30) / px_close * 1e4,
                          n_bars=len(g)))
    return pd.DataFrame(rows).set_index("date").sort_index()


def build(sym: str) -> pd.DataFrame:
    cfg = SESSIONS[sym]
    raw = load_m1(sym)
    loc = to_local(raw, cfg["tz"])
    S = session_prices(loc, cfg["open"], cfg["close"])
    S["weekday"] = S.index.dayofweek  # 0=Monday ... 4=Friday (ENTRY day = current day)
    S["next_open"] = S["px_open"].shift(-1)
    S["next_date"] = S.index.to_series().shift(-1)
    S["gap_cal_days"] = (S["next_date"] - S.index.to_series()).dt.days
    S["ov_bps_entryday"] = (S["next_open"] / S["px_close"] - 1.0) * 1e4
    # alternative convention (the trap): label by the OPEN day (t+1)
    S["ov_bps_openday"] = S["ov_bps_entryday"]  # same number, different row label
    # anti-artifact guard (roll/holiday/bad tick), |.| < 800 bps
    S.loc[S["ov_bps_entryday"].abs() > 800, ["ov_bps_entryday"]] = np.nan
    return S


if __name__ == "__main__":
    for sym in ("US100", "GER40"):
        S = build(sym)
        S.to_csv(OUT / f"{sym.lower()}_overnight_daily.csv", float_format="%.6g")
        n = S["ov_bps_entryday"].notna().sum()
        print(f"{sym}: {len(S)} cash sessions, {n} nights measured, "
              f"{S.index.min().date()} -> {S.index.max().date()}")
        print(S.groupby("weekday")["ov_bps_entryday"].agg(["mean", "count"]).round(3))
        print()
