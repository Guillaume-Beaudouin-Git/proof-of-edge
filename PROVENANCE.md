# Provenance

This repository carries the real history of the files it publishes, extracted from the private
research repository with `git filter-repo` (paths renamed to the public layout, the VPS address
and account identifiers replaced). Commit dates and messages are the originals; the final
commits are the public curation (translations, firm-name and balance scrubs, READMEs). Hashes
differ from the private repository's because the history was rewritten. The full repository is
published, with its own rewritten history, as
[research-archive](https://github.com/Guillaume-Beaudouin-Git/research-archive); the "archive"
links below point to the same commits there. The history is not scrubbed of account balances or
of the names of the private repository's files; only secrets, the server address, account
identifiers and local paths were replaced.

| study | pre-registration frozen | results added |
|---|---|---|
| `studies/crypto_flows_placebo` | `5887fe4` — 2026-06-10 12:23 (+0200), "Phase 0 audit + pre-registration FROZEN before data contact" ([archive](https://github.com/Guillaume-Beaudouin-Git/research-archive/commit/ba2b382)) | `2dfbc28` — 2026-06-10 12:55 (+0200), "0 survivors, 2 clean kills" ([archive](https://github.com/Guillaume-Beaudouin-Git/research-archive/commit/74a73d9)) |
| `studies/trend_futures_funnel` | `9c51b10` — 2026-06-14 14:27 (+0200), "LOCK pre-registration (non-crypto futures trend sleeve)", on branch `claude/trend-futures-sleeve` (the lock commit lived on a branch and is not in the archive, which publishes `main` only) | `ce7aacf` — 2026-08-24 16:39 (+0200), funnel P1–P4 and report merged into main ([archive](https://github.com/Guillaume-Beaudouin-Git/research-archive/commit/d4988c6)) |
| `studies/swap_killed_futures` | `PREREGISTRATION.md` dated 2026-07-15 in the document; the folder entered main in one commit, `7662f9b` — 2026-07-30 13:15 (+0200) ([archive](https://github.com/Guillaume-Beaudouin-Git/research-archive/commit/e7c3411)) | same commit |
| `studies/month_end_treasury_flow` | study and results in one commit, `6a3c866` — 2026-07-29 20:21 (+0200), "VEHICULE TROUVE" ([archive](https://github.com/Guillaume-Beaudouin-Git/research-archive/commit/435be54)) | same commit |
| `studies/gold_asia_overnight` | reports and code brought under version control on 2026-08-22 (`74328a9`, [archive](https://github.com/Guillaume-Beaudouin-Git/research-archive/commit/50246dc)), after the work; the reports carry their own dates (June 2026) | same |
| `studies/overnight_index_premium` | dossier and code, `bf8c069` — 2026-09-02 03:28 (+0200), "remonte les 6 dossiers du desk quant" ([archive](https://github.com/Guillaume-Beaudouin-Git/research-archive/commit/3d8ec64)); decisions recorded the day before in `053c45e` | same |

What this does and does not establish: for `crypto_flows_placebo` and `trend_futures_funnel`, the
pre-registration was committed before the results, and the commits are in this repository. For
the other four, the order is documented inside the files, not by the version control, and the
studies are presented accordingly.
