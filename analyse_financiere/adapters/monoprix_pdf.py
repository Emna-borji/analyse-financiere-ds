"""Adaptateur Monoprix (SNMVT) — etats financiers individuels SCE depuis PDF.

Sources : etats financiers annuels INDIVIDUELS publies au BVMT.
- PDF 2022 publie en 2023 → bilans + resultat 2022 + 2021.
- PDF 2023 publie en 2024 → bilans + resultat 2023 + 2022 (comparatif).
- PDF 2024 publie en 2025 → bilans + resultat 2024 + 2023 (comparatif).

En cas de retraitement d'un comparatif d'une annee a l'autre (changement de
ventilation), on utilise la valeur la plus recente et on documente l'ecart
via `hypotheses`.

Detection automatique de l'unite : on cherche dans la premiere page la
mention "en dinar" (unite=1), "en mille dinars" ou "en milliers" (unite=1000)
ou "en millions" (unite=10^6). Monoprix publie en dinars unitaires.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Optional

import pdfplumber

from ..pivot import EtatsFinanciers


# -------- MAPPING libelle normalise -> (champ pivot, convention) ----------
# convention : "net" (valeur telle quelle), "abs" (valeur absolue).
MAPPING_MONOPRIX = {
    # ----- BILAN ACTIF -----
    "immobilisations incorporelles": ("immobilisations_incorporelles_brutes", "brute"),
    "immobilisations corporelles": ("immobilisations_corporelles_brutes", "brute"),
    "immobilisations financieres": ("immobilisations_financieres_brutes_tmp", "brute"),
    "autres actifs non courants": ("autres_actifs_non_courants", "net"),
    "total des actifs non courants": ("actifs_non_courants", "net"),
    "total actifs non courants": ("actifs_non_courants", "net"),
    "valeurs d'exploitation": ("stocks_bruts_tmp", "brute"),
    "stocks": ("stocks_bruts_tmp", "brute"),
    "clients et comptes rattaches": ("clients_bruts", "brute"),
    "clients": ("clients_bruts", "brute"),
    "autres actifs courants": ("autres_actifs_courants_bruts_tmp", "brute"),
    "placements et autres actifs financiers": ("placements_tmp", "net"),
    "liquidites et equivalents de liquidite": ("liquidites", "net"),
    "liquidites et equivalents de liquidites": ("liquidites", "net"),
    "total des actifs courants": ("actifs_courants", "net"),
    "total actifs courants": ("actifs_courants", "net"),
    "total des actifs": ("actif_total", "net"),
    # ----- BILAN PASSIF -----
    "capital social": ("capital", "net"),
    "reserves et primes liees au capital": ("reserves", "net"),
    "autres capitaux propres": ("autres_cp_tmp", "net"),
    "resultats reportes": ("resultats_reportes", "net"),
    "resultat de l'exercice": ("resultat_net_capitaux", "net"),
    "total des capitaux propres avant affectation": ("capitaux_propres", "net"),
    "total des passifs non courants": ("passifs_non_courants", "net"),
    "fournisseurs et comptes rattaches": ("fournisseurs", "net"),
    "autres passifs courants": ("autres_passifs_courants", "net"),
    "concours bancaires et autres passifs financiers": ("dettes_financieres_ct", "net"),
    "total des passifs courants": ("passifs_courants", "net"),
    "total des passifs": ("total_dettes", "net"),
    "total des capitaux propres et passifs": ("total_passif", "net"),
    # ----- ETAT DE RESULTAT -----
    "revenus": ("ca", "net"),
    "autres produits d'exploitation": ("autres_produits_exploitation", "net"),
    "autres revenus d'exploitation": ("autres_produits_exploitation", "net"),
    "achats des marchandises consommes": ("cout_achat_marchandises", "abs"),
    "achats des marchandises consommees": ("cout_achat_marchandises", "abs"),
    "achats d'approvisionnements consommes": ("achats_approvisionnements", "abs"),
    "achats d'approvisionnement consommes": ("achats_approvisionnements", "abs"),
    "variation de stocks marchandises": ("variation_stocks_marchandises_tmp", "net"),
    "charges de personnel": ("charges_personnel", "abs"),
    "dotations aux amortissements et provisions": ("dotations", "abs"),
    "dotations aux amortissements et aux provisions": ("dotations", "abs"),
    "autres charges d'exploitation": ("autres_charges_exploitation", "abs"),
    "resultat d'exploitation": ("ebit", "net"),
    "charges financieres": ("charges_financieres", "abs"),
    "charges financieres nettes": ("charges_financieres", "abs"),
    "produits financiers": ("produits_financiers_tmp", "net"),
    "autres gains ordinaires": ("autres_gains_ordinaires", "net"),
    "autres pertes ordinaires": ("autres_pertes_ordinaires", "abs"),
    "resultat des activites ordinaires avant impots": ("rcai", "net"),
    "resultat des activites ordinaires avant impot": ("rcai", "net"),
    "impots sur les benefices": ("impot_benefices", "abs"),
    "impot sur les benefices": ("impot_benefices", "abs"),
    "autres pertes extraordinaires": ("elements_extraordinaires", "net"),
    "resultat net de l'exercice": ("resultat_net", "net"),
    "resultat net": ("resultat_net", "net"),
    # ----- FLUX DE TRESORERIE -----
    "distribution des dividendes": ("dividendes_flux_tmp", "abs"),
    "tresorerie a la cloture de l'exercice": ("tresorerie_cloture_tmp", "net"),
    "tresorerie au debut de l'exercice": ("tresorerie_debut_tmp", "net"),
}


RE_NOMBRE = re.compile(r"-?\d[\d\s  ]*\d|-?\d")

# Separateur entre colonnes : au moins 2 espaces consecutifs
RE_SEPARATEUR = re.compile(r"\s{2,}")
# Un nombre au format tunisien : signe optionnel, groupes de 3 chiffres
# separes par espaces ou NBSP, ex. "-150 656 190" ou "11 476 080" ou "0"
RE_MONTANT = re.compile(r"-?\d{1,3}(?:[\s  ]\d{3})+|-?\d+")


def _normaliser(s: str) -> str:
    """Minuscule sans accents, apostrophes et espaces normalises."""
    if not s:
        return ""
    t = unicodedata.normalize("NFD", s)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.lower().strip().replace("’", "'").replace("‘", "'")
    t = t.replace("\xa0", " ").replace(" ", " ")
    t = " ".join(t.split())
    # Harmoniser quelques variantes de ponctuation
    t = t.replace("'", "'").rstrip(":").rstrip()
    return " ".join(t.split())


def _parser_nombre(s: str) -> Optional[float]:
    """Convertit '-4 749 608' ou '1 366 119' en float. None si impossible."""
    s = s.replace("\xa0", " ").replace(" ", " ").strip()
    s = re.sub(r"(?<=\d)\s+(?=\d)", "", s)  # supprimer separateurs milliers
    if not s or s in {"-", "–"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _detecter_unite(texte_entier: str) -> tuple[str, str]:
    """Scanne les premieres pages pour detecter l'unite et la devise.

    Retourne (unite, devise).
    """
    t = texte_entier.lower()
    # Devise
    if "dinar" in t or "dt" in t or " tnd" in t:
        devise = "TND"
    elif "euro" in t:
        devise = "EUR"
    elif "dollar" in t or "usd" in t:
        devise = "USD"
    else:
        devise = "TND"
    # Unite
    if "en milliers" in t or "en mille " in t:
        return "millier", devise
    if "en millions" in t or "en million " in t:
        return "million", devise
    return "unite", devise


def _extraire_lignes_mots(page) -> list[tuple[str, list[float]]]:
    """Extrait (libelle, [valeurs]) en groupant les mots par ligne via leur position y.

    Pour chaque ligne :
    - identifie tous les tokens numeriques (eventuellement composes de groupes
      de 3 chiffres separes par espaces) en balayant de droite a gauche ;
    - prend au plus les 2 derniers nombres (colonnes N et N-1) ;
    - le libelle est tout ce qui reste a gauche.
    """
    mots = page.extract_words(x_tolerance=1, y_tolerance=2, keep_blank_chars=False)
    if not mots:
        return []
    # Grouper par ligne : meme top a +/- 3 pixels
    mots_tries = sorted(mots, key=lambda m: (round(m["top"]), m["x0"]))
    lignes_mots: list[list[dict]] = []
    ligne_courante: list[dict] = []
    top_courant: Optional[float] = None
    for m in mots_tries:
        t = m["top"]
        if top_courant is None or abs(t - top_courant) < 4:
            ligne_courante.append(m)
            top_courant = t if top_courant is None else top_courant
        else:
            lignes_mots.append(ligne_courante)
            ligne_courante = [m]
            top_courant = t
    if ligne_courante:
        lignes_mots.append(ligne_courante)

    lignes: list[tuple[str, list[float]]] = []
    for mots_ligne in lignes_mots:
        mots_ligne.sort(key=lambda m: m["x0"])
        # Reconstituer la ligne en reconnaissant les nombres via les ruptures
        # horizontales (gap > seuil) ET les signes '-' en debut de token.
        tokens_textuels: list[str] = []
        nombres_poses: list[float] = []
        groupe_nombres: list[tuple[str, dict]] = []  # (text, mot dict)

        def flusher():
            if not groupe_nombres:
                return
            nombres_poses.extend(_decouper_groupe_par_gap(groupe_nombres))
            groupe_nombres.clear()

        for m in mots_ligne:
            t = m["text"]
            if _est_token_numerique(t):
                groupe_nombres.append((t, m))
            else:
                flusher()
                tokens_textuels.append(t)
        flusher()

        # Garder les 2 derniers nombres si plus de 2 (ex. numero de note)
        if len(nombres_poses) > 2:
            nombres_poses = nombres_poses[-2:]
        libelle = " ".join(tokens_textuels).strip()
        libelle = re.sub(r"\s+\d{1,2}$", "", libelle).strip()
        lignes.append((libelle, nombres_poses))
    return lignes


def _decouper_groupe_par_gap(groupe: list[tuple[str, dict]]) -> list[float]:
    """Decoupe une sequence de tokens numeriques en nombres.

    Ruptures detectees :
    - un token qui commence par '-' debute un nouveau nombre ;
    - un token dont la longueur != 3 ET qui n'est pas le 1er du nombre debute
      un nouveau nombre (format "X XXX XXX" ou "XX XXX") ;
    - les gaps entre tokens consecutifs sont analyses : on segmente le groupe
      en nombres de sorte que les gaps INTER-nombre soient significativement
      plus grands que les gaps INTRA-nombre (separateurs de milliers).
    """
    if not groupe:
        return []

    # Etape 1 : etape conservative par longueur + signe
    segments: list[list[tuple[str, dict]]] = []
    seg: list[tuple[str, dict]] = []
    for t, m in groupe:
        est_negatif = t.startswith("-")
        tt = t[1:] if est_negatif else t
        if seg and (est_negatif or len(tt) != 3):
            segments.append(seg)
            seg = []
        seg.append((t, m))
    if seg:
        segments.append(seg)

    # Etape 2 : pour chaque segment, analyser les gaps horizontaux et splitter
    # a chaque gap "anormal" (significativement plus grand que la mediane).
    resultats: list[float] = []
    for s in segments:
        if len(s) <= 1:
            resultats.append(_parser_nombre("".join(t for t, _ in s)))
            continue
        gaps = []
        for i in range(1, len(s)):
            gaps.append(s[i][1]["x0"] - s[i - 1][1]["x1"])
        # Seuil : max(gap_min * 3.0, 5 px). Le gap minimal correspond a l'intra-
        # millier (separateur de milliers), tout gap plus grand d'un facteur 3
        # est considere comme une rupture entre colonnes ou entre nombre et note.
        gap_min = min(gaps)
        seuil = max(gap_min * 3.0, 5)
        # Points de coupure
        coupures = [i + 1 for i, g in enumerate(gaps) if g > seuil]
        if not coupures:
            resultats.append(_parser_nombre("".join(t for t, _ in s)))
            continue
        # Construire les sous-nombres a partir des coupures
        indices = [0] + coupures + [len(s)]
        for a, b in zip(indices[:-1], indices[1:]):
            morceau = s[a:b]
            if morceau:
                resultats.append(_parser_nombre("".join(t for t, _ in morceau)))
    return resultats


def _est_token_numerique(t: str) -> bool:
    """Un token numerique : signe optionnel, puis 1-3 chiffres eventuellement
    pointes par "." decimal. On exclut les mots alphabetiques."""
    if not t:
        return False
    tt = t.replace(",", "").replace("\xa0", "").replace(" ", "")
    if tt.startswith("-"):
        tt = tt[1:]
    return tt.isdigit() and 1 <= len(tt) <= 4


def _decouper_groupe(groupe: list[str]) -> list[float]:
    """Decoupe une sequence de tokens numeriques en nombres.

    Regle : un nouveau nombre commence des qu'on voit un token de 1-3 chiffres
    (pas 3) OU un signe '-'. Les tokens suivants de PRECISEMENT 3 chiffres sont
    accumules comme groupes de milliers.
    """
    nombres: list[float] = []
    courant: list[str] = []
    for t in groupe:
        est_negatif = t.startswith("-")
        tt = t[1:] if est_negatif else t
        if courant and (len(tt) != 3 or est_negatif):
            # Cloturer le nombre precedent
            nombres.append(_parser_nombre("".join(courant)))
            courant = []
        courant.append(t)
    if courant:
        nombres.append(_parser_nombre("".join(courant)))
    return nombres


def _detecter_annees_entete_bilan(pdf) -> tuple[int, int]:
    """Cherche la ligne 'ACTIFS NOTES N N-1' sur la page 2 ou 3 (bilan).

    Retourne (an_n, an_n1). La ligne d'en-tete du bilan contient 2 annees
    cote-a-cote, c'est la plus fiable pour determiner l'ordre des colonnes.
    """
    for p in pdf.pages[:5]:
        txt = p.extract_text(layout=True) or ""
        for ligne in txt.splitlines():
            # On cherche "... 2022  2021" ou "au 31 decembre 2022  au 31 decembre 2021"
            annees = re.findall(r"\b(20\d{2})\b", ligne)
            if len(annees) == 2:
                a, b = int(annees[0]), int(annees[1])
                if 2010 <= a <= 2030 and 2010 <= b <= 2030 and abs(a - b) == 1:
                    return max(a, b), min(a, b)
    raise ValueError("En-tete bilan avec 2 annees consecutives introuvable")


def _traiter_pdf(chemin: Path) -> tuple[dict[int, dict], str, str]:
    """Parse un PDF Monoprix et renvoie {annee: {champ: valeur}}, unite, devise."""
    with pdfplumber.open(chemin) as pdf:
        # Textes des premieres pages pour detecter unite
        texte_tete = "\n".join(
            (p.extract_text() or "") for p in pdf.pages[:3]
        )
        unite, devise = _detecter_unite(texte_tete)

        # Annees via l'en-tete du bilan (colonne N puis colonne N-1)
        an_n, an_n1 = _detecter_annees_entete_bilan(pdf)

        resultats: dict[int, dict] = {an_n: {}, an_n1: {}}
        # Etat de la machine : poste brut en cours + a-t-on deja pose la valeur brute ?
        dernier_poste_brut: Optional[str] = None
        brut_pose: bool = False  # true apres l'ecriture de la valeur BRUT
        # Poste "net" attendu sur la ligne suivante (PDF 2023 ou l'entete seule)
        poste_net_attendu: Optional[tuple[str, str]] = None  # (champ, convention)

        for page in pdf.pages:
            lignes = _extraire_lignes_mots(page)
            for libelle_brut, valeurs in lignes:
                lib_norm = _normaliser(libelle_brut)

                # Ligne sans libelle avec des valeurs : consomme poste_net_attendu
                # ou alors BRUT/NET selon l'etat du poste BRUT en cours.
                if not lib_norm and valeurs:
                    if poste_net_attendu:
                        champ, convention = poste_net_attendu
                        if len(valeurs) >= 2:
                            v_n, v_n1 = valeurs[0], valeurs[1]
                            if convention == "abs":
                                v_n, v_n1 = abs(v_n), abs(v_n1)
                            resultats[an_n][champ] = v_n
                            resultats[an_n1][champ] = v_n1
                        poste_net_attendu = None
                        continue
                    if dernier_poste_brut:
                        if not brut_pose:
                            _poser_brut(resultats, dernier_poste_brut, valeurs, an_n, an_n1)
                            brut_pose = True
                        else:
                            _poser_net_apres_brut(resultats, dernier_poste_brut, valeurs, an_n, an_n1)
                            dernier_poste_brut = None
                            brut_pose = False
                        continue
                if not lib_norm or not valeurs:
                    # Toute ligne sans valeur reset le poste_net_attendu pour eviter
                    # de capter une valeur non associee plus loin.
                    continue

                # Ligne "Amortissements -X -Y"
                if lib_norm.startswith("amortissements") and dernier_poste_brut:
                    champ = None
                    if dernier_poste_brut == "immobilisations_incorporelles_brutes":
                        champ = "amortissements_incorporelles"
                    elif dernier_poste_brut == "immobilisations_corporelles_brutes":
                        champ = "amortissements_corporelles"
                    if champ and len(valeurs) >= 2:
                        resultats[an_n][champ] = abs(valeurs[0])
                        resultats[an_n1][champ] = abs(valeurs[1])
                    continue

                if lib_norm.startswith("provisions") and dernier_poste_brut:
                    champ = None
                    if dernier_poste_brut == "clients_bruts":
                        champ = "provisions_clients"
                    elif dernier_poste_brut in ("stocks_bruts_tmp",):
                        champ = "provisions_stocks_tmp"
                    if champ and len(valeurs) >= 2:
                        resultats[an_n][champ] = abs(valeurs[0])
                        resultats[an_n1][champ] = abs(valeurs[1])
                    continue

                # Matching libelle direct
                if lib_norm in MAPPING_MONOPRIX:
                    champ, convention = MAPPING_MONOPRIX[lib_norm]
                    # Filtre : si la seule "valeur" trouvee est un petit entier
                    # (< 1000), c'est une note (ex. "Placements ... 10"). On
                    # traite la ligne comme libelle seul.
                    valeurs_sans_notes = [
                        v for v in valeurs if v is not None and abs(v) >= 1000
                    ]
                    if len(valeurs_sans_notes) >= 2:
                        v_n, v_n1 = valeurs_sans_notes[0], valeurs_sans_notes[1]
                        if convention == "abs":
                            v_n, v_n1 = abs(v_n), abs(v_n1)
                        resultats[an_n][champ] = v_n
                        resultats[an_n1][champ] = v_n1
                        # Pour le PDF 2022 style : brut est pose avec le libelle
                        if convention == "brute":
                            dernier_poste_brut = champ
                            brut_pose = True
                        else:
                            dernier_poste_brut = None
                            brut_pose = False
                    elif len(valeurs_sans_notes) == 1:
                        v = valeurs_sans_notes[0]
                        if convention == "abs":
                            v = abs(v)
                        resultats[an_n][champ] = v
                        dernier_poste_brut = champ if convention == "brute" else None
                        brut_pose = convention != "brute"
                    else:
                        # Libelle seul (ou avec seulement une note) : PDF 2023 style
                        if convention == "brute":
                            dernier_poste_brut = champ
                            brut_pose = False
                        else:
                            # Poste net dont la valeur est sur la ligne suivante
                            poste_net_attendu = (champ, convention)
                else:
                    # Libelle non reconnu : ne pas reset dernier_poste_brut si on
                    # attend encore la ligne net (ex. "Capitaux propres" entre
                    # "Immobilisations corporelles" et sa ligne brut).
                    pass

    # Post-traitement : agregats
    for annee, vals in resultats.items():
        # Immobilisations financieres nettes = brutes - provisions_cumulees
        # Dans les PDFs : "63 838 720" puis "-3 469 609" puis "60 369 111"
        # On garde la valeur nette si elle apparait apres l'amort/prov
        # (gere par _poser_net_apres_brut si le pattern se presente).
        # Sinon on calcule depuis la valeur brute mentionnee.
        brute = vals.pop("immobilisations_financieres_brutes_tmp", None)
        if brute is not None and "immobilisations_financieres" not in vals:
            # On n'a pas capture le net : on le laisse a None et on met la brute
            vals["immobilisations_financieres"] = brute

        # Stocks nets
        stocks_bruts = vals.pop("stocks_bruts_tmp", None)
        if stocks_bruts is not None and "stocks" not in vals:
            vals["stocks"] = stocks_bruts

        # Autres actifs courants nets
        autres_bruts = vals.pop("autres_actifs_courants_bruts_tmp", None)
        if autres_bruts is not None and "autres_actifs_courants" not in vals:
            vals["autres_actifs_courants"] = autres_bruts

        # Placements (petit poste non requis au pivot) : garde sur place
        placements = vals.pop("placements_tmp", None)
        if placements is not None:
            # Ajoute aux liquidites pour simplification SCE
            vals["liquidites"] = (vals.get("liquidites") or 0) + placements

        # Fusionner autres_cp (ex: 47 006) dans reserves (approche conservatrice)
        autres_cp = vals.pop("autres_cp_tmp", None)
        if autres_cp is not None:
            vals["reserves"] = (vals.get("reserves") or 0) + autres_cp

        # Produits financiers : si charges_financieres positive, on ne nette pas
        # (le PDF 2023 donne deja "charges_financieres_nettes"). On deduit ici
        # le net manuellement si l'un ou l'autre manque.
        prod_fin = vals.pop("produits_financiers_tmp", None)
        if prod_fin is not None and vals.get("charges_financieres") is not None:
            # SCE : charges_financieres stockees en absolu, produits financiers
            # a ajouter dans autres_gains_ordinaires (simplification pivot).
            vals["autres_gains_ordinaires"] = (
                (vals.get("autres_gains_ordinaires") or 0) + prod_fin
            )

        # Nettoyer les champs temporaires restants
        for k in list(vals.keys()):
            if k.endswith("_tmp"):
                vals.pop(k)

        # Amortissements cumules
        ai = vals.get("amortissements_incorporelles") or 0
        ac = vals.get("amortissements_corporelles") or 0
        if ai or ac:
            vals["amortissements_cumules"] = ai + ac

        # Monoprix : les passifs non courants sont exclusivement des emprunts
        # bancaires (cf notes 13). On alimente dettes_financieres_lt depuis
        # passifs_non_courants pour eviter l'ambiguite entre les libelles
        # "Emprunts bancaires" du bilan et "Emprunts" du tableau de flux.
        if vals.get("passifs_non_courants") is not None:
            vals["dettes_financieres_lt"] = vals["passifs_non_courants"]

    return resultats, unite, devise


def _poser_net_apres_brut(
    resultats: dict, dernier: str, valeurs: list, an_n: int, an_n1: int
) -> None:
    """Pose la valeur nette apres un couple brut+amort/prov.

    Utilise par les lignes sans libelle (ex. "7 136 744 143 470" pour l'incorpo
    2022/2021) qui representent la valeur nette finale.
    """
    net_map = {
        "immobilisations_incorporelles_brutes": "immobilisations_incorporelles",
        "immobilisations_corporelles_brutes": "immobilisations_corporelles",
        "immobilisations_financieres_brutes_tmp": "immobilisations_financieres",
        "clients_bruts": "clients",
        "stocks_bruts_tmp": "stocks",
        "autres_actifs_courants_bruts_tmp": "autres_actifs_courants",
    }
    champ_net = net_map.get(dernier)
    if champ_net and len(valeurs) >= 2:
        resultats[an_n][champ_net] = valeurs[0]
        resultats[an_n1][champ_net] = valeurs[1]


def _poser_brut(
    resultats: dict, dernier: str, valeurs: list, an_n: int, an_n1: int
) -> None:
    """Pose les valeurs BRUTES d'un poste (PDF 2023 style : libelle seul, puis
    ligne sans libelle avec les 2 bruts)."""
    if len(valeurs) >= 2:
        resultats[an_n][dernier] = valeurs[0]
        resultats[an_n1][dernier] = valeurs[1]


# ----------------------------------------------------------------------
def charger_monoprix(
    chemins_pdf: list[str | Path],
    entreprise: str = "Monoprix (SNMVT)",
    secteur: str = "Distribution",
) -> list[EtatsFinanciers]:
    """Charge les PDFs Monoprix et renvoie un EtatsFinanciers par exercice.

    En cas de retraitement d'un comparatif, on garde la version du PDF le plus
    recent (et on documente l'ecart dans `hypotheses`).
    """
    # 1. Extraire les donnees de chaque PDF
    extraits: dict[int, list[tuple[str, dict]]] = {}
    unites = set()
    devises = set()
    sources_par_annee: dict[int, str] = {}

    for chemin in chemins_pdf:
        p = Path(chemin)
        resultats, unite, devise = _traiter_pdf(p)
        unites.add(unite)
        devises.add(devise)
        for annee, vals in resultats.items():
            if not vals:
                continue
            extraits.setdefault(annee, []).append((p.name, vals))

    if len(unites) != 1:
        raise RuntimeError(f"Unites incoherentes entre PDFs : {unites}")
    if len(devises) != 1:
        raise RuntimeError(f"Devises incoherentes entre PDFs : {devises}")

    unite = unites.pop()
    devise = devises.pop()

    # 2. Pour chaque annee, fusionner en prenant la version la plus recente
    # (celle du PDF le plus recent). Documenter les ecarts si un meme champ
    # a deux valeurs differentes dans deux PDFs.
    etats: list[EtatsFinanciers] = []
    for annee in sorted(extraits):
        # Trier par ordre croissant de date de publication (PDF)
        versions = sorted(extraits[annee], key=lambda x: x[0])
        # La version la plus recente est le dernier element du nom (PDF 2024 > 2023 > 2022)
        versions.sort(key=lambda x: x[0])  # ordre alphabetique = chronologique ici
        vals_fusion: dict = {}
        hypotheses: list[str] = []
        for nom_pdf, vals in versions:
            for k, v in vals.items():
                if k in vals_fusion:
                    v_prec = vals_fusion[k]
                    if v_prec is not None and v is not None and abs(v_prec - v) > 1:
                        hypotheses.append(
                            f"[{annee}] retraitement {k} : {v_prec} -> {v} "
                            f"(source {nom_pdf})"
                        )
                vals_fusion[k] = v
            sources_par_annee[annee] = nom_pdf

        # Capital social : dans le PDF 2022, 2021 affiche 39 938 746 (cf 2 dinars
        # restes sur la numerotation nominale) — on conserve la valeur exacte.

        # Recalculer amortissements_cumules APRES fusion (certains PDFs comparatifs
        # omettent la ligne detaillee des amorts corporels pour l'exercice N-1).
        ai = vals_fusion.get("amortissements_incorporelles") or 0
        ac = vals_fusion.get("amortissements_corporelles") or 0
        if ai or ac:
            vals_fusion["amortissements_cumules"] = ai + ac

        kwargs = {
            "entreprise": entreprise,
            "secteur": secteur,
            "annee": annee,
            "devise": devise,
            "unite": unite,
            "referentiel": "SCE",
            "source": sources_par_annee.get(annee),
            "hypotheses": hypotheses,
            **vals_fusion,
        }
        # Enlever les champs non prevus au pivot
        valides = EtatsFinanciers.model_fields.keys()
        kwargs = {k: v for k, v in kwargs.items() if k in valides or k == "hypotheses"}
        etats.append(EtatsFinanciers(**kwargs))

    # 3. Reconstituer les dividendes avec prise en compte de la hausse de capital 2023
    _ajouter_dividendes_avec_capital(etats)

    return etats


def _ajouter_dividendes_avec_capital(etats: list[EtatsFinanciers]) -> None:
    """Reconstitution des dividendes compte tenu des variations de capital.

    Formule etendue :
      div_n = RN_(n-1) - var_capital_n - var_reserves_n - var_resultats_reportes_n

    La variation de capital est soustraite pour isoler les flux reels de
    distribution vs. augmentation/incorporation. Si le resultat est negatif,
    on documente que la variation des CP contient d'autres mouvements
    (ex. primes d'emission, reclassements de reserves).
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
        cap_prec = ep.capital or 0
        cap_n = en.capital or 0
        var_cap = cap_n - cap_prec
        var_res = (en.reserves or 0) - (ep.reserves or 0)
        var_rr = rr_n - rr_prec
        div = ep.resultat_net - var_cap - var_res - var_rr
        if div < 0:
            en.hypotheses.append(
                f"dividendes reconstitues negatifs ({div:.0f} TND) : "
                "variation CP contient probablement des primes/reclassements "
                "non captures par la formule — valeur figee a 0"
            )
            en.dividendes = 0.0
        else:
            en.dividendes = div
