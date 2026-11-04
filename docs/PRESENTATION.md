# Plan de soutenance — 10 minutes

Projet : **Analyse financière automatisée** — Master Data Science.
Deux mini-projets fusionnés : FinRatio Engine (chapitre 1) + FuncBalance (chapitre 2).

---

## Chronométrage indicatif

| Minute | Partie | Contenu |
|---|---|---|
| 0:00–1:00 | **1. Problématique** | Le problème métier, les difficultés data |
| 1:00–3:00 | **2. Architecture** | Schéma pipeline, choix clés |
| 3:00–6:00 | **3. Démo live** | Tests → Rapport HTML → Streamlit |
| 6:00–8:00 | **4. Résultats** | Corrigés C1–C5 reproduits + diagnostic Société X |
| 8:00–9:00 | **5. Limites et pistes** | Benchmark tunisien, autres adaptateurs |
| 9:00–10:00 | **6. Q&A** | Questions probables du jury |

---

## 1. Problématique (1 min)

> « Une banque tunisienne reçoit chaque semaine des liasses financières au
> format Excel SCE, des exports IFRS en anglais, des PDF scannés, et parfois
> des comptes consolidés au format XBRL de la SEC. Un analyste ressaisit
> manuellement, calcule 15 ratios dans un tableur, et rédige un avis. »

**Question** : comment transformer ce flot hétérogène en un diagnostic
automatisé, auditable, et comparé à un benchmark sectoriel, sans
re-saisie ni hallucination ?

Les quatre difficultés du cours :
1. **Formats hétérogènes** : SCE Tunisien, IFRS anglais, CSV long,
   JSON EDGAR, Excel années en lignes, PDF scanné.
2. **Libellés libres** : "Fournisseurs" vs "Trade payables" vs
   "AccountsPayableCurrent" désignent la même chose.
3. **Validation** : comment savoir si les données sont correctes ? L'équation
   `Actif = Passif` est un test unitaire naturel.
4. **Interprétation** : un ratio seul ne dit rien. Il faut une norme, le
   temps, le secteur, et les autres ratios.

---

## 2. Architecture (2 min)

### Schéma

```
      ┌─────────────────────────────────────────────┐
      │                 Sources                     │
      │  Excel SCE | CSV IFRS | JSON EDGAR | PDF    │
      └───────────────────┬─────────────────────────┘
                          │
                   ┌──────▼──────┐
                   │  Adapters   │   (un par format, pattern Strategy)
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │  EtatsFin.  │   Pydantic v2, 60+ champs ch.1+ch.2
                   │   (pivot)   │
                   └──────┬──────┘
                          │
       ┌──────────┬───────┼──────────┬──────────┐
       ▼          ▼       ▼          ▼          ▼
    quality   ratios   sig_caf  reclassement  mapping
       │       │         │          │           │
       │   ┌───▼────┐    │          │           │
       │   │ratios  │    │          │           │
       │   │ .yaml  │    │          │           │
       │   └────────┘    │          │           │
       │                 │     ┌────▼───────┐   │
       │                 │     │reclassement│   │
       │                 │     │   .yaml    │   │
       │                 │     └────────────┘   │
       └───────┬─────────┴──────────┬───────────┘
               │                    │
               ▼                    ▼
         commentaire.py       benchmark.py
         (Jinja2, pas de LLM)  (CSV + SEC EDGAR)
               │                    │
               └──────────┬─────────┘
                          ▼
                    restitution.py
                    (HTML + Streamlit)
```

### Trois choix clés à défendre

1. **Schéma pivot Pydantic v2 + libellés français**.
   *Pourquoi* : validation stricte à l'ingestion, messages d'erreur clairs,
   cohérence avec le vocabulaire du cours.

2. **YAML déclaratif + AST restreint pour les ratios**.
   *Pourquoi* : l'étudiant ou le prof peut ajouter un ratio sans toucher au
   Python. Pas d'`eval()` libre, un visiteur AST n'autorise que les opérateurs
   arithmétiques et quelques fonctions sûres (`abs`, `min`, `max`).

3. **Pas de LLM**.
   *Pourquoi* : le commentaire doit être traçable. Chaque phrase est un
   template Jinja2 dont les nombres sont lus directement du pivot.
   Zéro risque d'hallucination. Si on active un LLM au lot 6, c'est avec
   un garde-fou automatique qui vérifie que chaque nombre cité figure
   bien dans les données.

---

## 3. Démo live (3 min)

### Étape 1 — Montrer les tests

```bash
pytest -v
```

**45 tests verts**, dont les corrigés C1 à C5 de la Société X :
- common-size 2022/2023 (6 % points)
- 16 ratios × 2 exercices (31 asserts)
- SIG cascade complète (2 × 11 valeurs)
- CAF soustractive = CAF additive (invariant)
- Dividendes reconstitués par variation CP
- Bilan fonctionnel condensé + retraité
- 6 invariants comptables (A=P, FRNG−BFR=TN, CB inchangé, EENE conservent BFR+TN)

