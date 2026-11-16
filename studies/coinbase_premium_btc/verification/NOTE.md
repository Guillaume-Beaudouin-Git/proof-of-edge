# C9 h24 : vérification locale indépendante (2026-10-30)

## Réponse directe
- **C9 tient en local. MESURÉ.** Je l'ai reconstruite avec mon propre code et des données re-téléchargées. Le Sharpe IS
  2017-23 est de **1,61** (cloud 1,57) et le holdout 2024-26 de **1,85** (cloud 1,88). Les séries quotidiennes sont
  corrélées à 0,98 et je retrouve 1 377 des 1 391 jours actifs du cloud. Les dix années civiles sont positives, les
  deux jambes aussi. Les drapeaux FRAGILE du PREREG ne se lèvent pas : le Sharpe sans les 5 meilleurs trades est de
  1,52, la pire année pèse 21 % du P&L, et hors fenêtres de stress le Sharpe vaut 1,50.
- **Sharpe brut attendu hors échantillon : ≈ 1,15 (fourchette 0,9-1,4). JUGÉ, à partir de mesures.** Le 1,85 du
  holdout est le meilleur de trois horizons lus. La moyenne des trois holdouts donne 1,13. Le rétrécissement donne
  aussi 1,13, parce que la variance entre horizons est plus petite que le bruit d'échantillonnage. Un walk-forward qui
  choisit l'horizon sur le passé seul obtient 1,10 sur la fenêtre du holdout, et 1,39 sur 2019-2026.
- **Véhicule : le perp BTC Hyperliquid. Sharpe net attendu ≈ 0,85-0,9 en taker, ≈ 1,0 en maker. JUGÉ.** Le calcul est
  le brut attendu moins la traînée de coût mesurée : −0,28 de Sharpe en taker (9,2 bps aller-retour + funding réel), −0,11
  en maker. Sur l'historique complet, le net mesuré est de 1,39 en taker, avec un MaxDD de −8,7 %, une pire journée de
  −2,4 % et 8 plis annuels positifs sur 8. RESEARCH_PASS est donc **atteint**. PROPFIRM_PASS est hors sujet : la crypto
  n'est pas acceptée par FTMO.
- **Second choix : le MBT du CME via IBKR, ≈ 0,9-1,0 net. JUGÉ.** Mais sur 12 000 €, un lot vaut 57 % du compte. Le
  vol-targeting devient impossible : en arrondissant au lot, seuls 13 % des trades obtiennent au moins 1 lot. À 1 lot
  fixe, la vol monte à 23 %, le MaxDD à −23 % et la pire journée à −8,2 %, avec un skew qui reste positif (+3,4). Le
  nano Coinbase (0,01 BTC) rend la taille fine, mais au prix de ≈ 11 bps aller-retour.
- **Avant d'y mettre de l'argent :**
  1. L'accès réglementaire d'un résident français au perp HL, ou aux futures crypto CME/Coinbase via IBKR Ireland.
     C'est une question que je signale sans la trancher.
  2. Le forward papier opérationnel de 3-6 mois (`FORWARD_SPEC.md`). Il vérifie le signal, le coût et le funding. Il ne
     peut pas valider le Sharpe : l'effet minimum détectable est de 3,5 à 6 mois.
  3. Accepter l'enjeu réel. À 10 % de vol sur 12 000 €, un Sharpe de 0,9 rapporte de l'ordre de 1 000 €/an. La sleeve
     dépend d'une base USDT/USD qui peut disparaître.
- **Forward vrai (01-30/10/2026) : 10 trades, tous short, Sharpe −0,11, P&L ≈ 0. MESURÉ.** Le mois ne contient aucune
  information statistique (MDE 8,7).

Verdict selon le PREREG : **TIENT**. R1 est reproduit. Les deux jambes sont positives. L'estimation S1 retenue est
d'environ 1,15, au-dessus de 0,7. Un véhicule passe G1 en net.

## 1. Reproduction (MESURÉ ; `out/repro_summary.csv`, `code/run_repro.py`)
| | IS 2017-23 | holdout 2024-01 → 2026-09 | forward 10/2026 | cloud IS / HO |
|---|---|---|---|---|
| h24 | **1,61** (t 3,77 ; IC95 bloc [0,87 ; 2,36]) | **1,85** (t 2,91 ; [0,76 ; 2,89]) | −0,11 (10 trades) | 1,57 / 1,88 |
| h24 délai +1 h | 1,28 | 2,05 | −0,19 | 1,20 / 2,07 |
| h4 | 1,92 | 0,91 | −0,27 | 1,93 / 0,91 |
| h1 | 1,85 | 0,62 | −4,12 | 1,90 / 0,61 |

