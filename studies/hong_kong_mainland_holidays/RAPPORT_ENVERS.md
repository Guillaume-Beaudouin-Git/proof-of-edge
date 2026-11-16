# FBL-10b — Hong Kong pendant les fêtes continentales : l'envers se réplique avant Stock Connect. LANCER, sous conditions

> **Revérifié le 2026-10-20 : LANCER, sous conditions, tient.** Les séries sont Yahoo, hors `deep_history_utc`. Seul
> E4 lit le livre funded : sur le livre recalculé sur les caches corrigés, il donne ADMIS, ΔSR +0,079, p 0,010
> (`out/officiel_livre/`, `../data_checks/RAPPORT_reverification_officielle.md`).

**2026-10-19.** Lecture unique par `code/fbl10b.py`, selon `PREREG_ENVERS.md` (commit `3c947ae0`, avant la lecture ;
essai à blanc des deux branches au préalable). Sorties : `out/fbl10b.{txt,json}`, `out/fbl10b_jours.csv`. Un témoin hors
protocole, rapporté après la décision : `code/temoin_hk.py`, `out/temoin_hk.txt`.

## 1. La règle et le résultat

**La règle.** Les jours où Hong Kong cote et Shanghai est fermé, achat de HK50 à l'ouverture, revente à la clôture.
Le premier jour où les deux marchés rouvrent ensemble, vente à l'ouverture, rachat à la clôture. Environ 10 jours fermés
et 4 à 5 réouvertures par an.

**Étape 1, réplication sur une période jamais lue** (1997-07 → 2014-11, avant le canal sud). Écart aux jours
ordinaires, ^HSI de l'ouverture à la clôture :

| | seuil | mesuré | t HAC | |
|---|---|---|---:|---|
| R1, jours fermés (n 221) | ≥ +10 bps | **+21,90** | 2,95 | **tient** |
| R2, réouvertures (n 78) | ≤ −15 bps | **−32,28** | −2,32 | **tient** |

**L'envers n'est donc pas lié à Stock Connect** : il existait déjà avant. C'est un effet de calendrier des fêtes
continentales, mesuré maintenant sur deux périodes indépendantes.

**Étape 2, décision de lancement.**
- **Le trade** : achat les jours fermés, vente les réouvertures, stop à 2 %, K0 de 4 bps supposé.

| | mesure | |
|---|---|---|
| net par trade | 1997-2014 : **+20,5 bps** (n 299) ; 2014-2026 : +23,7 (n 180), soit +18,4 après la correction du choix du sens | |
| E3, espérance | combiné **+19,8 bps nets** (e.-t. 5,6), P(net > 0) ≈ 1 ; au coût de stress, +15,8 | tient |
| E1, 5 plis 1997-2026 | +40,2 / +7,4 / +13,0 / +5,2 / +43,0 : **5 sur 5** | tient |
| E4, admission funded à 3 000 $ | **ADMIS** : ΔSR +0,079 (p 0,011), P(perte sur 2 ans) −2,2 pts, trader 66,2 → 71,3 $/mois, pire séance −61 $ | tient |
| **verdict pré-enregistré** | **LANCER, sous réserve du coût réel de HK50.cash** | |

## 2. Ce qu'un chercheur senior vérifie

1. **Ce n'est pas un effet d'après-fête de Hong Kong.** Le témoin regarde le lendemain et la veille des jours où seul
   Hong Kong est fermé, Shanghai ouvert :

   | période | lendemain | veille |
   |---|---|---|
   | 1997-2014 | +6,5 (t 0,49) | −7,9 (t −0,69) |
   | 2014-2026 | +3,3 (t 0,35) | +10,4 (t 0,96) |

   Rien de significatif. L'effet tient à la fermeture **continentale**.
2. **C'est régulier.**
   - Les jours fermés sont positifs 13 années sur 18 avant 2014, et 10 sur 12 après.
   - Les réouvertures sont négatives 12 années sur 18, puis 10 sur 12.
   - Les deux jambes tiennent sur chaque sous-période :

     | sous-période | jours fermés | réouvertures |
     |---|---:|---:|
     | 1997-2007 | +27,6 | −44,2 |
     | 2008-2014 | +9,9 | −19,1 |
     | 2014-2026 | +27,7 | −36,6 |
3. **La jambe courte vit des grandes fêtes.**
   - Sur 1997-2014, les réouvertures font −36,9 après le Nouvel An lunaire, −66,6 après la fête nationale et −65,4 après
     la fête du Travail (semaine d'or jusqu'en 2007).
   - Après les petites fêtes, elles sont **positives sur les deux périodes** : +31,1 (n 19) puis +20,6 (n 16).
   - Restreindre la vente aux grandes fêtes serait une modification après lecture. Elle se pré-enregistrera à part ; la
     règle lancée reste celle qui a été testée.
4. **Le mécanisme n'est pas établi.** Une lecture plausible, non testée :
   - pendant les fêtes, Hong Kong est le seul marché chinois ouvert, et il porte seul l'exposition à la Chine, avec
     moins de nouvelles du continent ;
   - à la réouverture, les actions A réévaluent d'un coup, et Hong Kong corrige son avance.
5. **Le montant est petit.** ~15 trades par an × +20 bps × 3 000 $ ≈ **90 $/an avant partage**. La taille de la fiche
   est prudente : avec un stop à 2 %, la pire séance (−61 $) laisse de la marge sous le plafond de 149 $. Une taille
   plus grande demanderait une décision à part.
6. **La donnée est un indice, pas le CFD.** ^HSI vient de Yahoo, avec des ouvertures réelles depuis 1997. Le CFD
   HK50.cash peut s'en écarter à l'ouverture : c'est à vérifier.

## 3. Ce qu'il manque pour lancer

1. **HK50.cash sur le compte funded : le symbole existe**, vérifié le 2026-10-19 sur le VPS en lecture seule.
   - Le terminal en a l'historique sous `Bases/FTMO-Server4/history/HK50.cash/` (fichier `2026.hcc`).
   - Il figure parmi les 166 symboles du serveur du compte, avec JP225.cash, AUS200.cash et EU50.cash.
   - Restent à relever :
   - sa fourchette à 09:30 et à 16:00 HKT ;
   - sa commission et ses horaires (pause de midi) ;
   - sa marge.

   La fiche de spécifications FTMO du dépôt (`ftmo_specs_full.csv`) n'a pas de ligne HK50. Le livre aurait pourtant
   l'indice au panneau quotidien de l'univers FTMO.
2. **Un export M5 de HK50.cash**, à faire depuis le terminal, comme celui du 2026-10-13. Il vérifie que le CFD suit
   l'indice de l'ouverture à la clôture, sur la semaine d'or d'octobre 2026.
3. **Le calendrier des fermetures continentales.** Il est publié chaque fin d'année par le Conseil d'État ; le cerveau
   le publierait comme pour S2.
4. **Un module de l'EA — codé dans la v2.14 (PR #452, non déployée, jambe désarmée ; magic 15)** :
   - le symbole HK50.cash ;
   - une horloge de Hong Kong, sans changement d'heure ;
   - les clés `ea_hk_*`.

   **Premiers événements : le Nouvel An lunaire 2027** (février). L'envers n'a rien à faire avant.

## 4. Comptes

2 essais, la réplication et l'admission : compteur local du programme `orb_replacement` 52 → 54. Le témoin est rapporté
hors protocole et ne compte pas.
