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

## `data/ch1/benchmark_edgar_frames_2023.csv`

- **Télécharge depuis SEC EDGAR Frames API** (<https://data.sec.gov/>).
- Date de téléchargement : 2026-11-04.
- Concepts XBRL utilisés :
  - `Assets` (instant Q4) — 6 430 sociétés ;
  - `StockholdersEquity` (instant Q4) — 6 275 sociétés ;
  - `RevenueFromContractWithCustomerExcludingAssessedTax` (flux annuel)
    — 3 142 sociétés (balise ASC 606) ;
  - `NetIncomeLoss` (flux annuel) — 6 389 sociétés.
- Ratios dérivés : ROA, ROE, marge nette, autonomie financière.
- Population : **toutes les sociétés US ayant déposé un 10-K pour
  l'exercice fiscal 2023**. Aucun filtrage sectoriel (biais small cap
  déficitaire sur ROA médian proche de 0 %).
- Script d'actualisation :
  `EDGAR_USER_AGENT="Nom (email)" python -m scripts.actualiser_benchmark_edgar 2023`
- Licence : données publiques SEC, utilisation libre avec User-Agent
  descriptif (cf. <https://www.sec.gov/os/accessing-edgar-data>).
- Cache local des frames brutes : `.cache/edgar/` (gitignoré, ~3,7 MB).

---

## Fichiers à venir (lots suivants)

Les fichiers réels des entreprises B (Monoprix PDF), C (industrie IFRS SEC),
D (société US EDGAR), E (société US CP négatifs via EDGAR) seront ajoutés après
sélection et validation. Chacun aura :

- URL exacte de téléchargement,
- date de téléchargement,
- licence ou conditions d'usage,
- taux de change USD → TND utilisé si conversion (source + date du taux).

Les copies « défauts injectés » seront nommées `defauts_injectes_<fichier_source>.<ext>`.
