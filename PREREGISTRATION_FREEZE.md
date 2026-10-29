# Pre-registration freeze

What "frozen before the data is touched" means in this repository, study by study, with the
digest of the pre-registration file at the commit that froze it and at the current HEAD. The two
digests differ when the public curation edited the file afterwards (English wording, firm names,
balances, private paths); the freezing commit holds the original bytes and can be checked with
`git show <commit>:<path> | shasum -a 256`.

| study | file | frozen at | SHA-256 at that commit | SHA-256 at HEAD |
|---|---|---|---|---|
| `studies/crypto_flows_placebo` | `preregistration.md` | `293bc5d`, 2026-06-10 12:23 (+0200), 32 minutes before the results commit `4134939` | `36b5b49dcdb7c49fd61d1d5536e06760c9545f359c0a7b78847d0d964fc15da5` | `4ea6b40b7699b5ff5228d6055f7734a818d9bb8a3dd3410f0d6ea1ceae9cae77` |
| `studies/trend_futures_funnel` | `PREREG.md` | `b1d69fb`, 2026-06-14 14:27 (+0200), on branch `claude/trend-futures-sleeve`; the report was merged on 2026-08-24 (`57b9348`) | `0ef1ddcbfa69f4c75f53ccef85ce5ccc6145b992ce5990d06ec110466031d071` | `e496143980b1dcfca75e5360392f2ece3f19c911c3177dd42d05b905f6b94df6` |
| `studies/swap_killed_futures` | `PREREGISTRATION.md` | `6b0625d`, 2026-07-30 13:15 (+0200) — the document is dated 2026-07-15, but file and results entered version control in the same commit | `0784b4645ce0b841277a27653a513af9b4499ae0ff253d594f9608b757a715a2` | `4d75b728ed7f04baafcdce9e5a7fd0f586c5b0f2015db0b68a64e9556e3b578f` |

The three other studies have no separate pre-registration file and do not claim one:

| study | document | first committed | SHA-256 at HEAD |
|---|---|---|---|
| `studies/month_end_treasury_flow` | `RESULTS.md` — the hypothesis (B1) was frozen earlier in the programme, with t 4.65; this study re-measures it and chooses the vehicle | `b71bb56`, 2026-07-29 | `c01ab620170f176b68eab134cef044a7475d1543db95bae38ff4b0b35712ce69` |
| `studies/gold_asia_overnight` | `reports/gold_ASIA_23_8_due_diligence.md` — exploratory research followed by an independent risk audit, not a pre-registered test | `ffff6be`, 2026-08-22 | `63e71c9cae07e500e76efe1bb1db3ccc0ff24ed10ad0549c3caa1d60799971e0` |
| `studies/overnight_index_premium` | `DOSSIER_OVERNIGHT.md` — a re-analysis whose decision rules are stated at the top of the document; the original midweek selection it audits was post-hoc, and the dossier says so | `ac5c42d`, 2026-09-02 | `32b85fb9ecf342e68f7dcc39ee42aaefe953afea8b6357568757f9d08bf11a1f` |

Digests are recomputed by hand when a file changes; the commit history remains the authority.
