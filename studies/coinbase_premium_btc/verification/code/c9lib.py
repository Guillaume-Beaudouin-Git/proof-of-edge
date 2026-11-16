"""Bibliothèque de la vérification locale de C9 (code indépendant du cloud).

Conventions : index horaire = début de bougie UTC ; la valeur d'une bougie est connue à sa clôture (index + 1 h).
Un signal lu sur la bougie T entre au close de T et sort au close de T + h.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path


import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.api as sm  # noqa: E402

SCRATCH = Path("c9_verif")
RAW = SCRATCH / "raw"
CACHE = SCRATCH / "cache"
IS_END = pd.Timestamp("2023-12-31 23:00")
HO_END = pd.Timestamp("2026-09-30 23:00")
STRESS_MONTHS = ["2017-09", "2018-10", "2019-04", "2020-03", "2022-05", "2022-11", "2023-03"]


def _vision_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, header=None, usecols=[0, 1, 2, 3, 4, 5])
    if not np.issubdtype(df[0].dtype, np.number):
        df = df.iloc[1:].astype(float)
    t = df[0].astype("int64")
    t = np.where(t > 10**14, t // 1000, t)
    out = pd.DataFrame({"open": df[1].values, "high": df[2].values, "low": df[3].values,
                        "close": df[4].values, "volume": df[5].values},
                       index=pd.to_datetime(t, unit="ms"))
    return out


def load_binance(symbol: str, interval: str = "1h") -> pd.DataFrame:
    sub = "binance_spot_1h" if interval == "1h" else "binance_spot_1d"
    parts = [_vision_csv(p) for p in sorted((RAW / sub / symbol).glob("*.csv"))]
    tail = RAW / "binance_tail" / f"{symbol}.json"
    if interval == "1h" and tail.exists():
        raw = json.loads(tail.read_text())
        if raw:
            a = np.array([[float(x) for x in r[:6]] for r in raw])
            parts.append(pd.DataFrame({"open": a[:, 1], "high": a[:, 2], "low": a[:, 3], "close": a[:, 4],
                                       "volume": a[:, 5]}, index=pd.to_datetime(a[:, 0].astype("int64"), unit="ms")))
    df = pd.concat(parts)
    df = df[~df.index.duplicated(keep="first")].sort_index()
    if interval == "1h":
        now = pd.Timestamp.now("UTC").tz_localize(None).floor("h")
        df = df[df.index < now]
    return df


def load_coinbase(product: str) -> pd.DataFrame:
    df = pd.read_csv(RAW / "coinbase" / f"{product}_1h.csv")
    df.index = pd.to_datetime(df["time"], unit="s")
    df = df.drop(columns="time").sort_index()
    now = pd.Timestamp.now("UTC").tz_localize(None).floor("h")
    return df[df.index < now]


def load_rf_daily() -> pd.Series:
    df = pd.read_csv(RAW / "fred" / "DTB3.csv")
    df.columns = ["date", "v"]
    s = pd.to_numeric(df["v"], errors="coerce")
    s.index = pd.to_datetime(df["date"])
    s = s.dropna() / 100.0
    full = s.reindex(pd.date_range(s.index[0], pd.Timestamp.now().normalize() + pd.Timedelta(days=1), freq="D"))
    return full.ffill()


@dataclass
class Panel:
    idx: pd.DatetimeIndex
    bn_btc: pd.Series
    cb_btc: pd.Series
    prime: pd.Series
    prime_eth: pd.Series
    depeg: pd.Series
    z: pd.Series
    z_nofilter: pd.Series
    vol: pd.Series
    rf_h: pd.Series


def rolling_z(p: pd.Series, valid: pd.Series, n: int = 720) -> pd.Series:
    s = p[valid & p.notna()]
    m = s.rolling(n, min_periods=n).mean()
    sd = s.rolling(n, min_periods=n).std()
    return ((s - m) / sd).reindex(p.index)


def build_panel(price_field: str = "close") -> Panel:
    cache = CACHE / f"panel_{price_field}.pkl"
    if cache.exists():
        return pd.read_pickle(cache)
    bb, be = load_binance("BTCUSDT"), load_binance("ETHUSDT")
    cb, ce = load_coinbase("BTC-USD"), load_coinbase("ETH-USD")

    def px(df: pd.DataFrame) -> pd.Series:
        if price_field == "close":
            return df["close"]
        return (df["open"] + df["high"] + df["low"] + df["close"]) / 4

    start = max(bb.index[0], cb.index[0])
    end = min(bb.index[-1], cb.index[-1])
    idx = pd.date_range(start, end, freq="h")
    bnb, cbb = px(bb).reindex(idx), px(cb).reindex(idx)
    bne, cbe = px(be).reindex(idx), px(ce).reindex(idx)
    p = np.log(cbb / bnb)
    pe = np.log(cbe / bne)
    depeg = (p.abs() > 0.01) & (pe.abs() > 0.01) & (np.sign(p) == np.sign(pe))
    z = rolling_z(p, ~depeg)
    z0 = rolling_z(p, pd.Series(True, index=idx))
    close = bb["close"].reindex(idx)
    r = close.ffill().pct_change()
    r[close.isna()] = np.nan
    vol = r.rolling(720, min_periods=600).std() * np.sqrt(8760)
    rf = load_rf_daily()
    rf_h = (rf.reindex(idx.normalize()).values / 8760.0)
    panel = Panel(idx, close, cb["close"].reindex(idx), p, pe, depeg, z, z0, vol,
                  pd.Series(rf_h, index=idx).fillna(0.0))
    CACHE.mkdir(parents=True, exist_ok=True)
    pd.to_pickle(panel, cache)
    return panel


def run_strategy(pn: Panel, h: int = 24, thr: float = 2.0, delay: int = 0, use_filter: bool = True,
                 trade_px: pd.Series | None = None, vol_target: float = 0.10, wcap: float = 3.0,
                 z: pd.Series | None = None, sides: tuple[int, ...] = (1, -1)) -> pd.DataFrame:
    """Liste de trades non chevauchants. Retourne entry (bougie du signal + delay), exit, side, w, ret (brut prix)."""
    zz = z if z is not None else (pn.z if use_filter else pn.z_nofilter)
    px = trade_px if trade_px is not None else pn.bn_btc
    sig = pd.Series(0, index=pn.idx)
    sig[zz > thr] = 1
    sig[zz < -thr] = -1
    cand = np.flatnonzero(sig.values != 0)
    pxv = px.values
    vol = pn.vol.values
    sv = sig.values
    rows = []
    nxt = -1
    n = len(pn.idx)
    for i in cand:
        if i < nxt:
            continue
        s = int(sv[i])
        if s not in sides:
            continue
        e = i + delay
        x = e + h
        if x >= n:
            break
        if not (np.isfinite(pxv[e]) and np.isfinite(pxv[x]) and np.isfinite(vol[i]) and vol[i] > 0):
            continue
        w = min(vol_target / vol[i], wcap)
        rows.append((pn.idx[i], pn.idx[e], pn.idx[x], i, e, x, s, w, s * (pxv[x] / pxv[e] - 1.0), zz.values[i]))
        nxt = i + h
    return pd.DataFrame(rows, columns=["signal", "entry", "exit", "i", "e", "x", "side", "w", "ret", "z"])


def daily_pnl(pn: Panel, trades: pd.DataFrame, px: pd.Series | None = None, cost_rt: float = 0.0,
              extra_cost: pd.Series | None = None, start: pd.Timestamp | None = None,
              end: pd.Timestamp | None = None) -> pd.Series:
    """Série quotidienne UTC en excès du cash : somme des P&L horaires s·w·(r − rf), zéros à plat.

    Le rendement de la bougie b (close b−1 → close b) est daté du jour de b. Coût aller-retour × w au jour d'entrée.
    extra_cost : coût additionnel par trade (fraction du notionnel, signé = payé), indexé comme trades.
    """
    p = (px if px is not None else pn.bn_btc).ffill()
    r = p.pct_change().fillna(0.0).values
    rf = pn.rf_h.values
    pos = np.zeros(len(pn.idx))
    for e, x, s, w in zip(trades["e"].values, trades["x"].values, trades["side"].values, trades["w"].values):
        pos[e + 1:x + 1] = s * w
    hourly = pos * (r - rf)
    ser = pd.Series(hourly, index=pn.idx)
    cost = pd.Series(0.0, index=pn.idx)
    if len(trades):
        c = trades["w"].values * cost_rt
        if extra_cost is not None:
            c = c + trades["w"].values * extra_cost.values
        np.add.at(cost.values, trades["e"].values, c)
    d = (ser - cost).groupby(pn.idx.normalize()).sum()
    s0 = start if start is not None else d.index[0]
    e0 = end if end is not None else d.index[-1]
    return d.loc[s0:e0]


def sharpe(d: pd.Series, ann: float = 365.0) -> float:
    sd = d.std()
    return float(d.mean() / sd * np.sqrt(ann)) if sd > 0 else np.nan


def hac_t(x: pd.Series | np.ndarray, lags: int = 6) -> float:
    x = np.asarray(x, dtype=float)
    res = sm.OLS(x, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(res.tvalues[0])


def block_boot_ci(d: pd.Series, B: int = 2000, block: int = 10, seed: int = 7, ann: float = 365.0) -> tuple[float, float]:
    """Bootstrap stationnaire (Politis-Romano), blocs géométriques de moyenne `block`."""
    rng = np.random.default_rng(seed)
    x = d.values
    n = len(x)
    new_block = rng.random((B, n)) < 1.0 / block
    new_block[:, 0] = True
    starts = rng.integers(0, n, size=(B, n))
    # position = départ du bloc courant + rang dans le bloc
    pos_in = np.arange(n)[None, :] - np.maximum.accumulate(np.where(new_block, np.arange(n)[None, :], 0), axis=1)
    first = np.take_along_axis(starts, np.maximum.accumulate(np.where(new_block, np.arange(n)[None, :], 0), axis=1), axis=1)
    idx = (first + pos_in) % n
    y = x[idx]
    sd = y.std(axis=1)
    out = np.where(sd > 0, y.mean(axis=1) / np.where(sd > 0, sd, 1) * np.sqrt(ann), 0.0)
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def maxdd(d: pd.Series) -> float:
    c = d.cumsum()
    return float((c - c.cummax()).min())


def summary(d: pd.Series, ci: bool = False, ann: float = 365.0) -> dict:
    out = {"start": str(d.index[0].date()), "end": str(d.index[-1].date()), "days": len(d),
           "sharpe": sharpe(d, ann), "t_hac": hac_t(d), "ann_ret": float(d.mean() * ann),
           "ann_vol": float(d.std() * np.sqrt(ann)), "maxdd": maxdd(d), "worst_day": float(d.min()),
           "best_day": float(d.max()), "skew": float(d.skew())}
    if ci:
        out["ci95_lo"], out["ci95_hi"] = block_boot_ci(d, ann=ann)
    return out


def mde_sharpe(n_days: int, ann: float = 365.0, alpha: float = 0.05, power: float = 0.80) -> float:
    """Sharpe annualisé minimum détectable (test unilatéral, approximation SE ≈ 1/√T en années)."""
    from scipy.stats import norm
    years = n_days / ann
    return float((norm.ppf(1 - alpha) + norm.ppf(power)) / np.sqrt(years))
