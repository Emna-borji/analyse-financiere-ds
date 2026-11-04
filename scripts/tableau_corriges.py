"""Genere docs/TABLEAU_CORRIGES_SOCIETE_X.md : tableau exhaustif calcule vs corrige.

Utilise les memes tolerances que les tests pytest. Chaque ligne indique :
- valeur attendue (corrige PDF),
- valeur calculee,
- ecart absolu,
- tolerance utilisee par le test,
- statut (OK/KO).
"""
from pathlib import Path

from analyse_financiere.adapters.sce_excel import charger_societe_x
from analyse_financiere.ratios import calculer_ratios, common_size
from analyse_financiere.sig_caf import calculer_caf, calculer_sig
from analyse_financiere.reclassement import construire_bilan_fonctionnel


RACINE = Path(__file__).resolve().parent.parent


def ligne(nom, att, calc, tol):
    ecart = (calc - att) if calc is not None else None
    ok = "OK" if (ecart is not None and abs(ecart) <= tol) else "KO"
    if calc is None:
        calc_fmt, ecart_fmt = "n/c", "n/c"
    elif abs(att) >= 100:
        calc_fmt = f"{calc:,.2f}".replace(",", " ")
        ecart_fmt = f"{ecart:+.2f}"
    else:
        calc_fmt = f"{calc:.4f}"
        ecart_fmt = f"{ecart:+.4f}"
    att_fmt = f"{att:,.0f}".replace(",", " ") if abs(att) >= 100 else f"{att:.4f}"
    return f"| {nom} | {att_fmt} | {calc_fmt} | {ecart_fmt} | {tol} | {ok} |"


