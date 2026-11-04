"""Fixtures partagées."""
from pathlib import Path

import pytest

from analyse_financiere.adapters.sce_excel import charger_societe_x


RACINE = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def etats_societe_x():
    """Les deux exercices de la Société X, chargés avec retraitements."""
    etats = charger_societe_x(
        RACINE / "data" / "ch1" / "CAS_1_Societe_X_SCE_2023_2022.xlsx",
        RACINE / "data" / "ch2" / "societe_x_retraitements.yaml",
    )
    return {e.annee: e for e in etats}


@pytest.fixture(scope="session")
def ratios_yaml():
    return RACINE / "config" / "ratios.yaml"


@pytest.fixture(scope="session")
def reclassement_yaml():
    return RACINE / "config" / "reclassement.yaml"
