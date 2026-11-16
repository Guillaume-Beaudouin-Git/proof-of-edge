# S2 — Gotobi USDJPY dosé par le calendrier des règlements : pré-enregistrement

**2026-10-18. Écrit et commité avant tout lancement du script.** Personne n'a lu de rendement
gotobi postérieur au 2024-06-30 (`alpha_hunt_2026-10/synthese/out/holdout_check.txt`) ; moi non
plus. Le holdout est lu **une seule fois**, par `code/s2_holdout.py`. Cette même lecture rapporte
aussi les statistiques gelées de PR-C (§7), pour que personne n'ait à le relire.

## 1. Origine et contraintes

- **Idée.** CMB-05 (`../ideation/COMBINAISONS.md`), retenue en S2 dans
  `../ideation/SHORTLIST_IDEATION.md`.
- **Parent.** G1 / FL-F6, le gotobi USDJPY.
  - Découverte 2007-01 → 2024-06 : brut **4,05 bps** par événement (deux jambes, stop 25 bps),
    t HAC **6,87**, 1 257 événements (`alpha_hunt_2026-10/flows/RAPPORT.md` §3.6).
  - Coût FTMO mesuré : **1,87 bp** par événement, deux allers-retours, commission comprise
    (`alpha_hunt_2026-10/SYNTHESE.md`, ligne « Gotobi USDJPY », commit `2c029649`).
  - Ratio brut/coût **2,2×**, sous la porte 3× : mort au coût, donc rouvrable avec un angle neuf.
- **Pourquoi le holdout seulement.** PR-C (`alpha_hunt_2026-10/PREREG_phase3.md`, commit
  `db9a4d73`) interdit de tester une variante de calendrier sur la découverte. Et la découverte a
  déjà publié la fin de mois : −0,5, puis 2,5, puis 9,8 bps par période.
- **Décision de l'utilisateur, 2026-10-18 :** lancer sur le holdout malgré la puissance limitée
  (§6).

## 2. Hypothèse

Les règlements commerciaux japonais se concentrent sur deux dates :
- le **25** (paie, fournisseurs) ;
- le **dernier jour ouvré du mois**.

Si le gotobi est un flux de règlement, l'effet par événement doit être plus fort ces jours-là que
les autres gotobi (5, 10, 15, 20), et assez fort pour franchir la porte de coût.

## 3. Règle de trade (celle de PR-C, inchangée)

- **Calendrier.** `gotobi_days`, copie fidèle de `flows/code/f6_gotobi.py` :
  - le dernier jour ouvré (lundi-vendredi présent dans la donnée) ≤ 5, 10, 15, 20 et 25 ;
  - plus le dernier jour ouvré du mois ;
  - fériés japonais non retirés.
- **Jambe A.** Achat à l'ouverture de 23:00 UTC la veille, sortie à l'ouverture de 00:54 UTC.
- **Jambe B.** Vente à l'ouverture de 00:56 UTC, rachat à l'ouverture de 02:00 UTC.
- **Stop dur** à 25 bps du prix d'entrée, sur chaque jambe. Il est rempli au niveau du stop, ou à
  l'ouverture de la barre si elle s'ouvre au-delà (`flows/code/f6d_gotobi_stop.py::leg`, copié
  tel quel).
- **Événement écarté** si une jambe couvre moins de 80 % de ses minutes.
- **Mesure.** Brut par événement = jambe A + jambe B, en bps, même notionnel sur les deux jambes.

## 4. Partition, fixée ici avant lecture

- **DME** : le dernier jour ouvré du mois.
- **D25** : le jour retenu pour l'ancre 25.
- **AUTRES** : les jours retenus pour les ancres 5, 10, 15 et 20.
- **D = D25 ∪ DME.**

En cas de coïncidence de deux ancres sur un même jour (trou de données), la catégorie la plus dosée
l'emporte : DME, puis D25, puis AUTRES.

## 5. Données et fenêtre

