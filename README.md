# Analyse Financière — Master Data Science

Mini-projets 1 & 2 du cours **Analyse financière** (Master Data Science) :

- **FinRatio Engine** (chapitre 1) — ingestion d'états financiers hétérogènes,
  schéma pivot, moteur de ratios déclaratif, benchmark sectoriel par API.
- **FuncBalance** (chapitre 2) — bilan fonctionnel (FRNG, BFR, TN), SIG, CAF,
  retraitements, typologie des 6 situations.

Référentiel comptable principal : **SCE tunisien**. L'IFRS et l'US GAAP (via SEC
EDGAR / XBRL) sont traduits vers le même pivot.

## Périmètre

Les PDF du cours (dans `docs/`) font foi en cas de doute. Les corrigés des parties C
servent de jeux de test de référence.

Hors périmètre : banques et assurances (structure de bilan différente).

## Installation

Python **3.11+**.

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancement des tests

```bash
# Windows
.\.venv\Scripts\python.exe -m pytest -v

# Unix
./.venv/bin/python -m pytest -v
```

Pour sauter les tests qui dépendent du réseau (API SEC EDGAR, FMP…) ou qui sont lents :

```bash
pytest -v -m "not real and not network and not ocr"
```

## Structure du dépôt (en cours de construction)

```
analyse_financiere/     # paquet Python (créé au lot 1)
config/                 # YAML déclaratifs (ratios, reclassement, mapping)
data/
  ch1/                  # états financiers (Société X + 4 entreprises réelles à venir)
  ch2/                  # paramètres de retraitement
  SOURCES.md            # provenance de chaque fichier téléchargé
docs/
  Chapitre_1_*.pdf      # fiche de cours ch.1
  Chapitre_2_*.pdf      # fiche de cours ch.2
  journal.md            # décisions, hypothèses, écarts
tests/                  # jeux de test = corrigés C1 à C5
_base_v1/               # ancien projet BilanLens — lecture seule, non distribué
```

## Conventions

- Ratios du chapitre 1 : base **365 jours** (DSO, DPO, DIO).
- Grandeurs du chapitre 2 en jours de CA : base **360 jours** (FRNG, BFR, TN).
- Pas de poste inventé : un champ absent est marqué « non calculable ».

## Licence

MIT.
