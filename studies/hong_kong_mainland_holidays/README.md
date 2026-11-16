# hong_kong_mainland_holidays — what is published here

**The idea, and how it turned around.** When mainland China is on holiday and Hong Kong trades,
the mainland buyer is absent (no southbound Stock Connect flow). The first hypothesis (FBL-10)
was that Hong Kong should be *weak* on those days. It was pre-registered, read once, and
**falsified with the opposite sign**: Hong Kong is *stronger* on those days (+27.7 bps against
ordinary days, t 2.51, 2014–2026).

A post-hoc reversal proves nothing, so the reverse hypothesis (FBL-10b) was pre-registered in
turn and tested on a period never read before, 1997-07 → 2014-11, which also predates Stock
Connect:

| leg | threshold | measured | t_HAC | |
|---|---|---|---:|---|
| days Hong Kong trades and Shanghai is closed (n 221) | ≥ +10 bps | **+21.9 bps** | 2.95 | holds |
| first day both markets reopen (n 78) | ≤ −15 bps | **−32.3 bps** | −2.32 | holds |

So the effect is a mainland-holiday calendar effect, older than Stock Connect, measured on two
independent periods. A control on days when *only Hong Kong* was closed shows nothing
(t between −0.7 and +1.0): it is not a generic post-holiday effect.

**The trade.** Buy the Hong Kong index at the open and sell at the close on mainland-holiday
days; sell at the open and buy back at the close on the first common reopening. About ten
holiday days and four to five reopenings a year. Net per trade +19.8 bps combined (standard
error 5.6) at an assumed 4 bps cost, positive in five folds out of five (1997–2026).

**Verdict: launch, conditional on the real cost of the broker's HK50 contract (2026-10-19,
re-verified 2026-10-20).** Deployed in the live Expert Advisor since early November 2026 at
$3,000 notional, **disarmed: it has not traded yet**, pending the cost measurement and the
holiday calendar.

**Reading order.** `PREREG.md` → `RAPPORT.md` (the falsified first hypothesis) →
`PREREG_ENVERS.md` → `RAPPORT_ENVERS.md` (the replicated reverse and the launch decision). Code
under `code/`, outputs under `out/`. Data: Yahoo daily series of the Hang Seng and Shanghai
indices, fetched by `code/fetch.py` and `code/fetch_pre.py`, not redistributed.

**Language.** The documents are the French originals, unedited; this README is the English
summary.
