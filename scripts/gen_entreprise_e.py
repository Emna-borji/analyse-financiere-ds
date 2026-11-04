"""Genere `data/ch1/Entreprise_E_Services_annees_en_lignes.xlsx`.

Ce fichier teste l'adaptateur "annees en lignes" sur une societe de
services avec capitaux propres NEGATIFS a partir de 2022. Il inclut des
defauts volontaires conformes aux consignes du cours :

- 2020 : `actif_total` manquant (NaN) -> le controle qualite doit renvoyer
  'Bloquant'.
- 2021 : desequilibre A/P de 10 TND (sous le seuil 1 %, tolerable mais
  bien detecte par le controle).
- 2022-2023 : capitaux propres negatifs (-100 puis -1 150) -> garde-fou
  ROE / autonomie / gearing en 'non significatif'.

Usage :
    python -m scripts.gen_entreprise_e

Les nouvelles valeurs numeriques peuvent etre ajustees dans ce fichier.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


RACINE = Path(__file__).resolve().parent.parent

# Donnees synthetiques (en milliers, mais l'adaptateur lira comme "unite"
# faute d'une colonne devise/unite explicite — ce fichier teste bien ce cas).
LIGNES = [
    # 2020 : actif_total MANQUANT (NaN) -> declenche 'Bloquant' au controle
    {
        "Annee": 2020,
        "Revenus": 5000,
        "Achats approvisionnements consommes": -500,
        "Autres charges d'exploitation": -1500,
        "Charges de personnel": -2000,
        "Dotations aux provisions et aux amortissements": -400,
        "Resultat d'exploitation": 600,
        "Charges financieres nettes": -80,
        "Impot sur les benefices": -120,
        "Resultat net de l'exercice": 400,
        "Immobilisations corporelles": 2000,
        "Autres actifs non courants": 100,
        "Total des actifs non courants": 2100,
        "Stocks": 0,
        "Clients et comptes rattaches": 1200,
        "Autres actifs courants": 300,
        "Liquidites et equivalents de liquidites": 500,
        "Total des actifs courants": 2000,
        "Total des actifs": None,  # NaN volontaire -> controle 'Bloquant'
        "Capital social": 1000,
        "Reserves": 200,
        "Resultats reportes": 300,
        "Total des capitaux propres avant affectation": 1500,
        "Emprunts": 1800,
        "Total des passifs non courants": 1800,
        "Fournisseurs et comptes rattaches": 600,
        "Autres passifs courants": 100,
        "Concours bancaires et autres passifs financiers": 100,
        "Total des passifs courants": 800,
        "Total des passifs": 2600,
        "Total des capitaux propres et passifs": 4100,
    },
    # 2021 : desequilibre A/P = 10 (A=4300, P=4310) -> sous seuil 1%
    {
        "Annee": 2021,
        "Revenus": 5500,
        "Achats approvisionnements consommes": -600,
        "Autres charges d'exploitation": -1600,
        "Charges de personnel": -2100,
        "Dotations aux provisions et aux amortissements": -450,
        "Resultat d'exploitation": 750,
        "Charges financieres nettes": -100,
        "Impot sur les benefices": -150,
        "Resultat net de l'exercice": 500,
        "Immobilisations corporelles": 1900,
        "Autres actifs non courants": 150,
        "Total des actifs non courants": 2050,
        "Stocks": 0,
        "Clients et comptes rattaches": 1300,
        "Autres actifs courants": 350,
        "Liquidites et equivalents de liquidites": 600,
        "Total des actifs courants": 2250,
        "Total des actifs": 4300,  # <- 10 TND de difference avec passif
        "Capital social": 1000,
        "Reserves": 200,
        "Resultats reportes": 300,
        "Total des capitaux propres avant affectation": 1500,
        "Emprunts": 1900,
        "Total des passifs non courants": 1900,
        "Fournisseurs et comptes rattaches": 650,
        "Autres passifs courants": 150,
        "Concours bancaires et autres passifs financiers": 110,
        "Total des passifs courants": 910,
        "Total des passifs": 2810,
        "Total des capitaux propres et passifs": 4310,  # desequilibre 10
    },
    # 2022 : capitaux propres NEGATIFS (-100)
    {
        "Annee": 2022,
        "Revenus": 6000,
        "Achats approvisionnements consommes": -700,
        "Autres charges d'exploitation": -1800,
        "Charges de personnel": -2400,
        "Dotations aux provisions et aux amortissements": -500,
        "Resultat d'exploitation": 600,
        "Charges financieres nettes": -500,
        "Impot sur les benefices": -200,
        "Resultat net de l'exercice": -100,
        "Immobilisations corporelles": 1700,
        "Autres actifs non courants": 100,
        "Total des actifs non courants": 1800,
        "Stocks": 0,
        "Clients et comptes rattaches": 1100,
        "Autres actifs courants": 400,
        "Liquidites et equivalents de liquidites": 200,
        "Total des actifs courants": 1700,
        "Total des actifs": 3500,
        "Capital social": 1000,
        "Reserves": 0,
        "Resultats reportes": -1100,
        "Total des capitaux propres avant affectation": -100,
        "Emprunts": 2200,
        "Total des passifs non courants": 2200,
        "Fournisseurs et comptes rattaches": 700,
        "Autres passifs courants": 400,
        "Concours bancaires et autres passifs financiers": 300,
        "Total des passifs courants": 1400,
        "Total des passifs": 3600,
        "Total des capitaux propres et passifs": 3500,
    },
    # 2023 : capitaux propres TRES NEGATIFS (-1 150)
    {
        "Annee": 2023,
        "Revenus": 6200,
        "Achats approvisionnements consommes": -800,
        "Autres charges d'exploitation": -2000,
        "Charges de personnel": -2800,
        "Dotations aux provisions et aux amortissements": -550,
        "Resultat d'exploitation": 50,
        "Charges financieres nettes": -900,
        "Impot sur les benefices": -100,
        "Resultat net de l'exercice": -1050,
        "Immobilisations corporelles": 1500,
        "Autres actifs non courants": 50,
        "Total des actifs non courants": 1550,
        "Stocks": 0,
        "Clients et comptes rattaches": 1000,
        "Autres actifs courants": 450,
        "Liquidites et equivalents de liquidites": 50,
        "Total des actifs courants": 1500,
        "Total des actifs": 3050,
        "Capital social": 1000,
        "Reserves": 0,
        "Resultats reportes": -2150,
        "Total des capitaux propres avant affectation": -1150,
        "Emprunts": 2800,
        "Total des passifs non courants": 2800,
        "Fournisseurs et comptes rattaches": 750,
        "Autres passifs courants": 450,
        "Concours bancaires et autres passifs financiers": 200,
        "Total des passifs courants": 1400,
        "Total des passifs": 4200,
        "Total des capitaux propres et passifs": 3050,
    },
]


def main() -> Path:
    df = pd.DataFrame(LIGNES)
    chemin = RACINE / "data" / "ch1" / "Entreprise_E_Services_annees_en_lignes.xlsx"
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(chemin, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="bilan", index=False)
    print(f"OK : {chemin} ecrit ({len(df)} lignes).")
    return chemin


if __name__ == "__main__":
    main()
