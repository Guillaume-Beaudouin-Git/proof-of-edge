# proof-of-edge

[![tests](https://github.com/Guillaume-Beaudouin-Git/proof-of-edge/actions/workflows/tests.yml/badge.svg)](https://github.com/Guillaume-Beaudouin-Git/proof-of-edge/actions/workflows/tests.yml)

Systematic trading research, run solo, with one rule: **a strategy is guilty until proven
innocent, and most of them stay guilty.**

This is the public part of a private research programme started in 2024: a **research
pipeline** that takes a trading idea from a written hypothesis to a verdict and, for the few
that earn it, to a live automated book on a prop-firm (FTMO) account. It holds the research
engine, the method, and nine complete studies, each with its results and its verdict, its
pre-registration where one was written, and its code where the code is self-contained. The
record of how the survivors earned their place, and of what was rejected along the way, is
what is published here.

---

## The pipeline, in numbers (2026-11-16)

| stage | count |
|---|---|
| Pre-registration files written in the private programme | 148, across 122 study folders |
| Of those folders, readable in the public [research-archive](https://github.com/Guillaume-Beaudouin-Git/research-archive) (snapshot of 2026-10-29) | 57 |
| Studies written up in full in this repository | 9: three validated, two falsified, one open, two approved for launch, one kept on paper |
| Strategies trading on the FTMO account today | 1 (overnight index premium) |
| Approved for launch, deployed in the live system, not yet armed | 2 (USDJPY settlement days, Hong Kong on mainland holidays) |

Most ideas never reach the third row. That is the pipeline working. The first row is read from
the private repository and cannot be checked from this one.

---

## Status — November 2026

| | |
|---|---|
| **Live** | A fully automated book on an FTMO account (\$10k of simulated capital, real payouts; Swing two-step): both phases passed in 23 days with zero manual trades, live since August 2026 |
| **Live record** | 89 days (64 trading days) over two consecutive FTMO logins, chained; P&L **+$35.48** (+0.35 %), max drawdown **−2.12 %**, closest approach to the daily-loss floor $414 of a $500 allowance — [page](https://guillaume-beaudouin-git.github.io/proof-of-edge/live/) ([source](docs/live/index.html)) · [equity_daily.csv](studies/live_record/data/equity_daily.csv) · [trades.csv](studies/live_record/data/trades.csv) · [summary.json](studies/live_record/summary.json) · [method and provenance](studies/live_record/README.md) · [FTMO verified profile](https://profile.ftmo.com/user/E6X6MTH381). Self-reported from the system's own ledger; a broker statement is the next addition |
| **Execution** | MetaTrader 5 Expert Advisor on a Linux VPS, fed by a Python signal engine, under a watchdog, with a nightly replay of the model against the real P&L (the gap between the two is reported in the live record, and is not closed) |
| **Book** | Trading: the overnight index premium (US100, GER40). Deployed since early November 2026 and not yet armed, so never traded: `studies/gotobi_usdjpy` and `studies/hong_kong_mainland_holidays`. Paused: the opening-range breakout sleeve (since 2026-10-19). Switched off: gold and the earlier USDJPY sleeve (since 2026-09-30) |

The account is small and so are the returns. That is the point: the pipeline's first job is to
**falsify**, and making money comes second. The live system and the account identifiers stay
private; what is published is the method and the studies.

---

## How research works here

Five rules, each written after a specific failure.

**1. Pre-registration.** Hypothesis, signal construction, universe, metrics and **kill rules** are
frozen in a pre-registration file *before the data is touched*. Kill rules are not renegotiated
after seeing results. One study breaks this openly and says how: `studies/gotobi_usdjpy`. When a verdict later needs revisiting, an **amendment** is appended — never
an edit. `PROVENANCE.md` gives, for each study, the commit that froze the pre-registration and the
one that added the results, and `PREREGISTRATION_FREEZE.md` the SHA-256 of each pre-registration at
that commit: the version control of this repository proves the order for two of the nine studies; for
the other seven the order is documented inside the files only (for the three studies added in
November 2026, by private commits listed in `PREREGISTRATION_FREEZE.md`), and the studies say so.

**2. Measure the cost on the venue you actually trade.** A strategy was killed for weeks on a
spread borrowed from a different broker; measured natively on the account actually traded, the true cost was
about half (`LESSONS.md`, L63). A passive sampler now runs inside the live EA and records the real
bid/ask every minute.

**3. Read the distribution, never the maximum.** Testing hundreds of variants of one idea is not
data-mining *if the deliverable is the shape of the result distribution*. A real mechanism makes
its whole neighbourhood positive; a dead one produces a t-distribution indistinguishable from
noise. The maximum of N noisy trials is always impressive — it is compared against its own null.

**4. A matched placebo, every time.** Three separate false positives were caught this way in a
single week — including one that cleared every gate (18/18 cells at t > 2.5, positive after
costs) and turned out to be an artifact of **path-dependent position sizing**, invisible to
HAC standard errors because it lives in the sizing, not the residual (L61).

**5. Adversarial audit.** Findings are re-derived by an independent pass whose job is to break
them. It has overturned the author's own conclusions more than once.

The hard rules the engine enforces: signal at T−1, trade at T; excess returns over cash; HAC
standard errors (lag 6); walk-forward with at least five folds, never a single split; daily
volatility targeting; a multiple-testing correction whenever more than one configuration was
tried (Šidák, Deflated Sharpe Ratio); block bootstrap, never iid; in the studies, annualisation by the
measured number of observations per year wherever the series is not daily (L47).

---

## What is in this repository

```
core/reporting/      excess returns, HAC Sharpe, probabilistic and deflated Sharpe, drawdowns
core/validation/     combinatorial purged cross-validation, multiple-testing control, report pipeline
core/risk/           volatility-targeted sizing, correlation monitoring, prop-firm barrier simulator
core/admission/      the test a new sleeve must pass to enter the book (ΔSharpe at ERC weight,
                     block bootstrap, minimum detectable effect)
studies/             complete studies: pre-registration, results, verdict, and code where self-contained
studies/live_record/ the FTMO account's record: source extracts, builder, daily equity and trades, summary
docs/live/           the static page built from it (GitHub Pages)
LESSONS.md           the numbered lesson registry: one verdict per lesson, with the number that earned it
PROVENANCE.md        where and when each study's pre-registration and results were committed
PREREGISTRATION_FREEZE.md  SHA-256 of each pre-registration at its freezing commit and at HEAD
```

### The studies

| study | question | verdict |
|---|---|---|
| `studies/gold_asia_overnight` | Does gold's drift concentrate in the Asian session, and can it be collected without paying overnight financing? | **Validated.** Long XAUUSD 23:00 → 07:00 UTC, entered after the rollover: Sharpe 1.07 out of sample at 1.5 bp spread, DSR 0.92, walk-forward 5/5, alpha not beta (R² 0.001); hard conditions on rollover time, spread and entry hour. Not deployed on the CFD prop-firm account (rollover puts the swap back). |
| `studies/month_end_treasury_flow` | The month-end flow into duration is real (ZN, 2000–2026: +16 bps per event over the last three business days, t_HAC 4.79, placebo p = 0.0000, −0.13 bps on every other day) — on which vehicle and at which size is it collectable? | **Validated**, vehicle-bound: not on the CFD prop-firm account (no bonds), yes on a personal futures account at one ZN contract. |
| `studies/overnight_index_premium` | The deployed sleeve (US100, GER40, Monday and Tuesday nights): does Monday deserve to be traded? | **Validated (gross), open (net).** Pooled Monday + Tuesday clears the cumulative Šidák threshold gross for US100 (t 4.65), nearly for GER40; no Monday break survives a search-corrected test; the midweek selection is documented as post-hoc with its unresolved DSR caveat. |
| `studies/crypto_flows_placebo` | Token-unlock drift on crypto: net +337 bps per event, t 2.90, DSR 0.94 — real? | **Falsified.** The effect sits below the median of a *matched placebo calendar* of random volatility-matched days on the same tokens; flat dose–response, no insider gradient. Pre-registration committed before the results (`PROVENANCE.md`). |
| `studies/trend_futures_funnel` | Does classical trend-following on a non-crypto futures universe earn a slot in the book, once the CFD swap that killed it elsewhere is removed? | **Falsified.** Swap-immune (Sharpe 0.50 → 0.47 at 3× frictions) but thin: the configurations that survive the two-sided test fail the DSR, and the one that survives the DSR fails the two-sided test. Four-phase funnel with its trial log (50 trials logged, 29 counted for the DSR). |
| `studies/swap_killed_futures` | Nine pre-registered hypotheses on retail-accessible futures and ETF premia (month-end bond flow, commodity seasonality, cointegrated spreads, vol carry, trend), each re-costed, then a roll audit | **Open.** Two sleeves survive (month-end Treasury flow, crack-spread grid; correlation 0.17) after the roll audit removes a third as a roll artifact (`ROLL_AUDIT.md`); one hypothesis is deferred for lack of curve data; the other five are closed with their cause named. H4–H9 each have a `PREREG_H*` addendum before their `RESULTS_H*`; H1 and H3 are covered by the main pre-registration. Results and the audit script are published; the per-hypothesis engines are not. |
| `studies/gotobi_usdjpy` | Does USDJPY rise into the Tokyo fixing and fall back after it on Japanese settlement days, enough to pay its cost, when the trade is restricted to the 25th and the month-end? | **Approved for launch, narrowly; deployed, not yet traded.** Holdout 2024-07 → 2026-05: +6.19 bps gross per event (n 44, t_HAC 2.52) against a measured cost of 1.87; shrunk expectation +2.1 bps net, about +$110 a year on $10k, one losing year in three. Two earlier pre-registered readings said archive; the decision overrides them, waives the programme's 3 × cost gate on the long sample, and says so |
| `studies/hong_kong_mainland_holidays` | Is Hong Kong weak when mainland China is on holiday and its buyers are away? | **First hypothesis falsified with the opposite sign; the reverse, pre-registered in turn, replicated on an untouched earlier period.** 1997–2014: +21.9 bps on mainland-holiday days (t 2.95), −32.3 bps on the first common reopening (t −2.32). Approved for launch conditional on the broker's real cost; deployed, not yet traded |
| `studies/coinbase_premium_btc` | Does a Coinbase-over-Binance premium on Bitcoin predict continuation? | **Real and reproduced, smaller than it looks; paper only.** Only the 24-hour horizon holds out of sample (1.88); reproduced by an independent code (0.982 daily correlation with the original run); expected net ≈ 0.75 on the one vehicle that fits a small account, with 5 episodes of 45 making 73 % of the holdout P&L. No capital committed |

Each folder reads the same way: the pre-registration first, then the results, then the code (see each folder's README for what is and is not published).
Figures and result tables are committed; raw market data is not (see below).

### Running the tests, and reproducing a study

```
uv sync --extra dev --extra studies
uv run pytest -q
uv run python studies/month_end_treasury_flow/reproduce.py
```

The third command downloads the daily series from Yahoo Finance and re-runs the month-end
Treasury-flow study end to end; its captured output is committed under
`studies/month_end_treasury_flow/results/` (run of 2026-10-29: +16.25 bps per event, t_HAC 4.79,
311 events, as in `RESULTS.md`).

The `core/` package is self-contained (numpy, pandas, scipy, statsmodels, skfolio, matplotlib, jinja2). The other
study scripts are kept as they were run; they expect the data lake described below and are not
exercised by the test suite.

---

## What is not here

- **The live system.** The Expert Advisor, the signal engine, the supervisor, the reconciliation
  and anything that touches an account.
- **Market data.** Studies reference a data lake (`RESEARCH_DATA_ROOT`) that is not distributed:
  minute bars from the broker, Databento tick data, vendor files. The result tables and figures
  are committed so that every number in a report can be checked against its source file.
- **Research in progress.** A study is added here once it has reached a verdict. The three
  studies added in November 2026 are published as the French originals with an English README.

---

## Reading this repository

Start with `LESSONS.md` — it is the compressed version of everything learned. Then open a
study's pre-registration to see what a study looks like before it knows its answer, and its
results file to see how a verdict is written.

Code drafted with a coding assistant (Claude Code) and reviewed line by line by the author; every
question, protocol, kill rule and verdict is the author's. The three studies added in November
2026 were drafted in French by AI agents under the author's direction, reviews included; the
launch, archive and capital decisions are his.
