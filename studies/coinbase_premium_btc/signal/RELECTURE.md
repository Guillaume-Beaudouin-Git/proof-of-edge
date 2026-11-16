# C9 — Relecture indépendante (prime Coinbase → BTC)

**2026-10-30, relecteur indépendant.** `run.py` reproduit à l'identique par une réimplémentation séparée (IS 1,896 / 1,929 / 1,572 ;
holdout 0,610 / 0,909 / 1,876 ; délai +1 h 1,42 / 1,29 / 1,20 ; CSV relancés identiques au bit près, sorties redirigées hors `out/`).
Données ajoutées pour la relecture (hors dépôt) : Binance Vision 1 h OHLC spot BTC/ETH, perp USD-M BTCUSDT 1 h (2020→),
BTCUSDT 1 min, USDC/USDT et TUSD/USDT 1 h. Scripts : `scratchpad/c9/t0…t13*.py` (temporaires, non commités).

## (a) Verdict : **CONFIRMÉ AVEC RÉSERVES**
L'effet n'est **pas** un artefact de non-synchronisation (les trois diagnostics L66 le rejettent) et il existe en USD (Coinbase).
Mais (1) ce n'est pas une « demande US de BTC » : la composante propre au BTC ne porte que de la **convergence** entre bourses ;
la continuation vient de la composante **commune** aux primes BTC et ETH (≈ base USDT/USD + prime US/offshore générale) ;
(2) **seul h = 24 h est confirmé hors échantillon** ; h1 et h4 ne le sont pas et meurent au coût.

## (b) Contrôles (Sharpe √365, zéros inclus ; « IS/HO » = 2017-2023 / 2024-2026)
**L66 — les trois diagnostics, aucun ne s'effondre :**

