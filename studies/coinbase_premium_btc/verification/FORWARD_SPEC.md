# Spec du forward papier C9 h24 (à ne PAS installer avant l'accord de Guillaume et la fin du déploiement de l'EA v2.14)

## But, et ce qu'il ne peut pas prouver
Un forward de 3 à 6 mois ne peut **pas** valider le Sharpe : l'effet minimum détectable à 80 % de puissance est de
3,5 sur 6 mois et de 1,4 sur 3 ans (MESURÉ, `out/horizon_selection.json`). Son rôle est **opérationnel** : vérifier
que le signal calculé en direct est celui du backtest, que les coûts et le funding réels sont ceux du modèle, et
qu'aucune rupture structurelle n'apparaît (base USDT/USD). Le jugement de performance reste celui du backtest.

## Sources (publiques, sans clé)
- Coinbase Exchange REST `GET /products/BTC-USD/candles?granularity=3600` et `ETH-USD` (bougies closes seulement).
- Binance spot REST `GET /api/v3/klines?symbol=BTCUSDT&interval=1h` et `ETHUSDT`.
- Hyperliquid `POST /info` : `{"type":"l2Book","coin":"BTC"}` (mid, fourchette), `{"type":"fundingHistory","coin":"BTC"}`.
- FRED DTB3 (cash) une fois par jour.

## Calcul (horloge)
- Toutes les heures à HH:01:30 UTC (bougie HH−1 close et publiée des deux côtés ; si une bougie manque, réessayer
  à HH:03 puis HH:05, sinon journaliser `MISSING` et ne pas trader l'heure).
- Prime = ln(close Coinbase / close Binance) ; heure exclue si |prime BTC| et |prime ETH| > 1 % de même signe ;
  z = (prime − moyenne des 720 dernières heures valides) / écart-type idem ; poids w = 0,10 / (σ 720 h des rendements
  horaires Binance × √8760), plafonné à 3. Le code doit être `code/c9lib.py` (fonctions `rolling_z`, `run_strategy`),
  importé tel quel, pour que le backtest et le direct partagent une seule implémentation.
- Signal +1 si z > 2, −1 si z < −2, à plat sinon ; un trade à la fois ; sortie 24 h après l'entrée.
- Trade fictif : entrée au mid HL lu à la seconde du calcul ; sortie au mid HL 24 h plus tard ; coût taker 4,5 bps
  par côté + demi-fourchette lue ; funding HL réel sommé sur la fenêtre tenue.

## Journaux (append-only, CSV, un fichier par mois)
1. `signals_YYYY-MM.csv` : heure, close CB/BN BTC et ETH, prime, z, dépeg, σ, w, signal, latence de publication des bougies.
2. `trades_YYYY-MM.csv` : id, signal, entrée (heure, mid, fourchette), sortie, funding cumulé, P&L brut, coût, P&L net.
3. `recon_YYYY-MM.csv` : chaque nuit à 00:30 UTC, recalcul complet du backtest sur les données re-téléchargées
   (Binance Vision + Coinbase) pour les 30 derniers jours ; écart heure par heure z direct − z recalculé, et trades
   direct contre trades recalculés.

## Critères d'arrêt (immédiats)
- Réconciliation : plus de 2 % des heures avec un signal différent du recalcul, ou un trade manquant/en trop sur 7 jours.
- Coût : coût aller-retour réalisé médian > 15 bps sur 20 trades (modèle 9,2 bps ; point mort Sharpe 1 au brut
  historique ≈ 23 bps, mais ≈ 5 bps au brut attendu de 1,15 — JUGÉ, `NOTE.md` §4).
- Structure : écart-type glissant 720 h de la prime < 3 bps pendant 30 jours (la base USDT/USD a disparu), ou
  dépeg USDT/USDC > 1 % (pause jusqu'à 720 h après retour sous 0,3 %).
- Perte : P&L net cumulé sur 91 jours sous −2,2 % à 10 % de vol (5e centile historique des fenêtres de 91 jours, net
  HL taker, `out/forward_reference_quantiles.json` ; −2,8 % sur 2023-2026 seuls).

## Passage au réel (décision de Guillaume, pas automatique)
Après au moins 3 mois et 25 trades (médiane historique par 91 jours) : réconciliation et coûts dans les tolérances,
aucune alerte structurelle, P&L net au-dessus du 5e centile historique. Taille initiale : 10 % de vol cible, soit un
notionnel d'environ 15-30 % du compte quand une position est ouverte. Revue complète à 6 mois.

## Comparaison au backtest
Chaque mois : P&L quotidien direct contre `out/daily_h24_perp_hl_taker.csv` prolongé par le recalcul nocturne ;
nombre de trades, part long/short, brut par trade, funding par trade (référence : +0,7 bp/trade, p95 19 bps).
