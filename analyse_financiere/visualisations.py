"""Visualisations et exports (ch.1 + ch.2 lot 7).

- export CSV du lineage de chaque masse fonctionnelle ;
- plafonnement ("capping") des ratios pour les visualisations ;
- donnees pour heatmap centiles (ratios x exercices) ;
- donnees pour evolution temporelle (CA/FRNG/BFR/TN) ;
- donnees pour Sankey (postes sources -> masses fonctionnelles).

Les fonctions retournent des structures (DataFrame, dict Plotly) plutot
que de rendre directement, pour rester testables sans navigateur.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

import pandas as pd

from .benchmark import ReferenceRatio, rang_centile
from .reclassement import BilanFonctionnel


# =================================================================== lineage
def exporter_lineage_csv(
    bf: BilanFonctionnel,
    chemin: str | Path,
) -> Path:
    """Exporte le lineage du bilan fonctionnel en CSV.

    Une ligne par (masse, poste_source) avec montant et retraitement associe.
    Utile pour auditer d'ou vient chaque chiffre dans une masse fonctionnelle.
    """
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    lignes = []
    for nom_masse in [
        "emplois_stables", "ressources_stables",
        "actif_circulant_exploitation", "actif_circulant_hors_exploitation",
        "passif_circulant_exploitation", "passif_circulant_hors_exploitation",
        "tresorerie_active", "tresorerie_passive",
    ]:
        masse = getattr(bf, nom_masse)
        for l in masse.lignes:
            lignes.append({
                "annee": bf.annee,
                "masse": nom_masse,
                "poste_source": l.poste_source,
                "montant": l.montant,
                "retraitement": l.retraitement or "",
            })
    with chemin.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["annee", "masse", "poste_source", "montant", "retraitement"],
        )
        writer.writeheader()
        writer.writerows(lignes)
    return chemin


# =============================================================== capping
# Bornes raisonnables pour la restitution des ratios. Au-dela, un ratio
# devient aberrant (effet d'une tres faible denominateur) : on l'affiche
# cappee avec un suffixe "+" ou "-".
BORNES_RATIOS = {
    "roe": (-5.0, 5.0),           # -500% a +500%
    "roa": (-2.0, 2.0),           # -200% a +200%
    "marge_nette": (-2.0, 2.0),
    "gearing": (-10.0, 10.0),
    "autonomie_financiere": (-2.0, 2.0),
    "liquidite_generale": (0.0, 20.0),
    "liquidite_reduite": (0.0, 20.0),
    "endettement": (0.0, 10.0),
    "dso": (0.0, 365.0),
    "dio": (0.0, 365.0),
    "dpo": (0.0, 365.0),
}


def capper(id_ratio: str, valeur: float) -> tuple[float, bool]:
    """Plafonne une valeur de ratio aux bornes definies.

    Retourne (valeur_cappee, cappe). Si cappe=True, la valeur originale
    etait en dehors des bornes.
    """
    if valeur is None:
        return (None, False)
    if id_ratio not in BORNES_RATIOS:
        return (valeur, False)
    lo, hi = BORNES_RATIOS[id_ratio]
    if valeur < lo:
        return (lo, True)
    if valeur > hi:
        return (hi, True)
    return (valeur, False)


# =================================================================== heatmap
def donnees_heatmap_centiles(
    ratios_par_annee: dict[int, dict[str, float]],
    benchmark: dict[tuple[str, str], ReferenceRatio],
    secteur: str = "US_toutes_societes",
) -> pd.DataFrame:
    """Prepare la matrice (ratio x annee) de centiles pour une heatmap.

    Chaque cellule = rang_centile de la valeur dans la distribution de
    reference. NaN si le ratio est manquant ou absent du benchmark.
    """
    annees = sorted(ratios_par_annee)
    ids = set()
    for v in ratios_par_annee.values():
        ids.update(v.keys())
    ids = sorted(ids)
    matrice = []
    for rid in ids:
        ligne = {"ratio": rid}
        for an in annees:
            v = ratios_par_annee[an].get(rid)
            ref = benchmark.get((secteur, rid))
            if v is None or ref is None:
                ligne[str(an)] = None
            else:
                ligne[str(an)] = rang_centile(v, ref)
        matrice.append(ligne)
    return pd.DataFrame(matrice).set_index("ratio")


# ========================================================= time evolution
def donnees_evolution_temporelle(
    etats_par_annee: dict[int, "EtatsFinanciers"],
    bilans_par_annee: dict[int, BilanFonctionnel],
) -> pd.DataFrame:
    """Serie temporelle des grandeurs cles (CA, FRNG, BFR, TN) par exercice."""
    annees = sorted(etats_par_annee)
    rows = []
    for an in annees:
        e = etats_par_annee[an]
        bf = bilans_par_annee.get(an)
        row = {"annee": an, "ca": e.ca, "resultat_net": e.resultat_net}
        if bf is not None:
            row.update({
                "frng": bf.frng,
                "bfr": bf.bfr,
                "tn": bf.tn,
            })
        rows.append(row)
    return pd.DataFrame(rows).set_index("annee")


# ==================================================================== Sankey
def donnees_sankey(bf: BilanFonctionnel) -> dict:
    """Prepare les donnees pour un Sankey Plotly : postes sources -> masses.

    Renvoie {nodes: [labels], links: [{source, target, value}]}.
    """
    nodes: list[str] = []
    def idx(label: str) -> int:
        if label not in nodes:
            nodes.append(label)
        return nodes.index(label)

    links: list[dict] = []
    for nom_masse in [
        "emplois_stables", "ressources_stables",
        "actif_circulant_exploitation", "actif_circulant_hors_exploitation",
        "passif_circulant_exploitation", "passif_circulant_hors_exploitation",
        "tresorerie_active", "tresorerie_passive",
    ]:
        masse = getattr(bf, nom_masse)
        idx_masse = idx(nom_masse)
        for l in masse.lignes:
            links.append({
                "source": idx(l.poste_source),
                "target": idx_masse,
                "value": abs(l.montant),
            })
    return {"nodes": nodes, "links": links}