h24 en chiffres : 105 trades/an, 72 bps bruts par trade en IS, 45 au holdout. Vol réalisée 7 %, skew +5 à +6, MaxDD
−7,0 %, pire journée −2,4 %.

J'ai lu le code du cloud seulement après la reconstruction. Les écarts résiduels sont tous inférieurs à 0,05 et ont des
causes identifiées :
- ils commencent le z à 360 h, moi à 720 h ;
- leur fenêtre glissante compte des lignes calendaires (NaN inclus), la mienne des observations valides ;
- ils plafonnent le poids à 10, moi à 3 ;
- ils utilisent des rendements log, moi des rendements simples ;
- ils ne retirent pas le cash, moi si.

Les deux cas de MaxDD sont calculés en somme cumulée.

## 2. Concentration, stress, jambes (MESURÉ ; `out/concentration.csv`, `stress_depeg_h24.json`, `legs_h24.csv`, `by_*`)

**Part des meilleurs trades et Sharpe sans eux :**

| | top 1 | top 3 | top 5 | top 10 |
|---|---|---|---|---|
| Part du P&L, tout l'échantillon | 7 % | 15 % | 20 % | 31 % |
| Sharpe sans eux, tout l'échantillon | 1,62 | 1,59 | 1,52 | 1,38 |
| Sharpe sans eux, holdout | 1,78 | 1,61 | 1,47 | **0,98** |

Le holdout est plus concentré : ses 10 meilleurs trades font 56 % de son P&L.

**Par année :**

| Année | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| Sharpe | 2,21 | 1,42 | 1,91 | 2,15 | 1,92 | 1,47 | **0,59** | 2,08 | 1,80 | 1,65 |

Sur 38 trimestres, 8 sont négatifs, dont trois d'affilée de 2023-T2 à 2023-T4. Aucun trimestre ne dépasse 8,8 % du P&L.

**Les plus gros trades** (`out/top_trades_h24.csv`) :
- 02/04/2019, long, BTC +20 % en 24 h ;
- 12/03/2020, short, krach COVID ;
- 24/09/2019, short ;
- 07/11/2022, short, FTX ;
- 23/10/2023, long ;
- 12/03/2023, long, week-end du dépeg USDC : prime +79 bps, z 4,9.

Quatre des dix meilleurs tombent dans un mois de stress stablecoin. Les mois de stress portent 64 trades et 24 % du P&L.
Sans eux, le Sharpe vaut 1,50 sur tout l'échantillon, 1,34 en IS et 1,85 au holdout.

**Filtre de dépeg.** Il ne retire que des heures de 2017-2019 : 3 237 sur 3 283, et aucune depuis 2024. Il garde 9 des
10 meilleurs trades. Sans filtre, le Sharpe vaut 1,63 (IS 1,56, holdout identique). Ni le filtre ni les fenêtres de
stress ne fabriquent l'effet.

**Jambes (L25), en bps par trade :**

| | Longue | Courte |
|---|---|---|
| IS | +93 (t 3,40) | +55 (t 2,35) |
| Holdout | +62 (t 2,38) | +33 (t 1,64) |
| Forward | 0 trade | 10 trades, ≈ 0 |

La jambe courte est la plus faible hors échantillon. Elle reste positive, mais n'est plus significative seule.

## 3. Sélection de l'horizon (MESURÉ, puis estimation JUGÉE ; `out/horizon_selection.json`, `horizon_wf.csv`)

**Trois horizons, IS puis holdout :**

| Horizon | IS | Holdout |
|---|---|---|
| h1 | 1,85 | 0,62 |
| h4 | 1,92 | 0,91 |
| h24 | 1,61 | 1,85 |

**Trois estimations du Sharpe de h24 hors échantillon :**
- **(a) moyenne des trois holdouts : 1,13.**
- **(b) rétrécissement : 1,13.** L'erreur type du holdout h24 vaut 0,99, au-dessus de la dispersion entre horizons (variance
  0,42 < SE² 0,99), donc le rétrécissement est total.
