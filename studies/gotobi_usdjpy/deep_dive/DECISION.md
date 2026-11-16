# S2 — Gotobi USDJPY dosé : décision de la revue indépendante

**2026-10-19. Verdict : LANCER, de justesse.**
- À 2,5× l'équité (0,25 lot), en sautant les jours d'annonce, avec une règle d'arrêt écrite
  d'avance (§7.8).
- Pré-enregistrement : `PREREG_DEEP.md`, commit `e1643995`, avant tout calcul. Les cinq critères
  de décision tiennent (§6).

**Ce qu'il faut retenir avant de lancer :**
- **Ce n'est pas +3 023 $.** Ce chiffre est l'historique en échantillon. Il contient une décennie
  2007-2015 nulle (+31 $/an), et les heures du trade ont été choisies sur cette période.
- **L'espérance honnête est d'environ +110 $/an avant partage**, soit ~+90 $/an pour le trader :
  +2,1 bps nets par événement, ~21 événements par an une fois les annonces exclues.
- **Environ une année sur trois sera perdante** : 28 % au scénario central, 45 % si l'effet
  s'érode.
- **Le lancement repose sur l'effet gotobi en général, pas sur le dosage.** Que le 25 et la fin de
  mois battent les autres gotobi n'est pas établi : +1,1 bp, erreur-type 1,35.
- **Ce verdict lève la porte 3× du programme.** Si on la tient pour liante, le verdict est
  ARCHIVER : brut de long terme 4,51 bps, pour 5,61 requis.

## 1. Ce qui l'emporte

1. **Le coût est mesuré, et la donnée neuve le confirme.**
   - Sur 11 événements gotobi d'août à octobre 2026, au bid/ask réel du serveur FTMO, le coût vaut
     1,82 bp en moyenne (médiane 1,88, maximum 2,04). Le coût retenu était de 1,87.
   - La porte 3× protège d'abord contre un coût sous-estimé. Ce risque-là est fermé.
2. **L'espérance rétrécie reste positive.**
   - Méthode : méta-analyse à effets aléatoires des 7 périodes, avec une décote de sélection de
     0,5 bp.
   - Résultat : brut 3,98 bps, net +2,11 bps au coût mesuré, P(net > 0) = 0,84.
   - Au coût de stress de 2,5 bps, le net vaut encore +1,48 bp.
3. **Le stop borne la queue.**
   - Le pire événement vaut −50 bps (deux stops), soit −125 $ à 0,25 lot. Si le glissement double,
     il vaut −250 $, sous la perte journalière maximale de 500 $.
   - Le 31/10/2011, le MoF intervient pendant la jambe de vente : −24 bps avec le stop, −343 sans.
4. **Le pire scénario coûte peu.**
   - Érosion : le D futur vaut le G1 du holdout, 2,38 bps. La sleeve rapporte alors +30 $/an au
     coût mesuré et perd 7 $/an à 2,5 bps.
   - Si le net vrai est nul, la sleeve ne perd rien en espérance.
   - S'il vaut −2 bps, elle perd ~5 $ par événement. La règle d'arrêt la coupe alors d'ici
     48 événements 8 fois sur 10.
5. **L'effet est vivant dans la donnée la plus fraîche, et la sleeve est orthogonale.**
   - Août-octobre 2026, au prix FTMO réel : +8,5 bps exécutables par événement gotobi (n 11),
     dont +9,5 sur D (n 3). C'est descriptif, car l'erreur-type est d'environ 6 bps.
   - La corrélation avec chaque jambe du livre est ≤ 0,03 (`../RAPPORT_VALIDATION.md`).

## 2. Ce qui pèse contre, et que le verdict assume

- **La marge de coût est mince.** Le brut de long terme vaut 4,51 bps, soit 2,4× le coût, sous la
  porte 3×.
- **Il n'y a pas de dose sur 17 ans.** Les deux lectures pré-enregistrées qui pouvaient l'établir
  ont échoué : la validation (V1, V2 et V3) et le test de rupture.
- **Une décennie plate a déjà eu lieu.**
  - 2007-2015 : net +0,53 bp par événement, et 6 années perdantes sur 9.
  - Depuis 2016 : aucune année perdante sur 10.
