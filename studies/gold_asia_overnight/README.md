# gold_asia_overnight — what is published here

Long gold (XAUUSD) over the Asian session, 23:00 → 07:00 UTC, flat otherwise, vol-targeted,
entered after the broker's daily rollover so that no overnight financing is paid. The one
strategy of its family that met Sharpe > 1 (full sample and out of sample at ≤ 1.5 bp spread) and
DSR > 0.5, and that an independent risk audit found to be alpha rather than gold beta (β 0.01,
R² 0.001, α t 4.8).

Published, in reading order:

1. `reports/gold_overnight_strategy.md` — the finding and the rule.
2. `reports/gold_strategy_risk_audit.md` — look-ahead audit, beta regression, year-by-year,
   Monte-Carlo, top-day removal.
3. `reports/gold_ASIA_23_8_due_diligence.md` — the deployable variant, with its hard conditions
   (rollover time, spread, entry to the hour, long drawdowns).
4. `reports/metals_energy_due_diligence.md`, `reports/overnight_family_audit.md` — the same
   window on silver, WTI and others, and the family-level correlation audit.
5. `code/` — the research scripts (`eda.py`, `candidates.py`, `refine*.py`, `validate.py`,
   `risk_audit.py`, `stress_mc.py`, `audit_code.py`) and the reference implementation
   `strategy_overnight.py`, with the shared `engine/` package (data loading, backtest, stats,
   plotting) and the figures and summaries they produced under `code/results/`.

Not published: the minute-bar gold data (broker-sourced, true UTC, 2007–2026). The scripts expect
it under the data lake described in the top-level README.

Status in the programme: validated, not deployed on the FTMO account — the broker's
rollover time there puts the long swap back into the window and kills the edge (Sharpe −0.34);
the transfer to CME micro gold futures was studied separately.
