"""Benchmark sectoriel (ch.1 lot 5).

Deux sources :
1. Fichier de repli synthétique construit à partir de Damodaran Online
   (médianes sectorielles) et BACH (Banque de France). C'est le mode par
   défaut, hors ligne.
2. SEC EDGAR Frames API (optionnel, avec User-Agent descriptif et cache
   local). Construit la distribution d'un concept XBRL pour toutes les
   sociétés d'un code SIC à une date donnée.

Indicateurs produits :
- rang centile (position de l'entreprise dans la distribution),
- z robuste (basé sur médiane et MAD, résistant aux outliers),
- feu tricolore (vert / orange / rouge selon le sens favorable du ratio).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


RACINE = Path(__file__).resolve().parent.parent


# ------------------------------------------------- FICHIER DE REPLI CSV ----
@dataclass
class ReferenceRatio:
    secteur: str
    ratio: str
    q1: float
    mediane: float
    q3: float
    source: str


def charger_benchmark_csv(chemin: str | Path) -> dict[tuple[str, str], ReferenceRatio]:
    """Charge le CSV synthétique en dict {(secteur, ratio): ReferenceRatio}."""
    df = pd.read_csv(chemin)
    ref = {}
    for _, row in df.iterrows():
        r = ReferenceRatio(
            secteur=row["secteur"],
            ratio=row["ratio"],
            q1=float(row["q1"]),
            mediane=float(row["mediane"]),
            q3=float(row["q3"]),
            source=row["source"],
        )
        ref[(r.secteur, r.ratio)] = r
    return ref


# ------------------------------------------------ CALCULS STATISTIQUES ----
def rang_centile(valeur: float, ref: ReferenceRatio) -> float:
    """Approxime le rang centile par interpolation linéaire entre Q1, médiane, Q3.

    Pour une estimation plus fine, il faudrait la distribution complète.
    Avec seulement Q1, médiane, Q3, on approxime linéairement.
    """
    if valeur <= ref.q1:
        # Entre 0 et Q1 : on ne sait pas combien bas, on renvoie au plus 25
        return max(0, 25 * valeur / ref.q1) if ref.q1 else 0
    if valeur <= ref.mediane:
        return 25 + 25 * (valeur - ref.q1) / (ref.mediane - ref.q1)
    if valeur <= ref.q3:
        return 50 + 25 * (valeur - ref.mediane) / (ref.q3 - ref.mediane)
    # Au-delà de Q3 : on prolonge, borné à 99
    ecart = ref.q3 - ref.mediane
    if not ecart:
        return 99
    return min(99, 75 + 25 * (valeur - ref.q3) / ecart)


def z_robuste(valeur: float, ref: ReferenceRatio) -> float:
    """Z robuste basé sur la médiane et l'IQR (≈ 1.35 × MAD pour une loi normale)."""
    iqr = ref.q3 - ref.q1
    if iqr == 0:
        return 0
    # Facteur 0.7413 ≈ 1 / 1.35 pour rendre l'IQR comparable à l'écart-type
    return (valeur - ref.mediane) / (iqr * 0.7413)


def feu_benchmark(
    valeur: float, ref: ReferenceRatio, sens_favorable: str,
) -> str:
    """Feu tricolore par comparaison à la médiane et aux quartiles.

    Convention : pour un ratio 'plus_haut est meilleur', dépasser Q3 est
    vert, être sous Q1 est rouge. Inversement pour 'plus_bas'.
    """
    if sens_favorable == "plus_haut":
        if valeur >= ref.q3:
            return "vert"
        if valeur >= ref.q1:
            return "orange"
        return "rouge"
    if sens_favorable == "plus_bas":
        if valeur <= ref.q1:
            return "vert"
        if valeur <= ref.q3:
            return "orange"
        return "rouge"
    return "gris"


# --------------------------------------------- SEC EDGAR Frames API ----
_ENDPOINT_FRAMES = "https://data.sec.gov/api/xbrl/frames/us-gaap/{concept}/{unit}/CY{annee}Q4I.json"


def charger_edgar_frames(
    concept: str,
    annee: int,
    unit: str = "USD",
    user_agent: Optional[str] = None,
    cache_dir: Optional[str | Path] = None,
) -> list[dict]:
    """Télécharge une 'frame' SEC EDGAR : un concept XBRL pour toutes les sociétés.

    Exemples de concepts : 'Assets', 'Revenues', 'NetIncomeLoss'.
    L'URL est l'endpoint 'frames' du module data.sec.gov. User-Agent
    descriptif OBLIGATOIRE (sinon la SEC bloque).

    Cache : si `cache_dir` est fourni, la réponse est écrite / lue sur disque.
    Respect du débit : la SEC limite à 10 req/s. On temporise 0,15 s.
    """
    import requests

    ua = user_agent or os.environ.get("EDGAR_USER_AGENT")
    if not ua:
        raise RuntimeError(
            "EDGAR requiert un User-Agent descriptif. Renseignez-le "
            "dans l'environnement (variable EDGAR_USER_AGENT)."
        )
    url = _ENDPOINT_FRAMES.format(concept=concept, unit=unit, annee=annee)

    if cache_dir:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache = cache_dir / f"frame_{concept}_{unit}_{annee}.json"
        if cache.exists():
            with cache.open(encoding="utf-8") as f:
                return json.load(f).get("data", [])

    time.sleep(0.15)  # politique anti-DDoS
    resp = requests.get(url, headers={"User-Agent": ua}, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if cache_dir:
        cache.write_text(json.dumps(data), encoding="utf-8")

    return data.get("data", [])


def distribution_sectorielle(
    valeurs: list[float],
) -> dict[str, float]:
    """Calcule Q1, médiane, Q3 d'une distribution empirique."""
    if not valeurs:
        return {}
    s = pd.Series(valeurs).dropna()
    return {
        "q1": float(s.quantile(0.25)),
        "mediane": float(s.quantile(0.5)),
        "q3": float(s.quantile(0.75)),
        "n": int(len(s)),
    }