- **L1 est sensible à la décote.** Avec une décote de 1 bp au lieu de 0,5, P(net > 0) tombe à
  0,78, sous le seuil de 0,80. L1 échouerait alors de peu.
- **La sleeve est petite et bruitée.**
  - σ ≈ 214 $/an, pour ~110 $/an attendus.
  - Aucune règle d'arrêt ne tranche vite : après 48 trades réels, l'erreur-type du net reste
    d'environ 2,8 bps.

## 3. L'économie du flux depuis 2015

**Le mécanisme est documenté.**
- Au fixing de Tokyo (TTM, 9:55 JST), les ordres des clients penchent vers l'achat de devises, de
  façon prévisible (Ito et Yamada 2017).
- Les jours gotobi, les banques couvrent à l'avance la demande des importateurs, et USDJPY monte
  vers 9:55 (Bessho et al. 2023).
- Le dollar s'apprécie avant les fixings, puis revient (Krohn).

**Pourquoi le 25 et la fin de mois porteraient plus.**
- Au Japon, le schéma de paiement entre entreprises le plus courant est « clôture en fin de mois,
  paiement à la fin du mois suivant ».
- Les échéances au 25 sont fréquentes (paie, paiements au 25).
- Une dose est donc plausible a priori.

**Pourquoi elle serait apparue vers 2015-2016 : je n'ai trouvé aucune raison.**
- La date estimée de la rupture, le 29/01/2016, est celle de l'annonce des taux négatifs par la
  BoJ. Je ne connais aucun mécanisme qui relie les deux.
- Aucune source publique ne classe le 25 ou la fin de mois devant les autres gotobi en volume.
- Une hypothèse reste non vérifiée : la popularité de l'anomalie (Bessho et al.) concentrerait le
  front-running sur les dates les plus connues.

**Conclusion.** La dose reste non établie. L'estimation prospective (§5) ne lui accorde que ce que
donnent les données : +1,1 bp, avec une erreur-type de 1,35.

## 4. Robustesse — descriptif, aucun paramètre n'est choisi ici

Sources : `out/s2_deep.txt`, `out/s2_ea_logs.txt`, `out/s2_feed.txt`. Le contrôle est réussi : le
script retrouve D sur la découverte (4,333), sur le holdout (6,195), les 6 plis et les 462
événements publiés.

**Coût.** D, net par événement, et $/an pour 24 événements à 2,5× l'équité, avant partage.

| période | n | brut | net à 1,87 | net à 2,5 | net à 3,0 | brut / coût |
|---|---:|---:|---:|---:|---:|---:|
| 2007-2015 | 215 | +2,40 | +0,53 (+32 $) | −0,10 (−6 $) | −0,60 (−36 $) | 1,3× |
| 2016-2024 S1 | 203 | +6,38 | +4,51 (+268 $) | +3,88 (+231 $) | +3,38 (+201 $) | 3,4× |
| holdout 2024-07 → 2026-05 | 44 | +6,19 | +4,32 (+257 $) | +3,69 (+220 $) | +3,19 (+190 $) | 3,3× |
| **tout 2007-2026** | 462 | **+4,51** | **+2,64 (+157 $)** | +2,01 (+120 $) | +1,51 (+90 $) | **2,4×** |

**Jambes de D (bps).**

| | 2007-09 | 2010-12 | 2013-15 | 2016-18 | 2019-21 | 2022-24 S1 | holdout |
|---|---:|---:|---:|---:|---:|---:|---:|
| achat avant le fixing | −1,59 | +0,86 | +0,17 | +2,53 | +2,37 | +4,97 | +0,77 |
| vente après le fixing | +4,80 | +2,22 | +0,75 | +3,58 | +3,08 | +2,88 | +5,43 |

- La vente après le fixing est positive dans les 7 périodes ; elle porte ~70 % du brut sur 20 ans.
- L'achat est positif dans 6 périodes sur 7, mais plus instable.

