"""Tests du module scripts.monoprix_typologie.

Verifie :
- les 4 exercices (2021-2024) renvoient une situation typologique classee ;
- l'identite comptable FRNG = BFR + TN est respectee a 1 TND pres pour
  chaque exercice ;
- la situation trouvee est bien la situation 5 (Desequilibre grave) pour
  les 4 annees.
"""
from pathlib import Path

import pytest

from scripts.monoprix_typologie import (
    PDFS_PAR_DEFAUT,
    calculer_monoprix_typologie,
)


@pytest.fixture(scope="module")
def resultats():
    for p in PDFS_PAR_DEFAUT:
        if not Path(p).exists():
            pytest.skip(f"PDF Monoprix absent : {p}")
    return {r.annee: r for r in calculer_monoprix_typologie()}


def test_quatre_exercices(resultats):
    """Les 4 exercices 2021-2024 sont couverts."""
    assert set(resultats.keys()) == {2021, 2022, 2023, 2024}


@pytest.mark.parametrize("annee", [2021, 2022, 2023, 2024])
def test_identite_frng_bfr_tn(resultats, annee):
    """Invariant FRNG - BFR - TN = 0 (tolerance 2 TND, cf. test_monoprix_adapter.py).

    Les sources PDF publiees en TND arrondies au dinar accumulent jusqu'a
    2 TND d'ecart lors du calcul par agregation.
    """
    r = resultats[annee]
    assert abs(r.frng - r.bfr - r.tn) <= 2, (
        f"{annee}: FRNG={r.frng:.2f} BFR={r.bfr:.2f} TN={r.tn:.2f} "
        f"ecart={r.frng - r.bfr - r.tn:+.2f}"
    )


@pytest.mark.parametrize("annee", [2021, 2022, 2023, 2024])
def test_situation_classee(resultats, annee):
    """Chaque exercice a une situation non-nulle (classee)."""
    r = resultats[annee]
    assert r.situation.numero in {1, 2, 3, 4, 5, 6}, (
        f"{annee}: situation non classee {r.situation!r}"
    )


@pytest.mark.parametrize("annee", [2021, 2022, 2023, 2024])
def test_monoprix_situation_5(resultats, annee):
    """Monoprix 2021-2024 : triplet (-, -, -) -> situation 5 Desequilibre grave.

    FRNG negatif : le financement long terme ne couvre pas les immobilisations.
    BFR negatif : credit fournisseurs > stocks + clients (typique distrib).
    TN negative : la banque a court terme est aussi sollicitee.
    """
    r = resultats[annee]
    assert r.frng < 0, f"{annee}: FRNG attendu negatif, lu {r.frng:.0f}"
    assert r.bfr < 0, f"{annee}: BFR attendu negatif, lu {r.bfr:.0f}"
    assert r.tn < 0, f"{annee}: TN attendue negative, lue {r.tn:.0f}"
    assert r.situation.numero == 5


def test_evolution_frng_amelioration_2022_2024(resultats):
    """Entre 2022 et 2024, FRNG remonte (devient moins negatif)."""
    r2022 = resultats[2022]
    r2024 = resultats[2024]
    assert r2024.frng > r2022.frng, (
        f"FRNG 2022={r2022.frng:.0f} vs 2024={r2024.frng:.0f}"
    )


def test_evolution_tn_degradation_2022_2024(resultats):
    """Entre 2022 et 2024, TN se degrade (devient plus negative)."""
    r2022 = resultats[2022]
    r2024 = resultats[2024]
    assert r2024.tn < r2022.tn, (
        f"TN 2022={r2022.tn:.0f} vs 2024={r2024.tn:.0f}"
    )
