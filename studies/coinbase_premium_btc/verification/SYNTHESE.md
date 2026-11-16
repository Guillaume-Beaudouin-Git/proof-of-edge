# SYNTHÈSE — C9 h24 après vérification locale et relecture adversariale (2026-10-30)

À lire en premier. Détail des constats dans `REVUE.md` ; le dossier du chercheur est `NOTE.md` (non modifié). En cas de
désaccord entre les deux, `REVUE.md` et ce fichier prévalent.

## Réponse directe
**C9 h24 est réelle et reproduite, mais plus petite et plus épisodique que ne le laisse lire le holdout.** Reconstruite
deux fois en local avec deux codes indépendants (le chercheur, puis moi), elle donne Sharpe brut IS 1,61 et holdout 1,85
(cloud 1,57 / 1,88). Une fois corrigé le fait que 1,85 est le meilleur de trois horizons lus, le brut attendu est **≈ 1,1
(0,8-1,4)**. Sur le seul véhicule qui tient la taille d'un compte de 12 000 €, le perp BTC Hyperliquid, le net attendu en
taker est **≈ 0,75 (0,5-1,0)** : au bord du RESEARCH_PASS (> 0,7), pas confortablement dedans. Le chercheur disait 0,87 ;
l'écart vient d'une décote de devise d'exécution qu'il n'a pas comptée (le perp USDC ne suit pas Binance USDT en stress).

**Recommandation : ne pas mettre d'argent maintenant ; lancer le forward papier opérationnel (3-6 mois) seulement si la
question réglementaire est tranchée d'abord, et accepter qu'il ne prouvera rien sur le Sharpe.** À 10 % de vol sur
12 000 €, l'enjeu est de l'ordre de 800 à 1 000 €/an pour un travail d'exploitation horaire 24/7 et une dépendance à une base
USDT/USD dont l'amplitude a déjà été divisée par dix depuis 2019.

## Ce qui est MESURÉ et ce qui est JUGÉ
| Constat | Statut | Chiffre |
|---|---|---|
| Reproduction h24 par un code indépendant | MESURÉ | IS 1,605 / HO 1,854 ; corrélation 0,99998 avec le chercheur, 0,982 avec le cloud ; 657 / 264 trades |
| PREREG commité avant données et calcul | MESURÉ | 14:51 → données 14:54-15:06 → sorties 15:05 ; deux déviations mineures (vol min_periods 600, « 5 plis » faits en 8) |
| Deux jambes positives (L25) | MESURÉ | IS long +93 bps (t 3,4), short +55 (t 2,3) ; HO long +62 (t 2,4), short +33 (t 1,6, non significatif seul) |
| Dix années positives | MESURÉ | min 2023 à 0,59 ; 2024-2026 : 2,08 / 1,80 / 1,77 |
| Entrée à l'open suivant au lieu du close du signal | MESURÉ | 1,595 / 1,854 : l'instant d'exécution n'est pas le moteur |
| Mêmes trades aux prix Coinbase USD | MESURÉ | IS 1,33 / HO 1,72 (−17 % / −8 % de brut par trade) |
| Concentration par trade | MESURÉ | ALL sans top 5 : 1,53 ; HO sans top 10 : 0,98 |
| Concentration par épisode (grappes < 7 j) | MESURÉ | HO : 5 épisodes sur 45 = 73 % du P&L, Sharpe sans eux 0,72 ; ALL : 10 sur 125 = 56 % |
| Inflation du « meilleur de 3 horizons » | MESURÉ | bootstrap joint : +0,75 sous l'hypothèse d'horizons équivalents |
| Erreur type du holdout | MESURÉ (correction) | 0,60 (bootstrap 0,54), pas 0,99 ; rétrécissement 1,22 au lieu de 1,13 |
| Šidák | MESURÉ | k = 3 : p 0,0053 ; k = 42 (module cloud) : holdout p 0,072, IS p 0,0036 |
| Funding HL par trade | MESURÉ | +0,67 bp en moyenne, p95 18 bps ; longs +6,0, shorts −3,2 |
| Point mort (funding inclus) | MESURÉ | 22 bps AR à Sharpe 1, 33 bps à 0,7, 57 bps à 0 ; −0,028 Sharpe par bp |
| Frais HL palier 0 / IBKR MBT / CME MBT | MESURÉ (sources du jour) | 4,5 / 1,5 bps par côté ; 0,85 $ ; 1,15 $ |
| CME 24/7 depuis le 29/05/2026 | NON CONFIRMÉ | sources secondaires seulement (site CME inaccessible) |
| Brut attendu hors échantillon | JUGÉ | ≈ 1,1 (0,8-1,4) |
| Net attendu perp HL taker / maker | JUGÉ | ≈ 0,75 (0,5-1,0) / ≈ 0,9 si les ordres limite sont remplis |
| Accès réglementaire (résident français, DEX ; futures crypto via IBKR Ireland) | NON TRANCHÉ | question à poser avant tout forward |

