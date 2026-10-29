# Provenance

This repository carries the real history of the files it publishes, extracted from the private
research repository with `git filter-repo` (paths renamed to the public layout, the VPS address
and account identifiers replaced). Commit dates and messages are the originals (assistant co-signature trailers were
stripped); the final commits are the public curation (translations, firm-name and balance scrubs, READMEs). Hashes
differ from the private repository's because the history was rewritten. The full repository is
published, with its own rewritten history, as
[research-archive](https://github.com/Guillaume-Beaudouin-Git/research-archive); the "archive"
links below point to the same commits there. The history is not scrubbed of account balances or
of the names of the private repository's files; only secrets, the server address, account
identifiers and local paths were replaced.

| study | pre-registration frozen | results added |
|---|---|---|
| `studies/crypto_flows_placebo` | `293bc5d` — 2026-06-10 12:23 (+0200), "Phase 0 audit + pre-registration FROZEN before data contact" ([archive](https://github.com/Guillaume-Beaudouin-Git/research-archive/commit/b0d7853)) | `4134939` — 2026-06-10 12:55 (+0200), "0 survivors, 2 clean kills" ([archive](https://github.com/Guillaume-Beaudouin-Git/research-archive/commit/8313276)) |
| `studies/trend_futures_funnel` | `b1d69fb` — 2026-06-14 14:27 (+0200), "LOCK pre-registration (non-crypto futures trend sleeve)", on branch `claude/trend-futures-sleeve` (the lock commit lived on a branch and is not in the archive, which publishes `main` only) | `57b9348` — 2026-08-24 16:39 (+0200), funnel P1–P4 and report merged into main ([archive](https://github.com/Guillaume-Beaudouin-Git/research-archive/commit/d432fe0)) |
| `studies/swap_killed_futures` | `PREREGISTRATION.md` dated 2026-07-15 in the document; the folder entered main in one commit, `6b0625d` — 2026-07-30 13:15 (+0200) ([archive](https://github.com/Guillaume-Beaudouin-Git/research-archive/commit/3e1ca4f)) | same commit |
| `studies/month_end_treasury_flow` | study and results in one commit, `b71bb56` — 2026-07-29 20:21 (+0200), "VEHICULE TROUVE" ([archive](https://github.com/Guillaume-Beaudouin-Git/research-archive/commit/43e2a49)) | same commit |
| `studies/gold_asia_overnight` | reports and code brought under version control on 2026-08-22 (`ffff6be`, [archive](https://github.com/Guillaume-Beaudouin-Git/research-archive/commit/ee577a3)), after the work; the reports carry their own dates (June 2026) | same |
| `studies/overnight_index_premium` | dossier and code, `ac5c42d` — 2026-09-02 03:28 (+0200), "remonte les 6 dossiers du desk quant" ([archive](https://github.com/Guillaume-Beaudouin-Git/research-archive/commit/f34f327)); decisions recorded the day before in `6b05a7d` | same |

What this does and does not establish: for `crypto_flows_placebo` and `trend_futures_funnel`, the
pre-registration was committed before the results, and the commits are in this repository. For
the other four, the order is documented inside the files, not by the version control, and the
studies are presented accordingly.

The SHA-256 digest of each pre-registration file, at its freezing commit and at HEAD, is in
`PREREGISTRATION_FREEZE.md`.
