# S2 — Test de rupture : le gotobi dosé a-t-il changé de régime ? Pré-enregistrement

**2026-10-18. Écrit et commité avant le lancement du script sur les vrais prix.** Demandé par
l'utilisateur après l'historique annuel (`out/s2_historique.txt`).

## 1. Pourquoi, et ce qui a déjà été vu

- **Le motif est connu.** L'historique annuel montre un net de +0,53 bp par trade sur 2007-2015,
  puis de +4,48 bps sur 2016-2026, avec dix années positives de suite. Le découpage « 2016 » a été
  **lu dans ce tableau**.
- **Ce que corrige le test.** Le balayage de toutes les dates, avec un bootstrap sous l'hypothèse
  « pas de rupture », corrige le choix de la date (L64).
- **Ce qu'il ne corrige pas.** Le fait d'avoir décidé de tester après avoir vu le motif. C'est
  écrit ici, et ce sera rappelé avec le résultat.

## 2. Série et méthode

- **Série décisive : le brut par événement de D** (le 25 + fin de mois), dans l'ordre chronologique,
  de 2007-01 à 2026-05. Ce sont les mêmes 462 événements que la validation et l'historique (règle
  de trade de `PREREG.md` §3). C'est la série qu'on tradera.
- **Méthode : `break_scan` de `../overnight_hourly/code/analysis.py`, appelé tel quel.**
  - Rupture unique de la moyenne.
  - Balayage des dates entre 15 % et 85 % de l'échantillon.
  - |t| de la différence avant/après, avec HAC lag 6 de chaque côté.
  - p par bootstrap par blocs de 20 événements de la série démoyennée, 999 tirages : la
    distribution du sup|t| sous l'hypothèse « pas de rupture ».
- **Série rapportée, non décisive :** le contraste mensuel (moyenne des événements D du mois moins
  moyenne des AUTRES du mois), même méthode.

## 3. Décision

1. **Rupture significative** si p < 0,05. Sinon : **l'archive reste** (1 essai, compteur local
   37 → 38).
2. **Si elle l'est**, la date estimée τ̂ définit le régime récent. Il faut alors que la moyenne de D
   après τ̂ soit ≥ 5,61 bps, la porte de coût.
3. **Puis l'admission funded** sur la période après τ̂ (et jusqu'à la fin du livre), à 2,5×
   l'équité, avec la méthode et les fonctions de `PREREG_VALIDATION.md` §3 (1 essai de plus,
   compteur 38 → 39). Il faut ADMIS.
4. **LANCER** si 1, 2 et 3 tiennent ; **ARCHIVER** sinon, avec le critère qui manque.

**Biais déclarés.** La moyenne après τ̂ est surestimée, puisque le balayage choisit la date qui
maximise l'écart. L'admission sur cette période hérite de ce biais. Les deux sont rapportés avec la
moyenne d'avant τ̂.

## 4. Interdit après lecture

Changer la série, la méthode, le seuil, le balayage ou la taille.
