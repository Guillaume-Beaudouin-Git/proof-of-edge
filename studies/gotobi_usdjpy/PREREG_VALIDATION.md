# S2 — Validation : la dose sur la découverte (walk-forward) et l'admission au funded

**2026-10-18. Écrit et commité avant tout lancement du script sur les vrais prix.**

**Accord de l'utilisateur, 2026-10-18.** La règle de PR-C, qui interdit de tester une variante de
calendrier sur la découverte, est levée pour cette seule lecture. La décision qui suit est binaire :
lancer ou archiver. Il n'y a pas d'ombre papier.

## 1. Pourquoi cette lecture est légitime maintenant

- **La variante ne peut plus être choisie.** D (le 25 + la fin de mois) est gelée depuis le commit
  `1935996d`. Elle a passé son test sur le holdout (NON TUÉE, +6,19 bps, `RAPPORT.md`). Lire la
  découverte peut seulement la confirmer ou la tuer.
- **La règle dure exige un walk-forward d'au moins 5 plis.** Le holdout seul n'en donne qu'un.
- **Biais connus, rapportés avec le résultat :**
  - les heures et le stop de G1 ont été choisis sur cette découverte, parmi 35 configurations.
    Le niveau y est donc optimiste, pour D comme pour AUTRES ; le contraste entre les deux reste
    juste ;
  - la fin de mois y a été publiée par période (−0,5 / 2,5 / 9,8 bps). Le 25 ne l'a jamais été.

## 2. Étape 1 — la dose sur la découverte (1 essai, compteur local 32 → 33)

- **Données et règles.** Règle de trade, calendrier et partition identiques à `PREREG.md` §3-4.
  Découverte : 2007-01 → 2024-06-28, la fenêtre de G1.
- **Contrôle.** Le script doit retrouver G1 sur la découverte (4,05 bps) et D sur le holdout
  (+6,19 bps), à 0,01 près. Sinon il s'arrête.
- **Plis.** Les 6 plis de 3 ans de `flows/code/f6g_gotobi_checks.py` : 2007-09, 2010-12, 2013-15,
  2016-18, 2019-21, 2022-24 S1.
- **Statistiques.**
  - Contraste : régression du brut par événement sur une indicatrice de D, avec un t HAC6 sur la
    suite chronologique des événements.
  - Moyenne poolée de D.
  - Par pli : moyenne de D et moyenne de AUTRES.
- **Validé si les trois tiennent :**
  - **V1** : contraste > 0 avec t ≥ 2 ;
  - **V2** : D > AUTRES dans au moins 5 plis sur 6 ;
  - **V3** : moyenne de D sur la découverte ≥ 5,61 bps, la même porte que K1 (3 × 1,87).
- **À rapporter :** D25 et DME séparément, les deux jambes, le détail par pli.

## 3. Étape 2 — admission au livre funded (1 essai, compteur local 33 → 34)

- **Base.** « Livre complet − ORB seul » (`book_review_2026-10/out/sleeves_daily_pnl.csv`, commit
  `e0151e91`), soit le funded après la pause de l'ORB, comme pour P2.
- **Sleeve.**
  - Les événements D de la découverte et du holdout, nets de 1,87 bp.
  - Notionnel : **2,5 × 9 914 $**, la taille fixée par la pire séance (`PREREG.md` §6).
  - Chaque P&L est daté du jour du fixing. C'est le jour FTMO qui contient la fenêtre 23:00-02:00
    UTC.
- **Fenêtre.** 2013-10-01 → 2026-05-29, le recouvrement des deux séries. Les jours sans événement
  valent 0. L'index est l'union des dates des deux séries.
- **Méthode.** Celle de `p2_funded/code/admission.py`, fonctions importées telles quelles :
  - ΔSR par bootstrap par blocs de 20 jours (5 000 tirages) ;
  - P(perte du compte sur 504 séances), par bootstrap par blocs (10 000 chemins, plancher 9 000 $,
    perte journalière 500 $, retraits tous les 14 jours au-dessus de 10 000 $). Ce calcul est fait
    sans gouverneur : c'est une borne haute ;
  - pire séance de la sleeve.
- **Taille décisive : le notionnel déployable (2,5×), pas l'ERC.**
  - Pour une sleeve active ~24 jours par an, l'ERC donnerait ~11× l'équité. Sa pire séance
    dépasserait alors le plafond d'environ 4 fois, ce qui la rend infaisable ; c'est ce qui a tué
    P2.
  - L'ERC est rapporté à titre indicatif.
- **Verdict, avec la règle de P2 :**
  - REJET si ΔSR ≤ 0, si P(perte) monte de plus de 1 point, ou si la pire séance de la sleeve
    dépasse 149 $ ;
  - ADMIS si p(ΔSR ≤ 0) < 0,05 ;
  - UNDERPOWERED sinon.
- **À rapporter :** corrélations avec chaque colonne du livre (J1 compris), pire jour combiné,
  admission sur le holdout seul (2024-07 → 2026-05).

## 4. Décision finale

- **LANCER** si V1, V2 et V3 tiennent et si l'admission rend ADMIS. Deux points restent alors à
  régler avant le premier trade :
  - la règle FTMO sur les annonces : le Tankan (23:50 UTC) et le CPI japonais (23:30 UTC) tombent
    dans la jambe d'achat ;
  - le module EA.
- **ARCHIVER** sinon, en nommant le critère qui manque.

## 5. Interdit après lecture

Changer la partition, les plis, la taille, les seuils ou la méthode.
