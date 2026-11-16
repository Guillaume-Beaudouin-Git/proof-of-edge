# FBL-10 — Hong Kong sans l'acheteur continental (Stock Connect) : pré-enregistrement

**2026-10-19, vers 14:00. Écrit et commité avant tout calcul de rendement sur les jours d'événement.** Feu vert de
Guillaume : « On reprend la recherche ». Fiche : `../ideation/FABLE_IDEES.md`, FBL-10 (originalité 4/5, plausibilité
2/5).

## 1. Mécanisme et ce qui est déjà su

- **Le mécanisme.** Par le canal sud de Stock Connect, les investisseurs du continent sont devenus l'acheteur net
  structurel de Hong Kong. Pendant les fêtes continentales, Hong Kong reste ouvert mais le canal ferme : l'acheteur
  disparaît.
  - Les jours fermés devraient être faibles.
  - À la réouverture, les ordres accumulés arrivent d'un coup : le premier jour devrait être fort.
- **Aucun test antérieur dans le dépôt.**
- **Données récupérées avant ce commit** (`code/fetch.py`, dossier gitignoré `_data/`) : séries quotidiennes Yahoo,
  ^HSI, 2800.HK et 000001.SS, du 2014-01-02 au 2026-10-16. Seules la structure et la qualité ont été lues, aucun
  rendement d'événement :
  - ^HSI a des ouvertures réelles (0 % d'ouverture égale à la clôture de la veille) ;
  - 2800.HK en a 15,6 % de figées : il ne sera que rapporté.
- **Le calendrier vient de la donnée.**
  - **Jour fermé** : Hong Kong cote et Shanghai non.
  - **Réouverture** : le premier jour commun après une série de jours fermés.
  - Depuis le lancement (2014-11-17), sur les jours de ^HSI, cela fait **125 jours fermés et 55 réouvertures**, pour
    2 752 jours ordinaires.
  - Les 125 comprennent 5 veilles du Nouvel An lunaire (2021, 2022, 2024, 2025, 2026). Hong Kong y cote une
    demi-séance réelle, alors que 2800.HK y affiche un volume nul. Un premier décompte sur 2800.HK en donnait 120.
  - C'est une approximation. Le calendrier officiel de HKEX ferme aussi le canal un ou deux jours avant certaines
    fêtes, pour des raisons de règlement. Ces jours-là restent ici « ordinaires », ce qui ne peut que diluer l'effet.
- **La dose.** Les chiffres annuels d'achat net publiés et vérifiables manquent pour 2015-2023 : seuls 2024 (≈ HK$808
  Md) et 2025 (> HK$1 300 Md) sont trouvés. Mais l'encours du canal a été multiplié par ~4 entre 2018 (HK$789 Md) et
  2024 (HK$3 400 Md), d'après l'article HKEX *Southbound Stock Connect: Trends and Prospects*. **La dose se mesure donc
  par période : 2015-2019 (empreinte faible) contre 2020-2026 (empreinte forte).**

## 2. Données et mesures

- **Rendement d'un jour HK** : r = clôture / ouverture − 1 de ^HSI, en bps.
- **Contrôle sur l'or.** Séance asiatique de XAUUSD (`deep_history_utc`), de 20:00 New York la veille à 03:00 New York
  le jour HK. Les fêtes continentales ne tombent jamais dans une semaine de décalage d'heure d'été : le défaut
  d'horloge ne joue pas ici.
- **Coût** du trade sur HK50 FTMO : non mesuré. La fiche suppose ~4 bps aller-retour ; c'est K0 pour E1 et E4.
  - La fourchette réelle de HK50.cash est à relever au terminal avant tout déploiement.

## 3. Décision (1 essai ; 1 de plus pour E4 si elle est atteinte ; compteur local 51 → 52 ou 53)

Règle d'arrêt de la fiche ; les deux jambes sont exigées.

| | condition |
|---|---|
| **K1, jours fermés** | moyenne de r les jours fermés − moyenne les jours ordinaires **≤ −10 bps** |
| **K2, réouvertures** | moyenne de r les réouvertures − moyenne les jours ordinaires **≥ +15 bps** |
| **K3, dose** | chacun des deux écarts est plus marqué (dans son sens) sur 2020-2026 que sur 2015-2019 |
| **K4, or** | séance asiatique de l'or les jours fermés − les jours ordinaires **≤ 0** : même sens que l'acheteur absent |

Si K1 à K4 tiennent, on passe aux deux critères suivants.
- **Le trade.** Vente HK50 les jours fermés, achat les réouvertures, de l'ouverture à la clôture, à 3 000 $ (taille de
  la fiche).
  - Stop à 2 %, approché par les plus hauts et plus bas du jour : il est pris dès que le niveau est touché, à −2 %, plus
    le coût.
  - Coût K0 = 4 bps.
- **E1.** 5 plis chronologiques du P&L net : > 0 dans au moins 4.
- **E4.** Admission funded (méthode de P2, base « Livre complet − ORB seul », fenêtre 2014-11 → 2026-06) : ADMIS.

**LANCER** si tout tient, sous réserve de la fourchette réelle de HK50.cash. **ARCHIVER** sinon.

- **Nature de la mort.**
  - **Mécanique** si une jambe a le mauvais signe : jours fermés − ordinaires ≥ 0, ou réouvertures − ordinaires ≤ 0.
  - **De puissance** sinon.
- **Puissance, dite d'avance.** Avec σ ≈ 120 bps par séance, l'erreur-type vaut ~11 bps pour les jours fermés et ~16
  pour les réouvertures. Même avec un effet réel de −20 et +25 bps, la probabilité de tout passer reste d'environ 20 %.
  Sous l'hypothèse nulle, elle est d'environ 3 %.
- **Rapporté, sans décider :**
  - le t HAC de chaque jambe ;
  - le détail par fête : Nouvel An lunaire, fête du Travail, fête nationale, autres ;
  - le détail par année ;
  - la même mesure sur 2800.HK, avec sa réserve d'ouvertures figées.

## 4. Interdits

Après lecture, ne changer ni le calendrier, ni la mesure, ni les périodes, ni les seuils, ni le coût, ni la taille.
