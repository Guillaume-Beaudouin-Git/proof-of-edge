# S2 — Plan de lancement live du gotobi USDJPY (décision de Guillaume, 2026-10-19)

> **Mise en œuvre : EA v2.14, PR #452, NON déployée (2026-10-19, 16:00).**
>
> - Le code suit ce plan, avec ces écarts assumés (détail dans
>   `Multi_Asset/research/active/ea_v214_sleeves_2026-10/RECAP.md`, §4) :
>   - magics `InpMagicBase+13`/`+14`, et HK `+15`, au lieu de `+20`/`+21` : contigus au livre, une seule borne
>     (`MAGIC_LAST`) pour le breaker et le kill-file ;
>   - **v2.14** et non v2.13 : la v2.13 (R1 seul) suit sa propre revue ;
>   - liste d'annonces dans `ftmo_live/config/sleeves_calendar.json` (`s2_news.valid_until` + `skip`), et non un CSV ;
>   - motif de saut dans `audit.sleeves`, pas dans une clé `ea_s2_skip` ;
>   - taille recalculée chaque soir ;
>   - stop posé à 25 bps du prix demandé ;
>   - horloge `TzServerToUtc`, avec `TzCheck` OK exigé.
> - Défaut : rien n'est armé. Le §4 (vérifications bloquantes) reste à faire, plus la compilation MetaEditor.

**Statut : plan, aucun code live modifié.** Guillaume a décidé de lancer S2 sur la base de la revue
indépendante (`deep_dive/DECISION.md`, verdict « LANCER de justesse », porte 3× levée en
connaissance de cause). Ce document traduit la spécification du §7 de `DECISION.md` en
modifications du code live, avec les vérifications à faire avant le premier trade et le calendrier.

## 1. La règle, telle qu'elle sera tradée

- **Jours J.** D25 et DME, à la date de Tokyo.
  - D25 : le dernier jour de semaine ≤ 25 où USDJPY cote chez FTMO.
  - DME : le dernier jour de semaine du mois où USDJPY cote.
  - Fériés japonais non retirés.
- **Jambe A.** Achat USDJPY de 23:00 UTC la veille de J à 00:54 UTC.
- **Jambe B.** Vente de 00:56 à 02:00 UTC.
- **Stop serveur** à 25 bps du prix d'entrée, sur chaque jambe.
- **Taille.** 0,25 lot, soit ~2,5× l'équité. Pire événement attendu −125 $, plafond de séance
  149 $. La taille suit le multiplicateur du gouverneur.
- **Exclusions**, aucune choisie sur les rendements :
  - annonce JPY ou USD d'impact HIGH entre 22:58 UTC la veille et 02:02 UTC : tout l'événement est
    sauté ;
  - fourchette à l'ouverture d'une jambe > 2,0 bps : la jambe est sautée ;
  - entrée non exécutée dans les 60 s : la jambe est abandonnée.
- **Règle d'arrêt** (`DECISION.md` §7.8) :
  - suspension si le coût médian dépasse 2,5 bps sur 12 événements ;
  - archivage si le net moyen est sous −4 bps à 24 événements, ou négatif à 48 ;
  - suspension sur toute perte de séance > 149 $ ou tout incident de conformité.

## 2. Architecture : le cerveau décide, l'EA exécute

C'est le principe actuel : l'EA n'a aucune logique de signal et lit `Files/targets.json`.

- **Cerveau (`ftmo_live/brain.py`, `lib/statefiles.py`).** Chaque soir, avec les autres clés
  `ea_*`, il publie :

  | clé | contenu |
  |---|---|
  | `ea_s2_date` | date de Tokyo de la prochaine J, ou vide |
  | `ea_s2_arm` | 1 si cette nuit est tradée, 0 si un filtre l'exclut |
  | `ea_s2_lots` | 0,25 × multiplicateur du gouverneur, quantifié à 0,01 |
  | `ea_s2_stop_bps` | 25 |
  | `ea_s2_skip` | motif d'exclusion |

  - Le calendrier D25/DME vient d'une fonction pure, testée.
  - Le filtre d'annonces lit `ftmo_live/config/news_restricted_jpy_usd.csv`, une liste tenue à la
    main d'après le calendrier FTMO et vérifiée chaque semaine. Si la liste est périmée ou absente,
    alors `ea_s2_arm` vaut 0 : le défaut est de ne pas trader.
