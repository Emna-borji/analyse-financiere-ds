"""Tests des visualisations (ch.1 + ch.2 lot 7)."""
from pathlib import Path

import pandas as pd
import pytest

from analyse_financiere.adapters.sce_excel import charger_societe_x
from analyse_financiere.benchmark import charger_benchmark_csv
from analyse_financiere.ratios import calculer_ratios
from analyse_financiere.reclassement import construire_bilan_fonctionnel
from analyse_financiere.visualisations import (
    BORNES_RATIOS,
    capper,
    donnees_evolution_temporelle,
    donnees_heatmap_centiles,
    donnees_sankey,
    exporter_lineage_csv,
)


RACINE = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def etats_par_annee():
    return {
        e.annee: e for e in charger_societe_x(
            RACINE / "data" / "ch1" / "CAS_1_Societe_X_SCE_2023_2022.xlsx",
            RACINE / "data" / "ch2" / "societe_x_retraitements.yaml",
        )
    }


@pytest.fixture(scope="module")
def bilans_par_annee(etats_par_annee):
    return {
        an: construire_bilan_fonctionnel(
            e, RACINE / "config" / "reclassement.yaml", avec_retraitements=True,
        )
        for an, e in etats_par_annee.items()
    }


def test_capping_roe_tres_grand():
    """Un ROE de 1000% doit etre cappe a 500%."""
    v, cappe = capper("roe", 10.0)
    assert cappe is True
    assert v == 5.0


def test_capping_ratio_normal_inchange():
    """Un ROE normal (12%) ne doit pas etre cappe."""
    v, cappe = capper("roe", 0.12)
    assert cappe is False
    assert v == 0.12


def test_capping_ratio_sans_bornes_inchange():
    """Un ratio non present dans BORNES_RATIOS n'est pas cappe."""
    v, cappe = capper("ratio_inconnu", 999.0)
    assert cappe is False
    assert v == 999.0


def test_capping_valeur_none():
    """Capper None retourne (None, False)."""
    v, cappe = capper("roe", None)
    assert v is None
    assert cappe is False


def test_bornes_coherentes():
    """Chaque borne (lo, hi) doit verifier lo < hi."""
    for rid, (lo, hi) in BORNES_RATIOS.items():
        assert lo < hi, f"Bornes incoherentes pour {rid} : lo={lo}, hi={hi}"


def test_exporter_lineage_csv(bilans_par_annee, tmp_path):
    """Export CSV du lineage pour Societe X 2023."""
    bf = bilans_par_annee[2023]
    chemin = tmp_path / "lineage.csv"
    exporter_lineage_csv(bf, chemin)
    assert chemin.exists()
    df = pd.read_csv(chemin)
    # Doit contenir les 8 masses et les lignes sources
    assert set(df.columns) == {"annee", "masse", "poste_source", "montant", "retraitement"}
    assert len(df) > 10  # au moins 10 lignes lineage
    assert df["annee"].unique().tolist() == [2023]
    # Au moins les 4 grandes masses
    masses = set(df["masse"])
    assert "emplois_stables" in masses
    assert "ressources_stables" in masses
    # Au moins un retraitement credit-bail documente
    retraitements = set(df["retraitement"].dropna())
    assert any("credit_bail" in r for r in retraitements if r), (
        f"Retraitements : {retraitements}"
    )


def test_donnees_heatmap_centiles(etats_par_annee):
    """Heatmap : matrice ratio x annee avec centiles 0-100."""
    bench = charger_benchmark_csv(
        RACINE / "data" / "ch1" / "benchmark_edgar_frames_2023.csv"
    )
    ratios_par_annee = {}
    for an, e in etats_par_annee.items():
        ratios_par_annee[an] = {
            r.id: r.valeur for r in calculer_ratios(e, RACINE / "config" / "ratios.yaml")
        }
    df = donnees_heatmap_centiles(ratios_par_annee, bench)
    assert not df.empty
    # Pour les ratios du benchmark, les centiles doivent etre entre 0 et 100
    for col in df.columns:
        vals = df[col].dropna()
        for v in vals:
            assert 0 <= v <= 100, f"Centile hors bornes : {v}"


def test_donnees_evolution_temporelle(etats_par_annee, bilans_par_annee):
    """Evolution temporelle : DataFrame avec CA/FRNG/BFR/TN par annee."""
    df = donnees_evolution_temporelle(etats_par_annee, bilans_par_annee)
    assert "ca" in df.columns
    assert "frng" in df.columns
    assert "bfr" in df.columns
    assert "tn" in df.columns
    assert len(df) == 2  # 2022 et 2023


def test_donnees_sankey(bilans_par_annee):
    """Sankey : noeuds + liens positifs."""
    bf = bilans_par_annee[2023]
    s = donnees_sankey(bf)
    assert "nodes" in s and "links" in s
    assert len(s["nodes"]) > 0
    assert all(l["value"] >= 0 for l in s["links"]), "Toutes les valeurs doivent etre positives"
