"""Benchmark reel via SEC EDGAR Frames API.

Construit la distribution empirique de ratios cles (ROA, ROE, marge
nette, autonomie financiere, liquidite generale, liquidite reduite)
pour les societes US ayant depose un formulaire **10-K** pour l'exercice
fiscal donne. Produit un fichier CSV `data/ch1/benchmark_edgar_frames_YYYY.csv`
au meme format que le fichier synthetique de repli.

Sources : https://data.sec.gov/api/xbrl/frames/us-gaap/{concept}/USD/CYyyyy{...}.json
Concepts utilises (bilan = instant Q4, resultat/flux = annee entiere) :
- Assets (instant Q4) : total actif
- StockholdersEquity (instant Q4) : capitaux propres
- AssetsCurrent (instant Q4) : actifs courants (pour liquidite generale)
- LiabilitiesCurrent (instant Q4) : passifs courants
- InventoryNet (instant Q4) : stocks (pour liquidite reduite)
- RevenueFromContractWithCustomerExcludingAssessedTax (flux annuel) :
  chiffre d'affaires (balise ASC 606, la plus largement adoptee par les
  10-K modernes ; `Revenues` est l'ancien tag et ne couvre plus que ~6
  societes depuis 2019).
- NetIncomeLoss (flux annuel) : resultat net

**Provenance des valeurs** : la Frames API ne porte pas de champ `form` et
retourne UNE valeur par CIK (celle du dernier filing). Un bilan au 31/12
peut etre declare via :

- un 10-K (depot annuel) — majorite des cas pour exercices calendaires ;
- un 10-K/A (amendement d'un 10-K) qui corrige l'original ;
- un 10-Q posterieur qui presente le 31/12 comme comparatif N-1.

Pour le benchmark, c'est la **valeur au 31/12** qui compte, pas la forme du
depot : les trois cas ci-dessus citent le meme bilan annuel audite. Pour
isoler les seules societes a exercice calendaire, on filtre les frames sur
`end == YYYY-12-31` (les societes a exercice decale, ex. AAR CORP cloturant
au 31 mai, sont exclues).

Le test `tests/test_benchmark_edgar.py::test_echantillon_depot_10k`
echantillonne 10 CIK et confirme via l'API /submissions/ que la forme du
depot est bien dans {10-K, 10-K/A, 10-Q} (donc un depot SEC regulaire).

Avertissement : la population EDGAR est US et biaisee par les small caps
deficitaires (ROA median 2023 proche de 0 %). Pour une PME tunisienne,
ces medianes sont indicatives. Aucun filtre sectoriel SIC applique ici.
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


def _filtrer_fin_annee_civile(brut: list[dict], annee: int) -> list[dict]:
    """Garde uniquement les entrees dont `end` == 'YYYY-12-31' (exercice calendaire).

    Les societes a exercice fiscal decale (ex. AAR CORP cloturant au 31 mai)
    peuvent apparaitre dans la frame CY2023Q4I avec un 10-Q de novembre. En
    filtrant sur end=YYYY-12-31, on ne garde que les societes dont l'exercice
    coincide avec l'annee civile, qui deposent necessairement un 10-K pour
    cette date (par definition SEC).
    """
    cible = f"{annee}-12-31"
    return [d for d in brut if d.get("end") == cible]


FORMES_REGULIERES = {"10-K", "10-K/A", "10-Q", "10-Q/A"}


def forme_depot(cik: int, accn: str, user_agent: str) -> Optional[str]:
    """Retourne la forme (10-K, 10-Q, 8-K...) du depot `accn` pour la societe
    identifiee par `cik`. None si non trouvee dans les 1000 depots recents.
    """
    import time
    import requests

    cik_str = f"{int(cik):010d}"
    url = f"https://data.sec.gov/submissions/CIK{cik_str}.json"
    time.sleep(0.15)
    resp = requests.get(url, headers={"User-Agent": user_agent}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    recents = data.get("filings", {}).get("recent", {})
    for a, f in zip(recents.get("accessionNumber", []), recents.get("form", [])):
        if a == accn:
            return f
    return None


def verifier_depot_10k(cik: int, accn: str, user_agent: str) -> bool:
    """True si la forme du depot est dans FORMES_REGULIERES (10-K, 10-K/A,
    10-Q, 10-Q/A). Voir forme_depot() pour la forme exacte."""
    forme = forme_depot(cik, accn, user_agent)
    return forme in FORMES_REGULIERES


def construire_benchmark_edgar(
    annee: int,
    cache_dir: str | Path,
    seuil_minimal_societes: int = 100,
) -> RatiosEdgar:
    """Fetch les concepts XBRL necessaires et retourne les distributions des ratios.

    Si moins de `seuil_minimal_societes` societes ont des donnees croisees
    coherentes pour l'un des ratios, leve une RuntimeError plutot que
    renvoyer un benchmark non fiable.
    """
    cache_dir = Path(cache_dir)

    assets = charger_edgar_frames("Assets", annee, nature="instant", cache_dir=cache_dir)
    equity = charger_edgar_frames("StockholdersEquity", annee, nature="instant", cache_dir=cache_dir)
    ac = charger_edgar_frames("AssetsCurrent", annee, nature="instant", cache_dir=cache_dir)
    lc = charger_edgar_frames("LiabilitiesCurrent", annee, nature="instant", cache_dir=cache_dir)
    inv = charger_edgar_frames("InventoryNet", annee, nature="instant", cache_dir=cache_dir)
    revenus = charger_edgar_frames(
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        annee, nature="flux", cache_dir=cache_dir,
    )
    rn = charger_edgar_frames("NetIncomeLoss", annee, nature="flux", cache_dir=cache_dir)

    # Filtrer les societes a exercice calendaire (end=YYYY-12-31) : par
    # construction, un bilan a cette date provient d'un 10-K annuel.
    assets = _filtrer_fin_annee_civile(assets, annee)
    equity = _filtrer_fin_annee_civile(equity, annee)
    ac = _filtrer_fin_annee_civile(ac, annee)
    lc = _filtrer_fin_annee_civile(lc, annee)
    inv = _filtrer_fin_annee_civile(inv, annee)
    revenus = _filtrer_fin_annee_civile(revenus, annee)
    rn = _filtrer_fin_annee_civile(rn, annee)

    a = {d["cik"]: d["val"] for d in assets if d.get("val")}
    e = {d["cik"]: d["val"] for d in equity if d.get("val")}
    ac_m = {d["cik"]: d["val"] for d in ac if d.get("val")}
    lc_m = {d["cik"]: d["val"] for d in lc if d.get("val")}
    inv_m = {d["cik"]: d["val"] for d in inv if d.get("val")}
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

    # Autonomie = Equity / Total actif (Equity > 0, Assets > 0)
    communs_auto = [c for c in e if c in a and a[c] > 0 and e[c] > 0]
    autonomies = [e[c] / a[c] for c in communs_auto]

    # Liquidite generale = AC / LC
    communs_lg = [c for c in ac_m if c in lc_m and lc_m[c] > 0]
    liq_gen = [ac_m[c] / lc_m[c] for c in communs_lg]

    # Liquidite reduite = (AC - stocks) / LC. Si pas d'inventaire, on garde 0.
    liq_red = [
        (ac_m[c] - inv_m.get(c, 0)) / lc_m[c]
        for c in communs_lg if lc_m[c] > 0
    ]

    distributions = {
        "roa": distribution_sectorielle(roas),
        "roe": distribution_sectorielle(roes),
        "marge_nette": distribution_sectorielle(marges),
        "autonomie_financiere": distribution_sectorielle(autonomies),
        "liquidite_generale": distribution_sectorielle(liq_gen),
        "liquidite_reduite": distribution_sectorielle(liq_red),
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
