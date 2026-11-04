"""Tests du module scoring (score par famille + global + radar)."""
from pathlib import Path

import pytest

from analyse_financiere.adapters.sce_excel import charger_societe_x
from analyse_financiere.benchmark import charger_benchmark_csv
from analyse_financiere.ratios import calculer_ratios
from analyse_financiere.scoring import (
    FAMILLES_DEFAUT,
    PONDERATIONS_DEFAUT,
    calculer_score,
    donnees_radar,
)


RACINE = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def benchmark_edgar():
    return charger_benchmark_csv(
        RACINE / "data" / "ch1" / "benchmark_edgar_frames_2023.csv"
    )


@pytest.fixture(scope="module")
def ratios_societe_x_2023():
    etats = charger_societe_x(
        RACINE / "data" / "ch1" / "CAS_1_Societe_X_SCE_2023_2022.xlsx",
        RACINE / "data" / "ch2" / "societe_x_retraitements.yaml",
    )
    e2023 = [e for e in etats if e.annee == 2023][0]
    return {r.id: r.valeur for r in calculer_ratios(
        e2023, RACINE / "config" / "ratios.yaml",
    )}


def test_ponderations_somme_1():
    """La somme des ponderations par defaut doit valoir exactement 1.0."""
    assert abs(sum(PONDERATIONS_DEFAUT.values()) - 1.0) < 1e-9


def test_familles_couvrent_6_ratios_cles():
    """Les 3 familles couvrent 6 ratios du benchmark EDGAR."""
    tous = [r for ratios in FAMILLES_DEFAUT.values() for r in ratios]
    attendus = {
        "roa", "roe", "marge_nette",
        "autonomie_financiere",
        "liquidite_generale", "liquidite_reduite",
    }
    assert set(tous) == attendus


def test_ponderation_incoherente_leve_erreur(benchmark_edgar, ratios_societe_x_2023):
    """Une ponderation qui ne somme pas a 1.0 doit lever ValueError."""
    with pytest.raises(ValueError, match="sommer a 1"):
        calculer_score(
            ratios_societe_x_2023, benchmark_edgar,
            "SocieteX", 2023,
            ponderations={"rentabilite": 0.5, "solvabilite": 0.3, "liquidite": 0.3},
        )


def test_score_societe_x_2023(benchmark_edgar, ratios_societe_x_2023):
    """Societe X 2023 a un ROA = 11,9 % (centile >90 vs EDGAR).
    Son score rentabilite doit etre eleve (> 70/100)."""
    score = calculer_score(
        ratios_societe_x_2023, benchmark_edgar, "Societe_X", 2023,
    )
    rentabilite = [f for f in score.familles if f.nom == "rentabilite"][0]
    assert rentabilite.score_0_100 is not None
    assert rentabilite.score_0_100 > 70, (
        f"Score rentabilite Societe X 2023 = {rentabilite.score_0_100:.1f}, "
        f"attendu > 70"
    )


def test_score_global_dans_0_100(benchmark_edgar, ratios_societe_x_2023):
    """Le score global doit etre entre 0 et 100."""
    score = calculer_score(
        ratios_societe_x_2023, benchmark_edgar, "Societe_X", 2023,
    )
    assert score.score_global is not None
    assert 0 <= score.score_global <= 100


def test_donnees_radar(benchmark_edgar, ratios_societe_x_2023):
    """donnees_radar renvoie un dict axe->{score,ratios} utilisable pour plotly."""
    score = calculer_score(
        ratios_societe_x_2023, benchmark_edgar, "Societe_X", 2023,
    )
    radar = donnees_radar(score)
    assert set(radar.keys()) == {"rentabilite", "solvabilite", "liquidite"}
    for axe, data in radar.items():
        assert "score" in data
        assert "ratios" in data
        assert 0 <= data["score"] <= 100


def test_ratios_manquants_absents_du_benchmark(benchmark_edgar):
    """Si un ratio existe en pivot mais pas dans le benchmark, il est
    liste dans ratios_benchmark_manquants."""
    ratios_calcules = {"roa": 0.1, "dso": 50, "endettement": 0.4}
    score = calculer_score(
        ratios_calcules, benchmark_edgar, "Test", 2023,
        familles={"activite": ["dso", "endettement", "roa"]},
        ponderations={"activite": 1.0},
    )
    # dso et endettement ne sont PAS dans le CSV EDGAR
    assert "dso" in score.ratios_benchmark_manquants
    assert "endettement" in score.ratios_benchmark_manquants
    assert "roa" not in score.ratios_benchmark_manquants
