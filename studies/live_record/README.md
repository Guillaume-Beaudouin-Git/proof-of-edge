# Live record — the FTMO funded account

The page: [`docs/live/index.html`](../../docs/live/index.html) (served from `/docs` by GitHub
Pages). The numbers: [`summary.json`](summary.json), [`data/equity_daily.csv`](data/equity_daily.csv),
[`data/trades.csv`](data/trades.csv). The external anchor, independent of this repository:
the [FTMO verified trader profile](https://profile.ftmo.com/user/E6X6MTH381).

This folder is the file that the README's status table used to say was missing. It is a
self-reported record of a small account over a short history; the section *Limitations* says
what that means. Nothing in it is a claim of edge.

## What is recorded

A $10 000 FTMO funded account (Swing programme, two-step evaluation passed on the challenge
accounts before it), traded by the automated book described in the root README: overnight index
exposure on US100 and GER40 (Monday and Tuesday nights), and an opening-range breakout on US100.
The account was funded on 2026-08-17; the first snapshot of the funded account is the
2026-08-18 00:00 Paris mark, the first trade is on 2026-08-18.

## Provenance

No broker statement is used. The source is the runtime ledger of the live system itself, read
from the server it runs on, copied read-only on 2026-10-30 and reduced by `build_record.py extract`
to the extracts in `source/`:

| extract | origin | what it holds |
|---|---|---|
| `snapshots.csv` | the Expert Advisor's `state.json` as archived by the supervisor at 00:00 Paris (start-of-day) and at 22:58 Paris (end-of-day block), one row per calendar day | the broker's **balance and equity** as the terminal reports them, the EA's daily floor and static floor, which snapshot served as the close |
| `positions.csv` | the open positions listed in the same snapshots | instrument, lots, direction, notional in USD, per mark |
| `point_values.csv` | the contract specifications the EA exports at each start-of-day (`tick_value / tick_size`) | USD per index point per lot, per day: how GER40 (quoted in EUR) is converted |
| `fills.csv` | the EA's own fill log (one line per order it sent: requested price, fill price, slippage, latency) | every fill of the funded account |
| `swaps.csv` | the EA's log of the swap the broker billed per instrument and night | overnight financing actually paid |
| `reconcile.csv` | the nightly reconciliation log (real P&L of the day against a replay of the model on the day's prices, with a tolerance) | a diagnostic that the live system did what the model said |
| `adjustments.csv` | written by hand | balance changes that are not trading (see below) |

Dropped on purpose at extraction: order, deal and position tickets, magic numbers, the MT5
comment field, any path. Broker symbols are reduced to the instrument name. Account identifiers
never enter the runtime files that are read.

The SHA-256 of each extract is in `summary.json` and printed in the page footer; the page is
built by `build_record.py build`, which is a pure function of `source/` (the test
`test_committed_outputs_match_committed_source` rebuilds `summary.json` and `equity_daily.csv`
from the committed extracts and compares).

**How a reader can verify.** The FTMO profile linked above is published by the firm and shows the
account's verified status and its statistics as the firm computes them; it is the only
independent source. A broker statement (MetaTrader 5 "Account history" report, HTML or XLSX
export of the deals) would be the second one, and is not yet in this repository: it is the
next addition, and `extract` will take it as a cross-check of `fills.csv` and `swaps.csv` when
it is. Until then, the equity series rests on the terminal's own balance and equity as logged
by the EA, and the trade table on the EA's fill log.

## Methodology

**Marks.** Two marks per trading day: 00:00 Paris (the start-of-day snapshot, taken after the
broker has posted the night's swaps) and 22:58 Paris (the EA's end-of-day block; when the
broker's close-of-day tick freeze prevents that block, the pre-swap close at about 22:54 is used
and the row says `preswap_close`). Weekend 00:00 marks exist and are used for drawdown and
barrier distances, not as trading days.

**Daily P&L.** For trading day *d*, equity at the next trading day's 00:00 mark minus equity at
*d*'s 00:00 mark, both with external adjustments removed. The column sums exactly to the total.
A Friday therefore runs to Monday 00:00. The last row is the open day and carries no P&L.

**External adjustments.** A balance change with no fill and no swap behind it is not trading.
One is declared in `adjustments.csv`: on 2026-10-01 the balance went from $10 010.78 (flat close
of 2026-09-30) to $10 000.00. That is what an FTMO payout does (a withdrawal brings the balance
back to the initial capital); the statement that would document it is not in this repository,
so the row says so. The equity curve, the drawdown and the P&L exclude it; the page lists it.

**Drawdown.** On the trading-only equity curve (initial balance plus cumulative daily P&L),
distance to its running maximum, with the high-water mark never below the initial balance.
In dollars and in percent of the initial balance.

**FTMO barriers.** Daily loss: the account must not fall more than 5 % of the initial balance
below the balance recorded at 00:00 CE(S)T, so the floor is that balance minus $500 (the EA's
`daily_floor`, taken from the snapshot). Maximum loss: static, initial balance minus 10 %, so
$9 000. The distance reported for a day is the lowest mark in the day's window minus the floor;
**intraday lows are not in the export**, so the true closest approach can only be smaller than
what is shown. The percentage of the daily limit used by the worst day is that day's loss over
$500.

**Trades.** The fill log is paired into round trips per instrument and sleeve: entry reasons
(`ger40_on`, `rebalance`, `funded_orb_entry`, ...) open, the others close, oldest entry first.
Trade P&L is points times lots times the USD point value of the exit day, gross of swaps; FTMO
indices carry no commission. Two entries have no logged exit (the EA logs the orders it sends;
a server-side stop or a kill-file flatten is not logged): a 0.60-lot ORB short of 2026-09-07
closed on 2026-09-08, and a 0.04-lot gold short of 2026-09-29 closed by the flatten of
2026-09-30. Their P&L is in the equity series; they are absent from the trade statistics, which
is why gross trade P&L plus swaps does not equal the equity P&L.

**Exposure.** From the positions listed at each mark: the share of marks with a position in
the instrument, the average and maximum notional when held, and the average notional over all
marks as a share of the initial balance.

**Reconciliation.** Each night the live system replays the day in the research engine with the
real fills and compares the real P&L with the model's, with a tolerance of $5 plus a few basis
points of turnover and book. The page reports how many nights were logged, how many were
flagged above tolerance, and the largest residual. A flag is a question, not a verdict.

## Limitations

- **Self-reported.** The source is the system's own log of what the terminal showed it. The FTMO
  profile is the only external anchor; a broker statement is the missing second one.
- **Small account, short history.** Ten weeks, 54 trading days, 76 round trips, on $10 000. The
  daily P&L has a t-statistic near zero. Nothing here distinguishes the book from noise, and
  the page does not try to; it records what happened.
- **Two marks a day.** Barrier distances and drawdowns are on the 00:00 and 22:58 marks. The
  intraday path is not published.
- **The fill log is the EA's, not the broker's.** Two round trips are missing from the trade
  table for that reason (listed on the page). The equity series does not depend on the fill log.
- **Sleeve changes during the record.** The gold and USDJPY sleeves of the deployed book were
  switched off on 2026-09-30 / 2026-10-01 (the gold short of 2026-09-29 is the only gold trade
  in the window); the ORB has been long-only and gated since 2026-10-01 and was paused by its
  own gate at the end of October. The record covers the account as traded, not one fixed
  specification.

## Rebuilding

```
uv run python studies/live_record/build_record.py build
uv run pytest -q studies/live_record/tests
```

`extract` is the author's step: it needs the raw runtime folder and the terminal's files folder,
neither of which is distributed.