## Tableau par véhicule (série quotidienne avec zéros, √365, excès du cash ; historique 2017-09 → 2026-09)
| Véhicule | Coût AR | Net historique | Net holdout | MaxDD | Pire jour | Skew | Plis > 0 | Net attendu (JUGÉ) | Lecture |
|---|---|---|---|---|---|---|---|---|---|
| Brut, référence Binance | 0 | 1,67 | 1,85 | −7,0 % | −2,4 % | +5,1 | 8/8 | 1,1 | — |
| **Perp HL taker + funding** (prix Binance) | 9,3 bps + 0,7 | 1,37 | 1,48 | −9,1 % | −2,4 % | +5,0 | 8/8 | **≈ 0,8** | borne haute : le perp suit Binance |
| Perp HL taker, prix Coinbase USD | idem | 1,14 | 1,36 | −10,3 % | −2,5 % | +5,0 | 7/8 | ≈ 0,6 | borne basse : le perp suit l'USD en stress |
| Perp HL maker + funding | 3 bps + 0,7 | 1,54 | 1,69 | −7,8 % | −2,4 % | +5,1 | 8/8 | ≈ 0,9 | si 100 % remplis — non mesuré |
| MBT CME via IBKR, fractionnaire 24/7 | 5,9 bps + base | 1,50 | 1,66 | −7,9 % | −2,4 % | +5,0 | 8/8 | ≈ 0,9 | taille impossible : un lot = 57 % du compte |
| MBT 1 lot fixe, 12 k€ | idem | 1,47 | 1,35 | **−23,4 %** | **−8,2 %** | +3,4 | 8/8 | ≈ 0,8 à 23 % de vol | 2,4× la taille cible, L57 |
| MBT arrondi au lot | idem | — | — | — | — | — | — | inutilisable | 0 % des trades récents atteignent un lot |
| Nano BIT 0,01 BTC (Coinbase Derivatives via IBKR) | ≈ 11 bps + base | 1,35 | 1,44 | −9,1 % | −2,7 % | +4,5 | 8/8 | ≈ 0,7 | accès IBKR Ireland non confirmé |
| Spot long seul Binance | 20 bps | 1,13 | 1,19 | −5,5 % | −2,2 % | +5,7 | 7/8 | ≈ 0,6 | une jambe sur deux |
| Spot long seul Coinbase UE taker | 100 bps | −0,53 | −0,73 | −29 % | — | — | 3/8 | mort | — |

Les lignes MBT, nano et spot sont celles du chercheur (`out/vehicles.csv`), relues et cohérentes avec ma pente de coût ;
les lignes perp HL sont refaites (`revue/out/vehicules_revue.csv`). Le net attendu = brut attendu 1,1 moins la traînée
mesurée du véhicule, moins 0,05-0,2 de devise pour le perp HL.

## Ce que la relecture change par rapport à NOTE.md
1. **Net attendu HL taker 0,87 → ≈ 0,75.** Le perp HL est margé en USDC ; mesuré sur Coinbase USD, le même signal perd
   0,23 de Sharpe sur l'historique et 0,13 au holdout. La vérité est entre les deux bornes ; le chercheur n'a gardé que la
   haute. Cela place le véhicule au bord du seuil 0,7, avec une erreur type de 0,5.
2. **Le drapeau FRAGILE du PREREG était mal calibré.** Par trade, rien ne se lève. Par épisode, le holdout tient à 5 grappes
   (28 % des trades, 73 % du P&L) et vaut 0,72 sans elles. C9 est une collection d'épisodes : ~10 à 15 épisodes par an, dont
   3 à 5 paient. Conséquence pratique : un forward de 3-6 mois plat ne dit rien, et une année 2023 (0,59) est une année
   sans épisode, pas une année de pertes.
3. **Une erreur de calcul sans conséquence** : l'erreur type du holdout (0,99) mélangeait Sharpe annuel et formule
   quotidienne ; la bonne valeur est 0,60. Le rétrécissement devient 1,22 au lieu de 1,13 ; le 1,15 retenu reste dans la
   fourchette, et l'inflation du meilleur-de-trois mesurée (0,75) ramène aussi vers 1,1.
4. **Multiplicité réelle** : sur la famille de 42 configurations du module cloud, la confirmation holdout seule a p 0,072 ;
   c'est l'IS (p 0,0036 après Šidák 42) plus le holdout qui, ensemble, rendent l'effet crédible. À dire ainsi.
5. **Fragilité de spec** : une vol glissante qui ne tolère pas les heures Binance manquantes (104 en 2018) efface quatre
   années de signaux (IS 1,09 au lieu de 1,61). La version live doit traiter les trous comme le backtest.