- **(c) walk-forward annuel qui choisit l'horizon au meilleur Sharpe passé : 1,39 sur 2019-2026, 1,10 sur 2024-2026.** Il
  choisit h4 sept années sur huit, h24 seulement en 2026.

L'écart entre (a)-(b) et (c) vaut 0,26, sous le seuil de 0,3 du PREREG, donc la règle « garder la plus basse » n'est pas
déclenchée. **Je retiens ≈ 1,15 brut.** C'est JUGÉ.

Nuance : le Sharpe IS de h24 (1,61) n'est pas gonflé par la sélection, puisque h24 était le plus faible en IS. La même
logique que (a)-(b) le ramène sous l'effet d'une décroissance générique hors échantillon. Le 1,15 est donc prudent,
pas pessimiste.

Šidák sur les trois horizons : le p unilatéral du holdout h24 passe de 0,0018 à 0,0053 et reste significatif.
L'effet minimum détectable du holdout est de 1,50 : le holdout lui-même était à peine assez long pour voir l'effet.

## 4. Véhicules et coûts (MESURÉ sur l'historique ; `out/vehicles.csv`, `vehicles_detail.json`, `code/run_vehicles.py`)

Sharpe net sur la série quotidienne avec zéros, √365, en excès du cash. Les frais fixes en dollars sont convertis en
bps au prix de BTC du 30/10/2026 (77 174 $) : le MBT n'existe que depuis 2021 et le nano depuis 2022.

| Véhicule | Coût AR | Net, historique complet | Net, holdout | MaxDD | Pire jour | Skew | Plis > 0 | Net attendu (JUGÉ) |
|---|---|---|---|---|---|---|---|---|
| Brut (référence) | 0 | 1,67 | 1,85 | −7,0 % | −2,4 % | +5,1 | 8/8 | 1,15 |
| **Perp HL taker + funding réel** | 9,2 bps + funding | **1,39** | 1,53 | −8,7 % | −2,4 % | +5,0 | 8/8 | **≈ 0,87** |
| Perp HL maker + funding | 3 bps + funding | 1,56 | 1,74 | −7,5 % | −2,4 % | +5,0 | 8/8 | ≈ 1,0 (si remplis) |
| MBT fractionnaire, 24/7 | 5,9 bps + base | 1,50 | 1,66 | −7,9 % | −2,4 % | +5,0 | 8/8 | ≈ 1,0 (taille impossible sur 12 k€) |
| MBT, ancien horaire, signaux fermés sautés | idem | 1,23 | 1,81 | −7,1 % | −2,4 % | +5,1 | 8/8 | — |
| **MBT 1 lot fixe, 12 k€** (lot = 57 % du compte) | idem | 1,46 | 1,35 | **−23,4 %** | **−8,2 %** | +3,4 | 8/8 | ≈ 0,9, à 23 % de vol |
| MBT arrondi au lot, 12 k€ | idem | 1,37 | 1,84 | −4,9 % | −1,7 % | +15 | 8/8 | inutilisable (13 % des trades ≥ 1 lot) |
| Nano BIT arrondi au lot (0,01 BTC), 12 k€ | 11,3 bps + base | 1,35 | 1,44 | −9,1 % | −2,7 % | +4,5 | 8/8 | ≈ 0,8 |
| Spot long seul Binance (VIP 0) | 20 bps | 1,13 | 1,19 | −5,5 % | −2,2 % | +5,7 | 7/8 | ≈ 0,75 (une jambe) |
| Spot long seul Coinbase UE taker | 100 bps | −0,53 | −0,73 | −29 % | — | — | 3/8 | mort |

**Lecture.** Le net attendu est le brut retenu (1,15) moins la traînée mesurée du véhicule ; c'est JUGÉ. Au brut
attendu, chaque bp de coût aller-retour coûte environ 0,03 de Sharpe. Le point mort à Sharpe 1 tombe donc à ≈ 5 bps AR,
contre 23 bps sur le brut historique (MESURÉ : 22,8 bps à Sharpe 1 et 57 bps à Sharpe 0, funding inclus). Seul le maker
HL reste au-dessus de 1.

**a. Perp HL (MESURÉ).**
- Frais du palier 0 : taker 4,5 bps, maker 1,5 bps par côté.
- Fourchette : 0,13 bp sur 5 instantanés `l2Book` du 30/10. Impact d'un ordre de 100 k$ : 0,07-0,20 bp ; de 1 M$ :
  0,1-1,7 bp.