**Stop.**
- Sur les 462 événements : +4,51 avec le stop, +3,76 sans.
- Le stop pèse surtout en 2010-12 (+3,08 contre −1,49 sans), à cause de l'intervention de 2011.
- Au holdout, il coûte un peu : +6,19 contre +6,66 sans.
- On compte 69 stops (50 à l'achat, 19 à la vente), dont 2 remplis au-delà du niveau.
- C'est la seule protection contre une intervention : il reste.

**Distribution de D.**
- σ 19,1 bps ; asymétrie +0,60 ; kurtosis en excès 2,8 ; 60 % de gagnants.
- Quantiles 1 / 5 / 50 / 95 / 99 % : −39 / −24 / +4 / +37 / +57 bps.
- Les 10 % meilleurs événements font 91 % du brut total ; les 10 % pires en retirent 60 %.
- Le pire vaut −50 bps : 4 fois, avec les deux stops touchés le même jour. Vient ensuite −41,4
  bps, le 27/02/2026.

**Interventions du MoF** : événements D à ±1 jour ouvré d'une intervention (bps).

| date | jour | achat | vente | total | sans stop |
|---|---|---:|---:|---:|---:|
| 2011-10-31 | fin de mois, jour même | +0,7 | −25,0 | −24,3 | −343,2 |
| 2022-09-23 | le 25, lendemain | −11,4 | +0,7 | −10,7 | −10,7 |
| 2022-10-25 | le 25, lendemain | −25,0 | +3,1 | −21,9 | +9,5 |
| 2024-04-30 | fin de mois, lendemain | +34,2 | −2,9 | +31,3 | +31,3 |

**Fériés japonais et jour de semaine.**
- Fériés japonais : 32 événements D tombent un jour sans fixing (le 31 décembre quand c'est un jour
  de semaine, le 29-30 avril, quelques 25), à +2,68 bps contre +4,65 les autres jours. L'écart reste dans le bruit
  (erreur-type ~3,4). La règle gelée les garde, et je ne la modifie pas.
- Jour de semaine : lundi +4,84, mardi +4,76, mercredi +5,60, jeudi +4,05, vendredi +4,11
  (n 197, à cause des reports de week-end). Aucun effet.

**2026 S1, recoupé avec la donnée neuve.**
- **2026 S1** : −0,93 bp (n 10). Un seul événement pèse, le 27/02/2026 : −41,4, avec un stop à
  l'achat et −16,4 à la vente. Les 9 autres font +3,6 en moyenne.
- **Journaux de l'EA, au bid/ask FTMO réel**, du 20/08 au 15/10/2026 : 12 événements, dont 11
  complets. Le 25/08 manque d'une minute.

| | n | exécutable (bps) | net | coût réalisé |
|---|---:|---:|---:|---:|
| D | 3 | +9,46 (achat −4,42, vente +13,88) | +8,46 | 1,79 |
| autres gotobi | 8 | +8,16 | +7,16 | 1,84 |
| tous | 11 | +8,51 | +7,51 | 1,82 |

- Les trois événements D : 31/08 +1,9 ; 25/09 +2,7 ; 30/09 +23,9.
- La faiblesse de 2026 S1 ne se prolonge pas. Mais 11 événements ne prouvent rien.
- **Convention de prix.** La série historique est en prix bid. Selon le motif de fourchette par
  minute, le coût effectif varie d'environ ±0,3 bp autour de 1,87 : 1,6 sur le motif FTMO de
  2026. Je garde 1,87.

**Source des données.**
- Sur 172 événements communs (2018, puis 2024-01 → 2025-05), FTMO-Demo et Dukascopy donnent les
  mêmes rendements : D +4,90 contre +4,81 ; tous +3,15 contre +3,15 ; corrélation 1,000.
- La force du segment MT5 (+6,15 contre +3,41 sur Dukascopy 2007-17) est donc un effet de période,
  pas de source.

## 5. Espérance prospective

**Méta-analyse à effets aléatoires** (DerSimonian-Laird) sur les 6 plis et le holdout, avec des
erreurs-types HAC lag 6.

| série | 7 périodes (bps) | μ_RE, décote 0,5 | τ | écart-type prédictif |
|---|---|---:|---:|---:|
| **D** | +3,2 +3,1 +0,9 +6,1 +5,5 +7,9 +6,2 | **+3,98** (SE 1,02) | 1,88 | 2,13 |
| autres gotobi | +3,8 +7,7 +2,3 +3,6 +3,8 +2,1 +0,6 | +3,03 (SE 0,63) | 0 | 0,63 |
| G1, tous les gotobi | +3,6 +6,1 +1,8 +4,4 +4,3 +4,0 +2,4 | +3,44 (SE 0,52) | 0 | 0,52 |
| contraste D − autres | −0,5 −4,6 −1,4 +2,5 +1,7 +5,7 +5,6 | +1,10 (SE 1,35), sans décote | 2,39 | 2,74 |

Sensibilité de D à la décote : 4,42 bps sans décote, 3,55 avec une décote de 1 bp.

**Scénarios fixés d'avance.** Chaque case donne le $/an avant partage (24 événements, 2,5×), puis
P(année perdante), puis P(perte sur 2 ans). Bootstrap par blocs de 6 événements, 20 000 tirages.

| scénario | brut | coût 1,87 | coût 2,5 | coût 3,0 |
|---|---:|---|---|---|
| érosion (G1 du holdout) | 2,38 | +30 $ ; 45 % ; 43 % | −7 $ ; 52 % ; 53 % | −37 $ ; 58 % ; 60 % |
| **central** (μ_RE) | 3,98 | **+126 $ ; 28 % ; 20 %** | +88 $ ; 34 % ; 28 % | +58 $ ; 40 % ; 36 % |
| régime récent (2016-2026 − 0,5) | 5,85 | +237 $ ; 13 % ; 5 % | +199 $ ; 17 % ; 9 % | +169 $ ; 21 % ; 13 % |

- σ ≈ 214 $/an dans tous les scénarios.
- Avec l'exclusion des annonces (−13 % des événements), les $/an se multiplient par ~0,87. Le
  central devient ≈ +110 $/an, et P(année perdante) ≈ 30 %.

## 6. Règle de décision pré-enregistrée (1 essai, compteur local 38 → 39)

| critère | seuil | mesuré | |
|---|---|---|---|
| L1, espérance | net ≥ 1,5 bp et P(net > 0) ≥ 0,80 | +2,11 ; 0,84 | tient |
| L2, stress de coût | net à 2,5 bps ≥ 0 | +1,48 | tient |
| L3, érosion bornée | perte ≤ 60 $/an à 2,5 bps | 7 $/an | tient |
| L4, annonces | exclusions ≤ 20 % des D 2018-2026 | 13,1 % (26 sur 199) | tient (aveugle) |
| L5, donnée neuve | coût médian ≤ 2,5 bps ; ≤ 2 événements incomplets | 1,88 ; 1 | tient (aveugle) |

**Ce que la règle ne garantit pas.**
- L1 à L3 ont été fixés après lecture des rapports.
- L1 échouerait avec une décote de 1 bp.
- Seuls L4 et L5 étaient aveugles.

## 7. Spécification du module live (sans code)

### 7.1 Calendrier

- **Un événement J** est D25 ou DME du mois. J est une date de Tokyo (JST = UTC + 9 h, sans heure
  d'été).
  - D25 : le dernier jour de semaine ≤ 25 où USDJPY cote chez FTMO. Si le symbole ne cote pas ce
    jour-là (le 25 décembre par exemple), on recule d'un jour, comme le backtest, qui prend le
    dernier jour présent dans la donnée.
  - DME : le dernier jour de semaine du mois où USDJPY cote.
- **Fériés japonais : non retirés**, comme le veut la règle gelée.
- **Horaires fixes en UTC** : 23:00 la veille de J, puis 00:54, 00:56 et 02:00 le jour J.

### 7.2 Exclusions

Aucune n'est choisie sur les rendements.

- **Annonces.** Sauter tout l'événement si une annonce d'impact HIGH, en JPY ou en USD, est prévue
  entre 22:58 UTC la veille et 02:02 UTC.
  - Source : le calendrier MT5, plus une liste manuelle tirée du calendrier FTMO des annonces
    restreintes, vérifiée la semaine précédente. Ces deux sources couvrent les 24 jours D de l'année.
  - Vérification à 12:00 UTC et à 22:50 UTC la veille. Si le calendrier est illisible, pas de
    trade.
  - Effet attendu : ~3 événements par an, presque tous l'IPC national japonais (23:30 UTC) tombant
    un jour D25.
  - Rapporté sans décider : les jours exclus faisaient +7,83 bps (n 26), contre +5,68 pour les
    jours gardés. L'exclusion coûte donc un peu ; c'est le prix de la conformité.
  - ⚠ **Ajouté le 2026-10-21.** Le compte funded est un compte Swing. FTMO ne lui applique pas la restriction
    des annonces (`../LANCEMENT_S2.md` §4, point 1). L'exclusion reste dans la spécification. La retirer serait
    une décision de Guillaume, et non une obligation.
- **Garde de fourchette.** Ne pas ouvrir une jambe si la fourchette à l'ouverture dépasse 2,0 bps,
  soit près de 3× la plus haute médiane relevée à ces minutes (0,72). Les deux jambes sont
  indépendantes : B s'ouvre même si A a été sautée.
- **Garde de latence.**
  - Une entrée qui n'est pas exécutée dans les 60 s suivant l'heure prévue est abandonnée.
  - Une sortie est réessayée chaque seconde jusqu'à exécution, avec une alerte.

### 7.3 Horloge

- **Planifier en UTC** : `TimeGMT()` en live.
- **Contrôle à chaque événement.** `TimeTradeServer() − TimeGMT()` doit valoir +3 h pendant l'heure
  d'été US et +2 h sinon (serveur = New York + 7 h). Sinon : pas de trade, et une alerte.
- **Heures serveur qui en résultent :**
  - été US : 02:00, 03:54, 03:56, 05:00 ;
  - hiver US : 01:00, 02:54, 02:56, 04:00.
  - Prochain changement : le 1er novembre 2026.
- **Session.** USDJPY cote de 00:05 à 23:55 serveur (`ftmo_specs_full.csv`) : les quatre heures
  tombent hors de la pause.

### 7.4 Ordres

- **Jambe A.**
  - Achat au marché à 23:00:00 UTC la veille.
  - Stop serveur à 25 bps sous le prix d'exécution.
  - Clôture au marché à 00:54:00 UTC.
- **Jambe B.**
  - Vente au marché à 00:56:00 UTC.
  - Stop serveur à 25 bps au-dessus du prix d'exécution.
  - Rachat au marché à 02:00:00 UTC.
- **Règles communes.**
  - Pas d'objectif, pas de réentrée après un stop.
  - Même lot sur les deux jambes.
  - Aucune position S2 ne doit rester ouverte après 02:05 UTC. Sinon : clôture forcée, et une
    alerte.

### 7.5 Taille et marge

- **Notionnel** : 2,5× le solde, recalculé le 1er de chaque mois et arrondi au 0,01 lot. Aujourd'hui,
  2,5 × 9 914 $ = 24 785 $, soit 0,25 lot (1 lot = 100 000 USD).
- **Pire événement historique** : −125 $, sous le plafond de 149 $ (1,5 % du solde).
- **Commission** : 2,5 $ par lot et par côté, soit 2,50 $ par événement (1,0 bp).
- **Marge** : 1 000 $ par lot (levier 1:100), soit 250 $.
  - ⚠ **Corrigé le 2026-10-21.** Le compte funded est un compte Swing, au levier 1:30 sur le FX (marge du
    serveur : 3,33 %). La marge vaut donc 3 333 $ par lot, soit **833 $** à 0,25 lot. Avec le livre, on
    reste vers 13 % de l'équité, sous le plafond de 60 % (`../LANCEMENT_S2.md` §4).

### 7.6 J1 et gouverneur

- **Positions séparées** (compte en mode couverture) : S2 n'ajuste pas J1, et J1 n'ajuste pas S2.
  Leur corrélation vaut +0,02 (`../RAPPORT_VALIDATION.md`).
- **Plafond d'exposition.** Pendant la jambe A, la position longue USDJPY totale ne dépasse pas le
  notionnel de J1 plus 2,5× le solde. S2 ne double jamais sa taille, même si J1 est à zéro.
- **Gouverneur.** Avant 23:00 UTC, on additionne :
  - la perte du jour FTMO, réalisée et latente (les nuits US100 et GER40 peuvent être ouvertes) ;
  - et 250 $ (deux stops, glissement doublé).

  Si ce total dépasse le budget journalier du gouverneur, l'événement est sauté.

### 7.7 Journal, pour la règle d'arrêt

- **Par ordre** : heure prévue et heure réelle, bid/ask à l'heure prévue, prix exécuté, glissement
  contre le mid, fourchette, commission.
- **Par événement** : brut, net, stop touché, et motif de saut (annonce, fourchette, latence,
  gouverneur, horloge).

### 7.8 Règle d'arrêt, écrite d'avance

- **R1, coût (rapide).**
  - Coût réalisé = écart entre le mid à l'heure prévue et le prix exécuté sur les 4 ordres, plus la
    commission.
  - Si sa médiane sur les 12 derniers événements dépasse 2,5 bps : suspension.
- **R2, rendement (lent).**
  - Après 24 événements réels : ARCHIVER si le net moyen est inférieur à −4 bps.
  - Après 48 événements réels : ARCHIVER si le net moyen est négatif.
  - Probabilité d'arrêt d'ici 48 événements, selon le net vrai :

    | net vrai (bps) | +4,3 | +2,1 (central) | +0,5 | 0 | −2 |
    |---|---:|---:|---:|---:|---:|
    | P(arrêt à 24) | 1 % | 4 % | 10 % | 13 % | 30 % |
    | P(arrêt d'ici 48) | 5 % | 21 % | 44 % | 52 % | 80 % |

  - Une sleeve qui marche sera coupée à tort 1 fois sur 5. C'est le prix d'un effet mince. Une
    règle plus stricte en couperait davantage.
- **R3, queue.** Un événement qui perd plus de 1,5 % du solde (149 $) déclenche une suspension et
  une revue : le stop n'a pas tenu.
- **R4, conformité.** Suspension immédiate, jusqu'à correction, dans l'un de ces cas :
  - un ordre ou un stop exécuté à ±2 min d'une annonce restreinte ;
  - une position S2 encore ouverte après 02:05 UTC ;
  - un écart d'horloge.
- **Aucune ré-optimisation en cours de route** : ni les heures, ni le stop, ni le calendrier.

### 7.9 Avant le premier trade

> **État au 2026-10-21** (branche `claude/ea-v214-s2-hk50-2026-10`, `ea_v214_sleeves_2026-10/RECAP.md` §6) :
> - **le rejeu hors ligne est fait, CONFORME** (`code/rejeu_s2_journaux.py`) :
>   - le cerveau et l'EA v2.14 réels tournent sur les journaux d'août à octobre ;
>   - ils ne tradent que les 4 jours D, aux 4 heures, à 0,25 lot ;
>   - le résultat est égal à la formule de `s2_ea_logs.py` lue à 08:01 JST ;
> - **la commission est lue** : 2,50 $ par lot et par côté (mise à jour FTMO du 25/09/2025) ;
> - **le calendrier** : la v2.14 tient la liste d'annonces à la main (`sleeves_calendar.json`, `s2_news`), sans
>   lire le calendrier MT5. Le compte étant Swing, cette liste est un choix de prudence, plus une obligation
>   (`../LANCEMENT_S2.md` §4) ;
> - **les premiers événements** ne sont plus le 23/10 ni le 30/10 : la v2.14 se déploie après le 02/11, et le
>   premier événement est le 25/11.

- **Rejouer le module hors ligne** sur les journaux de l'EA (`spread_log_2026{08,09,10}.csv`). Il
  doit retrouver les 12 événements et les heures du §4. C'est un test du code, pas une ombre papier.
- **Vérifier le calendrier MT5 du terminal FTMO.** S'il ne classe pas l'IPC japonais en HIGH, tenir
  la liste à la main.
- **Lire la commission USDJPY** dans la fenêtre Spécification (attendu : 2,5 $ par lot et par côté).
- **Premiers événements éligibles :**
  - le 23/10/2026 (D25), probablement sauté si l'IPC national tombe ce jour-là — à vérifier ;
  - le 30/10/2026 (fin de mois). Si la BoJ décide ce jour-là (calendrier 2026 à vérifier), sa
    décision tombe d'habitude après 02:30 UTC, donc après la jambe B.
  - Le changement d'heure US du 1er novembre suit immédiatement.

## 8. Ce qui changerait le verdict

**Vers ARCHIVER :**
- tenir la porte 3× pour liante ;
- juger la décote de sélection ≥ 1 bp, ce qui donne P(net > 0) = 0,78 ;
- un coût réalisé supérieur à 2,5 bps (R1), ou une hausse de la commission FTMO ;
- des annonces restreintes par FTMO que le calendrier MT5 ne signale pas, sans liste manuelle
  tenue ;
- un EA qui ne sait pas planifier en UTC avec les gardes du §7.

**Vers plus de taille : rien.** Le plafond vient de la pire séance (1,5 % du solde), pas de
l'espérance. L'ERC donnerait 13,4×, et la pire séance dépasserait alors le plafond de plus de
4 fois (−688 $ contre −149 $).

**Ce qui ne doit pas le changer :** quelques mois de pertes. Ils sont dans la distribution
(P(année perdante) ≈ 30 %).

## 9. Non vérifié

- **La liste FTMO des annonces restreintes pour USDJPY**, et la sanction exacte : rupture selon le
  relevé local (`PropFirms/ftmo/rules.md`), annulation du trade selon une source tierce.
- **Le glissement réel des ordres au marché.** Les instantanés de minute ne le mesurent pas.
- **Les stops de la donnée EA** sont vérifiés sur des instantanés de minute, pas tick par tick.
- **La raison institutionnelle d'une dose depuis 2015** : aucune trouvée.
- **La comparaison de sources** ne couvre que 2018 et 2024-2025 : il manque Dukascopy 2019-2023 au
  cache.
- **La règle d'exclusion** a été comptée sur le calendrier du dépôt (impact HIGH). Celui du terminal
  MT5 peut classer autrement.

## 10. Comptes

- **1 essai**, la règle de décision L1-L5 : compteur local du programme `orb_replacement` 38 → 39.
- **Descriptif, non compté :**
  - `out/s2_deep.txt` (§2-4 du pré-enregistrement) ;
  - `out/s2_ea_logs.txt` (donnée neuve) ;
  - `out/s2_feed.txt` (ajouté après le pré-enregistrement).
- **Modifications de l'hypothèse G1 : 2 sur 3.** Ce sont le dosage D et l'exclusion des annonces.
  Les gardes de fourchette et de latence sont des règles d'exécution.
- **Code** : `code/s2_deep.py`, `code/s2_ea_logs.py`, `code/s2_feed.py`. Ils réutilisent
  `../code/s2_holdout.py` et `../code/s2_validation.py` sans les modifier.

**Sources publiques (§3) :**
- Ito, T., Yamada, M. (2017), *Puzzles in the Tokyo fixing in the forex market*, Journal of
  International Economics 109 ; NBER w22820 : https://www.nber.org/papers/w22820
- Bessho, H., Sugimoto, T., Suzuki, T. (2023), arXiv 2301.13204 : https://arxiv.org/abs/2301.13204
- Krohn, I., *Foreign Exchange Fixings and Returns Around the Clock*. Référence reprise de
  `alpha_hunt_2026-10/flows/RAPPORT.md`.
- Conditions de paiement au Japon (clôture et paiement en fin de mois) :
  https://stripe.com/us/resources/more/payment-terms-in-japan et
  https://invoicedataextraction.com/blog/japan-payment-terms-shimekiri-tegata
- Règle FTMO sur les annonces, deux lectures contradictoires :
  https://www.awaketrader.com/educacion/ftmo-news-trading-prohibition-guia et
  https://propvator.com/blog/is-news-trading-allowed-in-ftmo/
