# CLAUDE.md — instructions de travail

Ce document est **le contrat de travail** entre l'étudiant (Aymen) et tout contributeur,
humain ou agent, qui touche ce dépôt. Les règles sont celles du brief d'ouverture du projet.

## Contexte du projet

Master Data Science — cours « Analyse financière ».
Deux mini-projets fusionnés dans une seule base de code :

- **Mini-projet 1 « FinRatio Engine »** — chapitre 1, partie D, lots 1 à 7 : du bilan brut
  au diagnostic par ratios automatisé, benchmarké par API.
- **Mini-projet 2 « FuncBalance »** — chapitre 2, partie D, lots 1 à 5 : extension du
  schéma pivot pour le bilan fonctionnel (FRNG, BFR, TN, SIG, CAF), moteur de reclassement
  déclaratif, simulateur.

## Références qui font foi

En cas de doute, le PDF l'emporte sur toute mémoire humaine ou interprétation d'agent.

- `docs/Chapitre_1_Etats_financiers_et_ratios.pdf`
- `docs/Chapitre_2_Analyse_fonctionnelle.pdf`

**Les corrigés sont les jeux de test de référence** :

- Ch. 1, partie C (common-size + 15 ratios Société X 2022–2023).
- Ch. 2, parties C1 (SIG) à C4 (bilan fonctionnel). Le C5 (bilan retraité) est absent
  du corrigé : il sera recalculé à partir des informations de la partie B et montré
  à l'étudiant avant d'être figé en test.

## Règles de travail

### Collaboration

- **Mode apprentissage** : avant chaque lot, l'agent explique le concept financier
  en termes simples, puis son plan, et attend l'accord de l'étudiant. Avance d'un
  lot à la fois ; ne jamais passer au suivant sans feu vert.
- **Ne jamais inventer une donnée** : un poste absent est marqué « non calculable »,
  avec la liste explicite des données manquantes.
- Travaille uniquement dans ce dossier. Demander avant toute commande système
  (installation globale, configuration Git globale…).

### Dépôt

- Dépôt **public** : aucun secret, aucun fichier personnel.
- Les clés d'API vont dans `.env` (gitignoré). `.env.example` documente les variables.
- `_base_v1/` est l'ancien projet BilanLens, en **lecture seule**. On peut y reprendre
  l'extraction PDF/OCR comme adaptateur supplémentaire, mais pas les ratios ni l'UI.

### LLM et IA

- **Pas de LLM par défaut.** Les options du cours (embeddings au lot 2 ; LLM avec
  garde-fou anti-hallucination au lot 6) ne sont ajoutées qu'après feu vert explicite.

### Tests et journal

- Les tests restent verts : `.\.venv\Scripts\python.exe -m pytest -v` (Windows) ou
  `./.venv/bin/python -m pytest -v` (Unix).
- `docs/journal.md` doit être tenu à jour après chaque lot (décisions, hypothèses,
  écarts constatés).
- Proposer un message de commit à la fin de chaque lot. **Ne commiter et ne pousser
  que si l'étudiant le demande explicitement.**

## Conventions du cours (SCE tunisien)

- **Ratios du chapitre 1 sur 365 jours** (DSO, DPO, DIO…).
- **Grandeurs du chapitre 2 en jours de CA sur 360 jours** (FRNG, BFR, TN en jours).
- Référentiel comptable principal : SCE tunisien. L'IFRS (anglais) et l'US GAAP
  (XBRL/EDGAR) sont traduits vers le pivot via la table de correspondance de
  l'annexe 1 du chapitre 1.

## Choix d'architecture (lot 0)

- Paquet Python : `analyse_financiere` (repo : `analyse-financiere-ds`).
- Schéma pivot : **Pydantic v2**, libellés en **français** pour coller aux PDF et
  corrigés.
- CI : **Ubuntu, Python 3.11, une seule configuration** (rapide, suffisant).
- Formules des ratios et règles de reclassement : **YAML déclaratifs**, évalués
  via un **AST restreint** (jamais `eval()`).
- Chaque poste source conserve son **lineage** jusqu'à la masse fonctionnelle finale.

## Hypothèses signalées (annexes absentes du PDF)

Les trois points suivants sont documentés dans `docs/journal.md` et validés par
l'étudiant avant d'être figés dans les tests :

1. **Annexe 2 du ch.1 — format YAML des ratios** : proposé par l'agent.
2. **Annexe du ch.2 — règles de reclassement YAML** : proposées par l'agent.
3. **Corrigé C5 (bilan fonctionnel retraité)** : recalculé depuis la partie B,
   présenté à l'étudiant avant d'être figé en test.

## Entreprises B, C, D, E et benchmark

Les fichiers ne sont pas fournis. On les remplace par des **données réelles de même
nature**, en respectant les difficultés décrites dans le PDF. L'agent propose
d'abord des candidats concrets (nom, source, URL, difficulté couverte), puis attend
l'accord de l'étudiant avant tout téléchargement. Chaque fichier téléchargé est
documenté dans `data/SOURCES.md` (URL, date, licence).

Les défauts volontaires du cours (déséquilibre A/P de 10, valeur manquante) sont
injectés dans des **copies** `defauts_injectes_…`, jamais dans les fichiers d'origine.

## Attribution de commits (le cas échéant)

Les commits générés depuis cette session se terminent par :

    Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
