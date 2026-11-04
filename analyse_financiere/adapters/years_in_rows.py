"""Adaptateur « années en lignes » — Entreprise E.

Format : première colonne = année, les autres = postes comptables.
Exemple de source : certaines publications simplifiées de sociétés de
services où l'historique sur 4-5 ans est présenté en tableau horizontal.

Difficultés gérées :
- charges en négatif (dans ce format, les charges sont des flux de signe −),
- valeurs manquantes (cellule vide → poste « non calculable »),
- déséquilibre A/P volontaire (test des contrôles qualité),
- capitaux propres négatifs (test de garde-fou des ratios).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from ..pivot import EtatsFinanciers
from .sce_excel import MAPPING_SCE, _normaliser


def charger_annees_en_lignes(
    chemin_excel: str | Path,
    entreprise: str,
    secteur: str = "Services",
    devise: str = "TND",
    unite: str = "millier",
) -> list[EtatsFinanciers]:
    """Charge un Excel au format années en lignes et renvoie un EtatsFinanciers par exercice."""
    chemin = Path(chemin_excel)
    df = pd.read_excel(chemin)

    # La première colonne doit être l'année
    col_annee = df.columns[0]

    # Construire un index libellé normalisé → nom de colonne
    cols_normalisees = {_normaliser(c): c for c in df.columns if c != col_annee}

    etats: list[EtatsFinanciers] = []
    for _, row in df.iterrows():
        annee = int(row[col_annee])
        kwargs: dict = {
            "entreprise": entreprise,
            "secteur": secteur,
            "annee": annee,
            "devise": devise,
            "unite": unite,
            "referentiel": "SCE",
            "source": chemin.name,
        }

        for libelle_norm, (champ, convention) in MAPPING_SCE.items():
            if libelle_norm in cols_normalisees:
                col = cols_normalisees[libelle_norm]
                val = row[col]
                if pd.isna(val):
                    continue
                v = float(val)
                kwargs[champ] = abs(v) if convention == "abs" else v

        etats.append(EtatsFinanciers(**kwargs))

    return etats