### Étape 2 — Montrer le rapport HTML

```bash
python -m scripts.generer_rapports
start reports/Societe_X_2023.html
```

Montrer :
- Le waterfall SIG en SVG (du CA 4,23 M au RN 949 k).
- Le tableau des 16 ratios avec feux tricolores.
- Le bilan fonctionnel comparé (sans/avec retraitement).
- Le commentaire rédigé qui pointe :
  - Forces : marge nette 22,4 %, ROE 31,8 %.
  - Risques : liquidité immédiate 0,11, DN/EBITDA 2,45, situation 2.

### Étape 3 — Montrer le Streamlit

```bash
streamlit run app.py
```

Dans le navigateur :
- Sélectionner 2022 puis 2023, voir la dégradation.
- Onglet Ratios : feux rouges apparaissent sur la liquidité immédiate.
- Onglet SIG & CAF : la concordance CAF sous/add = 0 TND.
- Onglet Bilan fonctionnel : le passage situation 1 → situation 2.

---

## 4. Résultats — Corrigés reproduits (2 min)

Montrer le tableau comparatif :

| Mesure | Corrigé PDF | Calculé | Écart |
|---|---:|---:|---:|
| **C1 ch.1 — Common-size 2023** | | | |
| Actifs non courants / total | 79,3 % | 79,3 % | 0 % |
| Capitaux propres / total | 37,5 % | 37,5 % | 0 % |
| **C2 ch.1 — Ratios 2023** | | | |
| Liquidité générale | 1,28 | 1,28 | 0,00 |
| Endettement global | 1,67 | 1,67 | 0,00 |
| DN/EBITDA | 2,45 | 2,45 | 0,00 |
| ROE | 31,8 % | 31,8 % | 0,0 % |
| DSO | 62 j | 62 j | 0 j |
| **C1 ch.2 — SIG 2023** | | | |
| Valeur ajoutée | 2 448 503 | 2 448 503 | 0 |
| EBE | 1 628 256 | 1 628 256 | 0 |
| **C2 ch.2 — CAF 2023** | | | |
| CAF soustractive | 1 212 789 | 1 212 789 | 0 |
| CAF additive | 1 212 789 | 1 212 789 | 0 |
| Cap. remboursement | 3,40 ans | 3,40 ans | 0,00 |
| **C3 ch.2 — Dividendes** | | | |
| Dividendes 2023 | 661 826 | 661 826 | 0 |
| Autofinancement | 550 963 | 550 963 | 0 |
| **C4 ch.2 — Bilan fonctionnel 2023** | | | |
| FRNG | 401 275 | 401 275 | 0 |
| BFR | 704 315 | 704 315 | 0 |
| TN | −303 040 | −303 040 | 0 |

### Diagnostic Société X en 30 secondes

> *L'entreprise est rentable et solvable, mais sa liquidité est devenue
> faible. Un programme d'investissement de 4,46 M TND a été financé à
> 60 % par emprunt et le solde en vidant la trésorerie, alors que 78 %
> du résultat 2022 était distribué en dividendes. Un crédit additionnel
> à court terme est envisageable sous conditions : limitation des
> dividendes, suivi trimestriel de la trésorerie.*

Ce diagnostic est **calculé**, pas généré : chaque phrase du commentaire
est un template avec des nombres lus dans le pivot.

---

## 5. Limites, hypothèses et pistes (1 min)

### Hypothèses signalées (annexes absentes du PDF)

1. **Annexe 2 ch.1** (format YAML des ratios) : format proposé.
2. **Annexe ch.2** (règles de reclassement) : format proposé.
3. **Corrigé C5** (bilan fonctionnel retraité) : recalculé rigoureusement
   depuis les données de la partie B. Documenté dans
   `docs/GUIDE_COMPREHENSION.md`.

### Pertinence du benchmark pour une PME tunisienne

Le CSV synthétique de repli mixe Damodaran (US) et BACH (zone euro).
**Comparer une PME tunisienne à ces médianes est à relativiser** :
- Coût du capital local supérieur (BCT à 8 %) → gearing plus élevé
  mécaniquement normal.
- Secteur « services » Damodaran = sociétés cotées, pas PME.
- Pays et taille à corriger (par ex. appliquer un z sectoriel + un
  ajustement pays).

### Limites identifiées

- **Adaptateurs supplémentaires** (Monoprix PDF, EDGAR 10-K, format CSV
  long IFRS) : la structure est prête (dossier `adapters/`, pattern
  Strategy), les implémentations concrètes pour B, C, D, E sont des
  prochaines étapes.
- **Visualisation ch.2** : waterfall SIG en place ; Sankey (ressources →
  emplois) à développer avec plotly.
