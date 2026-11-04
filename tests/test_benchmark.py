"""Tests du module benchmark (ch.1 lot 5)."""
from pathlib import Path

from analyse_financiere.benchmark import (
    ReferenceRatio,
    charger_benchmark_csv,
    distribution_sectorielle,
    feu_benchmark,
    rang_centile,
    z_robuste,
)


RACINE = Path(__file__).resolve().parent.parent


def test_charger_benchmark_csv():
    ref = charger_benchmark_csv(RACINE / "data" / "ch1" / "benchmark_sectoriel_synthetique.csv")
    # Trois secteurs couverts : Services, Distribution, Industrie
    secteurs = {k[0] for k in ref}
    assert {"Services", "Distribution", "Industrie"} <= secteurs
    # Au moins quelques ratios clés par secteur
    assert ("Services", "marge_nette") in ref
    assert ("Distribution", "dio") in ref


def test_rang_centile_mediane():
    ref = ReferenceRatio("Services", "marge_nette", 0.05, 0.12, 0.22, "test")
    # Médiane → centile 50
    assert rang_centile(0.12, ref) == 50


def test_rang_centile_bornes():
    ref = ReferenceRatio("Services", "marge_nette", 0.05, 0.12, 0.22, "test")
    assert rang_centile(0.05, ref) == 25
    assert rang_centile(0.22, ref) == 75
    # Au-delà de Q3 → > 75
    assert rang_centile(0.35, ref) > 75


def test_z_robuste():
    ref = ReferenceRatio("Services", "marge_nette", 0.05, 0.12, 0.22, "test")
    # À la médiane → z = 0
    assert z_robuste(0.12, ref) == 0
    # Au-dessus de la médiane → z > 0
    assert z_robuste(0.30, ref) > 0


def test_feu_benchmark_plus_haut():
    ref = ReferenceRatio("Services", "marge_nette", 0.05, 0.12, 0.22, "test")
    assert feu_benchmark(0.30, ref, "plus_haut") == "vert"  # au-dessus de Q3
    assert feu_benchmark(0.10, ref, "plus_haut") == "orange"  # entre Q1 et Q3
    assert feu_benchmark(0.02, ref, "plus_haut") == "rouge"  # sous Q1


def test_feu_benchmark_plus_bas():
    ref = ReferenceRatio("Services", "dso", 30, 55, 90, "test")
    assert feu_benchmark(20, ref, "plus_bas") == "vert"  # sous Q1
    assert feu_benchmark(60, ref, "plus_bas") == "orange"
    assert feu_benchmark(120, ref, "plus_bas") == "rouge"


def test_societe_x_vs_benchmark_services():
    """La Société X (services) a une marge nette excellente vs le benchmark."""
    ref = charger_benchmark_csv(RACINE / "data" / "ch1" / "benchmark_sectoriel_synthetique.csv")
    ref_marge = ref[("Services", "marge_nette")]
    # Marge nette Société X 2023 = 22,4 %
    assert feu_benchmark(0.224, ref_marge, "plus_haut") == "vert"


def test_distribution_sectorielle():
    valeurs = [0.05, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30]
    d = distribution_sectorielle(valeurs)
    assert d["mediane"] == 0.15
    assert d["n"] == 7
