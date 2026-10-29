# Overnight dossier — US100 / GER40: does Monday deserve to be traded?

*September 2026. Read-only re-analysis of the deployed overnight sleeve. Scope: the overnight leg
only — long US100 from five minutes after the cash close to the next cash open, long GER40 from
five minutes after the Xetra close to the next Xetra open, held on Monday and Tuesday nights. The
intraday breakout leg is handled by another study and is not duplicated here. Translated from the
French original; account identifiers and the live configuration file are not reproduced.*

*Code: `code/build_overnight.py` (independent reconstruction from minute bars) →
`code/stats_lib.py` (HAC, block bootstrap, endogenous break) → `code/analysis.py` (every numbered
section below). Raw outputs: `results/*.csv`, `results/analysis_results.json`,
`results/analysis_final_run.txt`, `results/partC_proxy.txt`.*

---

## Opening verdict

**KEEP Monday AND Tuesday.** Not because Monday passes a rigorous significance threshold — **it
passes none**, neither local nor cumulative, taken alone (t_HAC6 = 2.27–2.29 over the full period,
against a local Šidák threshold of 3.10 and a cumulative one of 4.21). But because:

1. **The test that matches what is actually deployed — Monday + Tuesday POOLED as ONE hypothesis —
   is far more robust**: gross, US100 clears the hardest cumulative threshold (t = 4.65 > 4.21) and
   GER40 is a hair below (t = 4.18); net of measured real costs (spread + swap, asymmetric), both
   fall back under the cumulative threshold (t = 2.92 / 2.73) but stay economically positive
   (≈ +5 bps per night net) with p_bootstrap < 0.02.
2. **No temporal break in Monday (or Tuesday) survives an honest correction for the date search**:
   leaving the break point entirely free (not imposed) and testing its significance by block
   bootstrap over the SAME scan, p = 0.43 to 0.61 in all four cells. The story "Monday collapsed
   since 2022" rests on a split chosen after the fact — I cannot distinguish it statistically from
   noise.
3. **Cutting Monday DEGRADES the sleeve's risk/return ratio instead of improving it**: Monday and
   Tuesday are nearly uncorrelated (r = −0.08 to −0.15, same week), so combining them diversifies
   almost ideally — the annualised Sharpe of the pool (0.73 US100 / 0.75 GER40) strictly dominates
   "Tuesday alone" (0.54 / 0.46).
4. **The operational history incriminates a bug, not Monday**: the two losses that specifically hit
   Monday nights (on an earlier account, July 2026) came from a software bug (GER40 skipped on
   Mondays, a stale flag), not from an intrinsically bad edge — fixing the bug solved the problem
   without touching the Monday/Tuesday calendar.

Figure to remember: **cutting Monday would remove ≈ 51 % of the sleeve's net economic contribution
(2013–2026 reconstruction) to remove only 50 % of the nights of exposure** — there is no free
lunch, and the "cheaper alternative" box (Part D) is not "Tuesday alone", it is "de-leverage both
nights".

---

## A. Is Monday dead?

### A.1 Method — independent reconstruction, labelling trap checked

Source: true-UTC M1 OHLC for US100 and GER40 (cached as parquet), 2013-01 → 2026-06-05. Cash
sessions used, anchored **in exchange time WITH daylight saving**:
- **US100**: 09:30–16:00 America/New_York (NASDAQ-100 cash)
- **GER40**: 09:00–17:30 Europe/Berlin (Xetra)

These are exactly the native hours that correspond to the deployed sleeve (entry five minutes
after the cash close, exit at the next cash open, for each index).

**The night is labelled by the day of ENTRY** (the day of the close being held), not the day of
the open — this was the trap flagged by the coordinating note. Explicit check (Section 2 of the
script): **Friday**-entry nights have a median calendar gap of 3 days to the next row (the
weekend), confirming that the weekend gap is carried by the "Friday" row, not "Monday". Labelling
by entry day is confirmed correct.

### A.2 Gross measurement, HAC lag 6, full sample (recomputed independently)

