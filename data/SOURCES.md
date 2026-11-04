# Sources des fichiers de `data/`

Chaque fichier téléchargé doit être documenté ici : URL exacte, date de
téléchargement, licence ou conditions d'usage, et ce que le fichier couvre
dans le cours (quelle difficulté il teste).

Les fichiers générés localement (YAML reconstruits depuis le PDF du cours,
copies « défauts injectés ») sont également listés.

---

## `data/ch1/CAS_1_Societe_X_SCE_2023_2022.xlsx`

- **Fourni par l'étudiant** (document du cours, chapitre 1 partie B).
- Format : SCE tunisien, 3 feuilles (Actif, CP_et_Passif, résultat).
- Montants en dinars tunisiens (TND).
- Exercices : 2022 et 2023.
- Rôle dans le projet : cas de référence du mini-projet 1 et du mini-projet 2.
  Les corrigés C1–C4 (ch.1) et C1–C5 (ch.2) servent de tests.

## `data/ch2/societe_x_retraitements.yaml`

- **Reconstruit localement** depuis `docs/Chapitre_2_Analyse_fonctionnelle.pdf`,
  partie B, page 6 (tableau des informations complémentaires + paragraphe
  suivant pour les éléments de l'état de résultat).
- Date de reconstruction : 2026-11-02.
- Rôle : paramètres de retraitement du bilan fonctionnel de la Société X.

---

## `data/ch1/Entreprise_E_Services_annees_en_lignes.xlsx`

- **Synthétique** généré par `scripts/gen_entreprise_e.py` (généré ad-hoc).
- Date de génération : 2026-11-04.
- Rôle : tester l'adaptateur « années en lignes » sur une société de services
  avec **capitaux propres négatifs** (test du garde-fou `non significatif` pour
  ROE / endettement / autonomie / gearing).
- Défauts volontaires intégrés :
  * 2020 : `actif_total` manquant → le contrôle qualité renvoie `Bloquant`.
  * 2021 : déséquilibre A/P de 10 TND (sous le seuil 1 % donc tolérable, mais
    l'écart est bien capté par le contrôle).
  * 2022–2023 : capitaux propres négatifs (−100 puis −1 150).

Ce fichier n'est pas une donnée réelle. Les candidats réels pour l'entreprise E
(WeWork, Peloton, Yelp historique) restent à télécharger depuis SEC EDGAR.

## `data/ch1/benchmark_sectoriel_synthetique.csv`

- **Reconstitué** à partir des sources publiques Damodaran Online
  (<https://pages.stern.nyu.edu/~adamodar/>, janv. 2024) et BACH
  (Banque de France, <https://www.bach.banque-france.fr/>, 2023).
- Date de reconstitution : 2026-11-04.
- Couverture : Services, Distribution, Industrie — Q1, médiane, Q3 par ratio.
- Rôle : fichier de repli du benchmark quand les API ne sont pas accessibles.

## `data/ch1/monoprix_pdfs/*.pdf`

Etats financiers **individuels** annuels de la SNMVT « MONOPRIX »
(Societe Nouvelle Maison de la Ville de Tunis), publies sur le portail
de la Bourse de Tunis (BVMT) :

- `mnp-etats-financiers-annuels-individuels-31-12-2022.pdf` : couvre 2022 + 2021.
  <https://bvmt.com.tn/sites/default/files/societes/monoprix/etats-financiers/mnp-etats-financiers-annuels-individuels-31-12-2022.pdf>
- `mnp-etats-financiers-annuels-individuels-31-12-2023.pdf` : couvre 2023 + 2022.
  <https://bvmt.com.tn/sites/default/files/societes/monoprix/etats-financiers/mnp-etats-financiers-annuels-individuels-31-12-2023.pdf>
- `mnp-etats-financiers-annuels-individuels-31-12-2024.pdf` : couvre 2024 + 2023.
  (copie du fichier `_base_v1/tests/data/real_monoprix_2024.pdf` deja present
  dans le depot.)

**Date de telechargement** : 2026-11-04.
**Format** : SCE tunisien, dinars tunisiens (unite, pas milliers).
**Licence** : document public, publication reglementaire (depots BVMT).
**Role** : test de l'adaptateur Monoprix sur 4 exercices (2021-2024), avec
detection automatique de l'unite et de la devise. Les tests comparent les
valeurs extraites aux montants publies dans les PDF :

- Revenus 2021 = 618 317 561, 2022 = 627 130 137, 2023 = 684 081 159 TND ;
- Total bilan 2021 = 247 759 872, 2022 = 264 726 058 TND ;
- Resultat net 2021 = -429 449, 2022 = -585 002, 2023 = 5 876 040, 2024 = 6 834 166 TND ;
- Capital social 2023 = 50 691 472 (apres incorporation de reserves de 10,75 MTND
  en 2023 vs. 39 938 744 en 2022).

Retraitements captures entre PDF successifs : l'adaptateur documente dans
`EtatsFinanciers.hypotheses` tout ecart entre un comparatif et sa version
retraitee dans le PDF suivant (ex. reventilation Reserves + Primes vs.
Autres capitaux propres 2022 dans le PDF 2023).

## `data/ch1/benchmark_edgar_frames_2023.csv`

- **Télécharge depuis SEC EDGAR Frames API** (<https://data.sec.gov/>).
- Date de téléchargement : 2026-11-04.
- Concepts XBRL utilisés (bilan = instant Q4, flux = année entière) :
  - `Assets` (instant Q4)
  - `StockholdersEquity` (instant Q4)
  - `AssetsCurrent` (instant Q4) — pour la liquidité générale
  - `LiabilitiesCurrent` (instant Q4)
  - `InventoryNet` (instant Q4) — pour la liquidité réduite
  - `RevenueFromContractWithCustomerExcludingAssessedTax` (flux annuel,
    balise ASC 606 ; `Revenues` est l'ancien tag et ne couvre plus que
    ~6 sociétés depuis 2019)
  - `NetIncomeLoss` (flux annuel)
- Ratios dérivés : ROA, ROE, marge nette, autonomie financière,
  liquidité générale, liquidité réduite.
- **Filtrage** : `end == "2023-12-31"` strict pour ne retenir que les
  sociétés à exercice calendaire. Cela exclut automatiquement les 10-Q
  trimestriels (end 31/03, 30/06, 30/09) et les sociétés à exercice
  décalé (AAR CORP au 31/05, Microsoft au 30/06, etc.).
- **Provenance 10-K** : la Frames API ne porte pas de champ `form`, mais
  après filtrage par `end=2023-12-31`, les valeurs proviennent d'un 10-K
  annuel OU d'un 10-K/A (amendement) OU d'un 10-Q postérieur présentant
  le 31/12 en comparatif. Les trois citent le même bilan annuel audité.
  Vérification par échantillon dans
  `tests/test_benchmark_edgar.py::test_echantillon_depot_10k`.
- Population après filtrage : 2 268 sociétés US à exercice calendaire
  pour l'exercice 2023. Aucun filtrage sectoriel (biais small cap
  déficitaire sur ROA médian proche de 0 %).
- Script d'actualisation :
  `EDGAR_USER_AGENT="Nom (email)" python -m scripts.actualiser_benchmark_edgar 2023`
- Licence : données publiques SEC, utilisation libre avec User-Agent
  descriptif (cf. <https://www.sec.gov/os/accessing-edgar-data>).
- Cache local des frames brutes : `.cache/edgar/` (gitignoré, ~5 MB).

---

## `data/ch1/bvmt_pdfs/artes_2023.pdf` et `artes_2022.pdf`

Etats financiers **individuels** annuels de la société **Automobile Réseau
Tunisien & Service (ARTES)**, cotée BVMT (secteur distribution automobile).

- URL 2023 : <https://bvmt.com.tn/sites/default/files/societes/artes/etats-financiers/artes-etats-financiers-annuels-individuels-31-12-2023.pdf>
- URL 2022 : <https://bvmt.com.tn/sites/default/files/societes/artes/etats-financiers/artes-etats-financiers-annuels-individuels-31-12-2022.pdf>
- **Date de téléchargement** : 2026-11-04.
- **Format** : SCE tunisien, dinars tunisiens (unité).
- **Exercices couverts** : 2021 + 2022 (PDF 2022) et 2022 + 2023 (PDF 2023).
- **Vérification** : Capital 2023 = 38 250 000, RN 2023 = 27 126 932.
  Total actifs non courants structure cohérente (immobilisations
  incorporelles brutes, amortissements, net).
- **Rôle dans le projet** : jeu de données réel supplémentaire pour
  tester l'adaptateur PDF sur un autre secteur (concessionnaire
  automobile). L'adaptateur `monoprix_pdf.py` pourra être généralisé.
- **Licence** : document public BVMT (publication réglementaire).

## `data/ch1/bvmt_pdfs/sam_2023.pdf`

Etats financiers **individuels** 2023 de la **Société Atelier du Meuble
intérieurs (SAM)**, industrie du meuble.

- URL : <https://bvmt.com.tn/sites/default/files/societes/sam/etats-financiers/sam-etats-financiers-annuels-individuels-31-12-2023.pdf>
- Date de téléchargement : 2026-11-04.
- Format : SCE tunisien, dinars tunisiens.
- Rôle : variété sectorielle (industrie manufacturière) pour future
  comparaison inter-secteur.

## `data/ch1/edgar_companyfacts/CIK0000104169_walmart.json`

**Walmart Inc.** (CIK 104169) via l'API SEC EDGAR companyfacts.

- URL : <https://data.sec.gov/api/xbrl/companyfacts/CIK0000104169.json>
- **Date de téléchargement** : 2026-11-04.
- **Format** : JSON XBRL US GAAP (une entrée par (concept, filing, unit)).
- **Rôle** : démonstration de :
  - la **déduplication** : pour un couple (concept, end-date), plusieurs
    valeurs existent (10-K original, 10-K/A amendement, 10-Q comparatifs
    postérieurs). `scripts/extract_walmart.py` retient le filing le
    plus récent (max `filed`) ;
  - la **conversion USD → TND** avec taux documenté : 1 USD =
    **3,1217 TND** au 31/01/2024 (source : Banque Centrale de Tunisie,
    cours de référence).
- **Exercice fiscal Walmart** : FY2024 clôturé au 31 janvier 2024
  (exercice décalé, pas calendaire). Grandeurs clés extraites :
  Assets = 252,4 Mrd USD, Revenus = 642,6 Mrd USD, RN = 15,5 Mrd USD.
- **Tests** : `tests/test_walmart_extract.py` (6 tests passent sans réseau).
- **Licence** : données publiques SEC (utilisation libre avec User-Agent
  descriptif).

## Fichiers à venir (lots suivants)

Les copies « défauts injectés » seront nommées `defauts_injectes_<fichier_source>.<ext>`.
