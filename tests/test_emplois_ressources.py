"""Test explicite : emplois = ressources apres retraitements (ch.2).

Un bilan fonctionnel retraite DOIT verifier :
   ES + ACE + ACHE + TA = RS + PCE + PCHE + TP

C'est l'invariant du bilan par partie double. Si un retraitement introduit
un desequilibre, c'est un bug.
"""
from pathlib import Path

import pytest

from analyse_financiere.adapters.sce_excel import charger_societe_x
from analyse_financiere.reclassement import construire_bilan_fonctionnel


RACINE = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def etats_societe_x():
    return {
        e.annee: e for e in charger_societe_x(
            RACINE / "data" / "ch1" / "CAS_1_Societe_X_SCE_2023_2022.xlsx",
            RACINE / "data" / "ch2" / "societe_x_retraitements.yaml",
        )
    }


def _total_emplois(bf):
    return (
        bf.emplois_stables.total
        + bf.actif_circulant_exploitation.total
        + bf.actif_circulant_hors_exploitation.total
        + bf.tresorerie_active.total
    )


def _total_ressources(bf):
    return (
        bf.ressources_stables.total
        + bf.passif_circulant_exploitation.total
        + bf.passif_circulant_hors_exploitation.total
        + bf.tresorerie_passive.total
    )


@pytest.mark.parametrize("annee", [2022, 2023])
def test_emplois_egal_ressources_sans_retraitements(etats_societe_x, annee):
    """Societe X C4 (sans retraitements) : emplois = ressources."""
    bf = construire_bilan_fonctionnel(
        etats_societe_x[annee],
        RACINE / "config" / "reclassement.yaml",
        avec_retraitements=False,
    )
    ecart = abs(_total_emplois(bf) - _total_ressources(bf))
    assert ecart <= 0.01, (
        f"Annee {annee} (sans retraitements) : emplois={_total_emplois(bf):.2f} "
        f"vs ressources={_total_ressources(bf):.2f}, ecart={ecart:.2f} TND"
    )


@pytest.mark.parametrize("annee", [2022, 2023])
def test_emplois_egal_ressources_avec_retraitements(etats_societe_x, annee):
    """Societe X C5 (avec credit-bail + EENE) : emplois = ressources.

    Le credit-bail ajoute ES + RS du MEME montant (brut + amort + dette
    residuelle = brut, car brut = amort + dette). Les EENE ajoutent ACE + TP
    du meme montant. Dans les deux cas, la balance est preservee.
    """
    bf = construire_bilan_fonctionnel(
        etats_societe_x[annee],
        RACINE / "config" / "reclassement.yaml",
        avec_retraitements=True,
    )
    ecart = abs(_total_emplois(bf) - _total_ressources(bf))
    assert ecart <= 0.01, (
        f"Annee {annee} (avec retraitements) : emplois={_total_emplois(bf):.2f} "
        f"vs ressources={_total_ressources(bf):.2f}, ecart={ecart:.2f} TND"
    )


@pytest.mark.parametrize("annee", [2022, 2023])
def test_credit_bail_augmente_emplois_et_ressources_du_meme_montant(
    etats_societe_x, annee,
):
    """Avec vs sans retraitement : l'ajout du credit-bail doit augmenter
    strictement ES et RS du meme montant (valeur d'origine)."""
    e = etats_societe_x[annee]
    bf_sans = construire_bilan_fonctionnel(
        e, RACINE / "config" / "reclassement.yaml", avec_retraitements=False,
    )
    bf_avec = construire_bilan_fonctionnel(
        e, RACINE / "config" / "reclassement.yaml", avec_retraitements=True,
    )
    # Delta emplois stables = valeur d'origine du credit-bail
    delta_es = bf_avec.emplois_stables.total - bf_sans.emplois_stables.total
    assert delta_es == pytest.approx(e.credit_bail_valeur_origine or 0, abs=1)
    # Delta ressources stables = amort + dette = valeur d'origine
    delta_rs = bf_avec.ressources_stables.total - bf_sans.ressources_stables.total
    assert delta_rs == pytest.approx(e.credit_bail_valeur_origine or 0, abs=1)