- **EA (`ftmo_live/mt5/book_executor.mq5`)**, nouveau module S2 :
  - **Magics propres.** `InpMagicBase+20` pour la jambe A, `+21` pour la jambe B. Ils restent
    distincts de J1 (`+1`, même symbole USDJPY) : `SignedVolume` par magic ne les mélange jamais.
  - **Horloge UTC dérivée de l'heure de Paris de l'EA**, avec ses règles d'heure d'été. `TimeGMT`
    est non fiable sous wine (commentaire de l'EA) et n'est jamais utilisé pour décider.
  - **Quatre créneaux UTC** : entrée A, sortie A à 00:54, entrée B à 00:56, sortie B à 02:00.
    Drapeaux `g_done_s2_*` dans `ea_state.json`, datés par la date de Tokyo.
  - **Collision d'hiver.** En hiver, 23:00 UTC tombe à 00:00 CET, le créneau de bascule
    quotidienne de l'EA (réancrage de la perte journalière). Proposition : entrée A à **23:01 UTC**
    toute l'année. La sensibilité de 1 minute est à vérifier sur la donnée (descriptif) avant de
    figer.
  - **Ordres au marché avec SL serveur** (`request.sl`), comme la micro-ORB pose ses stops. Sortie
    au marché à l'heure, réessayée chaque seconde avec alerte. Garde de fourchette avant chaque
    entrée.
  - **Journal.** Lignes `fills.csv` (motifs `s2_a_in`, `s2_a_out`, `s2_b_in`, `s2_b_out`) et
    fourchette à chaque ordre, pour la règle d'arrêt.
- **Supervision.** `reconcile.py`, `supervisor.py` et `lib/invariants.py` doivent connaître les
  deux magics S2. Sans cela, une position S2 déclencherait une fausse alerte de position inconnue.

## 3. Tests à écrire ou mettre à jour

- **Calendrier D25/DME.**
  - Week-ends.
  - Le 25 décembre et le 1er janvier.
  - Les mois où le 25 tombe un samedi ou un dimanche.
  - Vérifier que la fonction reproduit `gotobi_days` et `categories` de la recherche sur 2007-2026.
- **Créneaux UTC dans `lib/clocks.py`.** Ajouter une horloge `"utc"` et les créneaux S2, puis
  étendre `tests/test_dst_ea_harness.py` : l'EA doit les déclencher aux bonnes heures en été, en
  hiver et pendant les semaines de décalage.
- **Harnais MQL5** (`tests/mql5_harness.py`) :
  - séquence complète A puis B ;
  - stop touché ;
  - entrée non exécutée ;
  - jambe sautée par la garde de fourchette ;
  - redémarrage de l'EA au milieu d'une jambe.
- **Ensemble des clés.** `statefiles`, cerveau et `monday_restamp`. Le restamp du lundi doit
  laisser `ea_s2_arm` à 0 en cas de doute.
- **Identité** de la nouvelle version de l'EA, et rapprochement avec les magics S2.

## 4. Vérifications bloquantes avant le premier trade

1. ~~**Liste FTMO des annonces restreintes pour USDJPY, et la sanction encourue.**~~ **Réglé le
   2026-10-21 : le compte funded est un compte Swing, que la restriction des annonces ne vise pas.**
   - **Preuve.** Les marges que le serveur rend à l'EA (`state.json`, `live_specs`) valent 3,33 % sur
     USDJPY (1:30) et 6,67 % sur les indices et l'or (1:15). Ce sont les leviers Swing publiés ; un compte
     Standard serait à 1:100 et 1:50.
   - **La règle.** La FAQ FTMO « Can I trade news? » (mise à jour le 2026-10-11) dit : « The Swing account
     type have no restrictions on trading during news releases ». Sur un compte Standard, l'infraction
     « may result in termination » du compte. La contradiction entre les sources est donc levée.
   - **Ce qui en découle.** L'exclusion des annonces (`deep_dive/DECISION.md` §7.2) n'est plus une
     obligation. C'était « le prix de la conformité ». La garder reste la spécification revue, et coûte
     environ 3 événements par an. La retirer est une décision de Guillaume.
2. ~~**Positions de sens opposé sur le même symbole dans le même compte.**~~ **Vérifié le
   2026-10-19** : `PropFirms/ftmo/rules.md:328` autorise la couverture à l'intérieur d'un même
   compte. J1 long et la jambe B courte peuvent donc coexister.
3. **Calendrier.** L'accès de l'EA au calendrier MT5 (fonctions `Calendar*`), ou bien la tenue
   manuelle de la liste.
4. ~~**Marge à 0,25 lot**, dans le plafond de marge du livre (0,6).~~ **Vérifié le 2026-10-21.**
   - Au levier Swing de 1:30, 0,25 lot prend 833 $, et non 250 $ (`DECISION.md` §7.5 comptait à 1:100).
   - Le livre de la nuit prenait 4,7 % de l'équité le 2026-10-21. Avec S2, on arrive vers 13 %, sous le
     plafond de 60 %.
   - L'EA v2.14 contrôle cette marge au serveur (`OrderCalcMargin`) avant chaque entrée.
   - La commission est confirmée : 2,50 $ par lot et par côté, pour tous les comptes depuis le 29/09/2025
     (mise à jour FTMO du 25/09/2025).
5. **Glissement.** Les premiers fills le mesurent : c'est le premier indicateur de la règle
   d'arrêt.

## 4 bis. A5b, ajoutée au même lancement (décision de Guillaume, 2026-10-19)

> ⚠ **Retirée le 2026-10-19 vers 02:30. A5b sort du lancement, sous réserve de confirmation par Guillaume.**
>
> - **Pourquoi.** Sur donnée corrigée, sa décision sur l'espérance échoue de justesse : net +1,28 pour un seuil de 1,5,
>   et P 0,78 pour un seuil de 0,80. Verdict : ARCHIVER (`../a5b_expiry/RAPPORT_SUITE.md`, bannière).
> - **Le défaut.** `deep_history_utc` décalait d'une heure ses échéances de mars
>   (`../data_checks/RAPPORT_deep_history_dst.md`).
> - **S2 n'est pas touchée.** USDJPY n'a pas de retard détecté dans les semaines de décalage.
>   - Confirmé le 2026-10-20 par la correction officielle : le fichier USDJPY n'a pas été modifié (PR #453).
>   - Sur le livre recalculé sur les caches corrigés, l'E4 de la validation donne ΔSR +0,144, p 0,000, comme avant
>     (`../data_checks/RAPPORT_reverification_officielle.md`).
>   - A5b reste ARCHIVER sur la donnée officielle.
> - Le texte ci-dessous est gardé pour mémoire.

Source : `../a5b_expiry/RAPPORT_SUITE.md`. LANCER de justesse sur l'espérance, ~33 $/an avant
partage. Elle n'a de sens que regroupée avec S2 dans le même déploiement.

- **Règle gelée de PR-B.** `GER40.cash`, vente au marché à 12:02:00 heure de Paris, rachat au marché
  à 13:00:00, le jour d'échéance mensuelle Eurex des options EURO STOXX 50 (le 3e vendredi, ou le
  jour de bourse précédent s'il est férié). Ni cible ni filtre.
- **Taille.** σ cible 0,5 % de l'équité par événement, soit ~1,8× l'équité (~17 850 $). Pire
  séance historique −129 $.
- **Stop de catastrophe.** PR-B n'en prévoit pas. Pour le live, je propose un stop serveur à
  **80 bps**, au-delà du pire événement de 2013-2026 (−75 bps) : il ne change rien à l'historique,
  et il plafonne une queue jamais vue à ~−145 $. Il ne tombe dans aucune fenêtre d'annonce
  restreinte connue entre 12:02 et 13:00 CET. **À valider par la session principale.**
- **Intégration.**
  - Même schéma que S2 : le cerveau publie `ea_a5b_date`, `ea_a5b_arm` et `ea_a5b_lots`.
  - L'EA exécute sur son horloge de Paris (créneaux 12:02 et 13:00), avec un magic propre
    (`InpMagicBase+30`), distinct de la jambe GER40 de nuit (`+3`).
  - Le calendrier des échéances Eurex est une fonction pure testée, qui couvre le Vendredi saint.
- **Règle d'arrêt live.**
  - Archivage si le net moyen réel est négatif à 24 échéances, ou sous −5 bps à 12.
  - Suspension sur toute perte de séance > 149 $.
- **Premières échéances :** 2026-11-20, puis 2026-12-18.

## 4 ter. FBL-10b, candidate (2026-10-19, à confirmer par Guillaume)

- **Source.** `../fbl10_hk/RAPPORT_ENVERS.md`.
- **La règle.** HK50 acheté les jours où Hong Kong cote et Shanghai est fermé, vendu à la réouverture, de l'ouverture à
  la clôture, avec un stop à 2 %, à 3 000 $. Elle est répliquée sur 1997-2014.
- **Avant tout code :**
  - confirmer HK50.cash sur le compte funded ;
  - relever sa fourchette et ses horaires ;
  - faire un export M5 pour vérifier que le CFD suit l'indice.
- **L'intégration** suivrait le même schéma que S2 : le cerveau publie la date et le sens, l'EA exécute à l'horloge de
  Hong Kong, avec un magic propre. Les premiers événements tombent en février 2027 : rien ne presse.

## 5. Calendrier

- **Pas avant que v2.12.1 soit déployée et vérifiée**, c'est-à-dire après le déploiement de ce
  lundi 2026-10-19 à 09:12 et ses contrôles du soir.
- **Une seule version suivante, v2.13**, qui regroupe S2 et R1 (sortie US100 à 08:25), si la
  session principale valide R1. Deux changements dans un seul déploiement, avec une seule
  procédure : revue, compilation sur le VPS, déploiement, traçabilité.
- **La PR touchera `*.mq5` et `ftmo_live/`** : elle sera mergée à la main (GARDE 1 et 2). Label
  `do-not-merge` dès l'ouverture.
- **Premiers événements possibles :**
  - 2026-10-23 (D25 d'octobre, avancé au vendredi) : probablement sauté de toute façon, à cause de
    l'IPC japonais de 23:30 UTC ;
  - 2026-10-30 (DME) ;
  - 2026-11-25 (D25), cible réaliste ;
  - 2026-11-30 (DME).
