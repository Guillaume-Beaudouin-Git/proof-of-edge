# S2 — Test de rupture : pas de rupture significative, l'archive reste

**2026-10-18.** Lecture unique par `code/s2_rupture.py`, selon `PREREG_RUPTURE.md` (commit
`b0e401da`, avant la lecture ; essai à blanc sur prix synthétiques, les deux branches exercées).
Sorties : `out/s2_rupture.{txt,json}`.

## 1. Résultat

| série | n | rupture estimée | avant | après | sup\|t\| | seuil 95 % (bootstrap) | p |
|---|---:|---|---:|---:|---:|---:|---:|
| **D, brut par événement (décisive)** | 462 | 2016-01-29 | +2,23 bps | +6,51 bps | 2,74 | 3,43 | **0,178** |
| contraste mensuel D − AUTRES (rapporté) | 233 mois | 2015-07-01 | −2,70 | +3,93 | 3,58 | — | 0,058 |

- **Le balayage retrouve la date vue à l'œil** (début 2016).
- **Mais cette date n'est pas significative**, une fois corrigé le fait qu'on cherche la meilleure
  date. Un saut de cette taille apparaît dans 18 % des séries sans rupture.
- **Décision pré-enregistrée : l'archive reste.** La porte de coût et l'admission n'étaient
  examinées que si la rupture était significative ; elles ne l'ont donc pas été.

## 2. Lecture

- **Le contraste est plus net que le niveau.** Depuis mi-2015, les jours dosés battent les autres
  gotobi de ~4 bps, alors qu'ils faisaient moins bien avant. Avec p 0,058, ce n'est pas assez :
  - le contraste n'est pas la série décisive ;
  - il reste au-dessus de 0,05 ;
  - le test a été décidé après avoir vu le motif, ce que le bootstrap ne corrige pas.
- **Ce qu'on peut en dire honnêtement.** Le gotobi dosé a probablement changé de régime vers
  2015-2016, mais 20 ans de données ne permettent pas de l'affirmer au seuil requis.
- **Quand rouvrir.** À la prochaine arrivée naturelle de données neuves : le prochain export FTMO,
  ou la mise à jour de `deep_history_utc`. Ce serait alors une lecture sur des données jamais vues,
  sans rien faire tourner sur le VPS d'ici là.

## 3. Comptes

1 essai : compteur local du programme `orb_replacement` 37 → 38. L'admission n'a pas été atteinte.
