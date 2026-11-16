# PREREG — vérification locale indépendante de C9 (base USDT/USD → BTC, tenue 24 h)

**Gelé le 2026-10-30, avant tout téléchargement et tout calcul.** Seuls les fichiers du cloud
(PREREG, RAPPORT, RELECTURE, SYNTHESE, HANDOFF) ont été lus ; leur `code/` n'est ouvert qu'après la
reconstruction, pour expliquer les écarts.

## Objet
Reproduire C9 h24 avec des données publiques re-téléchargées et un code écrit ici, puis dire sur quel
véhicule elle peut vivre et à quel coût. Recherche seule, aucun déploiement.

## Spec reconstruite (choix fixés ici, là où le texte du cloud est ambigu)
- Données : Coinbase Exchange REST public, bougies 1 h BTC-USD et ETH-USD ; Binance Vision spot 1 h
  BTCUSDT et ETHUSDT (fichiers mensuels, puis quotidiens pour le mois en cours). Horodatage = début de
  bougie UTC des deux côtés ; la prime de l'heure t se lit à la clôture de la bougie.
- prime_t = ln(C_Coinbase,t / C_Binance,t) sur les clôtures (jointure interne des heures présentes).
- Dépeg : heure exclue si |prime_BTC| > 1 % et |prime_ETH| > 1 % de même signe. Une heure exclue n'entre
  ni dans la moyenne/l'écart-type glissants, ni comme signal.
- z_t = (prime_t − moyenne des 720 dernières heures valides, t incluse) / écart-type idem (720 obs. exigées).
- Signal à la clôture de l'heure t : +1 si z_t > 2, −1 si z_t < −2. Entrée au close Binance BTCUSDT de t,
  sortie au close de t+24 h (horloge calendaire ; si le prix de sortie manque, trade écarté). Pas de
  chevauchement : prochain signal possible à l'heure de sortie.
- Poids w_t = 0,10 / (écart-type des 720 derniers rendements horaires Binance jusqu'à t × √8760), plafonné à 3.
- P&L horaire = s · w · (r_h − rf_h), r_h rendement simple horaire Binance BTCUSDT, rf = DTB3 FRED / 8760 ;
  série quotidienne UTC = somme des heures, zéros les jours à plat. (Excès du cash : position synthétique
  entièrement collatéralisée, équivalente à un future/perp.)
- IS 2017-08 → 2023-12 ; holdout 2024-01 → 2026-09-30 (fenêtre du cloud) ; **forward** 2026-10-01 → dernière
  heure disponible, rapporté à part.

## Contrôles et critères de décision
| # | Contrôle | Critère / lecture |
|---|---|---|
| R1 | Reproduction h24 | Sharpe IS et holdout à ±0,10 de 1,57 / 1,88, et ≥ 90 % des entrées du cloud retrouvées à la même heure ⇒ REPRODUIT ; sinon écart expliqué après lecture de leur code, ou NON REPRODUIT |
| R2 | h1 et h4 (nécessaires au §4) | même tolérance contre 1,90/1,93 (IS) et 0,61/0,91 (holdout) ; lecture seulement |
| C1 | Concentration | part du P&L total des 1/3/5/10 meilleurs trades ; Sharpe sans eux ; P&L par année et trimestre. **FRAGILE** si Sharpe complet sans les 5 meilleurs trades < 0,7, ou une seule année > 40 % du P&L |
| C2 | Fenêtres de stress stablecoin (09/2017, 10/2018, 04/2019, 03/2020, 05/2022, 11/2022, 03/2023) | P&L dedans/dehors ; trades retirés par le filtre de dépeg ; **DÉPENDANT AU STRESS** si Sharpe hors fenêtres < 0,7 |
| C3 | Deux jambes (L25) | bps/trade et t HAC par jambe, IS et holdout ; les deux > 0 exigé |
| S1 | Sélection d'horizon | (a) moyenne des trois holdouts ; (b) rétrécissement : holdout h24 ramené vers la moyenne des trois horizons ; (c) walk-forward expansif à 5 plis qui choisit l'horizon au meilleur Sharpe passé seul. **Estimation retenue = la plus basse des trois si elles divergent de plus de 0,3** |
| V1 | Véhicules (perp HL, MBT CME via IBKR, spot long seul) | Sharpe net, MaxDD, pire jour, point mort, capacité. Funding HL réel par fenêtre de 24 h (API `fundingHistory`, proxy funding Binance USD-M avant HL, rien avant 2020 : signalé) ; MBT : frais officiels, roll, base, horaires, lot de 0,1 BTC sur 12 000 € |
| G1 | RESEARCH_PASS par véhicule | Sharpe net > 0,7, MaxDD meilleur que −25 %, WF (5 plis expansifs, part des plis > 0) > 50 % |
| L38 | Régression sur BTC buy-and-hold vol-targeté | R² > 30 % ⇒ timing de beta |
| A1 | Corrélation avec Strategy A (TSMOM BTC/ETH/SOL, tanh long-only, signal.py) | rapportée ; admission de livre seulement si `_meta/current_focus.md` montre un livre perso réellement financé, sinon sleeve seule |
| P1 | Puissance | effet minimum détectable (Sharpe) à 80 % de puissance, α 5 %, pour holdout et forward |

Statistiques : Sharpe √365 sur série quotidienne avec zéros ; t HAC lag 6 ; IC95 par bootstrap stationnaire
(blocs moyens 10 j, 2 000 tirages) ; skew, MaxDD, pire jour ; Šidák sur la famille S1 (3 horizons).

## Verdict
- **TIENT** si R1 reproduit (ou écart expliqué sans effet sur le signe), C3 deux jambes > 0, S1 estimation
  retenue ≥ 0,7 brut, et au moins un véhicule passe G1 en net.
- **FRAGILE** si TIENT mais C1 ou C2 lève son drapeau.
- **NE TIENT PAS** sinon.

Aucune modification de la spec après lecture des résultats : toute variante est rapportée comme diagnostic et comptée.