| US100 (2013-01 → 2026-06, N = 3,299) | mean bps | t_HAC6 | n |
|---|---:|---:|---:|
| **Monday** | 8.320 | 2.271 | 621 |
| **Tuesday** | 8.637 | 2.905 | 685 |
| Wednesday | 1.233 | 0.331 | 676 |
| Thursday | 0.513 | 0.195 | 664 |
| Friday | 1.943 | 0.588 | 653 |

| GER40 (2013-10 → 2026-06, N = 3,231) | mean bps | t_HAC6 | n |
|---|---:|---:|---:|
| **Monday** | 8.140 | 2.291 | 639 |
| **Tuesday** | 6.749 | 2.657 | 657 |
| Wednesday | −0.322 | −0.111 | 648 |
| Thursday | 2.348 | 0.999 | 648 |
| Friday | 1.966 | 0.511 | 639 |

Cross-validation against the coordinating note's table (same shape, slightly different
source/window/session): US100 Monday 8.32 / t 2.27 here vs 6.65 / t 1.98 there; Tuesday 8.64 / t
2.91 vs 9.77 / t 3.13; GER40 Monday 8.14 / t 2.29 vs 7.70 / t 2.17; Tuesday 6.75 / t 2.66 vs 6.45
/ t 2.42. Same sign, same order of magnitude, same hierarchy (Tuesday > Monday ≫ Wednesday /
Thursday / Friday) on two independent reconstructions — the qualitative pattern is confirmed, not a
pipeline artifact.

### A.3 Multiple testing — Šidák at the cumulative n

26 tests counted this session (5 days × 2 instruments = 10 in A.2, 4 block-bootstrap Mon/Tue in
A.4, 4 endogenous breaks in A.5, 4 net-of-cost in A.6, 4 joint tests in A.7). **Local Šidák
(n = 26): |t| > 3.10. CUMULATIVE Šidák (n = 1,994 + 26 = 2,020, the programme's canonical
ledger): |t| > 4.21.**

**None of the 4 individual Monday/Tuesday cells (US100/GER40) passes the local threshold, let alone
the cumulative one.** The coordinating note used a Šidák at 20 cells (threshold 3.02, which I
recover at 3.016 with `sidak_threshold(20)`) — the right LOCAL calculation on its own grid, but
**the programme's rule is the cumulative n**, not the local n ("Δn_tests > 0: count your tests,
Šidák threshold at the cumulative n"). At the cumulative n, even the note's strongest cell (US100
Tuesday, t = 3.13) fails.

### A.4 Matched placebo — block bootstrap (H0: zero mean), Monday and Tuesday only

Block bootstrap (Politis–Romano, blocks of 20 observations, 4,000 replicates, series recentred to
0) — no iid:

| | mean bps | t_HAC6 | n | p_block_bootstrap |
|---|---:|---:|---:|---:|
| US100 Monday | 8.320 | 2.271 | 621 | 0.0428 |
| US100 Tuesday | 8.637 | 2.905 | 685 | 0.0043 |
| GER40 Monday | 8.140 | 2.291 | 639 | 0.0522 |
| GER40 Tuesday | 6.749 | 2.657 | 657 | 0.0120 |

*(p-values from the committed run, `results/analysis_results.json`; the French original quoted an
earlier run of the same script, 0.045 / 0.009 / 0.057 / 0.013 — same conclusions.)*

At an uncorrected 5 %, 3 of the 4 cells would pass (GER40 Monday marginal, p = 0.052). **But none
would pass a threshold corrected at the cumulative n** (which would require p ≈ 2.5 × 10⁻⁵ for a t
equivalent to 4.21). The block bootstrap confirms the analytical HAC — per-day individual
significance holds at an uncorrected level, not at the level that matters for this programme.

### A.5 ENDOGENOUS break — estimated date, not imposed, corrected by block bootstrap

The coordinating note's 2018–21 / 2022–26 split was chosen **after seeing the shape of the data** —
exactly the trap it flags itself. Correct test: scan ALL candidate break points (every 10
observations, 90-observation margin on each side), take the MAXIMUM |t_diff| (pre vs post, HAC on
each segment), then block bootstrap (blocks of 15, 300 replicates, **the same scan redone on each
replicate**) to obtain a p that natively corrects for the search over multiple candidates:

