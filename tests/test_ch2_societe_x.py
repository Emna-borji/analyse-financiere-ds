"""Tests du chapitre 2 : corrigés C1 (SIG), C2 (CAF), C3 (dividendes), C4 (bilan fonctionnel).

Valeurs attendues copiées depuis le PDF ch.2, pages 7–8.
"""
import pytest

from analyse_financiere.sig_caf import calculer_sig, calculer_caf
from analyse_financiere.reclassement import construire_bilan_fonctionnel
from analyse_financiere.typologie import classer


# =============================================================================
# C1 — Soldes intermédiaires de gestion
# =============================================================================
_SIG_ATTENDUS = {
    2023: {
        "production_exercice": 4229401,
        "consommations_intermediaires": 1780899,
        "valeur_ajoutee": 2448503,
        "ebe": 1628256,
        "rex": 1364124,
        "rcai": 1156924,
        "resultat_net": 948657,
        "taux_valeur_ajoutee": 0.579,
        "part_personnel": 0.335,
        "taux_ebe": 0.385,
        "poids_frais_financiers": 0.136,
    },
    2022: {
        "production_exercice": 3459549,
        "consommations_intermediaires": 1633250,
        "valeur_ajoutee": 1826299,
        "ebe": 1171051,
        "rex": 966547,
        "rcai": 975755,
        "resultat_net": 845182,
        "taux_valeur_ajoutee": 0.528,
        "part_personnel": 0.359,
        "taux_ebe": 0.339,
        "poids_frais_financiers": 0.001,  # 1 146 / 1 171 051
    },
}


@pytest.mark.parametrize("annee", [2022, 2023])
def test_sig_c1(etats_societe_x, annee):
    sig = calculer_sig(etats_societe_x[annee])
    for cle, attendu in _SIG_ATTENDUS[annee].items():
        obtenu = getattr(sig, cle)
        if isinstance(attendu, int):
            assert obtenu == pytest.approx(attendu, abs=1), f"{cle}@{annee}: {obtenu} vs {attendu}"
        else:
            assert obtenu == pytest.approx(attendu, abs=0.005), f"{cle}@{annee}: {obtenu} vs {attendu}"


# =============================================================================
# C2 — Capacité d'autofinancement
# =============================================================================
@pytest.mark.parametrize("annee,caf_att,cap_remb_att", [
    (2023, 1212789, 3.40),
    (2022, 1049686, 1.13),
])
def test_caf_c2(etats_societe_x, annee, caf_att, cap_remb_att):
    caf = calculer_caf(etats_societe_x[annee])
    assert caf.caf_soustractive == pytest.approx(caf_att, abs=1)
    assert caf.caf_additive == pytest.approx(caf_att, abs=1)
    assert caf.concordance_ok, f"Écart CAF sous/add = {caf.ecart}"
    assert caf.capacite_remboursement == pytest.approx(cap_remb_att, abs=0.01)


# =============================================================================
# C3 — Dividendes reconstitués + autofinancement
# =============================================================================
def test_dividendes_c3(etats_societe_x):
    e2023 = etats_societe_x[2023]
    assert e2023.dividendes == pytest.approx(661826, abs=1)

    caf = calculer_caf(e2023)
    assert caf.autofinancement == pytest.approx(550963, abs=1)


# =============================================================================
# C4 — Bilan fonctionnel SANS retraitement
# =============================================================================
@pytest.mark.parametrize("annee,attendus", [
    (2023, {
        "emplois_stables": 7380353,
        "ressources_stables": 7781628,
        "frng": 401275,
        "ace": 1557082,
        "pce": 852767,
        "bfr": 704315,
        "tn": -303040,
    }),
    (2022, {
        "emplois_stables": 2866484,
        "ressources_stables": 4573101,
        "frng": 1706617,
        "ace": 872361,
        "pce": 498649,
        "bfr": 373712,
        "tn": 1332905,
    }),
])
def test_bilan_fonctionnel_c4(etats_societe_x, reclassement_yaml, annee, attendus):
    bf = construire_bilan_fonctionnel(
        etats_societe_x[annee], reclassement_yaml, avec_retraitements=False,
    )
    assert bf.emplois_stables.total == pytest.approx(attendus["emplois_stables"], abs=1)
    assert bf.ressources_stables.total == pytest.approx(attendus["ressources_stables"], abs=1)
    assert bf.frng == pytest.approx(attendus["frng"], abs=1)
    assert bf.actif_circulant_exploitation.total == pytest.approx(attendus["ace"], abs=1)
    assert bf.passif_circulant_exploitation.total == pytest.approx(attendus["pce"], abs=1)
    assert bf.bfr == pytest.approx(attendus["bfr"], abs=1)
    assert bf.tn == pytest.approx(attendus["tn"], abs=1)

    # Invariant fondamental
    assert bf.frng - bf.bfr - bf.tn == pytest.approx(0, abs=0.01)