- Volume 24 h : 6,9 G$. Open interest : 40 000 BTC. Levier maximal 40×, ordre minimal 10 $. Capacité sans objet à
  l'échelle du compte.
- Funding : jamais extrême en moyenne, mais une queue existe. Signé, il coûte +0,7 bp par trade en moyenne (HL réel
  +0,6 sur 341 trades ; proxy Binance +1,0 sur 400). Le p95 en valeur absolue est de 19 bps. 190 trades d'avant
  09/2019 n'ont aucun funding (non modélisé).
- Sur les 56 trades des 200 derniers jours, le rendement du perp HL suit celui du spot Binance à 0,9999 près (écart
  moyen 1,9 bp).
- Garanties : DEX non régulé, risque de contrepartie sur le smart contract et le bridge. NON mesuré.

**b. MBT via IBKR.**
- Coûts (MESURÉ) : par côté, commission 0,85 $ + frais de bourse non-membre 1,15 $ + ≈ 0,02 $ de frais réglementaires ;
  tick de 0,50 $. Soit ≈ 4,54 $ AR = 5,9 bps à 77 k$.
- Base CME (MESURÉ, `out/cme_basis_by_year.csv`) : moins le cash, médiane annuelle de −4 % à +12 %. Cela fait
  ≈ 1,5 bp par trade de 24 h, neutre en moyenne entre longs et courts (+0,03 bp signé).
