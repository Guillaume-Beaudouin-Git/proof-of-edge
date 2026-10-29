# core — the research engine

| package | what it does |
|---|---|
| `reporting/` | excess returns over the FRED T-bill rate, HAC (Newey–West, lag 6) Sharpe, probabilistic and deflated Sharpe, drawdowns, the metrics table |
| `validation/` | combinatorial purged cross-validation (`cpcv.py`), multiple-testing corrections (`multi_test.py`: Deflated Sharpe, Harvey–Liu BHY), the HTML report pipeline |
| `risk/` | equal-risk-contribution and inverse-volatility sizing, rolling-correlation alerts, the prop-firm barrier Monte-Carlo simulator |
| `admission/` | the test a candidate sleeve must pass to enter the book: ΔSharpe at ERC weight, stationary block bootstrap, minimum detectable effect, barrier p(pass) |

Tests live next to each package (`*/tests/`); `uv run pytest -q` runs them all. The study scripts under
`studies/` are kept as they were run and are not part of the package.
