# S2 — Validation : ARCHIVÉE, la dose n'existe pas sur 17 ans

**2026-10-18.** Lecture unique par `code/s2_validation.py`, selon `PREREG_VALIDATION.md` (commit
`ea43ebe9`, avant le lancement ; essai à blanc sur prix synthétiques au préalable). Sorties :
`out/s2_validation.{txt,json}`.

**Contrôles réussis.** Le script retrouve G1 sur la découverte (4,050 bps) et D sur le holdout
(+6,195 bps).

## 1. Étape 1 — la dose sur la découverte (2007-01 → 2024-06)

| | n | brut (bps) | t HAC6 |
|---|---:|---:|---:|
| D (le 25 + fin de mois) | 418 | +4,33 | 5,10 |
| dont le 25 | 209 | +4,32 | — |
| dont la fin de mois | 209 | +4,34 | — |
| autres gotobi (5, 10, 15, 20) | 839 | +3,91 | 5,27 |
| **contraste D − AUTRES** | | **+0,42** | **0,37** |

D contre AUTRES, par pli de 3 ans (bps) :

| pli | 2007-09 | 2010-12 | 2013-15 | 2016-18 | 2019-21 | 2022-24 S1 |
|---|---:|---:|---:|---:|---:|---:|
| D | 3,22 | 3,08 | 0,91 | 6,11 | 5,45 | 7,85 |
| AUTRES | 3,76 | 7,67 | 2,28 | 3,57 | 3,76 | 2,10 |

- **V1 échoue** : le contraste vaut +0,42 bp, t 0,37.
- **V2 échoue** : D ne bat AUTRES que dans 3 plis sur 6.
- **V3 échoue** : D vaut 4,33 bps, sous la porte de 5,61. Et ce niveau est encore optimiste, puisque
  les heures du trade ont été choisies sur cette période.

## 2. Étape 2 — admission au funded (2013-10 → 2026-05, 301 événements, 2,5× l'équité)

| | verdict | ΔSR (p ≤ 0) | P(perte 2 ans), sans gouverneur | pire séance de la sleeve |
|---|---|---|---|---|
| **décisif, 2,5×** | **ADMIS** | +0,144 (0,000) | 53,4 % → 46,6 % | −129 $ |
| indicatif, ERC (13,4×) | REJET | +0,360 (0,038) | 52,5 % → 82,0 % | −688 $ |
| indicatif, holdout seul | UNDERPOWERED | +0,170 (0,076) | 80,5 % → 77,1 % | −107 $ |

- La sleeve seule a un Sharpe de 0,88. Sa corrélation avec chaque jambe du livre est ≤ 0,03 en
  valeur absolue.
- Pour le trader, le gain passe de 66 à 76 $/mois.

## 3. Décision : ARCHIVER (V1, V2 et V3 manquent)

**Pourquoi :**
1. **La dose n'existe pas.** Sur 17 ans, le 25 et la fin de mois rapportent autant que les autres
   gotobi (4,33 contre 3,91 bps). Le dosage était la seule raison de croire que S2 franchirait la
   porte de coût qui avait tué le gotobi. L'écart du holdout (6,19 contre 0,55) était donc très
   probablement du hasard.
2. **La marge sur le coût est trop mince.** Sur la longue période, le brut vaut 2,3 fois le coût
   (4,33 contre 1,87), là où le programme exige 3 fois. C'est la mort d'origine du gotobi (2,2×),
   qui revient telle quelle.
3. **Le gotobi s'affaiblit.** Tous jours confondus : 4,05 bps sur la découverte, 2,38 sur le
   holdout, soit 0,5 bp net. C'est l'érosion qu'annonce L23 pour les flux ancrés à un fixing.

**Ce que l'admission dit quand même, honnêtement :**
- L'effet gotobi est réel (t ≈ 5 sur 17 ans) et net-positif au coût mesuré.
- Au plafond de taille, il améliore le livre funded (ΔSR +0,14) sans toucher la barrière.
- La porte 3× est faite pour refuser précisément ce profil : un edge réel, mais une marge de coût
  qu'un élargissement de fourchette ou la poursuite de l'érosion suffisent à effacer.
- **Ce n'est pas une mort mécanique.** C'est une mort de coût. Elle est rouvrable sur un véhicule
  dont le coût par événement serait d'au plus ~1,4 bp ; aucun n'est connu aujourd'hui (le future
  JPY d'IBKR coûterait ~2,4 bps pour les deux allers-retours).

**Lecture descriptive, sans effet sur la décision.** D bat AUTRES dans les trois plis depuis 2016 et
sur le holdout. « La dose existe depuis 2016 » serait une nouvelle hypothèse, choisie après lecture.
Elle n'est pas retenue.

## 4. Comptes

2 essais : compteur local du programme `orb_replacement` 32 → 34.
