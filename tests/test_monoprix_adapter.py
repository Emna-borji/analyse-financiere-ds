"""Tests de l'adaptateur Monoprix sur 4 exercices (2021-2024).

Les valeurs de controle proviennent de la lecture directe des 3 PDFs
individuels (publies au BVMT). Chaque assertion compare la valeur
extraite a la valeur publiee dans le PDF correspondant.
"""
from pathlib import Path

import pytest

from analyse_financiere.adapters.monoprix_pdf import charger_monoprix


RACINE = Path(__file__).resolve().parent.parent
PDFS = [
    RACINE / "data" / "ch1" / "monoprix_pdfs" / "mnp-etats-financiers-annuels-individuels-31-12-2022.pdf",
    RACINE / "data" / "ch1" / "monoprix_pdfs" / "mnp-etats-financiers-annuels-individuels-31-12-2023.pdf",
    RACINE / "data" / "ch1" / "monoprix_pdfs" / "mnp-etats-financiers-annuels-individuels-31-12-2024.pdf",
]


@pytest.fixture(scope="module")
def etats_monoprix():
    for p in PDFS:
        if not p.exists():
            pytest.skip(f"PDF Monoprix absent : {p}")
    return {e.annee: e for e in charger_monoprix([str(p) for p in PDFS])}


def test_quatre_exercices(etats_monoprix):
    """4 exercices attendus : 2021, 2022, 2023, 2024."""
    assert set(etats_monoprix.keys()) == {2021, 2022, 2023, 2024}


def test_detection_unite_devise(etats_monoprix):
    """Monoprix publie en dinars unitaires, pas en milliers."""
    for e in etats_monoprix.values():
        assert e.unite == "unite", f"Annee {e.annee} : unite={e.unite}"
        assert e.devise == "TND"
        assert e.referentiel == "SCE"


# -------- Valeurs de controle imposees par l'enseignant ----------
def test_revenus_2021(etats_monoprix):
    """Revenus 2021 = 618 317 561 TND (PDF individuel 2022, page 4)."""
    assert etats_monoprix[2021].ca == pytest.approx(618_317_561, abs=1)


def test_revenus_2022(etats_monoprix):
    """Revenus 2022 = 627 130 137 TND."""
    assert etats_monoprix[2022].ca == pytest.approx(627_130_137, abs=1)


def test_revenus_2023(etats_monoprix):
    """Revenus 2023 = 684 081 159 TND."""
    assert etats_monoprix[2023].ca == pytest.approx(684_081_159, abs=1)


def test_total_bilan_2021(etats_monoprix):
    """Total bilan 2021 = 247 759 872 TND."""
    assert etats_monoprix[2021].actif_total == pytest.approx(247_759_872, abs=1)


def test_total_bilan_2022(etats_monoprix):
    """Total bilan 2022 = 264 726 058 TND."""
    assert etats_monoprix[2022].actif_total == pytest.approx(264_726_058, abs=1)


def test_resultat_net_2021(etats_monoprix):
    """Resultat net 2021 = -429 449 TND (deficit historique de l'exercice)."""
    assert etats_monoprix[2021].resultat_net == pytest.approx(-429_449, abs=1)


# -------- Valeurs complementaires verifiees dans les PDF --------
def test_resultat_net_2022(etats_monoprix):
    """RN 2022 = -585 002 TND."""
    assert etats_monoprix[2022].resultat_net == pytest.approx(-585_002, abs=1)


def test_resultat_net_2023(etats_monoprix):
    """RN 2023 = 5 876 040 TND (retour au benefice)."""
    assert etats_monoprix[2023].resultat_net == pytest.approx(5_876_040, abs=1)


def test_resultat_net_2024(etats_monoprix):
    """RN 2024 = 6 834 166 TND."""
    assert etats_monoprix[2024].resultat_net == pytest.approx(6_834_166, abs=1)


