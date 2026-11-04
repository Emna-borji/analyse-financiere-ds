"""Adaptateur SCE tunisien — fichier Excel 3 feuilles (Actif, CP_et_Passif, résultat).

Format cible : le fichier `CAS_1_Societe_X_SCE_2023_2022.xlsx`.
Chaque feuille a une ligne d'en-tête avec les années en colonnes, puis une
cascade de lignes libellé + valeurs. Certains postes sont présentés en
BRUT / Moins:Amort/Prov / NET sur trois lignes consécutives (immobilisations
incorporelles et corporelles, clients) : l'adaptateur reconstitue brute,
amortissement et valeur nette séparément pour alimenter à la fois le ch.1
et le ch.2.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from ..pivot import EtatsFinanciers


# Table de correspondance libellé SCE → champ pivot.
# Les libellés sont normalisés en minuscules sans accents avant match.
MAPPING_SCE = {
    # --- ACTIF ---
    "immobilisations incorporelles": ("immobilisations_incorporelles_brutes", "brute"),
    "immobilisations corporelles": ("immobilisations_corporelles_brutes", "brute"),
    "immobilisations financieres": ("immobilisations_financieres", "net"),
    "autres actifs non courants": ("autres_actifs_non_courants", "net"),
    "total des actifs non courants": ("actifs_non_courants", "net"),
    "stocks": ("stocks", "net"),
    "clients et comptes rattaches": ("clients_bruts", "brute"),
    "autres actifs courants": ("autres_actifs_courants", "net"),
    "liquidites et equivalents de liquidites": ("liquidites", "net"),
    "total des actifs courants": ("actifs_courants", "net"),
    "total des actifs": ("actif_total", "net"),
    # --- PASSIF ---
    "capital social": ("capital", "net"),
    "reserves": ("reserves", "net"),
    "resultats reportes": ("resultats_reportes", "net"),
    "resultat net de l'exercice": ("resultat_net_capitaux", "net"),
    "total des capitaux propres avant affectation": ("capitaux_propres", "net"),
    "emprunts": ("dettes_financieres_lt", "net"),
    "provisions pour risques et charges": ("provisions_risques_charges", "net"),
    "total des passifs non courants": ("passifs_non_courants", "net"),
    "fournisseurs et comptes rattaches": ("fournisseurs", "net"),
    "autres passifs courants": ("autres_passifs_courants", "net"),
    "concours bancaires et autres passifs financiers": ("dettes_financieres_ct", "net"),
    "total des passifs courants": ("passifs_courants", "net"),
    "total des passifs": ("total_dettes", "net"),
    "total des capitaux propres et passifs": ("total_passif", "net"),
    # --- RESULTAT ---
    "revenus": ("ca", "net"),
    "autres produits d'exploitation": ("autres_produits_exploitation", "net"),
    "variation des stocks des produits finis et semi-finis": ("production_stockee", "net"),
    "achats de matieres consommes": ("achats_matieres", "net"),
    "achats d'approvisionnements consommes": ("achats_approvisionnements", "net"),
    "charges de personnel": ("charges_personnel", "net"),
    "dotations aux provisions et aux amortissements": ("dotations", "net"),
    "autres charges d'exploitation": ("autres_charges_exploitation", "net"),
    "resultat d'exploitation": ("ebit", "net"),
    "charges financieres nettes": ("charges_financieres", "abs"),
    "autres gains ordinaires": ("autres_gains_ordinaires", "net"),
    "autres pertes ordinaires": ("autres_pertes_ordinaires", "abs"),
    "resultat des activites ordinaires avant impot": ("rcai", "net"),
    "impot sur les benefices": ("impot_benefices", "abs"),
    "elements extraordinaires": ("elements_extraordinaires", "net"),
    "resultat net de l'exercice": ("resultat_net", "net"),
}

# Alias du "Résultat net de l'exercice" : il apparaît deux fois (dans le CP
# et dans l'état de résultat). On garde les deux champs distincts.
ALIAS_RESULTAT_NET_RESULTAT = "resultat net de l'exercice_resultat"


def _normaliser(texte: str) -> str:
    """Minuscule, sans accents, espaces compactés."""
    if not isinstance(texte, str):
        return ""
    import unicodedata

    t = unicodedata.normalize("NFD", texte)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.lower().strip()
    # Variantes d'apostrophes / espaces
    t = t.replace("’", "'").replace(" ", " ").replace("\xa0", " ")
    t = " ".join(t.split())
    return t


def _est_moins(libelle_norm: str) -> Optional[str]:
    """Retourne 'amort' ou 'prov' si c'est une ligne 'Moins : …', sinon None."""
    if not libelle_norm.startswith("moins"):
        return None
    if "amortissement" in libelle_norm:
        return "amort"
    if "provision" in libelle_norm:
        return "prov"
    return "autre"