- Échéances : mensuelles, six cotées, fin le dernier vendredi à 16:00 Londres. Un trade de 24 h ne roule presque jamais.
- Horaires : avant le 29/05/2026, 40 % des trades avaient leur entrée ou leur sortie marché fermé (22 % pour l'entrée).
  Sauter ces trades coûte 20 % du P&L brut (Sharpe brut 1,67 → 1,36) ; les décaler en coûte 13 % (→ 1,44). Depuis le
  29/05/2026, le CME cote les cryptos 24/7, d'après des sources secondaires. La page IBKR du MBT affiche encore l'ancien
  horaire. La liquidité du premier week-end était d'environ 1,8 % d'un jour de semaine : les signaux de week-end
  restent à risque d'exécution. INCERTAIN.
- Marge : non consultée (page IBKR derrière une connexion). INCERTAIN.
- Granularité (L57) : sur 12 000 €, un lot de 0,1 BTC vaut 57 % du compte. Le vol-targeting à 10 % voudrait 15-30 %. On
  a donc le choix entre 1 lot, soit 3 à 4 fois la taille cible, et 0 lot. Contrairement au cas L57 du soja, le skew
  reste positif à 1 lot (+3,4), mais la vol monte à 23 %, le MaxDD à −23 % et la pire journée à −8,2 %. Le MaxDD respecte
  encore le seuil RESEARCH_PASS de −25 %, de peu.
- Nano Bitcoin (BIT, 0,01 BTC, Coinbase Derivatives) : IBKR le liste (commission 0,20 $ ; volume compté pour 1/100). Il
  est annoncé en 24/7, avec une version perpétuelle. Frais de bourse et de compensation : ≈ 0,19 $ + 0,02 $ NFA par
  côté, d'après une source secondaire de 2022 ; soit ≈ 11 bps AR. L'accès pour un client IBKR Ireland n'est pas
  confirmé. INCERTAIN.

**c. Spot, jambe longue seule.**
- Binance VIP 0 : 0,10 % par côté. Coinbase Advanced UE : 0,25 % maker, 0,50 % taker par côté, d'après une source
  secondaire de 09/2026 (page officielle inaccessible). Aux États-Unis, 0,90 % en taker.
- Au coût Binance, la jambe longue seule tient (1,13). Au taker Coinbase, elle meurt.

**Accès réglementaire (signalé, non tranché).** Trois questions restent ouvertes pour un particulier résidant en France :
- le statut des perps sur un DEX non régulé (HL) : MiCA ne couvre pas les dérivés ; la position de l'AMF sur les
  dérivés crypto vendus aux particuliers est à vérifier ;
- l'éligibilité aux futures crypto CME et Coinbase via IBKR Ireland : la permission « United States (Crypto) » est
  mentionnée par une source secondaire ;
- la fiscalité des gains sur dérivés crypto.

## 5. Corrélations (MESURÉ ; `out/vehicles_detail.json`)
- **L38** : régression sur BTC acheté et tenu, vol-targeté à 10 %. β −0,03, R² 0,2 %, corrélation −0,05, α 12 %/an
  (t HAC 4,76). C9 est orthogonale au beta BTC.
- **Strategy A** (TSMOM tanh long-only BTC/ETH/SOL, reconstruite depuis `signal.py`, quotidienne) : corrélation
  quotidienne 0,13, 0,08 au holdout, 0,18 en hebdomadaire.
- `_meta/current_focus.md` (29/10) ne montre **aucun livre perso financé en argent réel**. A est gelée ; B et A tournent
  sur le testnet HL. La sleeve est donc jugée seule, et RESEARCH_PASS est atteint en net (§4). Le test d'admission ERC
  n'a pas d'objet tant qu'aucun livre réel n'existe.

## 6. Forward papier
Spec complète dans `FORWARD_SPEC.md`. Rien n'est installé. Le forward attend l'accord de Guillaume et la fin du
déploiement de l'EA v2.14.

## 7. Ce qui reste incertain
1. Le Sharpe attendu : 1,15 brut est une estimation avec une erreur type d'environ 0,5. Sur 3 ans de réel, on ne
   distinguera pas 0,9 de 1,5.
2. Le régime 2023 : Sharpe 0,59, trois trimestres négatifs. C'est le seul épisode où l'arbitrage inter-bourses semble
   s'être resserré.
3. La base USDT/USD : la sleeve vit d'elle. Une régulation des stablecoins, des délistages MiCA ou un changement de la
   mécanique de frappe peuvent la fermer.
4. La jambe courte : t 1,64 hors échantillon.
5. Le funding avant 09/2019, non modélisé.
6. La liquidité du week-end sur le CME 24/7.
7. L'accès réglementaire, en §4.

## Sources consultées le 2026-10-30
- Hyperliquid, frais : https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
- Hyperliquid, funding (horaire, 1/8 du taux 8 h, intérêt 0,00125 %/h, plafond 4 %/h) :
  https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding
- Hyperliquid, API publique `l2Book`, `metaAndAssetCtxs`, `fundingHistory`, `candleSnapshot` : https://api.hyperliquid.xyz/info
- IBKR, commissions futures (MBT 0,85 $ ; Coinbase Nano 0,20 $ ; BFF 0,25 $) :
  https://www.interactivebrokers.com/en/pricing/commissions-futures.php
- IBKR, frais CME non-membre (Bitcoin Micro 1,15 $ ; BFF 0,35 $) : https://www.interactivebrokers.com/en/accounts/fees/CME.php
- IBKR, fiche MBT (0,1 BTC, tick 5 $/BTC, six mensuelles, fin le dernier vendredi 16:00 Londres, horaire affiché
  pré-24/7) : https://www.interactivebrokers.com/en/trading/cme-micro-bitcoin.php
- CME 24/7 depuis le 29/05/2026 (secondaires ; la page CME renvoie 403) :
  https://www.theblock.co/post/390491/cme-group-launch-24-7-crypto-futures-options-trading-may-29 et
  https://theblock.co/post/403304/cme-groups-crypto-derivatives-50-million
- Nano BTC chez IBKR (24/7, version perpétuelle) :
  https://www.theblock.co/post/389256/interactive-brokers-adds-nano-bitcoin-ether-futures-via-coinbase-derivatives
  ; frais de bourse (secondaire, 2022) : https://www.optimusfutures.com/nano-bitcoin-futures.php
- Binance, frais spot : https://www.binance.com/en/fee/schedule
- Coinbase Advanced (secondaire ; la page officielle renvoie 403) :
  https://cryptodaily.co.uk/2026/09/coinbase-advanced-fees-usdc-vip-tiers
- Données : Coinbase Exchange REST (`/products/{BTC,ETH}-USD/candles`), Binance Vision (klines spot 1 h et 1 j),
  Binance USD-M `fundingRate`, FRED DTB3 et DEXUSEU, yfinance `BTC=F`.
  Caches dans `scratchpad/c9_verif/raw/`, hors git ; script : `code/download.py`.

Compte des statistiques : `n_tests.json` (132 statistiques, aucune nouvelle configuration de signal).