- **Source.** `data/deep_history_utc/USDJPY_M1.csv` (vrai UTC), en lecture seule.
- **Holdout.** Événements datés du 2024-07-01 au 2026-05-31.
  - La donnée s'arrête le 2026-06-05. Juin 2026 est exclu, car `gotobi_days` y prendrait le
    2026-06-05 pour une fin de mois.
  - Les jours de juin restent disponibles comme voisins pour les placebos décalés.
- **Contrôle d'implémentation, avant de lire le holdout.**
  - Sur la découverte (< 2024-07-01), le script calcule le seul agrégat G1 publié, sans aucune
    partition.
  - Il doit retrouver 4,05 bps et t 6,87, à 0,01 près.
  - Sinon, il s'arrête sans lire le holdout.

## 6. Décision S2 — 1 essai, compteur local du programme 30 → 31

Porte de coût : **3 × 1,87 = 5,61 bps par événement**.

| règle | condition | verdict |
|---|---|---|
| K1 | moyenne de D < 5,61 bps | **TUÉE** |
| K2 | moyenne de D ≤ moyenne de AUTRES (pas de dose) | **TUÉE** |
| K3 | une des deux jambes a une moyenne négative sur D | **TUÉE** |
| — | aucune des trois | **NON TUÉE** |

- **NON TUÉE n'est pas une confirmation.** La suite serait une ombre papier d'au moins 12 mois
  (~24 événements par an), puis l'admission funded.
- **Puissance.**
  - ~46 événements dans D ; σ ≈ 20,7 bps (PR-C) ; erreur-type ≈ 3,1 bps.
  - P(tuée par K1) ≈ 0,96 si l'effet vrai est nul.
  - P(tuée par K1) ≈ 0,70 s'il vaut 4,05 bps, c'est-à-dire sans dose.
  - P(tuée par K1) ≈ 0,08 s'il vaut 10 bps.
- **À rapporter, sans décider :**
  - le t HAC6 de D et le MDE80 ;
  - D25 et DME séparément ;
  - le détail par année (2024 S2, 2025, 2026 S1) ;
  - les 8 calendriers D décalés de ±1 à ±4 jours, jours gotobi vrais exclus, avec le contrôle L58
    (moyenne du pool contre l'espérance inconditionnelle de la forme de trade) ;
  - le pire événement, en bps et à 2,5× l'équité ;
  - la part de barres à fourchette nulle entre 23:00 et 02:00 UTC (L60).

## 7. Statistiques gelées de PR-C, rapportées dans la même lecture

Telles que `PREREG_phase3.md` les définit, sur tous les événements gotobi du holdout.

- **Règles de mort :**
  - K1 : brut moyen ≤ 0 ;
  - K2 : les deux jambes de moyenne négative ;
  - K3 : le vrai calendrier sous la médiane des 8 calendriers décalés de ±1 à ±4 jours (mêmes
    reports, construction de `flows/code/f6b_gotobi_robust.py`, jours gotobi vrais exclus), avec
    le contrôle L58.
- **SURVIE.** Brut ≥ 2,0, aucune jambe < 0, et vrai calendrier dans le tiers supérieur, soit au
  rang 3 sur 9 au plus.
- **CONFIRMATION.** t HAC ≥ 2,0.
- **À rapporter sans décider :**
  - les fériés japonais, avec le calendrier manuel de `f6f_jp_holiday.py` étendu à 2025-2026
    (équinoxes : 20 mars, 23 septembre) ;
  - les fins de mois (= DME) ;
  - la part de la minute du fixing : fenêtres 23:00 → 00:55 / 00:55 → 02:00 sans stop, contre
    G1 sans stop ;
  - le pire événement.
- **Hors verdict.** G1 reste sous la porte de coût (2,2×). Ces chiffres ne changent pas le verdict
  de S2 et n'entrent pas dans le compteur de ce programme. Ils relèvent de PR-C.

## 8. Interdit après lecture

Changer la partition, les heures, le stop, la fenêtre, la porte de coût ou les seuils. Toute
variante est une nouvelle hypothèse, à tester sur de nouvelles données (forward).
