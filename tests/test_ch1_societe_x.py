"""Tests du chapitre 1 sur la Société X : corrigés C1 (common-size) et C2 (ratios).

Les valeurs attendues sont copiées EXACTEMENT du corrigé (page 8 du PDF ch.1).
Tolérance : 1 unité pour les montants (arrondi d'affichage), 0,01 pour les
ratios, 0,2 point de pourcentage pour les parts common-size.
"""
import pytest

from analyse_financiere.ratios import calculer_ratios, common_size
from analyse_financiere.quality import controler, Niveau


# =============================================================================
# C1 — Lecture des états financiers (common-size)
# =============================================================================
@pytest.mark.parametrize("annee,attendus", [
    (2023, {
        "actifs_non_courants_pct": 0.793,
        "actifs_courants_pct": 0.207,
        "liquidites_pct": 0.017,
        "capitaux_propres_pct": 0.375,
        "passifs_non_courants_pct": 0.463,
        "passifs_courants_pct": 0.162,
    }),
    (2022, {
        "actifs_non_courants_pct": 0.472,
        "actifs_courants_pct": 0.528,
        "liquidites_pct": 0.329,
        "capitaux_propres_pct": 0.616,
        "passifs_non_courants_pct": 0.246,
        "passifs_courants_pct": 0.139,
    }),
])
def test_common_size_c1(etats_societe_x, annee, attendus):
    cs = common_size(etats_societe_x[annee])
    for cle, val in attendus.items():
        assert cs[cle] == pytest.approx(val, abs=0.002), f"{cle}@{annee}: attendu {val}, obtenu {cs[cle]}"


# =============================================================================
# C2 — Tableau des ratios
# =============================================================================
_RATIOS_ATTENDUS = {
    2023: {
        "liquidite_generale": 1.28,
        "liquidite_immediate": 0.11,
        "endettement_global": 1.67,
        "autonomie_financiere": 0.375,
        "gearing": 1.34,
        "dette_nette_ebitda": 2.45,
        "couverture_interets": 6.16,
        "marge_nette": 0.224,
        "marge_operationnelle": 0.323,
        "marge_ebitda": 0.385,
        "roe": 0.318,
        "roa": 0.119,
        "rotation_actif": 0.53,
        "dso": 62.0,
        "dpo": 65.0,
        "taux_effectif_impot": 0.180,
    },
    2022: {
        "liquidite_generale": 3.81,
        "liquidite_immediate": 2.37,
        "endettement_global": 0.62,
        "autonomie_financiere": 0.616,
        "gearing": -0.10,
        "dette_nette_ebitda": -0.22,
        "couverture_interets": 843,
        "marge_nette": 0.244,
        "marge_operationnelle": 0.279,
        "marge_ebitda": 0.339,
        "roe": 0.313,
        "roa": 0.193,
        "rotation_actif": 0.79,
        "dso": 73.0,
        "dpo": 37.0,
        "taux_effectif_impot": 0.134,
    },
}


@pytest.mark.parametrize("annee", [2022, 2023])
def test_ratios_c2(etats_societe_x, ratios_yaml, annee):
    e = etats_societe_x[annee]
    resultats = {r.id: r.valeur for r in calculer_ratios(e, ratios_yaml)}

    for rid, attendu in _RATIOS_ATTENDUS[annee].items():
        obtenu = resultats.get(rid)
        assert obtenu is not None, f"{rid}@{annee} : non calculable"
        # Tolérance : jours = ±1, grands ratios = ±1, pourcentages = ±0,01
        if "dso" in rid or "dpo" in rid or "dio" in rid:
            tol = 1.0
        elif attendu is not None and abs(attendu) > 50:
            tol = 1.0
        elif attendu is not None and abs(attendu) > 1:
            tol = 0.02
        else:
            tol = 0.01
        assert obtenu == pytest.approx(attendu, abs=tol), \
            f"{rid}@{annee}: attendu {attendu}, obtenu {obtenu}"


# =============================================================================
# DIO non applicable (pas de stocks)
# =============================================================================
def test_dio_non_applicable_societe_x(etats_societe_x, ratios_yaml):
    for annee in (2022, 2023):
        resultats = {r.id: r for r in calculer_ratios(etats_societe_x[annee], ratios_yaml)}
        dio = resultats["dio"]
        assert dio.valeur is None
        assert "pas de stocks" in (dio.note or "").lower()


# =============================================================================
# Contrôles qualité
# =============================================================================
def test_qualite_societe_x_ok(etats_societe_x):
    for annee in (2022, 2023):
        controles = controler(etats_societe_x[annee])
        for c in controles:
            assert c.niveau != Niveau.BLOQUANT, f"Bloquant @{annee}: {c.nom} — {c.message}"
