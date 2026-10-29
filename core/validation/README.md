# core/validation — CPCV meta-methodology

Combinatorial Purged Cross-Validation (CPCV) for overfitting diagnosis, plus the
multiple-testing corrections used across the programme. Builds on `core/reporting/metrics.py`.

## Usage

```python
from core.validation.pipeline import generate_cpcv_report

path = generate_cpcv_report(
    returns=my_daily_returns,          # pd.Series, total returns
    strategy_name="My strategy",
    backtest_fn=my_backtest_fn,        # (train_idx, test_idx) -> float
    n_trials=322,                      # programme-wide trial count
    output_path="reports/my_strategy_cpcv.html",
    wf_baseline_sharpe=0.8,            # the walk-forward OOS Sharpe to compare against
)
```

`backtest_fn` must be self-contained: it receives integer index arrays into the returns
series and returns the out-of-sample Sharpe for that path.

## Files

| File | Purpose |
|------|---------|
| `cpcv.py` | `run_cpcv()` — CPCV engine via skfolio |
| `multi_test.py` | `deflated_sharpe()`, `harvey_liu_bhy()` |
| `pipeline.py` | `generate_cpcv_report()` — HTML report generator |
| `tests/test_cpcv.py` | the tests |

## CPCV vs walk-forward

| Dimension | Walk-forward | CPCV |
|-----------|--------------|------|
| Paths | 1 (expanding window) | C(k, k−p) × p (combinatorial) |
| Overfitting diagnostic | weak (single path) | strong (distribution of paths) |
| Computational cost | low | medium (scales with C(k, k−p)) |
| Correlated paths | n/a | yes — not iid, the CI is diagnostic only |

CPCV does not replace walk-forward; it diagnoses overfitting by showing whether the single
walk-forward path was a lucky draw from the full distribution.

## Scope

CPCV needs a large sample: ~250 trades over 3.5 years is not enough for 30+ paths with an
adequate train size. Apply it to daily series with N ≥ 1,500 observations.
