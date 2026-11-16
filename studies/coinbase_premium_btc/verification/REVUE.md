# REVUE — relecture indépendante et adversariale de la vérification locale de C9 h24 (2026-10-30)

Rôle : refaire les chiffres clés avec un code propre (`revue/revue_c9.py`, sorties `revue/out/`, compteur
`revue/n_tests.json`), chercher ce qui est faux, surévalué ou non testé. `NOTE.md` du chercheur n'est pas modifié ;
en cas de désaccord, ce fichier et `SYNTHESE.md` prévalent. Chaque constat est MESURÉ ou JUGÉ.

## 0. Verdict de relecture
**Le dossier du chercheur TIENT dans ses chiffres et dans sa méthode.** Je reproduis sa série à 0,99998 près avec un
code écrit séparément, et la série du cloud à 0,98. Ses chiffres clés sont justes (reproduction, concentration par trade,
jambes, années, funding, point mort, granularité du MBT). Je corrige **une erreur de calcul** (erreur type du holdout,
§4) sans effet sur la conclusion, et j'ajoute **trois constats qu'il n'a pas faits** : la concentration par ÉPISODE est
bien plus forte que par trade (§3), la devise d'exécution coûte 0,1 à 0,25 de Sharpe selon le prix auquel le perp HL
s'aligne (§5), et la confirmation du holdout est marginale si l'on compte les 42 configurations du module cloud lues sur ce
même holdout (§4). Mon estimation du net attendu sur le perp HL en taker est **≈ 0,75 (0,5-1,0)**, un cran sous le
≈ 0,87 du chercheur, au bord du RESEARCH_PASS.

## 1. Procédure : PREREG, anticipation, puissance (MESURÉ)
- **Ordre des horodatages** (git + mtime) : PREREG commité 14:51:02 → pages de frais 14:52-14:53 → données brutes
  14:54-15:06 → `c9lib.py`/`run_repro.py` 14:56 → sorties 15:05 → commit 15:06. Le PREREG précède bien le premier
  téléchargement et le premier calcul. ✓
- **Écarts à la spec gelée** : (i) `min_periods=600` sur la vol là où le PREREG dit « 720 derniers rendements » —
  déviation silencieuse, effet < 0,05 de Sharpe sur 2018 (ma lecture « 720 rendements valides » donne 1,37 contre son
  1,42) ; (ii) S1(c) annoncé « 5 plis » et fait en 8 choix annuels — plus exigeant, pas moins ; (iii) le « WF 8 plis »
  de G1 n'estime aucun paramètre : ce sont des sous-périodes, à nommer ainsi (le chercheur le dit en note, pas dans le
  tableau). Rien de ces écarts ne change un signe.
- **Anticipation** : signal au close de l'heure t (clôtures Coinbase et Binance), poids sur la vol connue en t, entrée au
  close de t. L'entrée à l'**open de la bougie suivante** (premier prix après le signal) donne IS 1,595 / HO 1,854
  contre 1,605 / 1,854 : le « même instant » n'est pas le moteur. Le délai +1 h (1,27 / 2,05) reste la lecture prudente.
- **Puissance** : effet minimum détectable à 80 % (α 5 %, unilatéral) : holdout 1,50 ; 6 mois 3,52 ; 1 an 2,49 ;
  3 ans 1,44. Le holdout (1,85) dépasse à peine son MDE ; le forward ne peut rien valider (le chercheur le dit).
- **Reproduction indépendante du chercheur** : il affirme avoir écrit son code avant d'ouvrir `run.py` du cloud. Je ne
  peux pas le vérifier, mais la structure diffère (dataclass, fenêtres sur observations valides, rendements simples,
  cash retiré) et les écarts résiduels sont ceux qu'il liste. Plausible.

## 2. Reproduction (MESURÉ ; `revue/out/repro.csv`, `variantes_prix.csv`)
| | IS 2017-23 | HO 2024-09/2026 | ALL | cloud IS / HO |
|---|---|---|---|---|
| h24, moi | **1,605** (t 3,76) | **1,854** (t 2,91) | 1,674 | 1,57 / 1,88 |
| h24, chercheur | 1,610 | 1,854 | 1,667 | |
| h24 délai +1 h | 1,273 | 2,046 | 1,492 | 1,20 / 2,07 |
| h4 | 1,919 | 0,907 | 1,613 | 1,93 / 0,91 |
| h1 | 1,851 | 0,616 | 1,470 | 1,90 / 0,61 |

