# month_end_treasury_flow — what is published here

Long the 10-year Treasury future (ZN) over the last three business days of each month, flat the
rest of the time: the month-end rebalancing flow into duration. The question of this study is not
whether the effect exists (it was found in an earlier hypothesis, see `studies/swap_killed_futures`,
H3) but on which vehicle, at which size, it is actually collectable.

Reproducible from public data: `uv run --extra studies python studies/month_end_treasury_flow/reproduce.py`
(Yahoo Finance daily series; the hourly steps use a rolling 730-day window and drift). The captured
output of the 2026-10-29 run is in `results/`.

Published: `RESULTS.md` (the full study: replication and split, session identification, hourly
shape, long-sample economics, prop-firm barrier simulation, vehicle verdict) and the seven scripts
under `code/`, one per step, in the order they were run.

Key figures (from `RESULTS.md`): on ZN, 2000–2026, the held window (18:00 → 15:00 ET over the
last three business days) returns +16.25 bps per event, t_HAC 4.79, 311 events, placebo
p = 0.0000; the frozen pre-registered figure was t 4.65. On the 5,554 other days the mean is
−0.13 bps (t −0.27): the effect is the flow, not duration beta. At one contract on a small
personal account: Sharpe 0.92 net of costs, twelve events a year.

Not published: the data (Yahoo and vendor futures series, fetched by `code/fetch_data.py`) and
the personal account figures, replaced by "small personal account".

Status in the programme: validated; not deployable on the FTMO account (no bond
instruments in its universe); deployable on a personal futures account at one contract.