def main():
    etats = {e.annee: e for e in charger_societe_x(
        RACINE / "data/ch1/CAS_1_Societe_X_SCE_2023_2022.xlsx",
        RACINE / "data/ch2/societe_x_retraitements.yaml",
    )}

    sortie = []
    sortie.append("# Societe X : valeurs calculees vs corriges (ch.1 C2 + ch.2 C1-C5)")
    sortie.append("")
    sortie.append("Genere par `python -m scripts.tableau_corriges`. Les tolerances sont")
    sortie.append("celles utilisees dans les tests pytest (`tests/test_ch1_societe_x.py` et")
    sortie.append("`tests/test_ch2_societe_x.py`).")
    sortie.append("")

    # --- C1 ch.1 common-size ---
    corriges_c1 = {
        2023: {"actifs_non_courants_pct": 0.793, "actifs_courants_pct": 0.207,
               "liquidites_pct": 0.017, "capitaux_propres_pct": 0.375,
               "passifs_non_courants_pct": 0.463, "passifs_courants_pct": 0.162},
        2022: {"actifs_non_courants_pct": 0.472, "actifs_courants_pct": 0.528,
               "liquidites_pct": 0.329, "capitaux_propres_pct": 0.616,
               "passifs_non_courants_pct": 0.246, "passifs_courants_pct": 0.139},
    }
    sortie.append("## Ch.1 C1 - Lecture common-size (tolerance 0.002 absolue)")
    sortie.append("")
    for annee in (2023, 2022):
        sortie.append(f"### {annee}")
        sortie.append("")
        sortie.append("| Poste | Attendu | Calcule | Ecart | Tol | Statut |")
        sortie.append("|---|---:|---:|---:|---:|---|")
        cs = common_size(etats[annee])
        for k, att in corriges_c1[annee].items():
            sortie.append(ligne(k, att, cs[k], 0.002))
        sortie.append("")

    # --- C2 ch.1 ratios ---
    corriges_c2 = {
        2023: {"liquidite_generale": (1.28, 0.02), "liquidite_immediate": (0.11, 0.01),
               "endettement_global": (1.67, 0.02), "autonomie_financiere": (0.375, 0.01),
               "gearing": (1.34, 0.02), "dette_nette_ebitda": (2.45, 0.02),
               "couverture_interets": (6.16, 0.02), "marge_nette": (0.224, 0.01),
               "marge_operationnelle": (0.323, 0.01), "marge_ebitda": (0.385, 0.01),
               "roe": (0.318, 0.01), "roa": (0.119, 0.01), "rotation_actif": (0.53, 0.01),
               "dso": (62.0, 1.0), "dpo": (65.0, 1.0), "taux_effectif_impot": (0.180, 0.01)},
        2022: {"liquidite_generale": (3.81, 0.02), "liquidite_immediate": (2.37, 0.02),
               "endettement_global": (0.62, 0.02), "autonomie_financiere": (0.616, 0.01),
               "gearing": (-0.10, 0.01), "dette_nette_ebitda": (-0.22, 0.01),
               "couverture_interets": (843.0, 1.0), "marge_nette": (0.244, 0.01),
               "marge_operationnelle": (0.279, 0.01), "marge_ebitda": (0.339, 0.01),
               "roe": (0.313, 0.01), "roa": (0.193, 0.01), "rotation_actif": (0.79, 0.01),
               "dso": (73.0, 1.0), "dpo": (37.0, 1.0), "taux_effectif_impot": (0.134, 0.01)},
    }
    sortie.append("## Ch.1 C2 - Tableau des ratios")
    sortie.append("")
    sortie.append("Tolerances : jours = +/-1 ; grandes valeurs (|v|>50) = +/-1 ; "
                  "ratios usuels = +/-0.02 ; pourcentages = +/-0.01.")
    sortie.append("")
    for annee in (2023, 2022):
        sortie.append(f"### {annee}")
        sortie.append("")
        sortie.append("| Ratio | Attendu | Calcule | Ecart | Tol | Statut |")
        sortie.append("|---|---:|---:|---:|---:|---|")
        res = {r.id: r.valeur for r in calculer_ratios(etats[annee], RACINE / "config/ratios.yaml")}
        for rid, (att, tol) in corriges_c2[annee].items():
            sortie.append(ligne(rid, att, res.get(rid), tol))
        sortie.append("")

    # --- C1 ch.2 SIG ---
    sig_att = {
        2023: {"production_exercice": 4229401, "consommations_intermediaires": 1780899,
               "valeur_ajoutee": 2448503, "ebe": 1628256, "rex": 1364124,
               "rcai": 1156924, "resultat_net": 948657},
        2022: {"production_exercice": 3459549, "consommations_intermediaires": 1633250,
               "valeur_ajoutee": 1826299, "ebe": 1171051, "rex": 966547,
               "rcai": 975755, "resultat_net": 845182},
    }
    sortie.append("## Ch.2 C1 - Soldes intermediaires de gestion (tolerance +/-1 TND)")
    sortie.append("")
    for annee in (2023, 2022):
        sortie.append(f"### {annee}")
        sortie.append("")
        sortie.append("| Solde | Attendu (TND) | Calcule | Ecart | Tol | Statut |")
        sortie.append("|---|---:|---:|---:|---:|---|")
        sig = calculer_sig(etats[annee])
        for k, att in sig_att[annee].items():
            sortie.append(ligne(k, att, getattr(sig, k), 1))
        sortie.append("")

    sortie.append("### Ratios de repartition (tolerance 0.005 absolue)")
    sortie.append("")
    repart_att = {
        2023: {"taux_valeur_ajoutee": 0.579, "part_personnel": 0.335,
               "taux_ebe": 0.385, "poids_frais_financiers": 0.136},
        2022: {"taux_valeur_ajoutee": 0.528, "part_personnel": 0.359,
               "taux_ebe": 0.339, "poids_frais_financiers": 0.001},
    }
    for annee in (2023, 2022):
        sortie.append(f"#### {annee}")
        sortie.append("")
        sortie.append("| Ratio | Attendu | Calcule | Ecart | Tol | Statut |")
        sortie.append("|---|---:|---:|---:|---:|---|")
        sig = calculer_sig(etats[annee])
        for k, att in repart_att[annee].items():
            sortie.append(ligne(k, att, getattr(sig, k), 0.005))
        sortie.append("")

    # --- C2 ch.2 CAF ---
    sortie.append("## Ch.2 C2 - Capacite d'autofinancement")
    sortie.append("")
    sortie.append("Tolerances : CAF sous/add = +/-1 TND ; capacite remb. = +/-0.01 an.")
    sortie.append("")
    caf_att = {
        2023: {"caf_soustractive": (1212789, 1), "caf_additive": (1212789, 1),
               "capacite_remboursement": (3.40, 0.01)},
        2022: {"caf_soustractive": (1049686, 1), "caf_additive": (1049686, 1),
               "capacite_remboursement": (1.13, 0.01)},
    }
    for annee in (2023, 2022):
        sortie.append(f"### {annee}")
        sortie.append("")
        sortie.append("| Mesure | Attendu | Calcule | Ecart | Tol | Statut |")
        sortie.append("|---|---:|---:|---:|---:|---|")
        caf = calculer_caf(etats[annee])
        for k, (att, tol) in caf_att[annee].items():
            sortie.append(ligne(k, att, getattr(caf, k), tol))
        sortie.append("")

    # --- C3 ch.2 Dividendes ---
    sortie.append("## Ch.2 C3 - Dividendes 2023 (tolerance +/-1 TND)")
    sortie.append("")
    sortie.append("| Mesure | Attendu | Calcule | Ecart | Tol | Statut |")
    sortie.append("|---|---:|---:|---:|---:|---|")
    sortie.append(ligne("dividendes_2023", 661826, etats[2023].dividendes, 1))
    caf23 = calculer_caf(etats[2023])
    sortie.append(ligne("autofinancement_2023", 550963, caf23.autofinancement, 1))
    sortie.append("")

    # --- C4 ch.2 Bilan fonctionnel ---
    sortie.append("## Ch.2 C4 - Bilan fonctionnel sans retraitement (tolerance +/-1 TND)")
    sortie.append("")
    c4 = {
        2023: {"emplois_stables": 7380353, "ressources_stables": 7781628,
               "frng": 401275, "ace": 1557082, "pce": 852767,
               "bfr": 704315, "ta": 137438, "tp": 440478, "tn": -303040},
        2022: {"emplois_stables": 2866484, "ressources_stables": 4573101,
               "frng": 1706617, "ace": 872361, "pce": 498649,
               "bfr": 373712, "ta": 1442247, "tp": 109342, "tn": 1332905},
    }
    for annee in (2023, 2022):
        sortie.append(f"### {annee}")
        sortie.append("")
        sortie.append("| Masse | Attendu | Calcule | Ecart | Tol | Statut |")
        sortie.append("|---|---:|---:|---:|---:|---|")
        bf = construire_bilan_fonctionnel(etats[annee], RACINE / "config/reclassement.yaml")
        valeurs = {"emplois_stables": bf.emplois_stables.total,
                   "ressources_stables": bf.ressources_stables.total,
                   "frng": bf.frng, "ace": bf.actif_circulant_exploitation.total,
                   "pce": bf.passif_circulant_exploitation.total, "bfr": bf.bfr,
                   "ta": bf.tresorerie_active.total, "tp": bf.tresorerie_passive.total,
                   "tn": bf.tn}
        for k, att in c4[annee].items():
            sortie.append(ligne(k, att, valeurs[k], 1))
        sortie.append(f"| **Invariant FRNG-BFR-TN** | 0 | {bf.frng - bf.bfr - bf.tn:.4f} | {bf.frng - bf.bfr - bf.tn:+.4f} | 0.01 | {'OK' if abs(bf.frng-bf.bfr-bf.tn) < 0.01 else 'KO'} |")
        sortie.append("")

    # --- C5 ch.2 Bilan fonctionnel retraite ---
    sortie.append("## Ch.2 C5 - Bilan fonctionnel RETRAITE (recalcule, pas de corrige PDF)")
    sortie.append("")
    sortie.append("Valeurs recalculees depuis la partie B du ch.2. Tolerance +/-1 TND.")
    sortie.append("Verification : FRNG retraite = FRNG non retraite (invariant credit-bail).")
    sortie.append("")
    c5 = {
        2023: {"emplois_stables": 7980353, "ressources_stables": 8381628,
               "frng": 401275, "ace": 1387082, "ache": 250000, "pce": 732767,
               "pche": 120000, "bfre": 654315, "bfrhe": 130000, "bfr": 784315,
               "ta": 137438, "tp": 520478, "tn": -383040},
        2022: {"emplois_stables": 3466484, "ressources_stables": 5173101,
               "frng": 1706617, "ace": 922361, "ache": 0, "pce": 498649,
               "pche": 0, "bfre": 423712, "bfrhe": 0, "bfr": 423712,
               "ta": 1442247, "tp": 159342, "tn": 1282905},
    }
    for annee in (2023, 2022):
        sortie.append(f"### {annee} retraite")
        sortie.append("")
        sortie.append("| Masse | Attendu | Calcule | Ecart | Tol | Statut |")
        sortie.append("|---|---:|---:|---:|---:|---|")
        bf = construire_bilan_fonctionnel(etats[annee], RACINE / "config/reclassement.yaml", avec_retraitements=True)
        valeurs = {"emplois_stables": bf.emplois_stables.total,
                   "ressources_stables": bf.ressources_stables.total,
                   "frng": bf.frng, "ace": bf.actif_circulant_exploitation.total,
                   "ache": bf.actif_circulant_hors_exploitation.total,
                   "pce": bf.passif_circulant_exploitation.total,
                   "pche": bf.passif_circulant_hors_exploitation.total,
                   "bfre": bf.bfre, "bfrhe": bf.bfrhe, "bfr": bf.bfr,
                   "ta": bf.tresorerie_active.total, "tp": bf.tresorerie_passive.total,
                   "tn": bf.tn}
        for k, att in c5[annee].items():
            sortie.append(ligne(k, att, valeurs[k], 1))
        sortie.append(f"| **Invariant FRNG-BFR-TN** | 0 | {bf.frng - bf.bfr - bf.tn:.4f} | {bf.frng - bf.bfr - bf.tn:+.4f} | 0.01 | {'OK' if abs(bf.frng-bf.bfr-bf.tn) < 0.01 else 'KO'} |")
        sortie.append("")

    chemin = RACINE / "docs" / "TABLEAU_CORRIGES_SOCIETE_X.md"
    chemin.write_text("\n".join(sortie), encoding="utf-8")
    print(f"Ecrit : {chemin}")


if __name__ == "__main__":
    main()