657 trades IS, 264 HO, 10 forward (identiques au chercheur). Corrélation quotidienne avec le cloud 0,982 ; 1 377 jours
actifs communs sur 1 391 (cloud) / 1 421 (moi). Le cloud écarte les trades à trou > h+2 h, d'où ses 14 jours de moins.

**Fragilité de spec découverte en route** : une vol glissante sur 720 lignes calendaires sans tolérance aux trous efface
2018-2021 (Binance a 104 heures manquantes en 2018, 170 au total) et donne IS 1,09 au lieu de 1,61. La lecture correcte
(720 rendements valides) redonne le résultat. Toute implémentation live doit traiter les heures manquantes comme le backtest.

**Devise d'exécution** (nouveau) : le P&L est mesuré sur Binance BTCUSDT. Aux prix Coinbase BTC-USD, mêmes trades :
IS **1,33** / HO **1,72** / ALL **1,44** (58 / 41 / 54 bps par trade contre 72 / 45 / 64) ; au mi-prix 1,47 / 1,79 / 1,56.
L'écart est la part de « convergence » de la prime (17 % du brut IS, 8 % au holdout). Voir §5 pour ce que cela implique
sur le perp HL.

## 3. Concentration : la vue par trade sous-estime la vue par épisode (MESURÉ ; `revue/out/concentration_episodes.csv`)
Par trade, je confirme le chercheur : ALL sans les 5 meilleurs 1,53, sans les 10 meilleurs 1,38 ; HO sans ses 10 meilleurs
0,98 (56 % du P&L). Mais les trades se suivent (un signal persistant produit des entrées consécutives). En grappes de trades
séparés de moins de 7 jours :

| | épisodes | top 1 | top 3 | top 5 | top 10 |
|---|---|---|---|---|---|
| ALL — part du P&L | 125 | 8 % | 22 % | 34 % | **56 %** |
| ALL — Sharpe sans ces épisodes | | 1,64 | 1,50 | 1,31 | 0,94 |
| HO — part du P&L | 45 | 20 % | 52 % | **73 %** | 100 % |
| HO — Sharpe sans ces épisodes | | 1,54 | 1,15 | **0,72** | ≈ 0 |

Au holdout, 5 épisodes (73 trades, 28 % des trades) font 73 % du P&L ; les 35 autres épisodes font 27 %. C'est la signature
d'une **collection d'épisodes** (même nature que le carry de funding du module cloud), pas d'une prime diffuse. JUGÉ : ce
n'est pas disqualifiant (skew +5, pas de queue gauche, 8 années sur 8 positives, 2023 à 0,59 reste > 0), mais (a) le
drapeau FRAGILE du PREREG, écrit par trade, était trop clément ; (b) un forward de 3-6 mois peut ne contenir AUCUN
épisode payant et paraître plat sans rien dire ; (c) la pire année (2023) est une année sans épisode, pas une année de
pertes. Pire trade : −2,0 % du compte (17/09/2024, long) ; pire épisode ≈ −2,6 %.

