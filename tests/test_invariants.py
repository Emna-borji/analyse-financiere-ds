"""Invariants comptables — ch.2 lot 4.

Chaque invariant est un test unitaire naturel. Si l'un casse, le pipeline
a produit un bilan incohérent. Tolérance : 0,01 TND sur la Société X.
"""
import pytest

from analyse_financiere.sig_caf import calculer_caf
from analyse_financiere.reclassement import construire_bilan_fonctionnel


TOLERANCE_TND = 0.01


# =============================================================================
# Invariant 1 — Actif = Passif (équation fondamentale)
# =============================================================================
@pytest.mark.parametrize("annee", [2022, 2023])
def test_invariant_actif_egal_passif(etats_societe_x, annee):
    e = etats_societe_x[annee]
    assert abs(e.actif_total - e.total_passif) < 1  # tolérance 1 TND (arrondis Excel)


# =============================================================================
# Invariant 2 — FRNG − BFR = TN (sans retraitement)
# =============================================================================
@pytest.mark.parametrize("annee", [2022, 2023])
def test_invariant_frng_bfr_tn(etats_societe_x, reclassement_yaml, annee):
    bf = construire_bilan_fonctionnel(etats_societe_x[annee], reclassement_yaml)
    assert abs(bf.frng - bf.bfr - bf.tn) < TOLERANCE_TND


# =============================================================================
# Invariant 3 — FRNG − BFR = TN (AVEC retraitements)
# =============================================================================
@pytest.mark.parametrize("annee", [2022, 2023])
def test_invariant_frng_bfr_tn_retraite(etats_societe_x, reclassement_yaml, annee):
    bf = construire_bilan_fonctionnel(
        etats_societe_x[annee], reclassement_yaml, avec_retraitements=True,
    )
    assert abs(bf.frng - bf.bfr - bf.tn) < TOLERANCE_TND


# =============================================================================
# Invariant 4 — CAF soustractive = CAF additive
# =============================================================================
@pytest.mark.parametrize("annee", [2022, 2023])
def test_invariant_caf_concordance(etats_societe_x, annee):
    caf = calculer_caf(etats_societe_x[annee])
    assert caf.concordance_ok, f"Écart CAF sous/add = {caf.ecart}"


# =============================================================================
# Invariant 5 — Le crédit-bail ne modifie PAS le FRNG
# =============================================================================
@pytest.mark.parametrize("annee", [2022, 2023])
def test_invariant_credit_bail_frng_inchange(etats_societe_x, reclassement_yaml, annee):
    bf_sans = construire_bilan_fonctionnel(etats_societe_x[annee], reclassement_yaml)
    bf_avec = construire_bilan_fonctionnel(
        etats_societe_x[annee], reclassement_yaml, avec_retraitements=True,
    )
    # Le FRNG doit rester identique entre les deux versions :
    #   +crédit-bail en ES (valeur origine)
    #   +crédit-bail en RS (amort cumulés + dette résiduelle = valeur origine)
    # Les deux contributions s'annulent. Les EENE ne touchent pas le FRNG non plus.
    assert abs(bf_sans.frng - bf_avec.frng) < TOLERANCE_TND


# =============================================================================
# Invariant 6 — Les EENE laissent BFR + TN inchangé (FRNG lui-même inchangé)
# =============================================================================
@pytest.mark.parametrize("annee", [2022, 2023])
def test_invariant_eene_conservation(etats_societe_x, reclassement_yaml, annee):
    """EENE : BFR augmente de X, TN baisse de X → BFR + TN inchangé."""
    bf_sans = construire_bilan_fonctionnel(etats_societe_x[annee], reclassement_yaml)
    bf_avec = construire_bilan_fonctionnel(
        etats_societe_x[annee], reclassement_yaml, avec_retraitements=True,
    )
    eene = etats_societe_x[annee].eene or 0

    # Prêt société sœur et dettes acq. immos déplacent ACE↔ACHE et PCE↔PCHE
    # mais le BFR TOTAL ne change pas.
    # EENE augmente ACE et TP du même montant → BFR +EENE, TN −EENE.
    delta_bfr = bf_avec.bfr - bf_sans.bfr
    delta_tn = bf_avec.tn - bf_sans.tn
    assert abs(delta_bfr - eene) < TOLERANCE_TND
    assert abs(delta_tn + eene) < TOLERANCE_TND