| | estimated break | n pre/post | mean pre | mean post | t_diff | p (search-corrected) |
|---|---|---:|---:|---:|---:|---:|
| US100 Monday | 2023-03-20 | 470/151 | 11.44 | −1.39 | −1.93 | **0.433** |
| US100 Tuesday | 2024-05-28 | 580/105 | 6.67 | 19.49 | +1.66 | **0.613** |
| GER40 Monday | 2022-02-07 | 420/219 | 12.34 | 0.09 | −1.83 | **0.460** |
| GER40 Tuesday | 2024-03-12 | 540/117 | 4.01 | 19.38 | +1.73 | **0.500** |

**None of the four breaks is significant.** Even letting the machine freely choose the BEST possible
break date to maximise the apparent gap, the result is not distinguishable from noise once the
search is corrected. Remarkable point: the direction of the "break" is not even consistent — Monday
appears to decline (11.4 → −1.4 and 12.3 → 0.1 bps) while Tuesday appears to INCREASE over the
same recent window (6.7 → 19.5 and 4.0 → 19.4 bps). That is the signature of a noisy resampling of
one pooled process, not of two distinct and opposite regimes. **The 2018–21 / 2022–26 table — like
mine, had it been presented the same way — is a post-hoc reading of a point that is not
statistically identifiable.**

This puts the question in the **POWER** category of the programme's reopening policy: short
post-break subsample (105–219 observations) ⇒ **UNDERPOWERED, NOT REJECTED** — I can neither
confirm nor exclude a real Monday decline; I can only say that no break is demonstrated with the
current data.

### A.6 Net of real cost — spread AND swap, asymmetric (L30)

Costs applied per night held (Monday/Tuesday = 1× the swap; the triple-swap day for US100/GER40 is
Friday, not concerned):
- **Recent measured round trip** (native measurement on the account, week of 2026-08-17):
  US100 1.045 bps, GER40 1.017 bps — replaces the June placeholder figure (2.2 bps), kept below as
  a sensitivity.
- **Measured LONG swap** (MT5 points dated 2026-06-10): US100 −2.1257 bps/night, GER40 −1.564
  bps/night. L30 asymmetry confirmed (short US100 would be +0.0917, short GER40 −0.1933 — but the
  sleeve is LONG-only; the asymmetry would only matter if the other side were ever considered,
  which is not the case here).

| | gross (t) | net, recent cost (t) | net, June spec cost, conservative (t) |
|---|---:|---:|---:|
| US100 Monday | 8.32 (2.27) | **5.15 (1.41)** | 3.99 (1.09) |
| US100 Tuesday | 8.64 (2.91) | **5.47 (1.84)** | 4.31 (1.45) |
| GER40 Monday | 8.14 (2.29) | **5.56 (1.56)** | 4.38 (1.23) |
| GER40 Tuesday | 6.75 (2.66) | **4.17 (1.64)** | 2.99 (1.17) |

Cost eats 1 to 2 points of t but **flips the sign of no cell** — even at the conservative June
cost, net expectation stays positive in all four cells. The sleeve is therefore not in the L33 zone
(sign flip at cost).

### A.7 JOINT Monday + Tuesday test — what is actually deployed

This is the test that best matches the live spec (one hypothesis "Monday or Tuesday" rather than
two separate ones):

| | GROSS mean (t) | GROSS p_boot | NET mean (t) | NET p_boot |
|---|---:|---:|---:|---:|
| US100 (n = 1,306) | 8.49 (**4.65**) | 0.0000 | 5.32 (2.92) | 0.0088 |
| GER40 (n = 1,296) | 7.44 (**4.18**) | 0.0005 | 4.85 (2.73) | 0.0155 |

**US100 gross clears the hardest cumulative threshold (4.65 > 4.21). GER40 gross is just below
(4.18 vs 4.21) — at a test level that had never received a correction of this calibre before
today, that is remarkably close.** Net of real costs, both fall back under 4.21 but stay
economically positive (≈ +5 bps/night) with p_bootstrap < 0.02 (uncorrected).