def test_capital_social_2023_apres_augmentation(etats_monoprix):
    """Capital 2023 = 50 691 472 (apres incorporation de reserves vs. 39 938 744 en 2022)."""
    assert etats_monoprix[2022].capital == pytest.approx(39_938_744, abs=1)
    assert etats_monoprix[2023].capital == pytest.approx(50_691_472, abs=1)


def test_actif_egal_passif(etats_monoprix):
    """A = P pour chaque exercice (tolerance 1 TND)."""
    for annee, e in etats_monoprix.items():
        if e.actif_total is None or e.total_passif is None:
            # 2021 : total_passif n'est pas sur la meme ligne (ligne finale PDF
            # "TOTAL DES CAPITAUX PROPRES ET DES PASSIFS" reportee comme actif_total
            # dans certaines mises en page). On accepte un seul des deux.
            continue
        ecart = abs(e.actif_total - e.total_passif)
        assert ecart <= 1, f"Annee {annee} : A-P = {ecart} TND"


def test_fournisseurs_2022(etats_monoprix):
    """Fournisseurs 2022 = 109 172 522 (page 3 du PDF 2022)."""
    assert etats_monoprix[2022].fournisseurs == pytest.approx(109_172_522, abs=1)


def test_cp_totaux_2024(etats_monoprix):
    """Capitaux propres avant affectation 2024 = 95 774 305."""
    assert etats_monoprix[2024].capitaux_propres == pytest.approx(95_774_305, abs=1)


def test_stocks_2024(etats_monoprix):
    """Stocks nets 2024 = 78 681 141 (inflation stocks suite reprise commerciale)."""
    assert etats_monoprix[2024].stocks == pytest.approx(78_681_141, abs=1)


def test_invariant_frng_bfr_tn(etats_monoprix):
    """FRNG = BFR + TN pour chaque exercice (tolerance 2 TND)."""
    from analyse_financiere.reclassement import construire_bilan_fonctionnel

    config_yaml = RACINE / "config" / "reclassement.yaml"
    for annee, e in etats_monoprix.items():
        bf = construire_bilan_fonctionnel(e, config_yaml, avec_retraitements=False)
        invariant = (bf.frng - bf.bfr) - bf.tn
        assert abs(invariant) <= 2, (
            f"Annee {annee} : FRNG({bf.frng:.0f}) != BFR({bf.bfr:.0f}) + TN({bf.tn:.0f}), "
            f"ecart={invariant:.0f}"
        )


def test_evolution_tn_2021_vers_2022(etats_monoprix):
    """TN 2021 = -27 378 448 (= 11 878 226 TA - 39 256 674 TP).
    TN 2022 = -864 323 (= 25 511 799 TA - 26 376 122 TP)."""
    from analyse_financiere.reclassement import construire_bilan_fonctionnel

    bf2021 = construire_bilan_fonctionnel(
        etats_monoprix[2021],
        RACINE / "config" / "reclassement.yaml",
        avec_retraitements=False,
    )
    bf2022 = construire_bilan_fonctionnel(
        etats_monoprix[2022],
        RACINE / "config" / "reclassement.yaml",
        avec_retraitements=False,
    )
    # Signe strict : TN reste negative, mais s'ameliore nettement entre 2021 et 2022
    assert bf2021.tn < -20_000_000, f"TN 2021 attendue tres negative, obtenu {bf2021.tn}"
    assert bf2022.tn > bf2021.tn + 20_000_000, (
        f"TN 2022 doit s'ameliorer d'au moins 20 MTND vs 2021"
    )


def test_hypothese_dividendes_negatifs_2023(etats_monoprix):
    """En 2023, la hausse de capital (10,75 MTND) rend la reconstitution
    naive negative : l'adaptateur doit poser dividendes=0 ET documenter."""
    e2023 = etats_monoprix[2023]
    assert e2023.dividendes == 0.0
    assert any("dividendes reconstitues negatifs" in h for h in e2023.hypotheses), (
        f"Hypothese attendue, obtenu : {e2023.hypotheses}"
    )