**Dose-réponse** (`revue/out/dose_reponse_h24.csv`) : au holdout l'effet vit à |z| ∈ [2 ; 2,5) (188 trades, +50 bps, t 3,3,
77 % du P&L) ; [2,5 ; 3) +42 bps (t 1,0) ; [3 ; 4) +48 (t 0,5) ; > 4 : −56 bps sur 7 trades (non significatif, pas un
« retournement » établi). La bande [1 ; 2), NON tradée, rapporte +20 bps (t 2,1) en IS et +29 bps (t 2,8) au holdout : le
seuil 2 n'a rien de spécial, l'effet est celui du signe de z, pas de l'extrême. **Ne pas en faire une variante** : ce serait
une sélection sur le holdout (le relecteur cloud l'avait déjà dit).

## 4. Sélection de l'horizon et multiplicité (MESURÉ puis JUGÉ ; `revue/out/selection_horizon.json`)
- **Correction d'une erreur de calcul du chercheur.** Son erreur type du holdout h24 (0,99) applique la formule de Lo avec
  le Sharpe ANNUEL au carré dans le terme (1 + SR²/2) ; avec le Sharpe quotidien, SE = 0,60 (bootstrap par blocs : 0,54).
  Conséquence sur son rétrécissement (b) : variance inter-horizons 0,42 > SE² 0,36, donc le rétrécissement n'est pas total
  : h24 rétréci = **1,22** au lieu de 1,13. Sans effet sur son 1,15 retenu (qu'il arrondit entre (a) 1,13 et (c) 1,10).
- **Inflation du « meilleur de trois »** : bootstrap par blocs JOINT des trois séries quotidiennes du holdout (corrélées
  0,64-0,75 entre elles) : E[max des 3] − E[moyenne des 3] = **0,75**. Sous l'hypothèse où les trois horizons auraient le
  même vrai Sharpe, lire le meilleur des trois gonfle de 0,75 en moyenne : 1,85 − 0,75 ≈ 1,10, cohérent avec la moyenne des
  trois (1,13) et le walk-forward (1,10 sur le holdout, 1,41 sur 2019-2026). JUGÉ : **brut attendu ≈ 1,1 (0,8-1,4)**, le
  1,15 du chercheur est dans la fourchette ; sa nuance « l'IS de h24 n'était pas gonflé » est juste (h24 était le pire IS).
- **Famille réelle** : C9 est un candidat parmi 9 du module cloud 1 (42 configurations, holdout « ouvert une fois » par
  candidat). Šidák sur 3 : p 0,0018 → 0,0053 (chercheur, confirmé). Šidák sur 42 : **0,072**. La confirmation holdout seule
  est marginale au niveau du module ; en revanche l'IS de h24 (t 3,76, p 8,5e-5) survit à la même famille (p 0,0036).
  JUGÉ : les deux lectures ensemble soutiennent un effet réel ; la grandeur reste incertaine (± 0,5).
- Horizons : h4 et h1 meurent au holdout (0,91 / 0,62) et au coût ; rien à ajouter au cloud.

## 5. Véhicules et coûts (MESURÉ ; `revue/out/vehicules_revue.csv`, `revue_summary.json`)
**Sources vérifiées le 2026-10-30** : Hyperliquid docs, palier 0 perps **taker 0,045 % / maker 0,015 %** (relu en ligne ;
remises staking 5-40 %, parrainage sur les 25 premiers M$). IBKR commissions futures : **MBT 0,85 $** fixe/côté (page
cachée par le chercheur, relue) ; frais CME non-membre **Bitcoin Micro 1,15 $** (page IBKR des frais CME, cachée, relue).
CME 24/7 : The Block (19/02/2026) annonce le **29/05/2026** « sous réserve de l'examen réglementaire » ; le site CME
bloque la lecture automatisée ; **non confirmé à la source primaire**, le chercheur le dit aussi.

| Véhicule (série quotidienne avec zéros, √365, excès du cash) | ALL | HO | MaxDD | pire jour | skew | plis > 0 |
|---|---|---|---|---|---|---|
| Brut (prix Binance) | 1,67 | 1,85 | −7,0 % | −2,4 % | +5,1 | 8/8 |
| Perp HL taker 9,3 bps + funding réel, convention du chercheur | 1,40 | 1,53 | −8,7 % | −2,4 % | +5,0 | 8/8 |
| idem, **short paie rf** (collatéral USDC non rémunéré) | 1,37 | 1,48 | −9,1 % | −2,4 % | +5,0 | 8/8 |
| Perp HL maker 3 bps + funding, short paie rf | 1,54 | 1,69 | −7,8 % | −2,4 % | +5,1 | 8/8 |
| Perp HL taker, **prix Coinbase USD** (borne basse) | **1,14** | **1,36** | −10,3 % | −2,5 % | +5,0 | 7/8 |
| Perp HL taker, mi-prix | 1,26 | 1,42 | −9,7 % | −2,5 % | +5,0 | 8/8 |

- **Signe du cash sur le short** : le chercheur crédite rf au short (convention future CME, cash gagé rémunéré). Sur HL le
  collatéral USDC ne rapporte rien et le benchmark est le cash : le short PAIE rf. Effet −0,02 à −0,05 : négligeable, noté.
- **Devise du perp HL** (nouveau, le point qui compte) : le perp est margé en USDC et son oracle est une médiane de
  bourses majoritairement en USDT. En régime calme il suit Binance à 0,9999 (56 trades, chercheur). En stress USDT/USDC —
  précisément quand les gros trades arrivent — il est arbitré vers le prix USD. La vérité est entre la ligne « Binance »
  et la ligne « Coinbase USD » : **1,14-1,40 historique, 1,36-1,53 holdout**. Le chercheur n'a pris que la borne haute.
- **Funding** (reparsé) : +0,67 bp/trade en moyenne (+0,62 sur les 341 trades à funding HL réel), p95 18,4 bps ; longs
  +6,0 bps/trade, shorts −3,2 (le taux HL moyen est de 14 %/an, le long paie). 190 trades d'avant 09/2019 sans funding.
- **Point mort** (brut Binance, funding inclus) : 22,4 bps AR à Sharpe 1 (chercheur 22,8), **33 bps à 0,7**, 57 à 0 ;
  pente −0,028 Sharpe par bp AR (chercheur ≈ −0,03). Au brut attendu 1,1, le point mort à 0,7 tombe vers 14 bps AR.
- **Net attendu, JUGÉ** : brut 1,1 − traînée taker+funding 0,28 − décote de devise 0,05-0,2 = **≈ 0,75 (0,5-1,0)** en
  taker ; ≈ 0,9 en maker si rempli (ordres limite sur 100-250 trades/an : taux de remplissage non mesuré). Le chercheur
  dit ≈ 0,87 / ≈ 1,0 : il omet la décote de devise. La différence est dans l'erreur type (0,5), mais elle place le
  véhicule AU BORD du RESEARCH_PASS (> 0,7), pas confortablement dedans. Le RESEARCH_PASS **mesuré** sur l'historique
  net (1,37) est atteint, même à la borne basse (1,14).
- **MBT via IBKR, 12 000 €** (confirmé) : un lot = 0,1 × 77 174 $ = 7 717 $ = **57 %** du compte (EURUSD 1,12) ; le poids
  cible médian des deux dernières années est 0,24 (p90 0,32) : un lot vaut 2,4× la taille cible et **0 % des trades
  récents** atteignent un lot. À 1 lot fixe : Sharpe 1,47, vol 23 %, MaxDD −23,4 %, pire jour −8,2 %, skew +3,4 (identique
  au chercheur). Frais 4,54 $ AR = 5,9 bps à ce prix. L57 s'applique : la granularité interdit le vol-targeting ; le
  MaxDD à −23 % passe le seuil −25 % de peu, à un levier 2,4× la cible. Pas un véhicule pour ce compte.
- **Spot long seul** : une jambe sur deux ; Binance 1,13, Coinbase taker mort (chercheur, non refait, cohérent avec la
  pente −0,028/bp : 100 bps AR ≈ −2,8 de Sharpe).

## 6. Corrélations, admission (lecture, non refait)
L38 β −0,03, R² 0,2 % et ρ(A) 0,13 sont plausibles et sans enjeu (la sleeve est orthogonale par construction : 24 h,
deux sens). Aucun livre perso financé en réel aujourd'hui : la sleeve se juge seule, d'accord avec le chercheur.

## 7. Ce qui n'est pas testé et ne peut pas l'être ici
1. Taux de remplissage maker sur HL (le ≈ 1,0 maker est conditionnel à 100 % de remplissage : optimiste).
2. Comportement du perp HL pendant un stress stablecoin (aucune donnée HL avant 05/2023 ; un seul épisode, 03/2023, hors
   fenêtre HL). C'est la source de la fourchette 1,14-1,40.
3. Liquidité CME le week-end et la permission IBKR Ireland pour les futures crypto : sources secondaires seulement.
4. Accès réglementaire d'un résident français au perp HL : signalé par le chercheur, hors de portée d'une relecture.
5. Écart-type de la prime : 4,7 bps en 2025, 5,9 en 2026, contre 35-55 bps en 2017-2019. Le critère d'arrêt du forward
   (< 3 bps sur 30 j) est à **1,7 bp** du niveau actuel : la base USDT/USD s'est déjà presque refermée en amplitude ;
   le signal vit dans ce qui reste.

## 8. Corrections à porter dans la lecture du dossier (résumé)
| # | Point | Chercheur | Relecture |
|---|---|---|---|
| 1 | SE du holdout h24 | 0,99 (SR annuel dans la formule de Lo) | 0,60 ; rétréci (b) 1,22, pas 1,13 — sans effet sur le 1,15 |
| 2 | Brut attendu | ≈ 1,15 (0,9-1,4) | ≈ 1,1 (0,8-1,4) ; inflation du max de 3 mesurée à 0,75 |
| 3 | Net attendu perp HL taker | ≈ 0,87 | **≈ 0,75 (0,5-1,0)** : décote de devise 0,05-0,2 omise |
| 4 | Concentration | par trade : pas FRAGILE | par épisode : HO 5 épisodes = 73 % du P&L, sans eux 0,72 — à dire |
| 5 | Famille Šidák | k = 3 | k = 42 au niveau du module cloud : holdout p 0,072, IS p 0,0036 |
| 6 | Signe de rf sur le short HL | encaissé | payé ; −0,02 à −0,05 |
| 7 | Vol min_periods | 600 (PREREG : 720) | déviation silencieuse, effet < 0,05 ; la live doit gérer les trous Binance |
| 8 | Sources CME 24/7 | secondaires | idem, non confirmé à la source ; le point est bien signalé |