**Conclusion of Part A**: Monday is not "dead" in the sense that a break could be demonstrated —
that break is NOT demonstrable, in either direction (underpowered). The sleeve as a whole (Monday +
Tuesday pooled, which is what is deployed) has a gross edge that clears the programme's hardest bar
for US100 and approaches it for GER40; net of real costs it drops below that bar but stays
economically positive. **Isolating Monday alone and judging it on its own t-statistic is
statistically the wrong test** — it never had the power to decide on its own.

---

## B. Was the "Monday + Tuesday" choice motivated or fortuitous?

**Post-hoc selection, documented and never resolved. Full archaeology:**

1. The June 2026 overnight verification report (dated 2026-06-03 in its body) is the document where
   the midweek concentration was DISCOVERED. It admits it explicitly (§4.6, verbatim):
   > "Day/night mapping … 6. Multiple testing — the robust figure is ALL nights (+4.90, t = 4.04),
   > not cherry-picked. **The midweek concentration is a post-hoc**, but **cross-confirmed
   > NQ + GER40 + US100** (3 markets, same day) → credible, not an isolated cell. Treat +4.9 as the
   > hard floor, midweek as the improvement."
   An honest acknowledgement at the time — but it is an admission of after-the-fact
   selection, not a pre-registration.

2. The overnight candidate log of the same date (2026-06-03) treats the "equity overnight premium"
   thesis in its ALL-NIGHTS version, with no mention of Monday/Tuesday specifically — confirming
   that on that date the canonical version of the edge was still "every night", not "midweek".

3. The canonical state document (§v2.1, after 2026-06-03) records the switch to the midweek
   selection and its statistical cost, verbatim:
   > "(5) Overnight: the load-bearing wall (+12.1 pts of ablation) BUT **DSR 0.29 FAIL on the
   > 40-cell selection grid (team)** → status: sleeve KEPT (massive funnel contribution, documented
   > mechanism, cross-confirmed on 3 markets by the archive) with **open selection caveat**;
   > **all-nights-vs-midweek sensitivity to be settled before signing**."
   DSR 0.29 is far below the L20 threshold (≥ 1.0–1.1) — the midweek selection, evaluated on its
   own search grid (40 cells, presumably day × instrument × window), formally fails the deflation
   test.

4. The live specification (dated 2026-06-10, **7 days after** the discovery) freezes
   `nights_held: Monday + Tuesday` in the challenge configuration AND in the deployed funded
   configuration — **without the DSR 0.29 caveat having been resolved**.

5. **The caveat was NEVER closed** — it is re-cited word for word in at least four later documents
   (the portfolio file, the pending canonical amendment, the timing attribution study — "Caveat
   maintained: the STANDALONE proof of the sleeve remains weak (DSR 0.29 vs its selection grid,
   audit); this verdict is in-container, not a validation of the signal per se" — and the
   vol-multiplier sweep pre-registration and study). Five citations of the same figure over more
   than two months, never followed by a formal resolution.

6. **No pre-registration earlier than 2026-06-03 exists.** Exhaustive search of `PREREG*` /
   `PRESPEC*` files in the June programme and the portfolio folder: every pre-registration that
   exists (nightly US100, overnight improvements, vol-multiplier sweep, gold Asia, soybean, gold
   dosing, funded anatomy) is dated **July 2026 or later**, i.e. after the midweek choice was
   already in production.

**Verdict of Part B: the selection is FORTUITOUS in the statistical sense (post-hoc, DSR-fail on its
own grid), MOTIVATED in the mechanism sense (cross-confirmed on 3 independent markets in the
founding document, which is a real safeguard against pure noise).** It was documented
honestly at the time (rare), but the resolve-before-signing clause was never honoured. My own
re-analysis (Part A, §A.7) is the first genuine attempt to settle this two-month-old caveat — and
the verdict it returns (gross edge robust at the pooled level, net positive but under the hardest
threshold) is closer to "survives a serious audit" than to "pure artifact", without being an
unreserved PASS.

