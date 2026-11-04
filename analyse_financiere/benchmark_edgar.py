"""Benchmark reel via SEC EDGAR Frames API.

Construit la distribution empirique de 4 ratios cles (ROA, ROE, marge
nette, autonomie financiere) pour toutes les societes US ayant depose
un 10-K pour l'exercice fiscal donne. Produit un fichier CSV
`data/ch1/benchmark_edgar_frames_YYYY.csv` au meme format que le fichier
synthetique de repli.

Sources : https://data.sec.gov/api/xbrl/frames/us-gaap/{concept}/USD/CYyyyy{...}.json
Concepts utilises :
- Assets (instant Q4) : total actif
- StockholdersEquity (instant Q4) : capitaux propres
- RevenueFromContractWithCustomerExcludingAssessedTax (flux annuel) :
  chiffre d'affaires (balise ASC 606, la plus largement adoptee par les
  10-K modernes ; `Revenues` est l'ancien tag et ne couvre plus que ~6
  societes depuis 2019).
- NetIncomeLoss (flux annuel) : resultat net

Avertissement : la population EDGAR est US et biaisee par les small caps
deficitaires (ROA median 2023 proche de 0 %). Pour une PME tunisienne,
ces medianes sont indicatives.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from .benchmark import charger_edgar_frames, distribution_sectorielle


@dataclass
class RatiosEdgar:
    """Structure portant les distributions des ratios EDGAR."""
    annee: int
    n_entreprises: int
    distributions: dict[str, dict[str, float]]  # ratio_id -> {q1, mediane, q3, n}


def construire_benchmark_edgar(
    annee: int,
    cache_dir: str | Path,
    seuil_minimal_societes: int = 100,
) -> RatiosEdgar:
    """Fetch les 4 frames et retourne les distributions des ratios.

    Si moins de `seuil_minimal_societes` societes ont des donnees croisees
    coherentes, leve une RuntimeError plutot que renvoyer un benchmark
    non fiable.
    """
    cache_dir = Path(cache_dir)

    assets = charger_edgar_frames("Assets", annee, nature="instant", cache_dir=cache_dir)
    equity = charger_edgar_frames("StockholdersEquity", annee, nature="instant", cache_dir=cache_dir)
    revenus = charger_edgar_frames(
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        annee, nature="flux", cache_dir=cache_dir,
    )
    rn = charger_edgar_frames("NetIncomeLoss", annee, nature="flux", cache_dir=cache_dir)

    a = {d["cik"]: d["val"] for d in assets if d.get("val")}
    e = {d["cik"]: d["val"] for d in equity if d.get("val")}
    r = {d["cik"]: d["val"] for d in revenus if d.get("val")}
    ni = {d["cik"]: d["val"] for d in rn if "val" in d}

    # ROA = NI / Assets (exige Assets > 0)
    communs_roa = [c for c in ni if c in a and a[c] > 0]
    roas = [ni[c] / a[c] for c in communs_roa]

    # ROE = NI / Equity (exige Equity > 0 : on exclut les CP negatifs du benchmark)
    communs_roe = [c for c in ni if c in e and e[c] > 0]
    roes = [ni[c] / e[c] for c in communs_roe]

    # Marge nette = NI / Revenus (exige Revenus > 0)
    communs_marge = [c for c in ni if c in r and r[c] > 0]
    marges = [ni[c] / r[c] for c in communs_marge]

    # Autonomie = Equity / Total passif = Equity / Assets (Equity > 0, Assets > 0)
    communs_auto = [c for c in e if c in a and a[c] > 0 and e[c] > 0]
    autonomies = [e[c] / a[c] for c in communs_auto]

    distributions = {
        "roa": distribution_sectorielle(roas),
        "roe": distribution_sectorielle(roes),
        "marge_nette": distribution_sectorielle(marges),
        "autonomie_financiere": distribution_sectorielle(autonomies),
    }

    n_min = min(d["n"] for d in distributions.values() if d)
    if n_min < seuil_minimal_societes:
        raise RuntimeError(
            f"Benchmark EDGAR non fiable : seulement {n_min} societes "
            f"sur un seuil requis de {seuil_minimal_societes}."
        )

    return RatiosEdgar(
        annee=annee,
        n_entreprises=n_min,
        distributions=distributions,
    )


def exporter_csv(bench: RatiosEdgar, chemin: str | Path, source_label: str) -> Path:
    """Exporte les distributions EDGAR au format CSV compatible charger_benchmark_csv.

    Le champ `secteur` prend la valeur 'US_toutes_societes' pour indiquer
    que la population est la totalite des societes US, sans filtre sectoriel.
    """
    lignes = []
    for ratio_id, dist in bench.distributions.items():
        if not dist:
            continue
        lignes.append({
            "secteur": "US_toutes_societes",
            "ratio": ratio_id,
            "q1": dist["q1"],
            "mediane": dist["mediane"],
            "q3": dist["q3"],
            "source": source_label,
        })
    df = pd.DataFrame(lignes)
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(chemin, index=False)
    return chemin


def comparer_societe_a_edgar(
    ratios_calcules: dict[str, float],
    bench: RatiosEdgar,
) -> dict[str, dict]:
    """Compare les ratios d'une entreprise aux distributions EDGAR.

    Retourne {ratio_id: {valeur, centile, z, feu}}. Un ratio non present
    dans le benchmark est omis.
    """
    from .benchmark import ReferenceRatio, feu_benchmark, rang_centile, z_robuste

    # Correspondance sens favorable (reprend la logique de config/ratios.yaml)
    sens = {
        "roa": "plus_haut", "roe": "plus_haut",
        "marge_nette": "plus_haut", "autonomie_financiere": "plus_haut",
    }

    comparaison = {}
    for rid, dist in bench.distributions.items():
        if rid not in ratios_calcules:
            continue
        v = ratios_calcules[rid]
        if v is None:
            continue
        ref = ReferenceRatio(
            secteur="US_toutes_societes", ratio=rid,
            q1=dist["q1"], mediane=dist["mediane"], q3=dist["q3"],
            source="EDGAR frames",
        )
        comparaison[rid] = {
            "valeur": v,
            "centile": rang_centile(v, ref),
            "z": z_robuste(v, ref),
            "feu": feu_benchmark(v, ref, sens.get(rid, "neutre")),
        }
    return comparaison
