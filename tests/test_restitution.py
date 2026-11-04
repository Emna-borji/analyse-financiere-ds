"""Smoke test de la restitution HTML."""
from pathlib import Path

from analyse_financiere.restitution import diagnostic_complet


RACINE = Path(__file__).resolve().parent.parent


def test_rapport_html_societe_x(etats_societe_x, ratios_yaml, reclassement_yaml, tmp_path):
    for annee, e in etats_societe_x.items():
        out = tmp_path / f"Societe_X_{annee}.html"
        res = diagnostic_complet(e, ratios_yaml, reclassement_yaml, out)
        assert out.exists()
        html = out.read_text(encoding="utf-8")
        # Vérifications minimales : les sections clés sont présentes
        assert "Diagnostic financier" in html
        assert "SIG" in html or "Soldes intermédiaires" in html
        assert "FRNG" in html
        assert res["situation"].numero in (1, 2, 3, 4, 5, 6)


def test_commentaire_societe_x_2023(etats_societe_x, ratios_yaml, reclassement_yaml):
    from analyse_financiere.commentaire import commenter
    from analyse_financiere.ratios import calculer_ratios
    from analyse_financiere.sig_caf import calculer_sig, calculer_caf
    from analyse_financiere.reclassement import construire_bilan_fonctionnel
    from analyse_financiere.typologie import classer

    e = etats_societe_x[2023]
    ratios = calculer_ratios(e, ratios_yaml)
    sig = calculer_sig(e)
    caf = calculer_caf(e, sig)
    bf = construire_bilan_fonctionnel(e, reclassement_yaml, avec_retraitements=True)
    sit = classer(bf.frng, bf.bfr, bf.tn)

    md = commenter(e, ratios, sig, caf, bf, sit)
    assert "948" in md  # résultat net
    # Pour 2023, situation 2 → attention "FRNG insuffisant"
    assert "FRNG insuffisant" in md or "situation 2" in md.lower()
