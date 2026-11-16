# VÉHICULES FR — C9 a-t-elle un autre véhicule que Hyperliquid pour un particulier résident français ? (2026-10-30)

Ceci n'est pas un avis juridique ni fiscal. Le document rapporte ce que publient les plateformes et ce que listent les
registres des régulateurs. Ce que Guillaume doit faire confirmer par un professionnel est listé en §3.
Étiquettes : **VÉRIFIÉ** = source primaire (URL et date de lecture en §5) ; **JUGÉ** = inférence ou source secondaire.

## 1. Réponse

**« HL seul compatible » : NON.** Le perp BTC/USD de Kraken (`PF_XBTUSD`) satisfait les sept critères. Kraken le
distribue dans l'EEE sous licence MiFID II, via Payward Europe Digital Solutions (CY) Ltd, inscrite à la CySEC sous le
n° 342/17 (VÉRIFIÉ). Le produit se trade long et short, 24 h/24 et 7 j/7, par pas de 0,0001 BTC. Les frais sont de
2 / 5 bps (maker/taker) et la fourchette mesurée de 1 $ sur 77 000 $. L'API et l'historique sont publics depuis 2022
(VÉRIFIÉ). Pour C9, la différence avec HL tient dans le bruit.

Les chiffres ci-dessous re-pricent la même liste de trades ; aucune configuration de signal n'est nouvelle :

| Fenêtre 2022-04 → 2026-10 (451 trades) | Sharpe net | Source |
|---|---|---|
| Brut, prix Binance | 1,64 | MESURÉ |
| HL taker, prix Binance (borne haute) | 1,26 | MESURÉ |
| HL taker, prix Coinbase USD (borne basse) | 1,13 | MESURÉ |
| **Kraken taker, au prix réel du perp `PF_XBTUSD`** | **1,16** (holdout 1,38) | MESURÉ |
| Kraken maker, entre les bornes Binance et Coinbase | 1,30-1,44 | MESURÉ (les bornes) |

**Net attendu hors échantillon (JUGÉ)** : on part du brut attendu de 1,1 (`SYNTHESE.md`) et on retire la traînée mesurée
de chaque véhicule. Cela donne **Kraken UE taker ≈ 0,6-0,65** et **maker ≈ 0,8 si les ordres sont remplis**, contre
**HL taker ≈ 0,6-0,8 et maker ≈ 0,9**. L'écart entre les deux est d'environ 0,1-0,15, pour une erreur type de 0,5.

**Pourquoi Kraken perd un peu.** C'est la leçon candidate L77 : le perp Kraken est indexé en USD. Sur les trades C9, son
rendement se place à mi-chemin entre Binance USDT et Coinbase USD (β 0,47, n = 452, MESURÉ). Le perp HL, lui, suit
Binance (β 1,0, mais seulement sur 56 trades et une période calme, donc peu informatif). C'est cohérent avec son oracle,
une médiane pondérée de places USDT (Binance 3, OKX 2, Bybit 2…, VÉRIFIÉ). Le funding est le même sur les deux : −0,87 et
−0,85 bp par trade sur les 101 trades communs (MESURÉ).

**Meilleure alternative : Kraken UE `PF_XBTUSD`.** C'est la seule autorisée et vérifiée au registre. Elle coûte au plus
0,15 de Sharpe et apporte un cadre MiFID II : protection contre le solde négatif, ségrégation, recours, KID. L'expression
« Si C9 n'a que HL… » ne s'applique donc pas telle quelle. Mon avis (JUGÉ) : prendre Kraken UE comme véhicule principal
du forward papier et journaliser HL en parallèle, ce qui ne coûte rien. On mesurerait ainsi l'écart réel au lieu de le
supposer. HL ne reste préférable que si les ordres maker y sont remplis et si l'écart de devise se confirme en stress.

**Ce qui reste à confirmer par Guillaume (JUGÉ).** Avant tout, que Kraken ouvre bien les dérivés à son compte de
résident français. L'API ne bannit aucun pays (`countriesBanned: []`) et la page d'éligibilité s'adresse à « l'EEE »,
mais l'ouverture dépend du questionnaire d'adéquation. Le reste figure en §3.

## 2. Tableau par véhicule

Coût à comparer au point mort brut de C9 : **22 bps AR pour un Sharpe de 1, 33 bps pour 0,7, 57 bps pour 0**
(funding inclus, `out/vehicles_detail.json`). Taille de C9 : w médian 0,19 (max 0,45), soit un notionnel médian
d'environ 2 750 € depuis 2024 (p10-p90 : 2 100-3 800 €). **Aucun trade ne dépasse 1× de levier** (MESURÉ), donc le
plafond ESMA de 2:1 sur les CFD crypto ne contraint jamais C9.

