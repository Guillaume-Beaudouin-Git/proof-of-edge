# Provenance

This repository carries the real history of the files it publishes, extracted from the private
research repository with `git filter-repo` (paths renamed to the public layout, the VPS address
and account identifiers replaced). Commit dates and messages are the originals; the final
commits are the public curation (translations, firm-name and balance scrubs, READMEs). Hashes
differ from the private repository's because the history was rewritten; the original hashes
are given for cross-reference with `research-archive`, which publishes the full repository.

| study | pre-registration frozen | results added |
|---|---|---|
| `studies/crypto_flows_placebo` | `5887fe4` — 2026-06-10 12:23 (+0200), "Phase 0 audit + pre-registration FROZEN before data contact" (original `97bf99e2`) | `2dfbc28` — 2026-06-10 12:55 (+0200), "0 survivors, 2 clean kills" (original `6d720e07`) |
| `studies/trend_futures_funnel` | `9c51b10` — 2026-06-14 14:27 (+0200), "LOCK pre-registration (non-crypto futures trend sleeve)", on branch `claude/trend-futures-sleeve` (original `6163805`) | `e2b52dd` — 2026-08-24 16:39 (+0200), funnel P1–P4 and report merged into main (original `abc4e3d7`) |
| `studies/swap_killed_futures` | `PREREGISTRATION.md` dated 2026-07-15 in the document; the folder entered main in one commit, `fad90df` — 2026-07-30 13:15 (+0200) (original `4a9094ec`) | same commit |
| `studies/month_end_treasury_flow` | study and results in one commit, `6a3c866` — 2026-07-29 20:21 (+0200), "VEHICULE TROUVE" | same commit |
| `studies/gold_asia_overnight` | reports and code brought under version control on 2026-08-22 (`c20684f`), after the work; the reports carry their own dates (June 2026) | same |
| `studies/overnight_index_premium` | dossier and code, `d70cb26` — 2026-09-02 03:28 (+0200), "remonte les 6 dossiers du desk quant"; decisions recorded the day before in `25a5c4a` | same |

What this does and does not establish: for `crypto_flows_placebo` and `trend_futures_funnel`, the
pre-registration was committed before the results, and the commits are in this repository. For
the other four, the order is documented inside the files, not by the version control, and the
studies are presented accordingly.
