# Analyse financière — Master Data Science

Pipeline complet d'analyse financière automatisée, réunissant les deux mini-projets
du cours :

- **FinRatio Engine** (chapitre 1) — ingestion d'états financiers hétérogènes
  (SCE tunisien, IFRS, EDGAR/XBRL), schéma pivot, moteur de ratios déclaratif,
  benchmark sectoriel par API.
- **FuncBalance** (chapitre 2) — bilan fonctionnel (FRNG, BFR, TN), SIG, CAF,
  retraitements (crédit-bail, EENE), typologie des 6 situations.

Référentiel comptable principal : **SCE tunisien**. Les PDF du cours (dans
`docs/`) font foi en cas de doute ; les corrigés C1–C5 servent de jeux de test.

## Démo rapide (3 commandes)

```bash
# 1. Installation
python -m venv .venv
.venv\Scripts\activate       # Windows (PowerShell)
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt

# 2. Tous les tests (45 tests verts : corrigés C1-C5 + invariants comptables)
pytest -v

# 3. Rapport HTML + dashboard interactif
python -m scripts.generer_rapports            # génère reports/*.html
streamlit run app.py                           # dashboard interactif
```

## Ce que fait le projet

| Lot | Chapitre | Module | Testé contre |
|---|---|---|---|
| 1 | ch.1 | `pivot.py`, `adapters/sce_excel.py` | Chargement 3 feuilles SCE |
| 2 | ch.1 | `mapping.py` + `config/mapping_libelles.yaml` | Précision/rappel ≥ 80 % sur jeu annoté |
| 3 | ch.1 | `quality.py` | Équation A=P, sous-totaux, signes |
| 4 | ch.1 | `ratios.py` + `config/ratios.yaml` | **Corrigé C2 : 16 ratios × 2 exercices** |
| 5 | ch.1 | `benchmark.py` + CSV synthétique + SEC EDGAR | Centile, z robuste, feu tricolore |
| 6 | ch.1 | `commentaire.py` | Règles expertes + Jinja2 |
| 7 | ch.1 | `restitution.py` + `app.py` | Rapport HTML autonome + Streamlit |
| 1-2 | ch.2 | Pivot étendu + `reclassement.py` + YAML | **Corrigé C4 bilan fonctionnel** |
| 3 | ch.2 | `sig_caf.py` | **Corrigés C1 SIG + C2 CAF 2 méthodes** |
| 4 | ch.2 | `tests/test_invariants.py` | FRNG−BFR=TN, CAF concordance, CB laisse FRNG constant, EENE conservent BFR+TN |
| 5 | ch.2 | `restitution.py` | Waterfall SIG, tableau bilan fonctionnel |

## Conventions du cours (fixes, voir `CLAUDE.md`)

- Ratios ch.1 base **365 jours** (DSO, DPO, DIO).
- Grandeurs ch.2 en jours de CA base **360 jours** (FRNG, BFR, TN).
- DPO : base d'achats = (achats approvisionnements + autres charges d'exploitation) × 1,19 TVA.
- Pas de poste inventé : un champ absent est marqué « non calculable ».
- Pas de LLM par défaut. Options du cours (embeddings lot 2, LLM lot 6) non activées.

## Structure du dépôt

