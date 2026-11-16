# S2 — Gotobi dosé (25 + fin de mois) : NON TUÉE, de justesse

**2026-10-18.** Lecture unique du holdout par `code/s2_holdout.py`, selon `PREREG.md` (commit
`1935996d`, avant le lancement). Le script a d'abord tourné à blanc sur des prix synthétiques.
Sorties : `out/s2_holdout.{txt,json}`, `out/s2_holdout_events.csv`.

## 1. Verdict

**Contrôle d'implémentation réussi.** Sur la découverte, le script retrouve le G1 publié :
1 257 événements, 4,050 bps, t 6,867.

**Holdout** : 2024-07-01 → 2026-05-29, 136 événements gotobi, dont 44 dans D.

| ensemble | n | brut (bps) | t HAC6 | pire (bps) |
|---|---:|---:|---:|---:|
| **D = le 25 + fin de mois** | 44 | **+6,19** | 2,52 | −41,4 |
| dont le 25 | 21 | +9,69 | 1,99 | −19,6 |
| dont la fin de mois | 23 | +3,00 | 1,20 | −41,4 |
| autres gotobi (5, 10, 15, 20) | 92 | +0,55 | 0,22 | −37,7 |

**Les trois règles de mort :**
- **K1** : 6,19 ≥ 5,61 (3 × 1,87). La porte passe, de 0,6 bp.
- **K2** : la dose va dans le sens prédit, D à +6,19 contre +0,55 pour les autres gotobi.
- **K3** : les deux jambes sont positives sur D, achat +0,77 et vente +5,43.

**S2 n'est pas tuée. Elle n'est pas confirmée pour autant.**
- La marge sur la porte (0,6 bp) est cinq fois plus petite que l'erreur-type (~2,9 bps). La
  probabilité que le vrai brut dépasse la porte est d'environ 0,6.
- Le MDE80 (8,2 bps) dépasse l'effet mesuré.
- Le t de 2,52 contre zéro reste sous le seuil Šidák du programme : t ≈ 3,15 pour 31 essais.

**Les contrôles vont dans le bon sens.**
- D arrive premier sur 9 calendriers décalés de ±1 à ±4 jours.
- Le pool des placebos (+0,85) est proche de l'inconditionnel (+1,08) : le contrôle L58 est bon.
- La part de barres à fourchette nulle entre 23:00 et 02:00 UTC est négligeable (0,1 à 0,7 %).

**Les fragilités, à garder en tête :**
- Presque tout vient de la vente après le fixing (+5,43). L'achat avant le fixing est presque
  nul (+0,77).
- C'est le 25 qui porte l'effet ; la fin de mois beaucoup moins. C'est l'inverse de la
  découverte, où la fin de mois montait à 9,8 bps en 2021-2024. Trader le 25 seul serait une
  nouvelle hypothèse, interdite sur ces données.
- Par année : 2024 S2 +7,84 (n 11), 2025 +8,51 (n 23), 2026 S1 **−0,93** (n 10).

## 2. En dollars, sur le compte funded

- **Net** ≈ 6,19 − 1,87 = 4,3 bps par événement. À 2,5× l'équité (~25 k$) et ~24 événements par
  an, cela fait **≈ 260 $/an avant partage**.
- C'est le chiffre du holdout, donc optimiste : une estimation qui franchit la porte de justesse
  est probablement surestimée (effet de sélection).
- **Pire événement à cette taille** : −103 $ au holdout, −132 $ avec le pire de la découverte
  (−53 bps). Les deux restent sous le plafond de 149 $.

## 3. PR-C (G1, tous les gotobi), rapporté hors verdict

- **Résultat.** 136 événements, +2,38 bps, t 1,29. Les deux jambes sont ≥ 0 et le vrai calendrier
  arrive premier sur 9.
- **Au sens de PR-C** : SURVIE, mais pas de CONFIRMATION (t < 2).
- **Toujours sous la porte de coût** : 1,3×.
- **Fériés japonais** : −4,02 bps (n 9) contre +2,83 les autres jours. C'est cette fois conforme
  au mécanisme, puisqu'il n'y a pas de fixing un jour férié. La découverte montrait l'inverse
  (+5,5, n 37).
- **Minute du fixing.** 00:54-00:56, exclue par G1, porte 40 % du brut sans stop (+4,30 avec, +2,59
  sans). Cette part n'est pas captable par la règle.

## 4. Suite

- **Ce que la pré-inscription prévoit** : une ombre papier d'au moins 12 mois (~24 événements),
  puis l'admission funded. Aucun déploiement avant.
- **Comment la tenir** : un calcul hors ligne chaque mois, sur l'export M1 USDJPY du terminal FTMO
  (gratuit), avec le même code et les mêmes règles. Rien ne change dans l'EA.
- **Ce qui est interdit** : changer la partition (« le 25 seul »), les heures ou le stop. Toute
  variante attend de nouvelles données.
- **Compteur local** du programme `orb_replacement` : 30 → 31.
