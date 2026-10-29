"""HAC (Newey-West) mean test, block-bootstrap placebo, and endogenous break
test (sup-statistic + block bootstrap) -- hand-written vectorised
implementations (fast, called thousands of times inside the bootstrap loops;
validated against statsmodels in `__main__`).
"""
from __future__ import annotations

import numpy as np


def hac_mean_t(x: np.ndarray, lag: int = 6) -> tuple[float, float, float, int]:
    """Return (mean, se_hac, t, n) for H0: E[x] = 0, Newey-West lag `lag`."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < max(10, lag + 2):
        return float("nan"), float("nan"), float("nan"), n
    mean = x.mean()
    d = x - mean
    gamma0 = float(np.dot(d, d) / n)
    lrv = gamma0
    for l in range(1, lag + 1):
        if l >= n:
            break
        w = 1.0 - l / (lag + 1)
        gl = float(np.dot(d[l:], d[:-l]) / n)
        lrv += 2.0 * w * gl
    lrv = max(lrv, 1e-12)
    se = np.sqrt(lrv / n)
    t = mean / se if se > 0 else float("nan")
    return mean, se, t, n


def block_bootstrap_null_pvalue(x: np.ndarray, lag: int = 6, n_boot: int = 4000,
                                 block: int = 20, seed: int = 0,
                                 recenter: bool = True) -> dict:
    """Matched placebo: block bootstrap (Politis-Romano, fixed blocks of size
    `block`, drawn with replacement) under H0 (series recentred to 0 if
    `recenter`), the same HAC statistic recomputed on each replicate.
    p = P(|t_boot| >= |t_obs|)."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    mean_obs, se_obs, t_obs, _ = hac_mean_t(x, lag)
    base = x - mean_obs if recenter else x
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    starts_pool = np.arange(0, max(n - block, 1))
    t_boot = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, len(starts_pool), size=n_blocks)
        idx = np.concatenate([np.arange(s, min(s + block, n)) for s in starts_pool[starts]])
        idx = idx[:n]
        xb = base[idx]
        _, _, t_b, _ = hac_mean_t(xb, lag)
        t_boot[b] = t_b
    p = float(np.mean(np.abs(t_boot) >= abs(t_obs)))
    return dict(mean=mean_obs, se=se_obs, t=t_obs, n=n, p_block_bootstrap=p,
                n_boot=n_boot, block=block)


def endogenous_break_search(x: np.ndarray, lag: int = 6, min_seg: int = 90,
                             step: int = 10) -> dict:
    """Sup-statistic for a break at an UNKNOWN date: for each candidate k
    (indices spaced by `step`, min_seg observations on each side),
    t = (mean_post - mean_pre) / sqrt(se_pre^2 + se_post^2) (HAC lag 6 on each
    segment). Returns the k that maximises |t| and the associated statistic (to
    be compared with its own bootstrap distribution, see
    `break_bootstrap_pvalue`)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    best = dict(k=None, t=0.0, mean_pre=np.nan, mean_post=np.nan)
    for k in range(min_seg, n - min_seg, step):
        pre, post = x[:k], x[k:]
        m0, s0, _, n0 = hac_mean_t(pre, lag)
        m1, s1, _, n1 = hac_mean_t(post, lag)
        if not (np.isfinite(s0) and np.isfinite(s1)):
            continue
        se = np.sqrt(s0 ** 2 + s1 ** 2)
        if se <= 0:
            continue
        t = (m1 - m0) / se
        if abs(t) > abs(best["t"]):
            best = dict(k=k, t=t, mean_pre=m0, mean_post=m1, n_pre=n0, n_post=n1)
    return best


def break_bootstrap_pvalue(x: np.ndarray, lag: int = 6, min_seg: int = 90,
                            step: int = 10, n_boot: int = 300, block: int = 15,
                            seed: int = 1) -> dict:
    """p-value of the break sup-statistic: BLOCK bootstrap (permutes the order of
    the blocks, destroying any true chronological break structure while
    preserving local autocorrelation); the same candidate scan is redone on
    each replicate -> natively corrects for the search over several break
    points (no separate Sidak correction is needed for THIS test, it is in the
    bootstrap)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    obs = endogenous_break_search(x, lag, min_seg, step)
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    starts_pool = np.arange(0, max(n - block, 1))
    t_boot = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, len(starts_pool), size=n_blocks)
        idx = np.concatenate([np.arange(s, min(s + block, n)) for s in starts_pool[starts]])
        idx = idx[:n]
        xb = x[idx]
        rep = endogenous_break_search(xb, lag, min_seg, step)
        t_boot[b] = rep["t"]
    p = float(np.mean(np.abs(t_boot) >= abs(obs["t"])))
    obs["p_break_bootstrap"] = p
    obs["n_boot"] = n_boot
    return obs


def sidak_threshold(n_tests: int, alpha: float = 0.05) -> float:
    """|t| threshold (normal approximation) for Sidak at n_tests, global two-sided alpha."""
    from scipy.stats import norm
    alpha_per = 1.0 - (1.0 - alpha) ** (1.0 / n_tests)
    return float(norm.ppf(1.0 - alpha_per / 2.0))


if __name__ == "__main__":
    import statsmodels.api as sm
    rng = np.random.default_rng(0)
    x = rng.standard_t(4, size=500) * 2 + 0.3
    # AR(1)-like clustering
    for i in range(1, len(x)):
        x[i] += 0.3 * x[i - 1]
    m, se, t, n = hac_mean_t(x, lag=6)
    res = sm.OLS(x, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    print("manual  :", m, se, t)
    print("statsm. :", res.params[0], res.bse[0], res.tvalues[0])
    print("sidak(20)=", sidak_threshold(20), "sidak(2014)=", sidak_threshold(2014))
