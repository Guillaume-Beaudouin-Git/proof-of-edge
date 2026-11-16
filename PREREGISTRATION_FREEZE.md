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

Studies added on 2026-11-16. Their pre-registrations were committed in the private repository
before the reading they govern; those commits are **not** in this repository's history nor yet
in the public archive, so here the order is documented, not provable from public version
control. The files are published byte for byte as they stand in the private repository today.

| study | file | committed privately | results committed privately | SHA-256 at HEAD |
|---|---|---|---|---|
| `studies/gotobi_usdjpy` | `PREREG.md` | `1935996d`, 2026-10-18 19:34 (+0200) | `RAPPORT.md`, `c52f59a8`, 19:36 | `6e4ff8e121578974c1c99cf069afff02ab0b420c3a53f8108953bda48c7bf930` |
| `studies/gotobi_usdjpy` | `PREREG_VALIDATION.md` | `ea43ebe9`, 2026-10-18 21:31 (+0200) | `RAPPORT_VALIDATION.md`, `aced2b95`, 21:32 (verdict: archive) | `e634505fe7317e00a82d1f17238cc4f858ebf3f7fd95aa84236ed6e49775a017` |
| `studies/gotobi_usdjpy` | `PREREG_RUPTURE.md` | `b0e401da`, 2026-10-18 22:04 (+0200) | `RAPPORT_RUPTURE.md`, `53a3e13b`, 22:05 (the archive stands) | `d432a3f57dbd51b52ca1a82cb021f4ebbff018a41567cf8299149f8df671f357` |
| `studies/gotobi_usdjpy` | `deep_dive/PREREG_DEEP.md` | `e1643995`, 2026-10-19 00:10 (+0200) | `deep_dive/DECISION.md`, `b7db5b44`, 00:23 (verdict: launch) | `9ea2bd6b2601386c7f72c67d23b735b48b752fa0284d5f0ab8a51d4b24e519a6` |
| `studies/hong_kong_mainland_holidays` | `PREREG.md` | `05590d18`, 2026-10-19 13:46 (+0200) | `RAPPORT.md`, `99ffd8b1`, 13:49 | `afa4c31c6145207c93e23dee395c38418471d6dbd600f3279cde6ef144ed64a0` |
| `studies/hong_kong_mainland_holidays` | `PREREG_ENVERS.md` | `3c947ae0`, 2026-10-19 13:52 (+0200) | `RAPPORT_ENVERS.md`, `dd4b064f`, 13:56 | `59df69658566c999260131d10de88b11c6daa0cf60dbf826cb360504b764edb6` |
| `studies/coinbase_premium_btc` | `signal/PREREG.md` | `04e80a0b`, 2026-10-30 02:09 (UTC) | `signal/RAPPORT.md`, `c7c41c54`, 02:24 | `c1a6397ee7f463b48b7f01e38f29b4fc6564bf03b303fdc8d94171b2c2fd19a7` |
| `studies/coinbase_premium_btc` | `verification/PREREG.md` | `95b107b5`, 2026-10-30 14:51 (+0100) | outputs the same afternoon | `6ad003de5bc7825352d492f043907c5a1d267c8b31db9ac329a3a41cf70136af` |

A gap of minutes between a pre-registration and its report is what a single pre-written
script produces: the scripts were dry-run on synthetic prices first, and the reports say so.

Digests are recomputed by hand when a file changes; the commit history remains the authority.
