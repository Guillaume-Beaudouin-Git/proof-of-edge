# FBL-10b — L'envers de FBL-10 : Hong Kong monte pendant les fêtes continentales et baisse à la réouverture. Réplication avant Stock Connect : pré-enregistrement

**2026-10-19, vers 13:55. Écrit et commité avant tout calcul de rendement sur la période 1997-2014.** Hypothèse neuve,
née de la lecture de FBL-10 (`RAPPORT.md`, commit `99ffd8b1`).

## 1. Origine

- **Ce que FBL-10 a trouvé**, du 2014-11 au 2026-10, sur ^HSI de l'ouverture à la clôture, en écart aux jours ordinaires :
  - les jours où Hong Kong cote et Shanghai non : **+27,7 bps** (n 125, t 2,51) ;
  - les jours de réouverture : **−36,6 bps** (n 55, t −2,75) ;
  - c'est l'inverse de FBL-10, et régulier : 10 années sur 12 pour chaque jambe.
- **Ce n'est qu'une observation post hoc**, le miroir d'une hypothèse réfutée. Elle ne se trade pas sans réplication
  indépendante.
- **La réplication possible.** Avant le 17 novembre 2014, les fêtes continentales fermaient déjà Shanghai pendant que
  Hong Kong cotait, mais le canal sud n'existait pas.
  - Si l'envers existe aussi avant 2014, c'est un **effet de calendrier des fêtes**, indépendant du canal. Il est alors
    répliqué hors de la période qui l'a fait naître.
  - S'il est nul avant 2014, il est lié au canal, et seule la donnée future pourra le valider.

## 2. Données (jamais lues en rendement)

- ^HSI et 000001.SS, quotidiens Yahoo, du 1997-07-02 au 2014-11-14 (`code/fetch_pre.py`).
  - Avant 1994, les ouvertures de ^HSI sont figées (jusqu'à 45,6 % des jours). Depuis 1997, 0 %.
  - Shanghai commence chez Yahoo le 1997-07-02.
- **Calendrier**, même définition que FBL-10 :
  - **221 jours fermés**, 78 réouvertures et 3 988 jours ordinaires ;
  - jusqu'à 5 jours fermés isolés (mars, juillet, décembre) peuvent venir de trous de la série de Shanghai. Ils sont
    gardés : la règle ne se retouche pas après lecture.
- **Mesure.** r = clôture / ouverture − 1 de ^HSI, en bps, en écart à la moyenne des jours ordinaires de la même
  période.

## 3. Décision (1 essai pour la réplication ; puis 1 pour E4 si elle est atteinte ; compteur local 52 → 53 ou 54)

**Étape 1, réplication 1997-2014.** Les seuils sont ceux de la fiche, retournés. Les deux jambes sont exigées.

| | condition |
|---|---|
| **R1, jours fermés** | écart aux jours ordinaires **≥ +10 bps** |
| **R2, réouvertures** | écart aux jours ordinaires **≤ −15 bps** |

- **Si R1 ou R2 échoue : ARCHIVER, de puissance.** L'envers n'est pas répliqué hors de la période Stock Connect. On le
  rouvrira avec la donnée future, sans ombre.

**Étape 2, seulement si R1 et R2 tiennent : décision de lancement.**
- **Le trade.** Achat HK50 les jours fermés, vente les réouvertures, de l'ouverture à la clôture, à 3 000 $.
  - Stop à 2 %, approché par le plus haut ou le plus bas du jour (−2 %, plus le coût).
  - K0 = 4 bps supposé ; la fourchette de HK50.cash est à relever au terminal.
- **E3, espérance**, en net par trade.
  - Deux estimations sont combinées par l'inverse des variances :
    - 2014-2026, la période de découverte, corrigée du choix du sens après lecture (−0,564 erreur-type, l'espérance du
      maximum de deux tirages) ;
    - 1997-2014, sans correction.
  - L1 : net ≥ 1,5 bp et P(net > 0) ≥ 0,80. L2 : net au coût de stress (2 × K0) ≥ 0.
- **E1.** 5 plis chronologiques du P&L net, de 1997 à 2026 : > 0 dans au moins 4.
- **E4.** Admission funded, méthode de P2, base « Livre complet − ORB seul », fenêtre de la base (2013-10 → 2026-06), à
  3 000 $ : ADMIS.
- **LANCER** si E3, E1 et E4 tiennent, sous réserve du coût réel de HK50.cash. **ARCHIVER** sinon, de puissance.

**Rapporté, sans décider :**
- t HAC de chaque jambe ;
- les sous-périodes 1997-2007 (semaines d'or de 7 jours en mai) et 2008-2014 ;
- le détail par fête ;
- le détail par année.

## 4. Interdits

Après lecture, ne changer ni le calendrier, ni la mesure, ni les seuils, ni la correction, ni le coût, ni la taille.