def _detecter_colonnes_annees(df: pd.DataFrame) -> tuple[int, dict[int, int]]:
    """Trouve la ligne d'en-tête et les colonnes des années.

    Retourne (index_ligne_en_tete, {annee: index_colonne}).
    """
    for i, row in df.iterrows():
        annees = {}
        for j, cell in enumerate(row):
            try:
                v = int(float(str(cell).strip()))
                if 1990 <= v <= 2100:
                    annees[v] = j
            except (ValueError, TypeError):
                pass
        if len(annees) >= 2:
            return i, annees
    raise ValueError("En-tête des années introuvable")


def _nombre(cell) -> Optional[float]:
    """Convertit une cellule en float ; None si vide."""
    if cell is None:
        return None
    s = str(cell).strip()
    if not s or s.lower() in {"nan", "none"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _extraire_feuille(df: pd.DataFrame, nom_feuille: str) -> dict[int, dict[str, float]]:
    """Retourne {annee: {champ_pivot: valeur}} pour une feuille SCE.

    Gère le pattern BRUT / Moins:Amort / NET sur trois lignes consécutives.
    Les valeurs 'amort' et 'prov' sont stockées en valeur absolue, pour
    coller à la convention du pivot.
    """
    idx_entete, cols_annees = _detecter_colonnes_annees(df)

    # Récupérer chaque ligne non vide après l'en-tête
    valeurs_par_annee: dict[int, dict[str, float]] = {a: {} for a in cols_annees}

    dernier_poste_brut = None  # pour chaîner avec sa ligne "Moins :" et le net

    for i in range(idx_entete + 1, len(df)):
        row = df.iloc[i]
        # Trouver le libellé : première cellule non vide, pas un code lettre
        libelle_brut = None
        for cell in row[:4]:
            if pd.notna(cell) and str(cell).strip():
                libelle_brut = str(cell).strip()
                break
        libelle_norm = _normaliser(libelle_brut) if libelle_brut else ""

        # Extraire les deux valeurs d'années
        valeurs = {a: _nombre(row.iloc[j]) for a, j in cols_annees.items()}
        a_des_valeurs = any(v is not None for v in valeurs.values())

        # Ligne "Moins : Amortissements / Provisions"
        type_moins = _est_moins(libelle_norm)
        if type_moins:
            if dernier_poste_brut is None:
                continue
            champ_brut, _ = dernier_poste_brut
            # Champ cible pour l'amortissement ou la provision
            if type_moins == "amort":
                if champ_brut == "immobilisations_incorporelles_brutes":
                    champ_moins = "amortissements_incorporelles"
                elif champ_brut == "immobilisations_corporelles_brutes":
                    champ_moins = "amortissements_corporelles"
                else:
                    champ_moins = None
            elif type_moins == "prov":
                if champ_brut == "clients_bruts":
                    champ_moins = "provisions_clients"
                else:
                    champ_moins = None
            else:
                champ_moins = None

            if champ_moins:
                for a, v in valeurs.items():
                    if v is not None:
                        valeurs_par_annee[a][champ_moins] = abs(v)
            continue

        if not libelle_norm or not a_des_valeurs:
            # Ligne du "net" qui suit le couple brut/amort : valeur sans libellé
            if (
                libelle_brut is None
                and a_des_valeurs
                and dernier_poste_brut is not None
            ):
                champ_brut, _ = dernier_poste_brut
                # Mapper vers le champ "net" correspondant
                if champ_brut == "immobilisations_incorporelles_brutes":
                    champ_net = "immobilisations_incorporelles"
                elif champ_brut == "immobilisations_corporelles_brutes":
                    champ_net = "immobilisations_corporelles"
                elif champ_brut == "clients_bruts":
                    champ_net = "clients"
                else:
                    champ_net = None
                if champ_net:
                    for a, v in valeurs.items():
                        if v is not None:
                            valeurs_par_annee[a][champ_net] = v
                dernier_poste_brut = None
            continue

        # Libellé reconnu dans la table
        if libelle_norm in MAPPING_SCE:
            champ, convention = MAPPING_SCE[libelle_norm]
            # Cas du "Résultat net de l'exercice" en double : dans le bilan
            # et dans le résultat. Si on est dans la feuille 'resultat', on
            # écrit resultat_net ; sinon on garde resultat_net_capitaux.
            if champ == "resultat_net_capitaux" and nom_feuille == "resultat":
                champ = "resultat_net"
            for a, v in valeurs.items():
                if v is not None:
                    valeurs_par_annee[a][champ] = abs(v) if convention == "abs" else v
            # Mémoriser le dernier poste BRUT pour chaîner avec Moins : …
            if convention == "brute":
                dernier_poste_brut = (champ, libelle_norm)
            else:
                dernier_poste_brut = None
        else:
            dernier_poste_brut = None

    # Dériver les amortissements cumulés (somme des amorts)
    for a, vals in valeurs_par_annee.items():
        ai = vals.get("amortissements_incorporelles", 0) or 0
        ac = vals.get("amortissements_corporelles", 0) or 0
        if ai or ac:
            vals["amortissements_cumules"] = ai + ac

    return valeurs_par_annee


def charger_societe_x(
    chemin_excel: str | Path,
    chemin_retraitements_yaml: Optional[str | Path] = None,
    entreprise: str = "Societe_X",
    secteur: Optional[str] = "Services",
) -> list[EtatsFinanciers]:
    """Charge le fichier Excel SCE 3-feuilles et renvoie un EtatsFinanciers par exercice.

    Si un chemin de retraitements YAML est fourni, les informations hors
    bilan (crédit-bail, EENE, pret société sœur, dettes acq. immos,
    charges financières nettes de contrôle, autres gains/pertes) y sont
    ajoutées.
    """
    chemin = Path(chemin_excel)
    xl = pd.ExcelFile(chemin)
    donnees: dict[int, dict[str, float]] = {}
    for nom_feuille in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=nom_feuille, dtype=str, header=None)
        extrait = _extraire_feuille(df, nom_feuille.lower())
        for annee, vals in extrait.items():
            donnees.setdefault(annee, {}).update(vals)

    # Retraitements YAML (chapitre 2)
    retraitements_par_annee: dict[int, dict] = {}
    hypotheses: list[str] = []
    if chemin_retraitements_yaml:
        with Path(chemin_retraitements_yaml).open(encoding="utf-8") as f:
            retr = yaml.safe_load(f)
        for annee_str, bloc in retr.get("exercices", {}).items():
            retraitements_par_annee[int(annee_str)] = bloc
        hypotheses = retr.get("hypotheses", [])

    etats: list[EtatsFinanciers] = []
    for annee, vals in sorted(donnees.items()):
        kwargs = {
            "entreprise": entreprise,
            "secteur": secteur,
            "annee": annee,
            "devise": "TND",
            "unite": "unite",
            "referentiel": "SCE",
            "source": chemin.name,
            **vals,
        }
        # Compléter avec le YAML de retraitements
        retr_an = retraitements_par_annee.get(annee, {})
        mapping_yaml = {
            "pret_societe_soeur_dans_autres_actifs_courants": "pret_societe_soeur",
            "dettes_acquisitions_immos_dans_autres_passifs_courants": "dettes_acquisitions_immos",
            "eene_hors_bilan": "eene",
            "credit_bail_valeur_origine": "credit_bail_valeur_origine",
            "credit_bail_amort_cumules": "credit_bail_amort_cumules",
            "credit_bail_duree_annees": "credit_bail_duree_annees",
        }
        for cle_yaml, champ_pivot in mapping_yaml.items():
            if cle_yaml in retr_an:
                kwargs[champ_pivot] = retr_an[cle_yaml]
        if hypotheses:
            kwargs["hypotheses"] = hypotheses

        # Garde-fou : si charges_financieres est absent dans l'Excel mais
        # fourni dans le YAML, on l'utilise.
        if kwargs.get("charges_financieres") is None and "charges_financieres_nettes" in retr_an:
            kwargs["charges_financieres"] = retr_an["charges_financieres_nettes"]

        etats.append(EtatsFinanciers(**kwargs))

    # Reconstituer les dividendes par variation des CP (ch.2, C3)
    _ajouter_dividendes(etats)

    return etats


def _ajouter_dividendes(etats: list[EtatsFinanciers]) -> None:
    """Pour chaque exercice n, reconstitue les dividendes versés en n.

    dividendes_n = resultat_net_(n-1) − (reserves_n − reserves_(n-1))
                                         − (resultats_reportes_n − resultats_reportes_(n-1))

    Hypothèse : pas d'augmentation de capital, pas d'autres mouvements sur
    les CP. C'est le choix du corrigé C3 (ch.2).
    """
    par_annee = {e.annee: e for e in etats}
    annees = sorted(par_annee)
    for i in range(1, len(annees)):
        a_prec, a = annees[i - 1], annees[i]
        ep = par_annee[a_prec]
        en = par_annee[a]
        if ep.resultat_net is None or ep.reserves is None or en.reserves is None:
            continue
        rr_prec = ep.resultats_reportes or 0
        rr_n = en.resultats_reportes or 0
        div = ep.resultat_net - (en.reserves - ep.reserves) - (rr_n - rr_prec)
        en.dividendes = div
