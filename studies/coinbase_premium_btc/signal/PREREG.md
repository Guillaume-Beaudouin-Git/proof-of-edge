# PREREG C9 — Prime Coinbase (Coinbase − Binance) comme proxy de demande US → continuation BTC

**Gelé le 2026-10-30 avant tout calcul.** (Les bougies ont été téléchargées, aucune statistique lue.)

## Hypothèse et mécanisme
Les acheteurs US (ETF/APs, institutionnels, retail US) s'exécutent sur Coinbase ; une prime persistante
de Coinbase sur Binance signale un flux non encore absorbé par l'arbitrage (Makarov-Schoar, JFE 2020 :
écarts inter-bourses persistants, liés à la pression d'achat locale). Hypothèse : la prime horaire
(z-score) prédit la continuation de BTC sur 1-24 h, dans les deux sens.

## Données
Coinbase Exchange REST public : BTC-USD, ETH-USD bougies 1 h, 2015/2016 → 2026-10. Binance spot BTCUSDT,
ETHUSDT 1 h (réduites aux mêmes horodatages ; fichiers 1 min Binance Vision déjà en cache, agrégés).
⚠ Coinbase cote en USD, Binance en USDT : la prime inclut le prix de l'USDT (dépeg 2022-2023) ⇒ la prime
est centrée par sa moyenne glissante 30 j (z-score) et les jours à |USDT − 1| > 1 % sont exclus (proxy :
prime moyenne sur ETH ET BTC simultanément déviante). Période IS 2017-01 → 2023-12 ; holdout 2024-01 →
2026-10 ouvert une fois.

## Signal (T−1) et exécution
- prime_t = ln(P_coinbase,t / P_binance,t), moyenne horaire ; z_t = (prime_t − moy 720 h) / écart-type 720 h.
- Position sur le perp/spot BTC prise au close de l'heure t : +1 si z_{t} > 2, −1 si z_{t} < −2, 0 sinon ;
  tenue h ∈ {1, 4, 24} heures (trois configurations), sans chevauchement (un signal à la fois).
- Vol-targeting 10 %/an (vol 30 j des rendements horaires de BTC, T−1). Série quotidienne = somme des
  P&L horaires du jour, zéros sinon, Sharpe √365.

## Critères (gelés)
- **H1** : pour au moins un horizon, Sharpe WF (5 plis expansifs 2018-2023) > 0,7 (objectif > 1,0),
  t HAC > 2,5 ; **deux jambes** (z > 2 et z < −2) > 0 (L25).
- **L38** : régression sur le buy-and-hold BTC vol-targeté ; R² > 30 % ⇒ timing de beta, présenté comme tel.
- **Placebo** : signal décalé de k ∈ {±24, ±48, ±72, ±168} heures (8 placebos) : l'observé > max des 8.
- **L26** : signal retardé d'une heure supplémentaire.
- **Holdout** 2024-2026 lu une fois. **Kill** : H1 fausse sur les 3 horizons ⇒ ARCHIVER.

## Compte
Configurations : 3 horizons = **3**.