**Additional point, outside the strict scope of the question but relevant to the recommendation**:
the nightly US100 pre-registration and verdict of July 2026 (on an earlier account, not the current
one) document the only two historical losses specifically associated with Monday nights (−$354,
−$402, both flattened by the 5-minute breaker). The settled diagnosis (hypothesis Hb2,
confirmed): this was NOT a defective Monday edge but a **software bug** — GER40 skipped Mondays (a
stale flag), making the book mono-sleeve US100 and undiversified precisely on those nights, hence
over-sized by the margin-cap mechanism. The fix (deployed 2026-07-14) restored the GER40 leg on
Mondays and "addresses" the problem according to that study's verdict. **The only empirical losses
attributable to "Monday" in the recent history have an identified and corrected operational cause,
not a market cause.**

---

## C. Does the NY Fed mechanism transfer?

**Honest limit stated up front**: the local M1 cache contains ONLY OHLC, **no volume**. I therefore
cannot build a true order-imbalance proxy as in Boyarchenko–Larsen–Whelan — instead I build two
proxies of **price dispersion** in the last half-hour of the session, being clear that this is NOT
the same thing:
- `range30_bps` = (high − low) over the last 30 minutes before the close, in bps of the close
- `twap_dev_bps` = gap between the closing price and the TWAP (a volume-free VWAP proxy) of those
  last 30 minutes

### C.1 Does the proxy predict the mean, or only the variance?

| | corr(proxy, SIGNED overnight) | corr(proxy, \|overnight\|) |
|---|---:|---:|
| US100 (n = 1,306) | **+0.215** | **+0.511** |
| GER40 (n = 1,296) | **+0.201** | **+0.455** |

The proxy is **2 to 2.5× more correlated with the MAGNITUDE** of the overnight return than with its
**sign/level**. That is the L54 signature: closing dispersion predicts mostly the VARIANCE of the
following night, not its direction. It does not exclude a positive contribution to the level
(r = 0.20 is not zero), but it means that the mechanism, if it exists, explains only a modest
fraction of the mean — most of the effect observed in Part A is not explained by this closing
dispersion.

### C.2 Has the proxy declined since 2021 (as the literature claims)?

| | slope range30_bps / year | slope \|twap_dev_bps\| / year |
|---|---:|---:|
| US100 | **+0.981** (INCREASES) | +0.087 |
| GER40 | −0.229 (slight decline) | −0.043 |

**US100 goes in the OPPOSITE direction to the thesis**: closing dispersion INCREASED over the
sample (driven by the 2020/2022 peaks), it did not decline. GER40 shows a very slight decline, of
negligible magnitude against year-to-year noise (inter-annual standard deviation ≫ slope). **The
"dispersion declining since 2021" channel of Boyarchenko–Larsen–Whelan (US equity futures, different
sample) is not clearly found in my proxy on US100/GER40 CFDs** — and in any case, Part A.5 found no
significant break to explain in the first place. I cannot say that the mechanism transfers; I can
say that my proxy does not confirm it, with the reservation that a true imbalance proxy (with volume
/ order book) could give a different result — data not available here.

### C.3 Does GER40 follow the same channel, or a distinct flow?

**I do not fabricate a correlation between the closing proxies of the two instruments**: the
closing windows are NOT simultaneous (Xetra closes 17:30 Paris/Berlin; US100 closes ≈ 22:00
Paris) — comparing "same calendar date" closing dispersions would compare two moments with no
direct flow link, which would manufacture a conclusion without foundation.

What IS honestly testable: the correlation of the overnight returns THEMSELVES (same entry date,
Monday + Tuesday):

**corr(US100_overnight, GER40_overnight) = +0.486 (n = 1,224)**

A moderate correlation, neither zero nor close to 1: **the two legs share a substantial common
component** (presumably a global equity risk-on/risk-off factor propagating from the US night to the
European morning), **but are not one and the same bet in disguise** — a significant fraction of
idiosyncratic variance per market remains. Neither "common channel" in the strict sense nor "fully
distinct transatlantic flow": in between, consistent with two equity markets linked by global beta
but with different refresh sessions.

---

## D. The decision, in numbers

Three options, same measured net costs (§A.6), annualised volatility in **√(obs/year)** (L47: 1
night/week = √52, 2 nights/week = √104):