| Véhicule | Offert au retail FR ? Licence | Produit | L/S | Horaires | Taille min | Maker / taker | Financement 24 h | Marge, cotation (L77) | Levier retail | API / historique | Net C9 re-pricé | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Hyperliquid** (référence) | Aucune licence ; absent du registre MiCA ESMA (VÉRIFIÉ) ; absent de la liste noire AMF (VÉRIFIÉ) ; avertissement FCA au Royaume-Uni (JUGÉ, presse) ; CGU : US, Ontario, pays sanctionnés exclus (JUGÉ, tiers) | Perp BTC | oui | 24/7 | 0,0001 BTC (JUGÉ) | 1,5 / 4,5 bps (VÉRIFIÉ) | Funding horaire, en moyenne +0,7 bp par trade (MESURÉ) | USDC ; oracle = médiane de places USDT (VÉRIFIÉ) ⇒ suit Binance | 40× | Oui / bougies 1 h ≈ 200 j | 1,36 sur tout l'historique, 1,26 depuis 2022-04 ; borne basse 1,13 ⇒ **attendu 0,6-0,8** | Compatible, non régulé |
| **Kraken UE `PF_XBTUSD`** | **Oui** : MiFID II, CySEC 342/17 (VÉRIFIÉ, registre CySEC) ; CASP MiCA Payward Europe Solutions (CBI, FR notifiée, VÉRIFIÉ) ; API : `countriesBanned: []`, plateformes « europa » et « payward_digital_solutions » (VÉRIFIÉ) | Perp BTC/USD (ISIN GB00BQ84JX13, `mtf: true`) | oui | 24/7 | 0,0001 BTC (VÉRIFIÉ) | 2 / 5 bps au palier 1 (VÉRIFIÉ) ; fourchette 1 $ = 0,13 bp (VÉRIFIÉ, instantané) | Funding horaire ; −0,87 bp par trade contre −0,85 pour HL sur les mêmes trades (MESURÉ) | USD (collatéral EUR, USD ou crypto) ⇒ à mi-chemin, β 0,47 (MESURÉ) | API : marge initiale retail 10 % (europa) ou 50 % (dlt) (VÉRIFIÉ) ; ESMA 2:1 probable (JUGÉ) | Oui, public sans compte / bougies 1 h et mark depuis 2022-03 ; funding sur 1 an (VÉRIFIÉ) | **Taker au prix réel : 1,16** (holdout 1,38) ; maker 1,30-1,44 ⇒ **attendu taker 0,6-0,65, maker ≈ 0,8** | **COMPATIBLE, régulé** |
| Coinbase UE (Coinbase Advanced) | Oui selon la presse, France citée nommément (JUGÉ) ; Coinbase Financial Services Europe, CySEC 374/19 (VÉRIFIÉ) | Futures « perp-style » à 5 ans, nano 0,01 BTC (JUGÉ) | oui | 24/7 (JUGÉ) | 0,01 BTC ≈ 770 $ ; arrondi médian 3 lots | « À partir de 0,02 % » + frais bourse, compensation et NFA (JUGÉ) | Funding horaire (VÉRIFIÉ sur le BIP US : 3 600 s) | EUR ou USDC (JUGÉ) ; le BIP CDE suit Coinbase USD, β −0,24 (MESURÉ, 103 trades) | 10× annoncé | Oui / BIP US public depuis 2025-07 (VÉRIFIÉ) | 0,92 en taker (JUGÉ 16 bps), 1,12 à 0,02 % (9 bps), 0,92 arrondi au lot ⇒ **attendu 0,35-0,55** | Compatible si confirmé, plus cher (frais fixes, L57) |
| OKX Europe X-Perps | MiFID II MFSA (presse) ; CASP MiCA OKX Europe (MFSA, FR notifiée, VÉRIFIÉ) ; accès « pays par pays » (JUGÉ) | Futures à 5 ans avec funding | oui | 24/7 (JUGÉ) | n.c. | 2 / 5 bps (JUGÉ, presse FR) | Funding | Multi-collatéral (EUR, USDC, BTC…) (JUGÉ) ; index OKX non vérifié | 10× annoncé | Oui (JUGÉ) | Non re-pricé (coûts ≈ Kraken ⇒ ≈ Kraken, JUGÉ) | Candidat si la France est ouverte ; à confirmer |
| Bitstamp UE | Licence MTF MiFID (Slovénie, presse) ; CASP Bitstamp Europe (CSSF, FR notifiée, VÉRIFIÉ) | Perps UE depuis 04/2026 (JUGÉ, tiers) | oui | 24/7 (JUGÉ) | n.c. | n.c. | n.c. | USD (JUGÉ) | 10× (JUGÉ) | n.c. | — | Non confirmé pour le retail FR |
| Gemini UE | MiFID II MFSA (presse) ; CASP Gemini Intergalactic EU (MFSA, FR notifiée, VÉRIFIÉ) | Perps USDC (JUGÉ) | oui | 24/7 | n.c. | n.c. | n.c. | USDC ⇒ proche de HL (JUGÉ) | n.c. | n.c. | — | Non confirmé pour le retail FR |
| One Trading | MiFID ; CASP NL (VÉRIFIÉ) ; perps retail DE/NL/AT seulement en 2025 (JUGÉ, presse) | Perp BTC/EUR | oui | 24/7 | n.c. | n.c. | n.c. | **EUR** : une troisième devise, non mesurée | n.c. | n.c. | — | Pas de France connue |
| Backpack EU | CASP Latvijas Banka 05/2026, FR notifiée (VÉRIFIÉ) ; MiFID CySEC (ex-FTX EU, presse) | Perps (JUGÉ) | oui | 24/7 | n.c. | n.c. | n.c. | n.c. | n.c. | n.c. | — | À vérifier |
| Bybit EU | CASP MiCA FMA (VÉRIFIÉ) ; **pas de MiFID**, perps exclus pour l'EEE (JUGÉ, tiers 10/2026) | Spot et marge | — | — | — | — | — | — | — | — | — | Non |
| Binance | Dérivés retirés en France depuis 2022 à la demande de l'AMF ; pas d'agrément MiCA au 1er juillet 2026 (JUGÉ, presse) ; absent du registre CASP ESMA (VÉRIFIÉ) | — | — | — | — | — | — | — | — | — | — | Non |
| Crypto.com UE | CASP Foris DAX MT (VÉRIFIÉ) ; pas de perps pour les Français (JUGÉ, tiers) | — | — | — | — | — | — | — | — | — | — | Non |
| Bitget | Absent du registre CASP ESMA (VÉRIFIÉ) | — | — | — | — | — | — | — | — | — | — | Non (non autorisé) |
| BitMEX, Deribit, Coinbase International | Aucune licence UE pour les dérivés ; absents du registre MiCA (VÉRIFIÉ) ; absents de la liste noire AMF (VÉRIFIÉ) | Perps | oui | 24/7 | petite | ≈ HL | funding | USD ou inverse | élevé | oui | non re-pricé | Même statut que HL, sans son avantage de devise : pas mieux |
| IG (CFD) | Oui : MiFID ; marge retail 50 % = 2:1 (VÉRIFIÉ) | CFD BTC/USD | oui | Week-end non vérifié | n.c. | **Fourchette min 150 $ ≈ 19 bps** (VÉRIFIÉ) | Long −25 %/an = −6,9 bps par nuit ; short +5 %/an (VÉRIFIÉ) | USD | 2:1 | MT4/API | 0,80 sur tout l'historique, 0,71 depuis 2022 (fourchette MINIMALE) ⇒ **attendu ≈ 0,2-0,3** | Coût ≈ point mort |
| eToro (CFD) | Oui ; KID FR 08/2026 (JUGÉ) | CFD | oui | 24/7 | — | **1 % par côté** (JUGÉ, presse) | + overnight | USD | 2:1 | — | **−4,1** | Mort |
| Saxo (crypto FX / CFD) | Pas confirmé pour le retail FR (JUGÉ) | Crypto FX | oui | **24×5½** (JUGÉ) | — | n.c. | n.c. | USD | — | — | Horaires 24×5 : −20 % des trades, −21 % du P&L brut (brut 1,33) | Non |
| IBKR spot crypto UE | CASP MiCA via IBKR Ireland (JUGÉ, communiqué 03/2026) | Spot, **long seul** | non | 24/7 | — | — | — | USD | — | — | Spot long seul ≈ 0,6 (dossier) | Une jambe sur deux |
| Turbos / KO sur BTC | Aucun turbo BTC trouvé sur Euronext Paris (JUGÉ) ; horaires émetteurs 8 h-22 h en semaine (JUGÉ) | Turbo | oui | **8-22 h, lun-ven** | — | Fourchette ≈ 50 bps (JUGÉ) | Intégré | EUR ou USD | — | — | −47 % des trades, −46 % du P&L brut ; net ≈ 0,04 | Mort |
| CME MBT via IBKR | Oui (IBKR Ireland, MiFID) | Micro-future 0,1 BTC | oui | 24/7 depuis le 29/05/2026 (JUGÉ, presse : CME annonce le 01/06) | **0,1 BTC = 57 % du compte** | 5,9 bps + base | Base CME | USD | — | Oui | 1 lot fixe : MaxDD −23 % (dossier) | Inutilisable (L57) |
| Coinbase Derivatives nano BTC via IBKR | Accès via IBKR Ireland **non confirmé** (JUGÉ) | Nano 0,01 BTC | oui | 24/7 | 0,01 BTC | ≈ 11 bps (dossier) | Base | USD | — | Oui | ≈ 0,7 (dossier) | Possible si IBKR Ireland l'ouvre |

