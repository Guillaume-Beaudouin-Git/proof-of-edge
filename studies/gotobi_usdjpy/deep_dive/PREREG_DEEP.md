# S2 — Revue indépendante : pré-enregistrement

**2026-10-19. Écrit et commité avant tout calcul de ce dossier** (`deep_dive/`). Demande de
l'utilisateur : décider LANCER ou ARCHIVER avec les données existantes, sans ombre papier.

## 1. Ce qui est déjà lu, ce qui est neuf

- **Déjà lu (rendements).** USDJPY M1 2007-01 → 2026-05 : découverte, holdout, historique,
  rupture. Tout calcul sur cette période est descriptif ou d'estimation.
  - Il n'est pas aveugle : les moyennes par pli et par année sont publiées dans `../RAPPORT*.md`
    et `../out/s2_historique.txt`.
- **Neuf.** Les prix bid/ask des journaux de l'EA (`data/raw/ftmo_ea_spread_logs/`,
  2026-08-17 → 2026-10-18).
  - Leur colonne de fourchette a déjà servi au coût de 1,87 bp (jusqu'au 2026-10-12).
  - Leurs prix n'ont jamais servi à un rendement gotobi.
- **Calendrier économique** (`economic_calendar_2018_2026_full.csv`) : dates et heures d'annonce
  seulement, aucun rendement.

## 2. Analyses descriptives (aucune décision ; compteur inchangé)

Sur les événements gotobi 2007-01 → 2026-05, règle gelée (`../PREREG.md` §3), avec le code de
`../code/s2_validation.py` :

1. **Coût** : net par événement de D à 1,87, 2,5 et 3,0 bps, par période (2007-15, 2016-24 S1,
   holdout, tout) ; $/an à 2,5× l'équité.
2. **Jambes** de D par pli et sur le holdout.
3. **Stop** : D avec et sans stop ; stops touchés par jambe ; P&L des jambes stoppées.
4. **Distribution** de D : quantiles, asymétrie, kurtosis, part du P&L des 10 % meilleurs
   événements, les 10 pires.
5. **Interventions du MoF** (dates publiques 2010-2024) à ±1 jour ouvré d'un événement D.
6. **Fériés japonais** parmi les événements D (calendrier de `f6f_jp_holiday.py`, étendu à
   2025-2026 comme dans `../code/s2_holdout.py`).
7. **Jour de semaine** de D, sur tout l'échantillon et depuis 2016.
8. **2026 S1** : les 10 événements, jambe par jambe.
9. **Années perdantes**, comptées sur l'historique.
10. **Annonces** : moyenne de D les jours exclus par la règle du §5 (L4), rapportée sans décider.

Rien dans ces tableaux ne choisit un paramètre.

## 3. Estimation prospective (non aveugle)

- **Méta-analyse à effets aléatoires** (DerSimonian-Laird) sur 7 périodes : les 6 plis de 3 ans
  de `../PREREG_VALIDATION.md` et le holdout.
  - Erreur-type de chaque période : HAC lag 6.
  - Faite pour D, AUTRES, G1 (tous les gotobi) et le contraste D − AUTRES.
- **Décote de sélection** h = 0,5 bp sur les plis de découverte.
  - Raison : les heures et le stop de G1 y ont été choisis parmi 35 configurations.
  - Elle reste modeste, car les 21 fenêtres voisines sont toutes positives.
  - Sensibilité : h = 0 et h = 1,0.
- **Net prospectif** = μ_RE − coût. **Loi prédictive** d'une nouvelle période :
  N(μ_RE, SE_RE² + τ²).
- **Trois scénarios, fixés ici :**
  - **érosion** : D vaut le G1 du holdout (2,38 bps), sans dose ;
  - **central** : μ_RE de D, décote comprise ;
  - **régime récent** : moyenne de D de 2016-01 à 2026-05, moins h.
- **Pour chacun**, au coût 1,87, 2,5 et 3,0 bps :
  - net par événement ;
  - $/an, avec 24 événements à 2,5× l'équité (24 785 $) ;
  - P(année perdante) et P(perte sur 2 ans), par bootstrap par blocs : blocs de 6 événements,
    20 000 tirages, sur les nets de D recentrés sur le scénario.

## 4. Donnée neuve : journaux de l'EA (descriptif ; ~4 événements D)

- **Horloge.** `ts_server` = UTC + 3 h sur toute la fenêtre (heure d'été US). Un instantané à la
  seconde 0 de chaque minute.
- **Par événement gotobi** : 12 attendus, dont 4 dans D (25 et 31 août, 25 et 30 septembre).
  - Jambe A exécutable : achat à l'ask de 23:00, vente au bid de 00:54.
  - Jambe B exécutable : vente au bid de 00:56, rachat à l'ask de 02:00.
  - Stop de 25 bps vérifié sur les instantanés de minute (bid pour A, ask pour B). C'est une
    approximation.
  - Rapportés aussi : le brut au mid ; le brut au bid, la convention de la série historique ; le
    coût réalisé, soit le brut au mid moins l'exécutable, plus 1,0 bp de commission.
- **Alarme pré-écrite, qui ne peut que bloquer :**
  - coût réalisé médian (fourchette + commission) > 2,5 bps par événement sur les 12 événements ;
  - ou une des 4 minutes absente pour plus de 2 événements.
- **Sinon, lecture purement descriptive.** Quatre événements ne confirment ni ne réfutent rien :
  leur erreur-type est d'environ 10 bps.

## 5. Règle de décision (1 essai, compteur local 38 → 39)

**LANCER** si les cinq critères tiennent. Sinon **ARCHIVER**, en nommant le critère manquant.

- **L1, espérance.** Net central (§3) ≥ 1,5 bp par événement au coût de 1,87 bp, et P(net > 0)
  ≥ 0,80 sous la loi prédictive.
- **L2, stress de coût.** Net central ≥ 0 au coût de 2,5 bps.
- **L3, érosion bornée.** Dans le scénario érosion au coût de 2,5 bps, la perte attendue ne
  dépasse pas 60 $/an.
- **L4, annonces.** La règle d'exclusion retire au plus 20 % des événements D de 2018-2026.
  - *Règle d'exclusion*, fixée ici sur sa seule logique, avant tout rendement : sauter
    l'événement si une annonce d'impact HIGH en JPY ou en USD est prévue entre 22:58 UTC la
    veille et 02:02 UTC le jour J.
  - Raison : sur le funded Standard, ouvrir ou fermer à ±2 min d'une annonce restreinte, stop
    compris, est interdit (`PropFirms/ftmo/rules.md`, section News trading). Le relevé local est
    une rupture immédiate ; une source tierce parle d'annulation du trade. Je retiens le cas le
    plus grave.
- **L5, donnée neuve.** Pas d'alarme au §4.

**Ce que ces seuils ne sont pas.**
- Ils sont fixés après lecture des rapports, donc pas à l'aveugle, sauf L4 et L5.
- Ils remplacent la porte 3× du programme par un critère d'espérance, avec un stress de coût et
  une règle d'arrêt live. C'est un choix de méthode, que je défends dans `DECISION.md`.
- **Si l'on tient la porte 3× pour liante, le verdict est ARCHIVER quoi qu'il arrive** : brut de
  long terme 4,5 bps contre 5,61 requis.

## 6. Interdit après lecture

Changer la règle de trade, le calendrier, la taille, les scénarios, les seuils ou la règle
d'exclusion.