| Option | Sharpe_ann US100 | Sharpe_ann GER40 | net $ captured (vs pool = 100 %) | nights of exposure / week |
|---|---:|---:|---:|---:|
| **1. Keep Monday + Tuesday (status quo)** | **0.732** | **0.748** | 100 % | 2 |
| 2. Reduce to Tuesday alone | 0.543 | 0.461 | US100 54 % / GER40 44 % | 1 |
| 3. De-leverage (Mon + Tue at half weight) | **0.732** (identical) | **0.748** (identical) | 50 % | 2 |

**Option 2 is DOMINATED, not merely less profitable.** Cutting Monday does not reduce the tail
either, as one might hope: the worst historical night of **Tuesday** (US100, net) is **−486.84
bps**, against **−298.53 bps** for the worst Monday night — Tuesday carries the fatter tail in this
sample, not Monday. Cutting Monday to "secure" the book is therefore a choice that, empirically,
removes the LESS risky night of the pair while keeping the one that produced the worst isolated
loss.

**Why the pool beats Tuesday alone (the L54 calculation)**: Monday and Tuesday are nearly
independent (corr = −0.084 US100 / −0.149 GER40, same week). Combining two bets of comparable
Sharpe and low correlation raises the aggregate Sharpe by a factor close to √2 (0.543 → 0.732 =
×1.35; 0.461 → 0.748 = ×1.62) — a pure diversification gain, not a sizing artifact.

**If the objective is to reduce the sleeve's risk (barrier, drawdown)**, the dominant option is NOT
"cut a night" but **de-leverage both nights at an equal reduced weight** (option 3, L54): Sharpe
and exposure duration unchanged, drawdown and dollars at risk reduced in proportion to the weight.
Cutting a day of equivalent expectation sacrifices diversification for nothing; reducing the weight
sacrifices nothing.

**Effect on the number of exposure days** — the only real point in favour of option 2: cutting
Monday halves the number of nights on which a gap can hit the daily barrier (fewer tail-risk
occasions, independently of size). But empirically (this paragraph), the worst night of the pair is
Tuesday, not Monday — so this reduction in the number of occasions does not target the right night
if the objective is specifically to remove the fattest tail. A proper p(pass) / duration
calculation (in the spirit of `core/admission/barrier.py`) would be needed to price this trade-off
properly at the real barrier — outside the strict overnight scope of this dossier, flagged as a lead
for the portfolio workstream.

### Final recommendation

**KEEP Monday and Tuesday, full weight, status quo.** If a reduction of the overnight sleeve's risk
is required for other reasons (book risk budget, funded drawdown), **prefer reducing the sleeve
weight (de-leveraging) to cutting a day from the calendar** — that preserves the Sharpe and the
diversification that cutting a day destroys. The DSR 0.29 caveat inherited from June should be
considered **partially resolved by this dossier** (the joint gross test clears / nearly clears the
programme's hardest bar, no break is demonstrable) but **not entirely** (net of real costs, the
joint test falls back under the cumulative threshold) — the honest status is **"keep, insufficient
evidence to cut"**, not "validated without reservation".

---

## Appendix — test count and files

- **26 tests** counted this session (10 in A.2, 4 + 4 in A.4/A.5, 4 in A.6, 4 in A.7). Local
  Šidák (n = 26) = 3.095. Cumulative Šidák (n = 1,994 + 26 = 2,020) = 4.211.
- The Part C proxies (descriptive correlations, not significance tests in the sense of the IC gate)
  are not counted in the 26 — they are diagnostics, not pre-registered gated hypotheses.
- Files: `code/build_overnight.py`, `code/stats_lib.py`, `code/analysis.py`,
  `results/us100_overnight_daily.csv`, `results/ger40_overnight_daily.csv`,
  `results/analysis_results.json`, `results/analysis_final_run.txt`, `results/partC_proxy.txt`.
- External sources cited (private programme, not published): the sleeve reconstruction and recent
  round-trip measurement of the funded-book attribution study; the live specification (measured
  swap, funded configuration, history of the midweek selection); the June 2026 overnight
  verification report, candidate log and canonical state; the portfolio and pending-amendment
  files; the timing attribution study; the vol-multiplier sweep pre-registration and study; the
  nightly US100 pre-registration and verdict.
