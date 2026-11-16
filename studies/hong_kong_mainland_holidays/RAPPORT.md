# FBL-10 — Hong Kong sans l'acheteur continental : ARCHIVER (mort mécanique, l'effet est à l'envers)

> **Revérifié le 2026-10-20 sur la donnée corrigée officiellement (PR #453) : ARCHIVER tient.** K4 (or) passe de −4,50
> à −4,37 bps, et la condition tient toujours (`../data_checks/RAPPORT_reverification_officielle.md`).

**2026-10-19.** Lecture unique par `code/fbl10.py`, selon `PREREG.md` (commit `05590d18`, avant la lecture ; essai à
blanc au préalable). Sorties : `out/fbl10.{txt,json}`, `out/fbl10_jours.csv`.

## 1. Résultat

Mesure : ^HSI, ouverture → clôture, écart aux 2 752 jours ordinaires (−4,80 bps en moyenne). Période : du lancement de
Stock Connect (2014-11-17) au 2026-10-16.

| | attendu | mesuré | t HAC | |
|---|---|---|---:|---|
| **K1, jours fermés** (n 125) | ≤ −10 bps | **+27,70** | +2,51 | échoue, **signe contraire** |
| **K2, réouvertures** (n 55) | ≥ +15 bps | **−36,55** | −2,75 | échoue, **signe contraire** |
| **K3, dose** | plus marqué en 2020-2026, dans le sens attendu | fermés +17,6 → +34,0 ; réouvertures −23,0 → −46,3 | | échoue : l'effet **inverse** grandit avec l'empreinte du canal |
| **K4, or** (séance asiatique) | jours fermés ≤ ordinaires | −2,87 contre +1,63 (écart −4,50) | | tient |

- **Mort mécanique**, selon la règle pré-enregistrée : les deux jambes ont le mauvais signe.
- **Contrôle de source.** 2800.HK donne la même chose, malgré ses ouvertures figées : fermés +27,8, réouvertures −33,4.

## 2. Ce que montre l'envers

- **Hong Kong monte quand le canal sud est fermé, et baisse le jour où il rouvre.**
  - Jours fermés positifs **10 années sur 12**, réouvertures négatives **10 années sur 12**.
  - Les deux effets sont deux fois plus forts depuis 2020, quand l'empreinte du canal a quadruplé.
- **Par fête.**

  | fête | jours fermés | réouvertures |
  |---|---:|---:|
  | Nouvel An lunaire | +38,1 (n 37) | −51,3 (n 16) |
  | fête nationale | +27,2 (n 48) | **−131,2 (n 13)** |
  | fête du Travail | +22,8 (n 17) | +18,6 (n 10) |
  | autres | +15,6 (n 23) | +20,6 (n 16) |

  La jambe des réouvertures tient aux deux grandes semaines, le Nouvel An lunaire et la semaine d'or d'octobre.
- **Un épisode pèse lourd.** En octobre 2024, Hong Kong a flambé pendant la fête nationale continentale (plan de
  relance), puis chuté le jour de la réouverture. Les jours fermés de 2024 font +136, les réouvertures −123.
- **Une lecture possible, non testée.** Les investisseurs continentaux allègent avant les fêtes, faute de pouvoir
  gérer leurs positions pendant la fermeture. Sans leurs ventes, Hong Kong monte. Ils reviennent vendeurs, ou
  arbitrent, à la réouverture.

## 3. Pourquoi on ne trade pas l'envers, et ce qu'il faudrait

- **Le miroir n'a pas été testé.** Acheter les jours fermés et vendre les réouvertures, c'est le miroir d'une
  hypothèse qu'on vient de réfuter, lu sur le même échantillon : c'est une observation post hoc.
- **Une réplication indépendante existe pourtant ici : la période d'avant Stock Connect**, avant novembre 2014.
  - Les fêtes continentales fermaient déjà Shanghai pendant que Hong Kong cotait, mais le canal n'existait pas.
  - **Si l'envers existe aussi avant 2014**, c'est un effet de calendrier des fêtes, pas de Stock Connect. Il resterait
    tradable, mais pour une autre raison.
  - **S'il est nul avant 2014**, il est lié au canal : sa seule validation hors échantillon sera la donnée future.
- **Ce test se pré-enregistre comme une hypothèse neuve**, sur des données jamais lues (^HSI et Shanghai depuis les
  années 1990).

## 4. Comptes

1 essai : compteur local du programme `orb_replacement` 51 → 52. L'admission n'a pas été atteinte.
