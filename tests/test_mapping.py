"""Tests du mapper de libellés (ch.1 lot 2)."""
from pathlib import Path

import pytest

from analyse_financiere.mapping import MapperLibelles


RACINE = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def mapper():
    return MapperLibelles(RACINE / "config" / "mapping_libelles.yaml")


def test_alias_exact(mapper):
    r = mapper.mapper("Immobilisations corporelles")
    assert r.champ_pivot == "immobilisations_corporelles_brutes"
    assert r.methode == "alias"


def test_alias_insensible_accents(mapper):
    r = mapper.mapper("IMMOBILISATIONS CORPORELLES")
    assert r.champ_pivot == "immobilisations_corporelles_brutes"


def test_fuzzy(mapper):
    # Léger typo
    r = mapper.mapper("Immobilisation corporelle")
    assert r.champ_pivot == "immobilisations_corporelles_brutes"
    assert r.methode in ("fuzzy", "regex", "alias")


def test_regex(mapper):
    # Match par regex sur "property.*plant.*equipment"
    r = mapper.mapper("Property, Plant and Equipment, Net")
    assert r.champ_pivot == "immobilisations_corporelles_brutes"


def test_non_reconnu(mapper):
    r = mapper.mapper("Lorem ipsum dolor sit amet")
    assert r.champ_pivot is None
    assert r.methode == "aucun"


def test_precision_rappel(mapper):
    """Évalue le mapping sur un petit jeu annoté."""
    verite = {
        "Immobilisations corporelles": "immobilisations_corporelles_brutes",
        "Cash and cash equivalents": "liquidites",
        "Stocks": "stocks",
        "Fournisseurs et comptes rattachés": "fournisseurs",
        "Total des actifs courants": "actifs_courants",
        "Revenus": "ca",
        "Résultat d'exploitation": "ebit",
        "Total equity": "capitaux_propres",
        "Trade payables": "fournisseurs",
        "Net income": "resultat_net",
    }
    rapport = mapper.mapper_liste(list(verite.keys()))
    metriques = rapport.precision_rappel(verite)
    # On vise au moins 80 % en précision et rappel sur ce jeu simple.
    assert metriques["precision"] >= 0.8
    assert metriques["rappel"] >= 0.8
