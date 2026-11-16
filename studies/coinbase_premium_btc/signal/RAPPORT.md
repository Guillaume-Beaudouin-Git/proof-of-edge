# C9 — Prime Coinbase (Coinbase − Binance) → continuation BTC : **PASS au brut — CONFIRMÉ AVEC RÉSERVES en relecture : seul h = 24 h tient hors échantillon, et le mécanisme est la base USDT/USD, pas la demande US**

**2026-10-30.** PREREG : `PREREG.md` (commit `04e80a0b`, avant tout calcul). Code : `code/run.py`
(+ `download_coinbase.py`). Sorties : `out/*.csv`. Données : Coinbase Exchange 1 h (BTC-USD 2015-07→,
ETH-USD 2016-05→, API publique sans clé) ; Binance spot 1 h BTCUSDT/ETHUSDT (Binance Vision, 2017-08→).
Primes horaires 2017-08-17 → 2026-09-30 (79 748 heures) ; 3 283 heures exclues par le proxy de dépeg USDT
(primes BTC et ETH simultanément > 1 % de même signe). IS 2017 → 2023, holdout 2024-01 → 2026-10 ouvert une fois.
Prime : moyenne +1,6 bps, écart-type 21 bps ; z > 2 : 2 143 heures, z < −2 : 3 608 heures.

## Verdict selon les critères gelés (série quotidienne, zéros les jours sans trade, Sharpe √365)

| Horizon | Sharpe IS | t HAC | Plis (2019-2023) | Holdout | Jambe long z>2 (bps/trade, t) | Jambe short z<−2 | Placebos décalés (8) | L38 R² | Délai +1 h IS / holdout |
|---|---|---|---|---|---|---|---|---|---|
| h = 1 h | **1,90** | 4,79 | 1,55 / 2,15 / 1,06 / 1,86 / 0,87 (5/5) | 0,61 (t 0,88) | +6,1 (t 2,08) | +8,9 (t 4,14) | max 1,17 < 1,90, 0/8 au-dessus | 0,2 % | 1,42 / 0,77 |
| h = 4 h | **1,93** | 4,97 | 1,33 / 2,77 / 1,05 / 1,72 / 0,65 (5/5) | 0,91 (t 1,42) | +17,3 (t 2,39) | +24,2 (t 4,08) | max 1,10 < 1,93, 0/8 | 0,8 % | 1,29 / **1,15** (t 1,97) |
| h = 24 h | **1,57** | 3,69 | 1,52 / 1,72 / 1,68 / 1,34 / 0,45 (5/5) | **1,88** (t 2,96) | +82,6 (t 3,04) | +66,8 (t 2,73) | max 2,08 > 1,57, **1/8 au-dessus** | 0,7 % | 1,20 / **2,07** (t 3,20) |

- **H1** : les trois horizons ont Sharpe WF > 1 et t > 2,5 ; les deux jambes sont positives (L25) à chaque
  horizon ⇒ **PASS**. Le placebo strict (observé > max des 8 décalages) passe à h = 1 et 4 ; à h = 24 un
  décalage sur 8 fait mieux (2,08) — l'horizon long garde plus de signal résiduel dans un décalage de
  24-48 h (la prime est persistante), ce qui est cohérent avec le mécanisme mais affaiblit le contrôle.
- **L38** : β ≈ −0,02 à −0,06, R² < 1 %, corrélation −0,05 à −0,09 contre BTC vol-targeté : **orthogonal à BTC**.
- **L26** : une heure de retard coûte 25-33 % du Sharpe IS, mais le holdout du délai-1 h est **meilleur**
  que sans délai (h4 1,15, h24 2,07) : l'effet n'est pas concentré dans la minute du signal.
- **L31** : les plis 5 (2023) sont les plus faibles (0,45-0,87) ; 2024-2026 repart (holdout h24 1,88).
- Distribution : skew quotidien **+1,9 à +6,7** (gains asymétriques, pas de queue gauche), MaxDD à 10 % de
  vol −7,5 % à −11 % en IS, pire jour −3,8 à −5,6 % @10 % vol.

## Point mort (brut par trade, coût aller-retour qui ramène le Sharpe à 1 puis 0)

| Horizon | Trades/an (IS) | Brut/trade | Coût RT à Sharpe 1 | Coût RT à Sharpe 0 | Lecture véhicule (JUGÉ) |
|---|---|---|---|---|---|
| 1 h | 562 | 7,8 bps | 3,5 bps | 7,8 bps | mort au taker (Binance perp 10 bps RT, HL ≈ 5-7) ; vivant seulement maker |
| 4 h | 255 | 21,4 bps | **9,3 bps** | 21,4 bps | ≈ Sharpe 1 au taker Binance perp (10 bps RT) ; > 1 sur Hyperliquid taker (≈ 5-7 bps RT, JUGÉ) et en maker |
| 24 h | 101 | 73,7 bps | **29 bps** | 73,7 bps | vivant sur tout véhicule retail (perp HL/Binance, spot Coinbase/Kraken) |

