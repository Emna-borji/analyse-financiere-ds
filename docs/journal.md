# Journal du projet

Journal des décisions, hypothèses et écarts rencontrés.
Les lots sont ceux des parties D des chapitres 1 et 2.

---

## 2026-11-02 — Lot 0 : mise en place du dépôt

### Décisions

- Nom du paquet : `analyse_financiere`. Nom du repo : `analyse-financiere-ds`.
- Schéma pivot : **Pydantic v2** (validation stricte + sérialisation YAML/JSON
  native + messages d'erreur clairs à l'ingestion).
- Libellés du pivot en **français** pour rester proches des PDF et corrigés.
- Formules de ratios et règles de reclassement : **YAML déclaratifs**, évaluation
  par **AST restreint** (jamais `eval()` libre).
- Base de jours : **365** pour les ratios du ch.1, **360** pour les grandeurs du
  ch.2 en jours de CA. Conforme au brief et aux PDF.
- CI : **Ubuntu, Python 3.11** uniquement (une seule configuration, suffisante pour
  un projet pédagogique).
- Lecture Excel : **openpyxl** seul (.xlsx). Pas de .xls dans le périmètre.
- `_base_v1/` reste **gitignoré** et en lecture seule : l'extraction PDF/OCR
  pourra y être réutilisée comme adaptateur supplémentaire au lot ch.1-1, mais
  les ratios et l'UI ne seront pas repris.

### Hypothèses (à valider dans les lots suivants)

1. **Annexe 2 du ch.1 — format YAML des ratios** : absente du PDF fourni. Un
   format proposé dans `config/ratios.yaml` sera présenté au moment du lot ch.1-4.
   Il doit permettre : id, famille, formule textuelle, sens favorable, unité,
   repère de seuil, garde-fous (division par zéro, capitaux propres négatifs,
   plafonnement des valeurs extrêmes).
2. **Annexe du ch.2 — règles de reclassement YAML** : absente du PDF. Format
   proposé pour le lot ch.2-2 : chaque champ pivot est associé à une masse
   fonctionnelle, ou ventilé par parts quand le poste est mixte (ex. autres
   actifs courants = prêt société sœur [ACHE] + reste [ACE]).
3. **Corrigé C5 (bilan fonctionnel retraité)** : absent du PDF. Il sera
   **recalculé à la main depuis les données de la partie B du ch.2** et montré
   à l'étudiant avant d'être figé en test au lot ch.2-5.
4. **Fichier `societe_x_retraitements.yaml`** : recréé depuis le tableau de la
   partie B du chapitre 2 (page 6). Source citée en commentaire dans le YAML.
   À valider visuellement par l'étudiant avant utilisation en test.

### Dépendances non encore à bord

- `streamlit`, `plotly`, `matplotlib` : ajoutés au lot de restitution (ch.1-7
  et ch.2-5).
- `hypothesis` : optionnel au lot ch.2-4 (tests property-based sur les
  invariants comptables).
- `sentence-transformers` : optionnel au lot ch.1-2 (embeddings multilingues).
  N'est jamais ajouté par défaut.

### Entreprises réelles à sélectionner

Candidats proposés au brief, à valider par l'étudiant avant tout téléchargement :

- **B** (distribution, stocks, milliers TND, 3 exercices) : Monoprix (BVMT), à
  partir des PDF de `_base_v1/tests/data/`, complétés si besoin par un rapport
  d'une autre année.
- **C** (industrie, IFRS en anglais, format long) : société industrielle IFRS
  déclarée à la SEC (20-F, companyfacts), convertie en CSV long.
- **D** (EDGAR, USD, doublons 10-K) : société US via API SEC EDGAR, convertie
  USD → TND avec taux documenté.
- **E** (services, années en lignes, capitaux propres négatifs) : société de
  services US à CP négatifs via EDGAR.
- **Benchmark** : fichiers sectoriels Damodaran (ou EDGAR frames), avec repli
  sur fichier synthétique construit à partir d'eux.
