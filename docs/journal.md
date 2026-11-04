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

---

## 2026-11-04 — Lots 1 à 7 ch.1 + Lots 1 à 5 ch.2 (Société X complète)

### Ce qui est livré

- **Schéma pivot Pydantic v2** (`analyse_financiere/pivot.py`) : 60+ champs
  couvrant le bilan (net + brut), l'état de résultat (tous les SIG du ch.2),
  les éléments hors bilan, les dividendes reconstitués.
- **Adaptateur SCE Excel 3-feuilles** (`adapters/sce_excel.py`) : reconnaît le
  motif brute / `Moins : Amortissements` / net et stocke les trois valeurs
  séparément. Reconstitue `amortissements_cumules`. Charge le YAML de
  retraitements. Reconstitue les dividendes par variation des CP.
- **Contrôles qualité** (`quality.py`) : A=P, sous-totaux, signes, CP négatifs,
  valeurs manquantes critiques, cohérence SIG. 3 niveaux OK/Avert./Bloquant.
- **Moteur de ratios déclaratif** (`ratios.py` + `config/ratios.yaml`) : 16
  ratios, AST restreint (pas d'`eval()`), garde-fous (division par zéro,
  CP négatifs, stocks nuls). Évalue à partir du pivot + variable dérivée
  `achats_ttc` pour le DPO.
- **SIG + CAF 2 méthodes** (`sig_caf.py`) : cascade complète, test de
  concordance, capacité de remboursement, autofinancement.
- **Reclassement + retraitements** (`reclassement.py` + `config/reclassement.yaml`) :
  deux modes (C4 condensé / C5 retraité). Crédit-bail, EENE, ventilation
  hors exploitation. Lineage conservé pour chaque masse.
- **Typologie** (`typologie.py`) : 6 situations.
- **Mapping** (`mapping.py` + `config/mapping_libelles.yaml`) : alias + regex
  + fuzzy (rapidfuzz ≥ 85). Précision/rappel mesurés sur jeu annoté.
- **Benchmark** (`benchmark.py`) : CSV synthétique (Damodaran + BACH),
  client SEC EDGAR frames (User-Agent + cache + 10 req/s), centile,
  z robuste, feu tricolore.
- **Commentaire** (`commentaire.py`) : 15 règles expertes + Jinja2. Pas
  de LLM.
- **Restitution** (`restitution.py` + `app.py`) : rapport HTML autonome
  avec waterfall SIG en SVG inline + dashboard Streamlit 5 onglets.
- **Documentation** : `README.md` complet, `docs/GUIDE_COMPREHENSION.md`
  (lot par lot avec chiffres Société X), `docs/PRESENTATION.md` (plan
  soutenance 10 min + Q&A probables).

### Tests : 45 verts

- Smoke YAML Société X (lot 0).
- Common-size 2022/2023 (C1 ch.1).
- 16 ratios × 2 exercices contre corrigé C2 (ch.1).
- DIO non applicable (pas de stocks).
- Contrôles qualité.
- SIG 2022/2023 contre C1 ch.2.
- CAF 2 méthodes + capacité remb. contre C2 ch.2.
- Dividendes + autofinancement contre C3 ch.2.
- Bilan fonctionnel condensé contre C4 ch.2.
- Bilan fonctionnel retraité C5 (recalculé, invariant respecté).
- 6 invariants (A=P, FRNG−BFR=TN, CAF concordance, CB laisse FRNG constant,
  EENE conservent BFR+TN).
- Mapping (alias, regex, fuzzy, précision/rappel ≥ 80 %).
- Benchmark (centile, z robuste, feu).
- Rapport HTML + commentaire.

### Décisions

- **C5 recalculé** : montré en détail dans `docs/GUIDE_COMPREHENSION.md`.
  FRNG inchangé par le crédit-bail (invariant). TN passe de −303 040 à −383 040
  après ajout des EENE (80 000). Dette résiduelle CB = 360 000 (valeur
  d'origine 600 000 − amort cumulés 240 000).
- **Benchmark synthétique uniquement** pour l'instant. Le client SEC EDGAR
  est fonctionnel mais non branché en démo : un appel réel réclame un
  User-Agent et dépend de la disponibilité réseau.
- **Entreprises B, C, D, E** : le framework d'adaptateurs est prêt (pattern
  Strategy, pivot invariant), mais seule la Société X est pleinement
  implémentée pour la soutenance de demain. Les écritures des 4 autres
  adaptateurs sont des prochaines étapes clairement balisées.

### Commandes de démo

- `pytest -v` (45 tests verts)
- `python -m scripts.generer_rapports` (génère `reports/*.html`)
- `streamlit run app.py` (dashboard sur localhost:8501)