Capacité : BTC seul, 100-250 trades/an, notionnel libre ⇒ pas de contrainte de lot (perp fractionnable).

## Réserves à faire relire
1. **Alignement des horloges** : Coinbase `time` et Binance `open_time` sont des débuts de bougie UTC ;
   la prime à l'heure t utilise les deux clôtures à t+1h, et le trade part de la clôture Binance de la
   même heure (même instant). La variante délai +1 h est la référence prudente (L26).
2. **USDT** : la prime porte le prix de l'USDT ; le z-score 30 j absorbe les dérives lentes, le filtre
   dépeg retire les épisodes 2022-2023 ; un biais résiduel possible lors des mouvements rapides de l'USDT.
3. **Qualité des bougies Coinbase 2017-2018** (volumes faibles, trous) : les heures manquantes sont
   simplement absentes (jointure interne) ; un trou > h+2 heures annule le trade.
4. **Short BTC** : la jambe short (z < −2) porte la moitié de l'edge ; sur spot elle n'existe pas (perp ou
   marge nécessaire). Sur HL/Binance perp, le funding est un coût de portage sur 1-24 h (négligeable à 4 h,
   ≈ 1-3 bps/jour à 24 h quand il est extrême — non modélisé ici, à inclure dans le point mort).
5. Deux cryptos (BTC signal + BTC trade) : pas de cross-section ; c'est un time-series sur UN actif.

## Compte
Configurations : 3 horizons (déclarées 3). Diagnostics : délai, placebos, jambes, L38, plis, point mort.

## Relecture indépendante (`RELECTURE.md`, autre modèle, 2026-10-30) : **CONFIRMÉ AVEC RÉSERVES**

1. **Pas un artefact de synchronisation (L66)** — les trois diagnostics tiennent : (a) entrée retardée d'une barre :
   77 / 64 / 67 % du Sharpe IS conservés (h1 / h4 / h24) ; (b) les mêmes trades rapportent aussi sur Coinbase en USD,
   avec le même signe (h4 +13,2 bps, t 3,0, contre +21,4 sur Binance ; h24 +61,1 contre +73,7) ; (c) prime recalculée
   sur (O+H+L+C)/4 : IS 1,36 / 1,41 / 1,25, holdout 0,73 / 0,95 / 1,75. Horloges alignées (corrélation 0,967 au
   décalage 0) ; entrer 1-5 min après le signal ou sur le perp donne la même chose ; funding négligeable.
2. **Le mécanisme est mal nommé.** La prime propre au BTC (BTC − ETH, neutre en USDT) ne prédit rien (IS −0,06 / −0,21 /
   0,05) et son résidu ne donne que de la convergence entre bourses (Binance +1,09 t 2,2, Coinbase −1,01 t −2,0). La
   continuation vient de la **composante commune aux primes BTC et ETH, dominée par la base USDT/USD** (corrélation 0,87
   avec −ln(USDC/USDT)). Vrai nom : **« base stablecoin / bourses US contre offshore → BTC »**, pas « demande US de BTC ».
3. **Seul h = 24 h tient hors échantillon** : holdout 1,88 (t 2,96), 1,75 sur Coinbase, deux jambes positives, **1,54 net
   de 10 bps**. h1 : holdout 0,61, nul en 2024-2025. h4 : holdout 0,91 (t 1,4) mais 0,25 sans ses 5 meilleurs jours,
   jambe short +2,3 bps (t 0,5), net 0,17 à 5 bps ⇒ non viable.
4. **Défauts mineurs** : à h24 le placebo qui bat l'observé est k = −24 (le z FUTUR) : corrélation contemporaine, pas
   persistance (ma lecture était fausse) ; dans `common/stats.py`, `summary()` annualise l'IC bootstrap et les plis en √252
   alors que le Sharpe des séries crypto est en √365 ⇒ **IC et plis des tableaux C8/C9 à multiplier par 1.204**
   (h24 IS : IC [0,85 ; 2,30] → [1,03 ; 2,77] ; h4 : [1,27 ; 2,55] → [1,53 ; 3,07]) ; point mort h24 sur la série
   quotidienne : 23,8 / 64 bps (contre 29 / 73,7 annoncés par trade) ; dans le holdout l'effet vit à |z| 1-2 et s'inverse
   au-delà de |z| > 4.
5. **Estimation du relecteur** : h4 ≈ 0,7 (0,4-1,0), ≈ 0 net ⇒ non viable ; **h24 ≈ 1,3 (0,9-1,6), ≈ 1,1 net de 10 bps**.

**Verdict retenu : une sleeve, h = 24 h, sous son vrai nom (base USDT/USD et bourses US vs offshore), Sharpe brut OOS
≈ 1,3, net ≈ 1,1 ; h1 et h4 abandonnés.** Dépendance structurelle à l'USDT (si la base USDT/USD disparaît, le signal
aussi) : à surveiller, pas à ignorer.