# =============================================================================
# C5 — Bilan fonctionnel RETRAITÉ (valeurs recalculées depuis les données du PDF)
# =============================================================================
# Hypothèses : crédit-bail (ES +600 000, RS +amort, RS +dette résiduelle),
#              EENE (ACE +EENE, TP +EENE),
#              prêt société sœur (retiré des AC → ACHE),
#              dettes acq. immos (retirées des APC → PCHE).
# Les valeurs ci-dessous sont celles obtenues par application rigoureuse des
# règles du cours ; elles seront affichées à l'étudiant dans le journal.
_C5_ATTENDUS = {
    2023: {
        "emplois_stables": 7980353,  # 7 380 353 + 600 000
        "ressources_stables": 8381628,  # 7 781 628 + 240 000 (amort CB) + 360 000 (dette CB)
        "frng": 401275,  # inchangé : invariant crédit-bail
        "ace": 1387082,  # 1 557 082 − 250 000 (prêt sœur) + 80 000 (EENE)
        "ache": 250000,
        "pce": 732767,  # 852 767 − 120 000 (dettes acq.)
        "pche": 120000,
        "bfre": 654315,
        "bfrhe": 130000,
        "bfr": 784315,
        "ta": 137438,
        "tp": 520478,  # 440 478 + 80 000 EENE
        "tn": -383040,  # -303 040 − 80 000
    },
    2022: {
        "emplois_stables": 3466484,  # 2 866 484 + 600 000
        "ressources_stables": 5173101,  # 4 573 101 + 120 000 (amort) + 480 000 (dette CB)
        "frng": 1706617,  # inchangé
        "ace": 922361,  # 872 361 + 50 000 (EENE)
        "ache": 0,
        "pce": 498649,
        "pche": 0,
        "bfre": 423712,
        "bfrhe": 0,
        "bfr": 423712,
        "ta": 1442247,
        "tp": 159342,  # 109 342 + 50 000
        "tn": 1282905,
    },
}


@pytest.mark.parametrize("annee", [2022, 2023])
def test_bilan_fonctionnel_retraite_c5(etats_societe_x, reclassement_yaml, annee):
    bf = construire_bilan_fonctionnel(
        etats_societe_x[annee], reclassement_yaml, avec_retraitements=True,
    )
    att = _C5_ATTENDUS[annee]
    assert bf.emplois_stables.total == pytest.approx(att["emplois_stables"], abs=1)
    assert bf.ressources_stables.total == pytest.approx(att["ressources_stables"], abs=1)
    assert bf.frng == pytest.approx(att["frng"], abs=1)
    assert bf.actif_circulant_exploitation.total == pytest.approx(att["ace"], abs=1)
    assert bf.actif_circulant_hors_exploitation.total == pytest.approx(att["ache"], abs=1)
    assert bf.passif_circulant_exploitation.total == pytest.approx(att["pce"], abs=1)
    assert bf.passif_circulant_hors_exploitation.total == pytest.approx(att["pche"], abs=1)
    assert bf.bfre == pytest.approx(att["bfre"], abs=1)
    assert bf.bfrhe == pytest.approx(att["bfrhe"], abs=1)
    assert bf.bfr == pytest.approx(att["bfr"], abs=1)
    assert bf.tresorerie_active.total == pytest.approx(att["ta"], abs=1)
    assert bf.tresorerie_passive.total == pytest.approx(att["tp"], abs=1)
    assert bf.tn == pytest.approx(att["tn"], abs=1)
    assert bf.frng - bf.bfr - bf.tn == pytest.approx(0, abs=0.01)


# =============================================================================
# C6 — Typologie des 6 situations
# =============================================================================
def test_typologie_societe_x(etats_societe_x, reclassement_yaml):
    # 2022 sans retraitement : FRNG > 0, BFR > 0, TN > 0 → situation 1 équilibre
    bf22 = construire_bilan_fonctionnel(etats_societe_x[2022], reclassement_yaml)
    sit22 = classer(bf22.frng, bf22.bfr, bf22.tn)
    assert sit22.numero == 1

    # 2023 sans retraitement : FRNG > 0, BFR > 0, TN < 0 → situation 2 FRNG insuffisant
    bf23 = construire_bilan_fonctionnel(etats_societe_x[2023], reclassement_yaml)
    sit23 = classer(bf23.frng, bf23.bfr, bf23.tn)
    assert sit23.numero == 2
