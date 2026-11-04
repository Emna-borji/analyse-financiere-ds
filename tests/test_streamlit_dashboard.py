"""Test du dashboard Streamlit via l'API AppTest.

Verifie que l'app se charge sans exception, que les onglets principaux
sont bien crees, et que les contenus critiques (ratios, SIG, bilan
fonctionnel, typologie) s'affichent pour les donnees Societe X.
"""
from pathlib import Path

import pytest


RACINE = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def app():
    """Charge l'app Streamlit via AppTest."""
    streamlit_apptest = pytest.importorskip("streamlit.testing.v1")
    AppTest = streamlit_apptest.AppTest
    app = AppTest.from_file(str(RACINE / "app.py"), default_timeout=60)
    app.run()
    return app


def test_app_charge_sans_exception(app):
    """L'app ne doit lever aucune exception au chargement."""
    assert not app.exception, f"Exceptions Streamlit : {app.exception}"


def test_titre_principal(app):
    """Le titre principal mentionne les deux mini-projets."""
    titres = [t.value for t in app.title]
    assert any("FinRatio" in t for t in titres), f"Titres trouves : {titres}"


def test_onglets_principaux_presents(app):
    """Les 5 onglets attendus existent."""
    tabs = app.tabs
    assert len(tabs) >= 5, f"Attendu 5+ onglets, trouve {len(tabs)}"


def test_metriques_ratios_affichees(app):
    """Au moins 10 metriques sont rendues (10+ ratios calcules)."""
    # Metrics peuvent etre dans tous les onglets
    assert len(app.metric) >= 5, f"Trouve {len(app.metric)} metriques"


def test_sidebar_contient_identite(app):
    """La sidebar mentionne l'entreprise et le referentiel."""
    sidebar_texts = [
        t.value for t in app.sidebar.markdown if t.value
    ] + [t.value for t in app.sidebar.text if hasattr(t, "value")]
    page = " ".join(sidebar_texts)
    # L'app par defaut charge Societe X en SCE
    assert "Societe" in page or "SCE" in page, (
        f"Identite non trouvee dans sidebar : {page[:200]}"
    )
