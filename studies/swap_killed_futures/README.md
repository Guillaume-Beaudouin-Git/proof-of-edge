# swap_killed_futures — what is published here

Nine pre-registered hypotheses (H1–H9) on retail-accessible futures and ETF premia, re-examined
on a venue without CFD swap, then a roll audit of the survivors.

Published: `PREREGISTRATION.md`, the per-hypothesis addenda `PREREG_H4` … `PREREG_H9`, the
results files `RESULTS_H1` … `RESULTS_H9` (H2 was deferred for lack of curve data and has none),
`ROLL_AUDIT.md`, and `AUDIT_book.py`, the independent re-audit that rebuilds the sleeve returns
saved in `audit_sleeve_returns.parquet`.

Not published: the per-hypothesis engines (`engine_h*.py`) referenced in the pre-registration.
They depend on the private data lake and are not self-contained.

Account sizes in these documents are expressed as a "small personal account" or as an index
(start = 100); the original figures were a specific personal balance.