`n.c.` = non trouvé dans une source publique lisible aujourd'hui. Les « net » sont des Sharpe historiques re-pricés
(série quotidienne avec zéros, excès du cash, short payant rf, √365) : `out_fr/vehicules_fr.csv`. Les « attendus » sont
JUGÉS : brut attendu 1,1 moins la traînée mesurée.

## 3. À confirmer par Guillaume (avec un professionnel pour les points 3 à 5)
1. **Kraken** : ouverture effective des dérivés UE à un résident français. Il faut réussir le questionnaire d'adéquation
   et lire le KID, puis vérifier dans l'interface le levier retail réellement appliqué : l'API affiche deux barèmes,
   10 % et 50 %.
2. **Coinbase UE et OKX X-Perps** : la France est-elle ouverte (OKX ouvre pays par pays) ? Quels sont les frais exacts par
   contrat ? Les pages Coinbase renvoient 403 aujourd'hui.
3. **Fiscalité** : gains sur un future MiFID (Kraken, Coinbase) contre gains sur un perp de DEX (HL). Les régimes peuvent
   différer (PFU sur instruments financiers à terme, ou régime des actifs numériques, ou BNC). Il faut aussi déclarer les
   comptes ouverts à l'étranger (formulaires 3916 / 3916-bis).
4. **HL** : utiliser un DEX non autorisé dans l'EEE n'est pas listé comme interdit pour l'utilisateur. Il n'est pas sur la
   liste noire AMF, mais il n'est pas non plus sur la liste blanche, et il n'offre aucune protection. L'ESMA (24/02/2026)
   considère que les perps relèvent probablement du régime CFD, quel que soit le lieu de négociation, ce qui vise les
   entreprises qui les distribuent. Il faut faire qualifier l'exposition personnelle.
