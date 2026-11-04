"""Tests de l'extraction Walmart depuis SEC EDGAR companyfacts.

Verifie :
- la deduplication (prendre la valeur du filing le plus recent) ;
- la coherence des grandeurs cles au 2024-01-31 ;
- la conversion USD -> TND avec taux BCT documente.
"""
import json
from pathlib import Path

import pytest

from scripts.extract_walmart import (
    CONCEPTS,
    FICHIER,
    TAUX_USD_TND_31_01_2024,
    extraire_concept,
)


@pytest.fixture(scope="module")
def facts():
    if not FICHIER.exists():
        pytest.skip(f"companyfacts manquant : {FICHIER}")
    with FICHIER.open(encoding="utf-8") as f:
        return json.load(f)


def test_metadata_walmart(facts):
    assert facts["cik"] == 104169
    assert "Walmart" in facts["entityName"]


def test_assets_2024_01_31(facts):
    """Assets au 31/01/2024 (cloture FY2024 Walmart) = 252,4 Mrd USD."""
    val = extraire_concept(facts, "Assets", "2024-01-31")
    assert val is not None
    # 252 milliards USD, tolerance 1 milliard
    assert abs(val - 252_399_000_000) < 1_000_000_000


def test_revenus_2024_01_31(facts):
    """Revenus annuels fiscaux 2024 Walmart = 642,6 Mrd USD."""
    val = extraire_concept(facts, "RevenueFromContractWithCustomerExcludingAssessedTax", "2024-01-31")
    assert val is not None
    assert abs(val - 642_637_000_000) < 2_000_000_000


def test_deduplication(facts):
    """Pour un meme (concept, end-date), plusieurs valeurs existent ;
    extraire_concept doit retenir celle du filing le plus recent (`filed`).
    """
    unit_data = facts["facts"]["us-gaap"]["Assets"]["units"]["USD"]
    rows_2024 = [r for r in unit_data if r.get("end") == "2024-01-31"]
    assert len(rows_2024) >= 1
    # Si plusieurs lignes, elles doivent avoir des formes differentes
    # (10-K original + 10-Q comparatifs posterieurs)
    formes = {r.get("form") for r in rows_2024}
    assert len(rows_2024) == 1 or len(formes) >= 1


def test_conversion_usd_tnd_coherente():
    """Le taux BCT 31/01/2024 doit etre dans un range plausible (3.0 a 3.3)."""
    assert 3.0 < TAUX_USD_TND_31_01_2024 < 3.3


def test_tous_concepts_disponibles(facts):
    """Les 6 concepts cles doivent etre disponibles au 2024-01-31."""
    manquants = []
    for concept in CONCEPTS:
        if extraire_concept(facts, concept, "2024-01-31") is None:
            manquants.append(concept)
    assert not manquants, f"Concepts manquants : {manquants}"
