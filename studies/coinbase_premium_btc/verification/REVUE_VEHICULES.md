# REVUE VÉHICULES — vérification indépendante de `VEHICULES_FR.md` (2026-10-30)

Ce document prévaut sur `VEHICULES_FR.md` en cas de désaccord. Il n'est ni un avis juridique ni un avis fiscal : il
rapporte ce que publient les plateformes et ce que listent les registres, et il nomme ce qu'un professionnel doit
confirmer (§5). Étiquettes : **VÉRIFIÉ** = source primaire lue le 2026-10-30 (URL en §6) ; **MESURÉ** = recalculé ici ;
**JUGÉ** = inférence ou source secondaire. Aucune inscription, connexion, KYC ni clé d'API ; aucun identifiant envoyé.

## 1. Réponse

**« HL est-il le seul véhicule compatible ? » — Non, mais avec une nuance que le rapport du surveyor écrase.**

- **Le produit Kraken UE `PF_XBTUSD` est compatible sur les sept critères (VÉRIFIÉ / MESURÉ)** : long et short, 24 h/24 et
  7 j/7 (28,5 % des bougies horaires tombent le week-end, 0 trou depuis 2025 — MESURÉ sur 40 377 bougies publiques),
  pas de 0,0001 BTC (`contractValueTradePrecision: 4`, `askSize: 0.0001` — VÉRIFIÉ), frais 0,02 / 0,05 % (VÉRIFIÉ),
  fourchette 1 $ (VÉRIFIÉ, instantané 18:10 UTC), API et historique publics depuis 2022-03-22 (VÉRIFIÉ), même carnet
  pour les plateformes `europa` et `payward_digital_solutions` que pour le reste du monde (VÉRIFIÉ, `platformsPermitted`).
- **L'accès d'un résident français n'est pas démontré, il est seulement non exclu (VÉRIFIÉ par absence).** La page
  d'éligibilité EEE (mise à jour 10/12/2025) s'adresse à « l'EEE » sans lister de pays ; la page générale d'éligibilité
  (mise à jour 28/07/2026) exclut nommément 15 pays ou régions (Royaume-Uni, Canada, Nouvelle-Zélande, Russie, Australie
  hors wholesale…) et **pas la France**. Aucune page Kraken ne dit « France : oui ». Le `countriesBanned: []` de l'API
  est un champ technique, pas une liste d'éligibilité retail : il est vide pour tous les instruments. Le surveyor
  écrit « **Oui** » en colonne « Offert au retail FR » ; la formulation juste est « **non exclu, à confirmer à
  l'ouverture** ».
- **Le re-pricing tient (MESURÉ)** : le script `code/run_vehicules_fr.py` relancé redonne les 64 lignes à l'identique
  (Sharpe, t, rendement, MaxDD), et un contrôle par trade indépendant (`code/revue_vehicules_check_l77.py`) confirme
  L77 : sur 452 trades 2022-03 → 2026-10, le perp Kraken rend **−2,0 bp/trade** de moins que Binance (t −4,6) et
  **+2,1 bp** de plus que Coinbase (t +4,9), β 0,47. L'écart Kraken−Binance se referme : −2,9 bp en 2022, −3,3 en 2024,
  −1,4 en 2025, **−0,15 en 2026** (76 trades), ce qui suggère que la décote de devise est elle-même en train de
  disparaître avec la base USDT/USD.
- **Conclusion** : la condition « si C9 n'a que HL… » ne s'applique pas telle quelle. Il existe au moins un véhicule
  régulé MiFID II (Kraken UE) qui fait la même chose à 0,05-0,15 de Sharpe près, et deux autres (OKX Europe X-Perps,
  Coinbase UE) dont les frais ou l'index restent à confirmer. Le choix « HL ou rien » devient « HL, ou Kraken UE si
  l'onboarding dérivés passe ». Le surveyor a raison sur le fond ; il surjoue la certitude sur l'accès.