| Diagnostic | h1 | h4 | h24 | Signature d'un artefact (L66) |
|---|---|---|---|---|
| (a) saut : entrée retardée d'1 barre, IS (part conservée) | 1,47 (77 %) | 1,23 (64 %) | 1,06 (67 %) | 6-46 % |
| (a') 2 barres / 3 barres, IS | 0,31 / 0,59 | 0,95 / 0,46 | 1,07 / 0,97 | — |
| (b) mêmes trades, patte Binance, bps/trade (t) | +7,8 (4,5) | +21,4 (4,8) | +73,7 (4,0) | — |
| (b) mêmes trades, patte **Coinbase USD** (t) | **+3,7 (2,1)** | **+13,2 (3,0)** | **+61,1 (3,4)** | signe OPPOSÉ |
| (b) part « convergence » (prime CB−BN qui se referme) | 53 % | 38 % | 17 % | 100 % |
| (c) prime OHLC/4 des deux côtés, IS / HO | 1,36 / 0,73 | 1,41 / 0,95 | 1,25 / 1,75 | effondrement |
| (c) prime (H+L)/2, IS / HO | 0,86 / 0,45 | 1,24 / 0,86 | 1,05 / 1,99 | effondrement |
| (c) prime sur l'open de t+1 (1er trade) des deux côtés, IS / HO | 1,71 / 0,35 | 1,68 / 0,67 | 1,51 / 1,92 | — |

Nuance : à h1 l'effet tient en ~2 h (0,31 à +2 barres) et, en 2017-2018, h1 est de la convergence pure (Sharpe Coinbase −0,18 / −0,19).

**Mécanisme (décisif pour le récit).** Prime BTC − prime ETH (neutre USDT) : IS −0,06 / −0,21 / 0,05 → **rien**. Prime ETH seule → BTC :
1,32 / 1,48 / 0,94. Régression jointe (z commun zc + résidu BTC zr, β glissant médian 0,87, HAC) : le résidu BTC prédit Binance
**+1,09 (t 2,2) et Coinbase −1,01 (t −2,0)** à h1 = convergence pure, et ≈ 0 à h4/h24 ; la composante commune prédit les deux pattes
(h4 : BN +5,6 t 4,5 / CB +4,7 t 3,8 ; holdout t 2,9 / 2,7 ; h24 holdout t 3,1 / 2,9). Proxy USDT/USD = −ln(USDC/USDT) Binance :
corrélation de niveau 0,87 avec la prime BTC ; son z prédit BTC-USD (Coinbase) à h4 (IS t 2,7, HO t 2,3) et h24 (t 2,0 / 2,8).

**Horloges (2).** Corrélation des rendements horaires CB/BN : décalage 0 = 0,967 (2017 0,86 ; ≥ 0,98 dès 2019), ±1 h = −0,02 ;
chocs du 12/03/2020 10:00 (−20 % / −19 %) et du 19/05/2021 12:00 sur la même bougie ⇒ alignement correct, pas de décalage d'une heure.

**Exécution (3).** Entrée réelle après la clôture du signal (minutes Binance), IS / HO : h4 1,91 / 0,92 (1er trade de t+1),
1,83 / 0,85 (+1 min), 1,73 / 0,93 (+5 min), 1,52 / 0,92 (+30 min) ; h24 1,52-1,54 / 2,01-2,13 jusqu'à +5 min. L'exécution « au prix du
signal » n'est pas le moteur ; la variante délai +1 h est une référence prudente, pas indispensable. Perp USD-M (2020→) = spot :
h4 1,94 / 0,90, h24 1,57 / 1,88 (la convergence est aussi captée par le perp). Funding signé : −0,3 bps/trade (h4), −0,9 (h24).

**USDT (4).** Hors fenêtres de stress connues (09/2017, 10/2018, 04/2019, 03/2020, 05/2022, 11/2022, 03/2023) : 1,79 / 1,82 / 1,46 IS
(−0,1) ; sans filtre : 1,74 / 2,03 / 1,53. Le filtre 1 % ne retire que 2017-2019 (3 237 h sur 3 283). Mais le contrôle neutre-USDT
est nul : retirer les dépegs ne suffit pas, **la base USDT fait partie du signal**, elle n'en est pas un bruit.

**Placebos (5).** Décalages retardés k = +24…+168 : h1 ≤ 0,26, h4 ≤ 0,34, h24 ≤ 0,48 → largement battus. Les 4 décalages k < 0
utilisent le z **futur** : le 2,08 qui bat h24 est **k = −24 (look-ahead)**. Il mesure la corrélation contemporaine prime/prix
(z > 2 suit +120 bps sur 24 h, z < −2 suit −112 bps), pas « un signal résiduel persistant » comme l'écrit le RAPPORT.

**Code (6).** `run_strategy` correct : entrée i, sortie i+h, P&L sur r1[i+1..i+h], pas de chevauchement (i += h), trou > h+2 h écarté,
w = vol 720 h décalée (T−1), z_t n'utilise que l'information disponible en t. Aucun biais d'anticipation trouvé.

**Années / jambes (7).** Sharpe par année, Binance (Coinbase entre parenthèses) :

| | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| h1 | 3,44 (−0,18) | 2,13 (−0,19) | 1,87 (1,35) | 2,50 (1,30) | 1,52 (0,84) | 2,20 (1,88) | 0,98 (0,49) | 0,28 (−0,17) | 0,06 (−0,26) | 1,46 (1,28) |
| h4 | 2,38 (−0,13) | 2,88 (1,43) | 1,60 (1,27) | 3,28 (2,56) | 1,46 (0,89) | 2,01 (1,79) | 0,73 (0,32) | 0,44 (0,14) | 1,14 (0,88) | 1,29 (1,16) |
| h24 | 1,87 (1,07) | 1,25 (0,80) | 1,83 (1,60) | 2,08 (1,80) | 2,08 (1,83) | 1,56 (1,44) | 0,52 (0,30) | 2,07 (1,86) | 1,84 (1,71) | 1,81 (1,75) |

2017-2018 = 19 / 18 / 12 % du P&L IS ; IS hors 2017-2018 : 1,82 / 1,86 / 1,63 (Coinbase 1,20 / 1,42 / 1,41) → pas de dépendance
à la période de forte prime. Jambes holdout (Binance, bps/trade, t) : h1 long +2,7 (1,2), short −0,1 (−0,1) ; h4 long +8,9 (1,2),
short +2,3 (0,5) ; h24 long +58,8 (2,3), short +36,7 (1,8). Jambe longue IS sur Coinbase : h1 +1,7 (t 0,6), h4 +8,5 (t 1,2).

**Point mort (8).** Trades/an (557 / 253 / 100) et brut/trade (7,8 / 21,4 / 73,7 bps) cohérents avec la série. Recalculé sur la série
quotidienne pondérée (coût × w à chaque trade) : SR1 / SR0 = 3,2 / 6,8 ; 9,5 / 19,0 ; **23,8 / 64** bps (rapport : 3,5 / 7,8 ; 9,3 / 21,4 ;
29 / 73,7). Holdout net : h4 **0,17 à 5 bps, −0,58 à 10 bps** ; h24 1,71 à 5 bps, **1,54 à 10 bps**.

## (c) Défauts
**Bloquants pour la formulation actuelle (pas pour le résultat h24) :**
1. **« PASS sur les 3 horizons »** : seul h24 est confirmé hors échantillon (HO 1,88, t 2,96, IC bloc √365 [0,75 ; 2,89] ; Coinbase 1,75 ;
   deux jambes > 0). h1 : HO 0,61 (t 0,88), nul en 2024-2025, jambe short HO −0,1. h4 : HO 0,91 (t 1,42, IC [−0,34 ; 2,00]),
   **0,25 sans les 5 meilleurs jours**, jambe short HO +2,3 bps (t 0,5), net 0,17 à 5 bps. Les présenter comme « IS seulement ».
2. **Mécanisme mal nommé (L37)** : la prime spécifique au BTC (« demande US ») ne prédit que la convergence Binance↔Coinbase ;
   la continuation vient de la composante commune BTC/ETH, dominée par la base USDT/USD. Renommer (« prime USDT/US-offshore
   commune → BTC ») et ajouter le risque USDT (régime : dépeg, délistages MiCA, changement de la mécanique de frappe).

**Mineurs :**
3. Placebos : 4 sur 8 sont des look-ahead (k < 0) ; l'interprétation du 2,08 à h24 est inversée (voir 5). Contrôle à refaire avec les
   seuls décalages retardés ; et, L66 oblige, ce placebo temporel ne suffit pas — les trois diagnostics ci-dessus le complètent.
4. Annualisation incohérente dans `common/stats.py` : `summary` calcule l'IC bootstrap en √252 alors que le Sharpe est en √365 (bornes
   ×0,83 : HO h24 [0,63 ; 2,40] → [0,75 ; 2,89] ; le point IS h1 1,90 n'est pas au bord de son IC, qui est [1,29 ; 2,47]) ; `fold_table`
   et `alpha_ann` en √252 (plis sous-estimés ×0,83, conservateur) ; `maxdd_at_10vol` à ≈ 12 % de vol réelle (365 j/an).
5. Le « walk-forward » n'estime aucun paramètre : c'est un tableau de sous-périodes 2019-2023 (2017-2018 hors plis) ; le nommer ainsi.
6. Point mort optimiste de 10-20 % à h24 (cf. 8) ; le funding est négligeable et légèrement défavorable à la jambe longue.
7. Dose-réponse : l'effet est continu dès |z| < 1 (h4 IS +2,3 bps, t 2,1) ; hors échantillon il vit à |z| 1-2 (h4 +6,9 / +6,1, t 3,1 / 2,2)
   et s'inverse à |z| > 4 (h24 −46 bps, t −3,0, n 56) ; seuil 3 → h4 HO 0,08. Le seuil 2 n'a rien de spécial ; ne pas re-sélectionner
   a posteriori seuil 1,5 (HO 1,63 / 1,52 / 1,87) ni la composante commune : ce serait de la sélection sur le holdout.
8. Pli 2023 faible partout (h4 0,73, h24 0,52) : à surveiller en L31 (arbitrage inter-bourses plus rapide après 2023 pour h1/h4).

## (d) Estimation honnête du Sharpe brut hors échantillon
- **h = 4 h : ≈ 0,7 (fourchette 0,4-1,0)**, ≈ 0,5 en USD propre (Coinbase). Le holdout (0,91) est non significatif, porté par quelques
  jours et la seule jambe longue ; au coût taker (5-10 bps) il est **≈ 0** ⇒ non viable.
- **h = 24 h : ≈ 1,3 (fourchette 0,9-1,6)**, ≈ 1,1 net de 10 bps. On rabat le holdout (1,88, délai +1 h 2,07, Coinbase 1,75) vers l'IS
  (1,57) pour tenir compte des trois horizons testés, de la dépendance aux meilleurs jours (0,92 sans les 10 meilleurs jours du holdout)
  et du pli 2023 (0,52). C'est le seul horizon annonçable, sous le nom de son vrai mécanisme.