- **Benchmark temps réel** : le client SEC EDGAR Frames est implémenté
  et testé ; le branchement sur un code SIC spécifique en live reste
  à démontrer en démo.

---

## 6. Questions probables du jury

### Q1 : Pourquoi Pydantic v2 et pas une dataclass ?

**R** : La validation est stricte à l'ingestion (`extra="forbid"` → une
faute de frappe dans un libellé source lève une erreur immédiate), la
sérialisation YAML/JSON est native (`.model_dump()`, `.model_validate()`),
et les messages d'erreur citent exactement le champ fautif — précieux
quand on jongle avec 60+ champs.

### Q2 : Comment garantissez-vous qu'un ratio ajouté dans le YAML ne casse rien ?

**R** : Trois protections :
1. L'AST n'autorise qu'un sous-ensemble sûr : `BinOp`, `UnaryOp`, `Name`,
   `Constant`, `Call` restreint à `abs/min/max`.
2. Les garde-fous (division par zéro, CP négatifs, stocks nuls) renvoient
   `None` + une note, pas d'exception.
3. Les tests pytest sont paramétrés : si j'ajoute un ratio, je couvre
   immédiatement les deux exercices de la Société X.

### Q3 : Pourquoi reconstituer les dividendes et pas les lire ?

**R** : Les dividendes ne figurent pas au bilan ni à l'état de résultat :
ils sont dans la note d'affectation du résultat. Les reconstituer par
variation des CP est la **méthode comptable rigoureuse** (identité
`CP_n = CP_(n-1) + RN_(n-1) − dividendes_n`, sous hypothèse d'absence
d'augmentation de capital). C'est exactement ce que fait le corrigé C3.

### Q4 : Pourquoi 365 jours ch.1 et 360 jours ch.2 ?

**R** : C'est la convention du cours. Le ch.1 raisonne en durée calendaire
(DSO = combien de jours en moyenne mes clients me doivent de l'argent), le
ch.2 en jours commerciaux (base 360 pour les grandeurs fonctionnelles,
cohérent avec les conventions bancaires et BACH). Le code applique
strictement la convention de chaque chapitre.

### Q5 : Qu'est-ce qui vous protège contre un adaptateur buggé ?

**R** : Trois couches :
1. **Contrôles qualité** : équation `A=P`, sous-totaux, signes. Un
   adaptateur qui se trompe produit un bloquant visible.
2. **Invariants comptables en pytest** : FRNG − BFR = TN, CAF sous = CAF
   add, crédit-bail laisse FRNG constant. Ce sont des **tests oracles**
   qui ne dépendent pas des données.
3. **Lineage** : chaque masse fonctionnelle conserve la liste des postes
   sources et retraitements. En cas de doute, on remonte le fil.

### Q6 : Comment le projet évolue pour les 4 entreprises non fournies ?

**R** : Le pattern Strategy des adaptateurs rend l'ajout mécanique :
- **B (Monoprix)** : les PDF annuels BVMT sont dans `_base_v1/tests/data/` ;
  réutiliser l'extraction PDF existante (OCR + pdfplumber), puis un
  adaptateur similaire à `sce_excel.py` avec conversion milliers → unités.
- **C (industrie IFRS)** : charger un 20-F de la SEC, parser le format
  « long » (une ligne par poste XBRL).
- **D (EDGAR)** : utiliser l'API companyfacts (déjà dans `benchmark.py`
  pour les frames), dédupliquer les faits par date d'end et prendre le
  dernier 10-K, convertir USD → TND.
- **E (CP négatifs)** : WeWork ou Peloton (si années en lignes dispos).
- Chaque adaptateur produit la même liste d'`EtatsFinanciers`, donc la
  suite du pipeline est inchangée.

### Q7 : Et si on activait le LLM ?

**R** : Au lot 6 optionnel. Le gabarit Jinja2 actuel serait complété par
un commentaire narratif court (3 phrases). **Garde-fou obligatoire** :
une fonction qui extrait tous les nombres du texte généré et vérifie
qu'ils figurent dans le pivot. Un nombre non trouvé → le commentaire
LLM est rejeté et on retombe sur le template déterministe. Zéro
hallucination tolérée.

### Q8 : Comment ce projet pourrait servir à une vraie banque ?

**R** : Le pipeline tel qu'il est produit en < 1 seconde par exercice
un rapport HTML avec feux, radar, commentaire, et les grandeurs
fonctionnelles. Pour une banque, les étapes suivantes seraient :
1. **Scoring bancaire** : un score global par famille (déjà en partie
   dans `commentaire.py`), ensuite calibré sur un historique de défauts.
2. **Benchmark local** : construire un fichier sectoriel à partir des
   états financiers BVMT (public, PDF), stocké en cache.
3. **Flux de trésorerie prévisionnel** : prolonger au chapitre 3 (hors
   périmètre ici).