## 2. Ce qui tient, ce qui est corrigé

| Affirmation de `VEHICULES_FR.md` | Statut | Constat |
|---|---|---|
| Kraken UE : entité Payward Europe Digital Solutions (CY) Ltd, CySEC 342/17 | **TIENT** (VÉRIFIÉ) | Page d'éligibilité EEE Kraken : « PEDSL-CY … CySEC (licence 342/17) » ; registre CySEC (cache `cysec/cif.html`) : « Payward Europe Digital Solutions (CY) Limited (ex I.F. Greenfields Wealth Ltd) ». |
| Kraken UE : « **Oui** » offert au retail FR | **CORRIGÉ → « non exclu, à confirmer »** | Aucune liste positive ; France absente de la liste d'exclusion du 28/07/2026 ; `countriesBanned` est vide partout (technique). |
| Frais Kraken 2 / 5 bps, palier 1 | TIENT (VÉRIFIÉ) | Grille FR : « Maker Futures 0,02 % / Taker Futures 0,05 % (volume < 5 M$ / 30 j) ». |
| Fourchette 1 $ = 0,13 bp | TIENT (VÉRIFIÉ, instantané) | Ticker 18:10 UTC : bid 77 033 / ask 77 034 ; `askSize 0.0001`. |
| 24/7, 0,0001 BTC, ISIN GB00BQ84JX13, `mtf: true` | TIENT (VÉRIFIÉ + MESURÉ) | API instruments ; bougies : 28,5 % week-end (attendu 28,6 % si 24/7), 0 trou > 1 h depuis 2025-01-01. |
| Levier retail : 10 % (`europa`) ou 50 % (`dlt`) ; ESMA 2:1 probable | TIENT, précisé | `marginSchedules.europa.retail.initialMargin 0.10` (VÉRIFIÉ). La déclaration ESMA du 24/02/2026 dit que les perps « are likely to fall within the scope of the existing national product intervention measures » (VÉRIFIÉ) ; la mesure nationale française est la décision AMF du 1er août 2019 (VÉRIFIÉ, texte lu p. 1-6 ; le chiffre 2:1 pour les crypto-CFD n'est pas dans ces pages, il est constaté chez IG : marge 50 %). Non liant pour C9 (w max 0,45). |
| Funding Kraken ≈ HL (−0,87 vs −0,85 bp/trade, 101 trades) | TIENT (MESURÉ) | Un an d'API : moyenne +0,95 bp/24 h payé par les longs, |moy| 1,7 bp/24 h, p95 4,4 bp/24 h. |
| Kraken taker au prix réel : 1,16 (HO 1,38), entre Binance 1,23 et Coinbase 1,09 | TIENT (MESURÉ, reproduit à l'identique) | Par trade : KR 43,9 bp, BN 45,9, CB 41,8 ; β 0,472. |
| Net attendu Kraken taker 0,6-0,65, maker ≈ 0,8 ; HL 0,6-0,8 / 0,9 | TIENT (JUGÉ) | Même arithmétique que `SYNTHESE.md` (brut attendu 1,1 moins traînée). Erreur type 0,5 : l'écart Kraken/HL est dans le bruit. |
| Oracle HL = médiane pondérée de places USDT (Binance 3, OKX 2, Bybit 2…) | TIENT, précisé (VÉRIFIÉ) | « Binance, OKX, Bybit, Kraken, Kucoin, Gate IO, MEXC, Hyperliquid … weights 3, 2, 2, 1, 1, 1, 1, 1 » ; pour BTC, le spot HL est exclu. Kraken (USD) pèse 1/10 : l'oracle est à 90 % USDT. Le β de 1,0 de HL n'est mesuré que sur 56 trades calmes. |
| Coinbase UE : France « citée par la presse » (JUGÉ) | TIENT, un cran plus solide | The Block (09/03/2026) cite l'annonce Coinbase : « 26 European countries, including Germany, France and Netherlands » ; perp-style à 5 ans, funding horaire, levier 10×, EUR ou USDC. Les pages Coinbase renvoient toujours 403 (Cloudflare). Le « 0,02 % par contrat » est annoncé « as low as », hors frais bourse / compensation / NFA ; le minimum de 0,15 $ par contrat connu est celui des contrats US, non confirmé pour l'UE. |
| OKX X-Perps : frais « 2 / 5 bps (JUGÉ, presse) » | **AMÉLIORÉ → VÉRIFIÉ** | Page OKX en-eu : « X-Perps trading starts at 2 bps maker and 5 bps taker for standard accounts » ; OKX Europe Markets Ltd, MFSA ; « supported European country » sans liste ; test de caractère approprié. France : presse FR seulement (JUGÉ). Contrat 0,0001 BTC (tiers, non confirmé). Index non vérifié. |
| Gemini UE : « perps non confirmés pour le retail FR » | TIENT, nuancé | La page support Gemini (3 fetchs → 403) liste, d'après son extrait de recherche, la France parmi les pays EEE desservis, avec une note « Perpetuals are only available to Institutional clients in these countries » dont le périmètre n'est pas lisible. Entité Gemini Intergalactic EU Artemis Ltd (MFSA). JUGÉ : à confirmer. |
| Bybit EU : pas de MiFID, perps exclus | TIENT (JUGÉ) | Demande MiFID déposée 09/2025 auprès de la FMA ; non délivrée selon la presse FR de 09/2026. |
| Bitstamp UE, One Trading, Backpack : n.c. / pas de France | TIENT | Pages Bitstamp bloquées (Incapsula). Rien de nouveau. |
| IG : fourchette minimale 150, financement long 25 %/an, short +5 %/an, marge 50 % | TIENT (VÉRIFIÉ) | Page IG MT4 crypto : « 0,0694 % par jour (25 %/an) » long, « 0,0139 % (5 %/an) » short, couverture 50 % ; la page des commissions donne « Bitcoin 150 » sans unité. Horaires week-end non confirmés par IG. |
| CME 24/7 depuis le 29/05/2026 (« JUGÉ, presse ») | TIENT, un cran plus solide | Communiqué CME daté du 01/06/2026 existe (URL cmegroup.com, texte non lisible) ; The Block du 02/06 : « launched last Friday » = 29/05. Reste JUGÉ faute du texte CME. |
| Hyperliquid : CGU « US, Ontario, pays sanctionnés » (JUGÉ, tiers) | TIENT (JUGÉ) | `hyperliquid.xyz/terms` est une application JavaScript : non lisible sans navigateur. Le cache du surveyor (`pages1/hl_terms.out`) est une coquille vide ; son étiquette JUGÉ était honnête. |
| « Aucun trade ne dépasse 1× » | TIENT (MESURÉ) | w max 0,448 ; 0 % des trades > 1. |

## 3. Véhicules manqués par le surveyor

| Véhicule | Ce qui est établi | Verdict pour C9 |
|---|---|---|
| **Robinhood Europe (perps via Bitstamp)** | Robinhood Europe, UAB, Banque de Lituanie (VÉRIFIÉ). Barème du 01/09/2026 : « 0.02% maker / 0.02% taker Robinhood fee ; 0.00% maker / 0.02% taker venue fee … assessed on the order notional USD value » ⇒ **4 bps AR maker, 8 bps AR taker** (VÉRIFIÉ) ; funding toutes les 8 h ; liquidation 0,05 % ; 24/7 ; levier jusqu'à 10× ; test de caractère approprié ; « restrictions et critères d'éligibilité s'appliquent », aucune liste de pays (VÉRIFIÉ). Notionnel en USD, marge affichée en EUR. | **Compatible en coût, moins cher que Kraken taker (8 contre 10,1 bps) ; incompatible en exploitation** : pas d'API de trading, application seulement ⇒ un signal horaire 24/7 devrait être passé à la main. À garder comme véhicule de secours manuel. Index Bitstamp USD ⇒ L77 probablement ≈ Kraken (JUGÉ, non mesuré). France : Robinhood EU est distribué dans l'EEE dont la France (presse) ; les perps « varient selon la région » (JUGÉ). |
| Eurex Nano FTSE Bitcoin Index Futures (USD) | « USD 0.01 per index point (≈ 1/100 BTC, ~800 $) », « Monday – Friday : 1:15 – 22:00 CET » (VÉRIFIÉ, page Eurex). Via IBKR. | **Non compatible** : fermé la nuit (22:00 → 01:15) et le week-end ; C9 entre 20 % du temps le week-end et la restriction 24×5 lui coûte déjà 20 % des trades (`out_fr`). Frais fixes sur 800 $ de notionnel ⇒ L57. |
| Kraken Pro spot sur marge (XBT/USD, long et short) | Frais spot palier bas 0,40 / 0,80 % (grille FR, VÉRIFIÉ — attention, bien supérieurs aux 0,25 / 0,40 % souvent cités) ; marge BTC : ouverture 0,01-0,02 % + rollover 0,01-0,02 % / 4 h (VÉRIFIÉ) ⇒ ≥ 80 bps AR + 6-12 bps/24 h. | **Mort** : point mort brut de C9 à Sharpe 0 = 57 bps AR. |
| Pepperstone EU et autres CFD CySEC (BTC/USD 24/7, sans commission) | Pepperstone EU Ltd, CySEC 388/20 ; crypto « 24/7 » ; site « not intended for residents of Belgium, Spain or the United States » (VÉRIFIÉ). Fourchette et swap chargés dynamiquement : **non lisibles** sans navigateur. | **Non évalué** : à comparer à IG (19 bps de fourchette + 6,9 bps/nuit long = point mort). Un CFD à ~4 bps de fourchette et ~6 bps/nuit vaudrait ≈ Kraken taker, mais rien n'est vérifié. |
| Trade Republic / Scalable : turbos et KO sur BTC (émetteurs allemands) | Horaires émetteurs 8-22 h en semaine (survey, JUGÉ). | Même mort que les turbos Euronext : −47 % des trades. |

## 4. Tableau final (ce que la revue retient)

| Véhicule | Accès retail FR | Coût AR + 24 h | Devise / L77 | Net re-pricé 2022-04+ | Verdict |
|---|---|---|---|---|---|
| Hyperliquid perp BTC (référence) | Aucune licence ; absent du registre MiCA et de la liste noire AMF (VÉRIFIÉ) ; CGU non lisibles (JUGÉ) | 9,1 bps + funding ≈ +0,7 bp | USDC ; oracle à 90 % USDT (VÉRIFIÉ) | 1,26 (Binance) / 1,13 (Coinbase) ; attendu 0,6-0,8 | Compatible, non régulé |
| **Kraken UE `PF_XBTUSD`** | MiFID II CySEC 342/17 (VÉRIFIÉ) ; **France non exclue, non confirmée** | 10,1 bps taker / 4,0 maker ; funding ≈ HL | USD ; β 0,47 (MESURÉ, t −4,6 vs Binance) ; écart 2026 ≈ 0 | **1,16 au prix réel** (HO 1,38) ; attendu 0,6-0,65 taker, ≈ 0,8 maker | **Compatible, régulé, accès à confirmer** |
| OKX Europe X-Perps | MiFID II MFSA (VÉRIFIÉ) ; EEE, France par la presse (JUGÉ) | 2 / 5 bps (VÉRIFIÉ) ; funding n.c. | Index non vérifié | Non re-pricé ; ≈ Kraken (JUGÉ) | Candidat n° 2, à confirmer |
| Coinbase UE perp-style | CySEC 374/19 (VÉRIFIÉ) ; France nommée par Coinbase (via The Block) | « dès 0,02 % » + frais fixes n.c. | Coinbase USD (β −0,24 sur 103 trades) | 0,92-1,12 ; attendu 0,35-0,55 | Compatible si confirmé, plus cher |
| Robinhood EU perps (Bitstamp) | Banque de Lituanie (VÉRIFIÉ) ; France (JUGÉ) | **8 bps taker / 4 maker** (VÉRIFIÉ) ; funding 8 h | USD (Bitstamp) ; L77 ≈ Kraken (JUGÉ) | ≈ 1,2 (par la pente −0,028/bp, JUGÉ) | Pas d'API ⇒ secours manuel |
| Gemini UE, Bitstamp UE, Backpack, One Trading | Non confirmés / pas de France | n.c. | — | — | À confirmer, rien de vérifié |
| Bybit EU, Binance, Bitget, Crypto.com | Pas de perps pour un Français (JUGÉ / VÉRIFIÉ registre) | — | — | — | Non |
| IG CFD | MiFID, 2:1 (VÉRIFIÉ) | 19 bps + 6,9 bps/nuit long (VÉRIFIÉ) | USD | 0,71-0,80 ; attendu 0,2-0,3 | Point mort |
| CME MBT via IBKR | 24/7 depuis le 29/05/2026 (JUGÉ, presse + URL CME) | 5,9 bps + base | USD | 1 lot = 57 % du compte | Inutilisable (L57) |
| Eurex nano USD, Kraken spot marge, turbos, eToro, Saxo 24×5 | — | — | — | — | Morts (horaires ou coût) |

## 5. À confirmer par Guillaume (avec un professionnel pour 3 à 5)

1. **Kraken UE** : l'onboarding dérivés d'un résident français aboutit-il (questionnaire, NIF, KID) ? C'est la seule
   question qui sépare « Kraken compatible » de « HL seul ». Vérifier ensuite la marge réellement appliquée (10 % ou 50 %)
   et si Kraken a reclassé le produit sous le régime CFD après la déclaration ESMA du 24/02/2026.
2. **OKX Europe** et **Coinbase UE** : France ouverte à son compte ? Frais exacts par contrat et par côté ; index du perp
   (USD ou USDT) — c'est la variable L77.
3. **Fiscalité** : future MiFID (Kraken, OKX, Coinbase, Robinhood) contre perp de DEX (HL) ; PFU sur instruments
   financiers à terme, régime des actifs numériques ou BNC ; formulaires 3916 / 3916-bis pour tout compte à l'étranger.
4. **Hyperliquid** : qualification de l'usage personnel d'une plateforme non autorisée dans l'EEE. La déclaration ESMA vise
   les entreprises, pas les clients (VÉRIFIÉ) ; elle ne dit rien de l'utilisateur. Absent de la liste noire AMF (VÉRIFIÉ).
5. **Passeport France** des entités CySEC 342/17 et 374/19 et de OKX Europe Markets Ltd : le REGAFI n'a pas répondu à la
   requête publique (page « not found » le 30/10) ; à chercher au registre ESMA des entreprises d'investissement ou sur la
   fiche CySEC de l'entité (onglet passporting).

## 6. Méthode et sources

- Re-pricing : `code/run_vehicules_fr.py` relancé sur les mêmes téléchargements publics (`c9_vehicles_dl/`, hors git) ;
  sortie identique colonne par colonne à `out_fr/vehicules_fr.csv` (MESURÉ). Contrôle indépendant par trade :
  `code/revue_vehicules_check_l77.py` → `out_fr/revue_vehicules_check_l77.txt` (12 statistiques descriptives, aucune
  nouvelle configuration de signal ; non ajoutées au compteur, à réconcilier à la clôture si l'on veut).
- API publique Kraken Futures (instruments, ticker `PF_XBTUSD`, bougies 1 h, funding v4) lue le 30/10 18:10 UTC ;
  bougies et funding du cache du surveyor relus ici.

VÉRIFIÉ (primaires, lues le 2026-10-30) :
- Kraken, éligibilité EEE (10/12/2025) : https://support.kraken.com/fr/articles/derivatives-eligibility-requirements-eea
- Kraken, éligibilité générale et pays exclus (28/07/2026) : https://support.kraken.com/fr/articles/360023786632-kraken-derivatives-eligibility
- Kraken, grille de frais (futures 0,02 / 0,05 % ; spot ; marge) : https://www.kraken.com/features/fee-schedule
- Kraken Futures API : https://futures.kraken.com/derivatives/api/v3/instruments , …/v3/tickers/PF_XBTUSD ,
  https://futures.kraken.com/api/charts/v1/trade/PF_XBTUSD/1h , https://futures.kraken.com/derivatives/api/v4/historicalfundingrates?symbol=PF_XBTUSD
- Hyperliquid, frais (0,045 / 0,015 %) et oracle : https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees , …/hypercore/oracle
- OKX Europe X-Perps (2 / 5 bps, MFSA) : https://www.okx.com/en-eu/x-perps
- Robinhood Europe, frais perps : https://www.robinhood.com/eu/en/support/articles/perpetual-futures-fees ; FAQ :
  https://robinhood.com/eu/en/support/articles/perpetual-futures-frequently-asked-questions ; barème PDF du 01/09/2026 :
  https://cdn.robinhood.com/assets/robinhood/legal/fee_schedule_EU.pdf ; page produit : https://www.robinhood.com/eu/en/perpetual-futures
- ESMA, déclaration du 24/02/2026 : https://www.esma.europa.eu/node/228326 (PDF ESMA35-243228190-8024)
- AMF, décision du 1er août 2019 (CFD, clients non professionnels), p. 1-6 lues :
  https://www.amf-france.org/sites/institutionnel/files/contenu_simple/regles_professionnelles_approuvees/ (fichier « Decision du 1er aout 2019 … »)
- IG France, conditions MT4 crypto : https://www.ig.com/fr/portail-d-aide/trading-sur-cfd/frais-et-commissions/quelles-sont-les-conditions-de-trading-mt4-sur-crypto-monnaies ; commissions : https://www.ig.com/fr/commissions-cfd
- Eurex, crypto (nano USD, horaires) : https://www.eurex.com/ex-en/markets/crypto
- Pepperstone EU, BTC/USD (entité, exclusions) : https://pepperstone.com/en-eu/markets/cryptocurrencies/btc-usd/
- Registre CySEC (cache du surveyor `cysec/cif.html`) : https://www.cysec.gov.cy/en-GB/entities/investment-firms/cypriot/

JUGÉ (secondaires ou non lisibles) :
- Coinbase UE : https://www.theblock.co/post/392797/coinbase-opens-crypto-futures-trading-europe (cite l'annonce Coinbase ; coinbase.com en 403)
- Kraken, 26 pays : chiffre qui concerne Coinbase dans l'article Finance Magnates du 16/03/2026, pas Kraken :
  https://www.financemagnates.com/cryptocurrency/cysec-regulated-kraken-unit-adds-futures-tied-to-equities-commodities-fx/
- Gemini, éligibilité (403 ×3, extrait de recherche seulement) : https://support.gemini.com/hc/en-us/articles/12086543664283
- CME 24/7 : https://www.theblock.co/post/403304/cme-groups-crypto-derivatives-50-million ; communiqué CME du 01/06/2026 (URL existante, texte non lisible)
- Bybit EU MiFID en attente : presse FR 09/2026 ; Robinhood EU en France : presse 2025-2026.
- Hyperliquid, CGU : https://hyperliquid.xyz/terms (application JavaScript, non lisible).
