# overnight_index_premium — what is published here

The deployed sleeve: long US100 and GER40 from just after the cash close to the next cash open,
on Monday and Tuesday nights. This dossier (September 2026) answers one question the programme had left
open for two months: does Monday deserve to be traded, or had it "collapsed since 2022"?

Published: `DOSSIER_OVERNIGHT.md` (translated from the French original), the three scripts under
`code/` (independent reconstruction from minute bars, statistics library with HAC, block bootstrap
and endogenous break search, and the analysis that produces every numbered section), and the raw
outputs under `results/` (the reconstructed overnight series for both indices, the results JSON
and the run logs; the two `.txt` logs are the original run's output and are in French, the
script's messages were translated afterwards and a re-run reproduces them in English).

What the dossier establishes: per-day t-statistics never clear the programme's cumulative Šidák
threshold; the pooled Monday + Tuesday test — the object actually deployed — does clear it gross
for US100 (t = 4.65 > 4.21) and nearly for GER40 (4.18); no break in Monday survives a
search-corrected test (p = 0.43–0.61); cutting Monday would remove half the net contribution and
keep the night with the fatter tail. The midweek selection is also documented as post-hoc, with its
unresolved DSR 0.29 caveat, and the dossier says so.

Not published: the live configuration (weights, exact timestamps), the account identifiers, the
broker, and the June 2026 documents the dossier cites.