5. **Passeport FR des entités MiFID** (CySEC 342/17, 374/19) : le vérifier au REGAFI. Je ne l'ai pas consulté.

## 4. Ce qui est mesuré, et les limites
- Re-pricing seul : `code/run_vehicules_fr.py`, les mêmes 931 trades que `run_vehicles.py`, sans nouveau signal.
  Il produit 89 statistiques (`out_fr/_nt_vehicules_fr.json`).
- Le perp HL taker au prix Binance redonne 1,364 sur tout l'historique, contre 1,373 dans `revue/` (fenêtres de
  funding légèrement différentes) et 1,485 au holdout (identique).
- La comparaison au prix réel ne couvre que Kraken (2022-04 → 2026-10, 452 trades, écart type Binance−Coinbase de
  9,4 bps par trade). Pour HL, les 56 trades disponibles tombent en période calme (écart type 3,6 bps) : son β de 1,0 ne
  prouve pas qu'il suit Binance en stress.
- Le funding Kraken ne sort de l'API publique que sur 1 an. Avant cela, le proxy est HL, puis Binance.
- Les frais fixes en dollars (nano, IG) sont ancrés au prix BTC du 30/10 (77 174 $), comme dans `run_vehicles.py`.
- La fourchette IG est la fourchette **minimale** affichée ; le coût réel est plus élevé.
- Leçon candidate (nommée, non numérotée) : « l'index d'un perp régulé UE est en USD : sur un signal de base USDT/USD,
  le véhicule régulé vaut la moitié de la décote de devise (β ≈ 0,5) ».

