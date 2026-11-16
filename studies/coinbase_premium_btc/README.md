# coinbase_premium_btc — what is published here

**The idea.** When Bitcoin trades at a premium on Coinbase (USD) over Binance (USDT), does the
price continue over the following hours? Hourly premium 2017-08 → 2026-09 (79,748 hours), signal
when the premium z-score exceeds 2 in absolute value, in-sample 2017–2023, holdout 2024-01 →
2026-10 opened once.

**Verdict: real and reproduced, but smaller and more episodic than the holdout suggests. No
capital; paper forward only.**

Two folders:

- `signal/` — the pre-registered test (`PREREG.md`, `RAPPORT.md`) and its adversarial reading
  (`RELECTURE.md`). Three horizons pass in-sample (Sharpe 1.90 / 1.93 / 1.57 at 1 h / 4 h / 24 h,
  five folds out of five each), but **only the 24-hour horizon holds out of sample** (1.88,
  t 2.96), and the mechanism turns out to be the USDT/USD basis, not US demand.
- `verification/` — an independent local reproduction (`PREREG.md`, `NOTE.md`), then a hostile
  review of it (`REVUE.md`, `SYNTHESE.md`, to be read first) and a vehicle study
  (`REVUE_VEHICULES.md`, `VEHICULES_FR.md`).

What the review found (the two expected Sharpe ratios are its judgement, the rest is measured):

| | figure |
|---|---|
| Reproduction by a second, independent code | in-sample 1.61, holdout 1.85; correlation 0.99998 between the two local reproductions, 0.982 with the original run |
| Inflation from picking the best of three horizons | about +0.75 of Sharpe (joint bootstrap) |
| Expected gross Sharpe out of sample | ≈ 1.1 (0.8 – 1.4) |
| Expected net on the one vehicle that fits a small account (BTC perpetual, taker) | ≈ 0.75 (0.5 – 1.0): at the edge of the programme's research gate (0.7) |
| Concentration | in the holdout, 5 episodes out of 45 make 73 % of the P&L; Sharpe without them 0.72 |

Why no capital: the expected net sits on the gate, the P&L is concentrated in a few episodes,
the amplitude of the USDT/USD basis has been divided by ten since 2019, and the regulatory
access question for the vehicle was not settled. A paper forward of three to six months is the
only step approved; the review itself notes that it will prove nothing about the Sharpe.

**Language.** The documents are the French originals, unedited; this README is the English
summary. Data: Coinbase Exchange and Binance Vision public hourly files, fetched by the
download scripts, not redistributed.