6. Mineur : le short sur HL paie le cash (collatéral USDC non rémunéré), −0,02 à −0,05 ; `min_periods=600` sur la vol là
   où le PREREG dit 720 ; le « WF » de G1 est un tableau de sous-périodes (rien n'est estimé).

## Recommandations
1. **Ne pas déployer en argent réel sur ces chiffres.** Le Sharpe net attendu (≈ 0,75) est égal au seuil, à ± 0,5 près ;
   le véhicule est un DEX non régulé ; l'enjeu annuel (≈ 800-1 000 €) ne rémunère pas le risque opérationnel et juridique
   tant que la question réglementaire n'est pas tranchée.
2. **Trancher d'abord l'accès** (résident français : perp sur DEX ; futures crypto CME/Coinbase via IBKR Ireland). Si la
   réponse est « IBKR seulement », le dossier est clos pour ce compte : le MBT impose 2,4× la taille cible (L57) et le nano
   n'est pas confirmé.
3. **Si l'accès HL est acceptable** : forward papier selon `FORWARD_SPEC.md`, avec deux ajouts : (a) journaliser le prix HL
   contre Binance ET Coinbase à chaque entrée/sortie pour mesurer où le perp se place (c'est la variable qui sépare 0,6 de
   0,8) ; (b) compter les épisodes, pas les trades : au moins 3 épisodes payants ou 6 mois avant toute lecture. Le forward
   ne valide pas le Sharpe (MDE 3,5 à 6 mois) ; il valide le signal, le coût et la devise.
4. **Maker plutôt que taker** si le forward est lancé : +0,15 de Sharpe à la clé, à condition de mesurer le taux de
   remplissage (un ordre limite au mid sur un signal de continuation est souvent non rempli dans le bon cas).
5. **Surveiller l'amplitude de la prime** : écart-type 4,7 bps en 2025, 5,9 en 2026, contre 35-55 en 2017-2019 ; le
   critère d'arrêt (< 3 bps sur 30 j) est à 1,7 bp du niveau actuel. La base USDT/USD peut se refermer sans bruit.
6. **Ne pas « améliorer »** : la bande |z| ∈ [1 ; 2) rapporte +29 bps/trade au holdout (t 2,8) et le seuil 2 n'a rien de
   spécial ; toute variante lue sur le holdout maintenant est de la sélection a posteriori. Si une variante est voulue,
   PREREG d'abord, forward ensuite.

## Décisions qui reviennent à Guillaume
1. Accepter ou non un véhicule DEX non régulé pour le livre perso (question juridique et fiscale, hors recherche).
2. Lancer le forward papier HL (coût : une machine qui calcule chaque heure, 3-6 mois, sans preuve de Sharpe à l'arrivée)
   ou classer C9 « réelle, trop petite pour ce compte ».
3. Si forward : taker (≈ 0,75 attendu) ou maker avec mesure du remplissage (≈ 0,9 si rempli).
4. Réconcilier les compteurs : chercheur 132 + relecture 117 = 249 statistiques locales, aucune nouvelle configuration de
   signal ; module cloud 1 = 42 configurations ; registre global 321 figé.
5. Leçons candidates à graver (nommées, non numérotées) : « une vol glissante doit tolérer les trous de la venue source »
   ; « le drapeau de concentration se lit par épisode, pas par trade, quand les signaux persistent » ; « la devise de
   marge du véhicule est un paramètre du backtest ».

## Décisions de Guillaume (30/10/2026)
- **Véhicule : Hyperliquid.** « Je préfère Hyperliquid à Kraken personnellement, si la différence est minime alors go
  sur Hyperliquid (j'ai déjà un compte dessus en plus). » Le choix ne coûte rien de mesurable : sur les mêmes trades
  2022-04 → 2026-10, Kraken au prix réel du perp fait 1,16 net taker contre 1,26 (HL au prix Binance) / 1,13 (HL au prix
  Coinbase), un écart dans le bruit (MESURÉ). L'alternative régulée (Kraken UE `PF_XBTUSD`, accès « non exclu, à
  confirmer à l'ouverture du compte ») reste documentée dans `VEHICULES_FR.md` et `REVUE_VEHICULES.md`.
- **Forward papier : approuvé** (« Oui on pourra lancer en papier »), sur Hyperliquid, selon `FORWARD_SPEC.md`, avec
  les prix Binance et Coinbase journalisés en parallèle comme la spec le demande déjà. Rien n'est installé : installation
  sur le VPS seulement après le déploiement de l'EA v2.14, et avec l'accord explicite de Guillaume.
- **Argent réel : non décidé.** Pas avant la fin du forward, ni avant que les points fiscaux et juridiques de
  `REVUE_VEHICULES.md` §5 aient été vérifiés avec un professionnel.

## Fichiers
- `REVUE.md` : constats détaillés et corrections ; `revue/revue_c9.py` : code indépendant ; `revue/out/` : sorties
  (`repro.csv`, `variantes_prix.csv`, `dose_reponse_h24.csv`, `concentration_episodes.csv`, `selection_horizon.json`,
  `wf_horizon.csv`, `jambes_h24.csv`, `vehicules_revue.csv`, `revue_summary.json`, `daily_h24_revue.csv`) ;
  `revue/n_tests.json` : 117 statistiques de relecture.
- Chercheur : `NOTE.md`, `PREREG.md`, `FORWARD_SPEC.md`, `n_tests.json` (132), `code/`, `out/`.
- Rien n'a été installé, déployé ni poussé ; aucune donnée personnelle envoyée ; caches de données hors git.
