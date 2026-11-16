# gotobi_usdjpy — what is published here

**The idea.** In Japan, corporate settlements cluster on the "gotobi" days (the 5th, 10th, 15th,
20th, 25th and the last business day of the month): importers buy dollars into the Tokyo fixing,
and USDJPY tends to rise before it and fall back after. This study tests a *dosed* version of
the trade, restricted to the 25th and the month-end, as a replacement candidate for a paused
sleeve of the live book.

**The trade.** Leg A: long from 23:00 UTC the evening before to 00:54 UTC (the fixing is at
00:55 UTC). Leg B: short from 00:56 to 02:00 UTC. A hard stop at 25 bps on each leg; days with
a high-impact JPY or USD announcement in the window are skipped.

**Verdict: launch, narrowly, by an independent review that overrode two earlier "archive"
readings (2026-10-19).** Deployed in the live Expert Advisor since early
November 2026, **disarmed: it has not traded yet.** Arming is a separate, manual decision; when
it trades, the fills will appear in `studies/live_record` with the sleeve named.

Key figures, each from the file named:

| | figure | source |
|---|---|---|
| Discovery sample, all gotobi days | 1,257 events, +4.05 bps, t 6.87 | `RAPPORT.md` |
| Holdout 2024-07 → 2026-05, the 25th and month-end | 44 events, **+6.19 bps gross**, t_HAC 2.52 | `RAPPORT.md` |
| Holdout, the other gotobi days | 92 events, +0.55 bps, t 0.22 | `RAPPORT.md` |
| Kill rule K1 (gross ≥ 3 × the measured cost of 1.87 bps) | 6.19 ≥ 5.61: passes by 0.6 bp | `RAPPORT.md` |
| Cost re-measured on the broker's real bid/ask, 11 events | 1.82 bps mean (max 2.04) | `deep_dive/DECISION.md` |
| Shrunk expectation (random-effects meta-analysis of 7 periods) | +2.11 bps net per event, P(net > 0) = 0.84 | `deep_dive/DECISION.md` |
| What it is worth on a $10k account | about +$110 a year before the profit split; one losing year in three | `deep_dive/DECISION.md` |

What the decision does **not** claim, in its own words: the in-sample history is not the
expectation; the superiority of the 25th and month-end over the other gotobi days is *not*
established (+1.1 bp, standard error 1.35); and the verdict waives the programme's "gross ≥ 3 ×
cost" gate on the long sample (4.51 bps against 5.61 required). Held to that gate, the verdict
would be *archive*. Two earlier pre-registered readings in this folder concluded *archive*, and
`PREREG.md` required a paper shadow of at least twelve months; the launch overrides both, on
criteria of which three (L1–L3) were set after the reports had been read. The decision says so. The launch rests on a measured cost, a bounded tail (stops) and a written
stopping rule.

**Reading order.** `PREREG.md` (frozen before the holdout was read) → `RAPPORT.md` (holdout) →
`PREREG_VALIDATION.md`, `RAPPORT_VALIDATION.md` (17-year validation: V1–V3 fail, pre-registered verdict **archive**; book admission passes) → `PREREG_RUPTURE.md`,
`RAPPORT_RUPTURE.md` (break test: not significant, p 0.178, the archive stands) → `deep_dive/PREREG_DEEP.md` and `deep_dive/DECISION.md`
(independent review: launch or archive) → `LANCEMENT_S2.md` (launch conditions). Code under
`code/` and `deep_dive/code/`, outputs under `out/`.

**Language.** The documents are the French originals, unedited; this README is the English
summary. **Not published:** the minute-bar history and the broker spread logs the scripts read
(they expect `RESEARCH_DATA_ROOT`); the scripts are kept as they were run, apart from that path.
