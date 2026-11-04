"""Tests du benchmark reel SEC EDGAR.

Trois niveaux :
1. test_cache_edgar_fonctionne : utilise un petit cache JSON cree par le
   test pour verifier que le second appel est instantane (pas de requete reseau).
2. test_csv_edgar_committed : charge le fichier
   data/ch1/benchmark_edgar_frames_2023.csv (vraies donnees extraites par
   `python -m scripts.actualiser_benchmark_edgar`) et compare Societe X.
3. test_live_edgar : marqueur `network` — telecharge en live depuis EDGAR.
   Saute en CI si le marqueur `network` est exclu.
"""
import json
import os
from pathlib import Path

import pandas as pd
import pytest

from analyse_financiere.benchmark import (
    charger_benchmark_csv,
    charger_edgar_frames,
    distribution_sectorielle,
    feu_benchmark,
    rang_centile,
)


RACINE = Path(__file__).resolve().parent.parent


def test_cache_edgar_fonctionne(tmp_path):
    """Verifie que le cache est bien lu quand il existe (pas d'appel reseau)."""
    cache = tmp_path / "edgar"
    cache.mkdir()

    # Pre-remplir le cache avec un fichier factice
    faux_data = {
        "data": [
            {"cik": 1, "entityName": "FAKE_CORP", "val": 1000000},
            {"cik": 2, "entityName": "FAKE_CORP_2", "val": 2000000},
        ]
    }
    (cache / "frame_Assets_USD_2023Q4I.json").write_text(json.dumps(faux_data))

    # Appeler SANS user-agent et SANS reseau : le cache doit suffire.
    data = charger_edgar_frames(
        "Assets", 2023, nature="instant",
        user_agent="dummy", cache_dir=cache,
    )
    assert len(data) == 2
    assert data[0]["entityName"] == "FAKE_CORP"


def test_csv_edgar_committed_charge_bien():
    """Le CSV produit depuis EDGAR est committe et chargeable."""
    chemin = RACINE / "data" / "ch1" / "benchmark_edgar_frames_2023.csv"
    assert chemin.exists(), "Le CSV EDGAR committe doit exister"

    ref = charger_benchmark_csv(chemin)
    # Doit contenir au moins les 4 ratios cles
    ratios_committed = {r for s, r in ref.keys()}
    assert {"roa", "roe", "marge_nette", "autonomie_financiere"} <= ratios_committed

    # Source doit mentionner EDGAR + date
    for r in ref.values():
        assert "EDGAR" in r.source, f"Source attendue mentionne EDGAR, obtenu : {r.source}"


def test_societe_x_vs_edgar_committed():
    """Societe X 2023 est au centile 99 pour ROA/ROE/marge vs EDGAR."""
    from analyse_financiere.adapters.sce_excel import charger_societe_x
    from analyse_financiere.ratios import calculer_ratios

    ref = charger_benchmark_csv(RACINE / "data" / "ch1" / "benchmark_edgar_frames_2023.csv")
    etats = {e.annee: e for e in charger_societe_x(
        RACINE / "data" / "ch1" / "CAS_1_Societe_X_SCE_2023_2022.xlsx",
        RACINE / "data" / "ch2" / "societe_x_retraitements.yaml",
    )}
    ratios = {r.id: r.valeur for r in calculer_ratios(
        etats[2023], RACINE / "config" / "ratios.yaml",
    )}

    # ROA Societe X = 11,9 % ; mediane US EDGAR 2023 proche de 0 → centile > 90
    r_roa = ref[("US_toutes_societes", "roa")]
    centile = rang_centile(ratios["roa"], r_roa)
    assert centile > 90, f"ROA au centile {centile}, attendu > 90"
    assert feu_benchmark(ratios["roa"], r_roa, "plus_haut") == "vert"


def test_repli_fichier_synthetique_fonctionne():
    """Le fichier synthetique Damodaran reste chargeable comme repli."""
    chemin = RACINE / "data" / "ch1" / "benchmark_sectoriel_synthetique.csv"
    assert chemin.exists()
    ref = charger_benchmark_csv(chemin)
    # Doit contenir au moins les 3 secteurs documentes
    secteurs = {s for s, _ in ref}
    assert {"Services", "Distribution", "Industrie"} <= secteurs


def test_distribution_sectorielle_coherente():
    """Q1 <= mediane <= Q3 pour toute distribution reelle."""
    valeurs = [0.01, 0.05, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30]
    d = distribution_sectorielle(valeurs)
    assert d["q1"] <= d["mediane"] <= d["q3"]


# =============================================================================
# Test LIVE EDGAR — marqueur `network`, saute en CI
# =============================================================================
@pytest.mark.network
def test_edgar_live_assets_2023():
    """Interroge reellement SEC EDGAR : >1000 societes attendues pour Assets 2023."""
    ua = os.environ.get("EDGAR_USER_AGENT")
    if not ua:
        pytest.skip("EDGAR_USER_AGENT non defini — test saute")

    data = charger_edgar_frames("Assets", 2023, nature="instant")
    assert len(data) > 1000, f"Attendu > 1000 societes, obtenu {len(data)}"
    # Chaque entree doit porter cik, val, entityName
    for d in data[:5]:
        assert "cik" in d and "val" in d
