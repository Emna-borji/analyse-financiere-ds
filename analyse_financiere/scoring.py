"""Score par famille + score global pondere + radar (ch.1 lot 5 etendu).

Pour chaque ratio calcule, on obtient son centile dans le benchmark EDGAR.
On normalise en score 0-100 selon le sens favorable (plus_haut ou plus_bas),
on moyenne par famille, puis on pondere pour un score global.

Familles et ponderations (defaut pour PME tunisienne / distribution) :
- Rentabilite  : 40% (ROA, ROE, marge nette)
- Solvabilite  : 30% (autonomie financiere)
- Liquidite    : 30% (liquidite generale, liquidite reduite)

Justification des ponderations :
  La rentabilite pilote la valeur long-terme (Damodaran, "The Dark Side of
  Valuation"), d'ou son poids superieur. Solvabilite et liquidite sont
  equivalentes car elles couvrent respectivement le long et le court terme
  du risque de faillite.

Les ponderations sont parametrables via l'argument `ponderations` pour
permettre de les ajuster par secteur (ex. plus de liquidite pour la
distribution ou la restauration, plus de solvabilite pour l'industrie
lourde).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .benchmark import ReferenceRatio, rang_centile


# ------- Table des familles et des sens favorables (depuis config/ratios.yaml)
FAMILLES_DEFAUT = {
    "rentabilite": ["roa", "roe", "marge_nette"],
    "solvabilite": ["autonomie_financiere"],
    "liquidite": ["liquidite_generale", "liquidite_reduite"],
}

PONDERATIONS_DEFAUT = {
    "rentabilite": 0.40,
    "solvabilite": 0.30,
    "liquidite": 0.30,
}

# Sens favorable des ratios. "plus_haut" = valeur elevee est bonne.
SENS_FAVORABLE = {
    "roa": "plus_haut",
    "roe": "plus_haut",
    "marge_nette": "plus_haut",
    "autonomie_financiere": "plus_haut",
    "liquidite_generale": "plus_haut",
    "liquidite_reduite": "plus_haut",
    "endettement": "plus_bas",
    "gearing": "plus_bas",
    "dso": "plus_bas",
    "dio": "plus_bas",
    "dpo": "plus_haut",  # delai fournisseurs long = favorable (gain BFR)
}


@dataclass
class ScoreRatio:
    """Score d'un ratio individuel."""
    id: str
    valeur: Optional[float]
    centile: Optional[float]
    score_0_100: Optional[float]  # 0=mauvais, 100=excellent


@dataclass
class ScoreFamille:
    """Score d'une famille de ratios."""
    nom: str
    ratios: list[ScoreRatio] = field(default_factory=list)
    score_0_100: Optional[float] = None


@dataclass
class ScoreGlobal:
    """Score global pondere."""
    entreprise: str
    annee: int
    familles: list[ScoreFamille] = field(default_factory=list)
    ponderations: dict[str, float] = field(default_factory=dict)
    score_global: Optional[float] = None
    ratios_benchmark_manquants: list[str] = field(default_factory=list)


def _score_depuis_centile(centile: float, sens: str) -> float:
    """Converti un centile (0-99) en score (0-100) selon le sens favorable."""
    if sens == "plus_haut":
        return float(centile)
    if sens == "plus_bas":
        return 100.0 - float(centile)
    return 50.0  # neutre


def calculer_score(
    ratios_calcules: dict[str, float],
    benchmark: dict[tuple[str, str], ReferenceRatio],
    entreprise: str,
    annee: int,
    secteur: str = "US_toutes_societes",
    familles: dict[str, list[str]] = None,
    ponderations: dict[str, float] = None,
) -> ScoreGlobal:
    """Calcule le score detaille d'une entreprise par rapport a un benchmark.

    - `ratios_calcules` : {id_ratio: valeur} issu de `calculer_ratios()`.
    - `benchmark` : {(secteur, ratio): ReferenceRatio} issu de
      `charger_benchmark_csv()`.
    - `familles` et `ponderations` : permettent de surcharger les defauts.
    """
    familles = familles or FAMILLES_DEFAUT
    ponderations = ponderations or PONDERATIONS_DEFAUT

    if abs(sum(ponderations.values()) - 1.0) > 1e-6:
        raise ValueError(
            f"Les ponderations doivent sommer a 1.0, obtenu "
            f"{sum(ponderations.values())}"
        )

    score = ScoreGlobal(entreprise=entreprise, annee=annee, ponderations=ponderations)
    ratios_benchmark_manquants: list[str] = []

    for nom_famille, ratios_famille in familles.items():
        sf = ScoreFamille(nom=nom_famille)
        scores_valides = []
        for rid in ratios_famille:
            v = ratios_calcules.get(rid)
            if v is None:
                sf.ratios.append(ScoreRatio(id=rid, valeur=None, centile=None, score_0_100=None))
                continue
            ref = benchmark.get((secteur, rid))
            if ref is None:
                ratios_benchmark_manquants.append(rid)
                sf.ratios.append(ScoreRatio(id=rid, valeur=v, centile=None, score_0_100=None))
                continue
            centile = rang_centile(v, ref)
            sens = SENS_FAVORABLE.get(rid, "neutre")
            s = _score_depuis_centile(centile, sens)
            sf.ratios.append(ScoreRatio(id=rid, valeur=v, centile=centile, score_0_100=s))
            scores_valides.append(s)
        if scores_valides:
            sf.score_0_100 = sum(scores_valides) / len(scores_valides)
        score.familles.append(sf)

    # Score global pondere : moyenne des scores familiaux, uniquement
    # pour les familles avec au moins un ratio valide.
    numer = 0.0
    denom = 0.0
    for sf in score.familles:
        if sf.score_0_100 is not None:
            poids = ponderations.get(sf.nom, 0.0)
            numer += sf.score_0_100 * poids
            denom += poids
    if denom > 0:
        score.score_global = numer / denom

    score.ratios_benchmark_manquants = sorted(set(ratios_benchmark_manquants))
    return score


def donnees_radar(score: ScoreGlobal) -> dict[str, dict]:
    """Prepare les donnees pour un graphique radar.

    Renvoie {axe: score_0_100} pour chaque famille, utilisable directement
    dans matplotlib polaire ou plotly scatterpolar.
    """
    return {
        sf.nom: {
            "score": sf.score_0_100 if sf.score_0_100 is not None else 0.0,
            "ratios": {r.id: r.score_0_100 for r in sf.ratios},
        }
        for sf in score.familles
    }