## 5. Sources (toutes lues le 2026-10-30)
VÉRIFIÉ (primaires) :
- Bulletin MFSA du 09/03/2026 reprenant la déclaration ESMA35-243228190-8024 du 24/02/2026 (les perps relèvent
  probablement des mesures CFD, que la négociation ait lieu sur une plateforme ou non) :
  https://www.mfsa.mt/wp-content/uploads/2026/03/Circular-on-ESMA-Public-Statement-Identifying-Derivatives-within-the-Scope-of-CFDs-National-Product-Intervention-Measures.pdf
- Registre MiCA des CASP de l'ESMA (CSV, mis à jour le 31/08/2026) : https://www.esma.europa.eu/sites/default/files/2024-12/CASPS.csv
- Registre CySEC des entreprises d'investissement (342/17 Payward ; 374/19 Coinbase FSE) : https://www.cysec.gov.cy/en-GB/entities/investment-firms/cypriot/
- Liste noire AMF (recherche publique par autocomplétion ; Hyperliquid, BitMEX, Deribit et Bybit absents) :
  https://www.amf-france.org/fr/espace-epargnants/proteger-son-epargne/listes-noires-et-mises-en-garde
- Kraken Futures API, instruments et ticker `PF_XBTUSD` : https://futures.kraken.com/derivatives/api/v3/instruments ,
  https://futures.kraken.com/derivatives/api/v3/tickers/PF_XBTUSD ; bougies :
  https://futures.kraken.com/api/charts/v1/trade/PF_XBTUSD/1h ; funding :
  https://futures.kraken.com/derivatives/api/v4/historicalfundingrates?symbol=PF_XBTUSD
- Grille de frais Kraken (version FR) : https://www.kraken.com/features/fee-schedule
- Éligibilité aux dérivés Kraken pour l'EEE (mise à jour le 10/12/2025) : https://support.kraken.com/fr/articles/derivatives-eligibility-requirements-eea
- Hyperliquid, frais / funding / oracle : https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees ,
  …/trading/funding , …/hypercore/oracle
- Coinbase, API publique des produits futures et bougies BIP-20DEC30-CDE : https://api.coinbase.com/api/v3/brokerage/market/products?product_type=FUTURE
- IG France, conditions MT4 crypto (financement, marge de 50 %) :
  https://www.ig.com/fr/portail-d-aide/trading-sur-cfd/frais-et-commissions/quelles-sont-les-conditions-de-trading-mt4-sur-crypto-monnaies ;
  fourchette minimale de 150 : https://www.ig.com/fr/commissions-cfd

JUGÉ (secondaires) :
- Coinbase UE, 26 pays dont la France : https://www.theblock.co/post/392797/coinbase-opens-crypto-futures-trading-europe
- OKX X-Perps : https://cointelegraph.com/news/okx-europex-perps-regulated-crypto-derivatives ,
  https://coinacademy.fr/actu/okx-lance-x-perps-europe-derives-crypto-reglementes-levier-10x/
- Kraken UE : https://www.businesswire.com/news/home/20250520169459/en/
- Accès des Français aux perps, octobre 2026 : https://www.coinperps.com/learn/best-crypto-exchanges-france
- Binance et la France : https://coinacademy.fr/actu/crypto-binance-restreint-produits-derives-france/ ,
  https://cryptoactu.com/binance-france-sans-agrement-mica-1er-juillet/
- One Trading : https://www.thetradenews.com/one-trading-expands-retail-access-for-crypto-perpetual-futures-venue/
- Gemini UE : https://coindesk.com/policy/2025/05/09/gemini-secures-mifid-ii-license-from-malta-to-offer-derivatives-in-eea
- Bitstamp MTF : https://cointelegraph.com/news/bitstamp-secures-trading-facility-license-europe
- CME 24/7 : https://www.marketsmedia.com/cme-launches-24-7-crypto-futures-options-trading/
- Hyperliquid, FCA et pays restreints : https://cryptoast.fr/hyperliquid-hype-fca-britannique-met-en-garde-contre-plateforme/ ,
  https://www.datawallet.com/fr/crypto/hyperliquid-supported-and-restricted-countries
- eToro : https://cryptoast.fr/frais-etoro/ ; Saxo : https://home.saxo/en-mena/rates-and-conditions/crypto-fx/spreads-and-commissions
- IBKR, spot crypto dans l'EEE : https://interactivebrokers.ie/en/general/about/mediaRelations/3-31-2026.php

Aucune inscription, connexion, KYC ni clé d'API ; aucun identifiant personnel envoyé. Téléchargements publics dans le
scratchpad (`c9_vehicles_dl/`), hors git.