```
analyse_financiere/
  pivot.py                       # schéma Pydantic v2 (60+ champs ch.1+ch.2)
  adapters/
    sce_excel.py                 # SCE Tunisien 3 feuilles (Société X)
    # À venir : ifrs_long.py, edgar_facts.py, years_in_rows.py, sce_milliers.py
  quality.py                     # contrôles OK / Avertissement / Bloquant
  ratios.py                      # AST restreint pour évaluer les formules
  sig_caf.py                     # cascade SIG + CAF 2 méthodes
  reclassement.py                # bilan fonctionnel + retraitements + lineage
  typologie.py                   # 6 situations FRNG/BFR/TN
  mapping.py                     # YAML + regex + rapidfuzz (score ≥ 85)
  benchmark.py                   # centile + z robuste + SEC EDGAR frames
  commentaire.py                 # règles expertes + Jinja2
  restitution.py                 # rapport HTML autonome (SVG inline)

config/
  ratios.yaml                    # 16 ratios déclaratifs (formule + repère + garde-fous)
  reclassement.yaml              # règles de reclassement + retraitements
  mapping_libelles.yaml          # alias + regex SCE / IFRS / US GAAP

data/
  ch1/
    CAS_1_Societe_X_SCE_2023_2022.xlsx     # cas de référence du cours
    benchmark_sectoriel_synthetique.csv    # repli (Damodaran + BACH)
  ch2/
    societe_x_retraitements.yaml           # reconstitué depuis partie B ch.2
  SOURCES.md

docs/
  Chapitre_1_Etats_financiers_et_ratios.pdf
  Chapitre_2_Analyse_fonctionnelle.pdf
  journal.md                     # décisions + hypothèses signalées
  GUIDE_COMPREHENSION.md         # explication pédagogique de chaque lot
  PRESENTATION.md                # plan de soutenance 10 min

tests/                           # 45 tests pytest, tous verts
app.py                           # Dashboard Streamlit
scripts/generer_rapports.py      # Génération des rapports HTML en batch
```

## Exemples d'usage

### En Python (pipeline complet)

```python
from pathlib import Path
from analyse_financiere.adapters.sce_excel import charger_societe_x
from analyse_financiere.restitution import diagnostic_complet

etats = charger_societe_x(
    "data/ch1/CAS_1_Societe_X_SCE_2023_2022.xlsx",
    "data/ch2/societe_x_retraitements.yaml",
)
for e in etats:
    res = diagnostic_complet(
        e,
        "config/ratios.yaml",
        "config/reclassement.yaml",
        Path(f"reports/{e.entreprise}_{e.annee}.html"),
    )
    print(f"{e.annee}: Situation {res['situation'].numero} — {res['situation'].nom}")
```

### Benchmark (rang centile + feu)

```python
from analyse_financiere.benchmark import charger_benchmark_csv, rang_centile, feu_benchmark
ref = charger_benchmark_csv("data/ch1/benchmark_sectoriel_synthetique.csv")
r = ref[("Services", "marge_nette")]
print(rang_centile(0.224, r))                 # Société X 2023 : vers 75+
print(feu_benchmark(0.224, r, "plus_haut"))   # 'vert'
```

### SEC EDGAR (optionnel, nécessite User-Agent)

```python
import os
os.environ["EDGAR_USER_AGENT"] = "Analyse Financiere DS (ton.email@exemple.com)"
from analyse_financiere.benchmark import charger_edgar_frames, distribution_sectorielle
data = charger_edgar_frames("Revenues", 2023, cache_dir=".cache/edgar")
dist = distribution_sectorielle([d["val"] for d in data])
print(dist)  # Q1, médiane, Q3 des revenus 2023 pour toutes les sociétés 10-K
```

## Résultats sur la Société X

Tous les chiffres des corrigés C1 à C4 sont reproduits à l'unité près.
Le corrigé C5 (bilan fonctionnel retraité), absent du PDF, est recalculé
et documenté dans `docs/GUIDE_COMPREHENSION.md`.

**Diagnostic 2023** : Situation 2 (FRNG insuffisant). Marges exceptionnelles
(nette 22,4 %, EBE 38,5 %), mais DN/EBITDA passé de −0,22 à 2,45, trésorerie
immédiate à 0,11 et DPO allongé de 28 jours. L'entreprise finance un
programme d'investissement de 4,46 M TND à 60 % par emprunt, en distribuant
662 k TND de dividendes qui auraient permis de limiter le recours aux
concours bancaires.

## CI

GitHub Actions, Ubuntu + Python 3.11 : `pytest -m "not real and not network and not ocr"`.

## Documentation complète

- `docs/GUIDE_COMPREHENSION.md` — ce que fait chaque lot, chiffres Société X à l'appui.
- `docs/PRESENTATION.md` — plan de soutenance 10 min, démo pas-à-pas, questions probables + réponses.
- `CLAUDE.md` — contrat de travail et conventions du cours.
- `docs/journal.md` — décisions datées, hypothèses signalées.

## Licence

MIT.
