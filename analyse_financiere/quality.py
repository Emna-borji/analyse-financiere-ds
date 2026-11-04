"""Contrôles qualité sur un EtatsFinanciers (lot 3 du ch.1).

Trois niveaux : OK, Avertissement, Bloquant. Le niveau Bloquant indique que
le reste du pipeline doit être interrompu pour cet exercice.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .pivot import EtatsFinanciers


class Niveau(str, Enum):
    OK = "OK"
    AVERTISSEMENT = "Avertissement"
    BLOQUANT = "Bloquant"


@dataclass
class Controle:
    nom: str
    niveau: Niveau
    message: str
    ecart: Optional[float] = None


def _presence(e: EtatsFinanciers, champs: list[str]) -> list[str]:
    """Liste des champs attendus manquants."""
    return [c for c in champs if getattr(e, c, None) is None]


def controler(e: EtatsFinanciers, tolerance_relative: float = 0.01) -> list[Controle]:
    """Exécute tous les contrôles qualité sur un exercice.

    `tolerance_relative` : écart toléré sur l'équation actif = passif
    (défaut 1 %, conforme au cours).
    """
    controles: list[Controle] = []

    # --- 1. Équation fondamentale Actif = CP + Passifs ---
    if e.actif_total and e.total_passif:
        ecart = abs(e.actif_total - e.total_passif)
        ref = max(abs(e.actif_total), abs(e.total_passif))
        ecart_rel = ecart / ref if ref else 0
        niveau = Niveau.OK if ecart_rel < tolerance_relative else Niveau.BLOQUANT
        controles.append(Controle(
            nom="equation_fondamentale",
            niveau=niveau,
            message=f"Actif = {e.actif_total:.2f}, Total CP+Passif = {e.total_passif:.2f}, écart {ecart:.2f} ({ecart_rel:.2%})",
            ecart=ecart,
        ))

    # --- 2. Cohérence sous-totaux actif ---
    if e.actifs_courants is not None and e.actifs_non_courants is not None and e.actif_total is not None:
        attendu = e.actifs_courants + e.actifs_non_courants
        ecart = abs(e.actif_total - attendu)
        ref = abs(e.actif_total) or 1
        niveau = Niveau.OK if (ecart / ref) < tolerance_relative else Niveau.AVERTISSEMENT
        controles.append(Controle(
            nom="sous_totaux_actif",
            niveau=niveau,
            message=f"AC + ANC = {attendu:.2f}, Actif total = {e.actif_total:.2f}, écart {ecart:.2f}",
            ecart=ecart,
        ))

    # --- 3. Cohérence CP ---
    if (
        e.capital is not None
        and e.reserves is not None
        and e.resultats_reportes is not None
        and e.resultat_net_capitaux is not None
        and e.capitaux_propres is not None
    ):
        attendu = e.capital + e.reserves + e.resultats_reportes + e.resultat_net_capitaux
        ecart = abs(e.capitaux_propres - attendu)
        ref = abs(e.capitaux_propres) or 1
        niveau = Niveau.OK if (ecart / ref) < tolerance_relative else Niveau.AVERTISSEMENT
        controles.append(Controle(
            nom="sous_totaux_cp",
            niveau=niveau,
            message=f"Capital + réserves + RR + RN = {attendu:.2f} vs CP {e.capitaux_propres:.2f}",
            ecart=ecart,
        ))

    # --- 4. Signes attendus ---
    valeurs_positives_attendues = {
        "actif_total": e.actif_total,
        "ca": e.ca,
    }
    for nom, val in valeurs_positives_attendues.items():
        if val is not None and val < 0:
            controles.append(Controle(
                nom=f"signe_{nom}",
                niveau=Niveau.BLOQUANT,
                message=f"{nom} négatif ({val:.2f}) : anomalie majeure",
            ))

    # --- 5. Capitaux propres négatifs : avertissement, pas bloquant ---
    if e.capitaux_propres is not None and e.capitaux_propres < 0:
        controles.append(Controle(
            nom="cp_negatifs",
            niveau=Niveau.AVERTISSEMENT,
            message=f"Capitaux propres négatifs ({e.capitaux_propres:.2f}) : situation de faillite technique ; certains ratios seront marqués non significatifs",
        ))

    # --- 6. Valeurs manquantes clés ---
    champs_critiques = ["ca", "actif_total", "capitaux_propres"]
    manquants = _presence(e, champs_critiques)
    if manquants:
        controles.append(Controle(
            nom="valeurs_manquantes_critiques",
            niveau=Niveau.BLOQUANT,
            message=f"Postes critiques manquants : {', '.join(manquants)}",
        ))

    # --- 7. Cohérence SIG : REX = EBE - dotations (si tout est connu) ---
    if (
        e.ebit is not None
        and e.ca is not None
        and e.achats_approvisionnements is not None
        and e.autres_charges_exploitation is not None
        and e.charges_personnel is not None
        and e.dotations is not None
    ):
        va = e.ca - (e.achats_approvisionnements + e.autres_charges_exploitation)
        ebe = va - e.charges_personnel
        rex = ebe - e.dotations
        ecart = abs(e.ebit - rex)
        ref = abs(e.ebit) or 1
        niveau = Niveau.OK if (ecart / ref) < tolerance_relative else Niveau.AVERTISSEMENT
        controles.append(Controle(
            nom="coherence_sig",
            niveau=niveau,
            message=f"REX reconstitué par SIG = {rex:.2f} vs REX = {e.ebit:.2f}",
            ecart=ecart,
        ))

    return controles


def rapport_qualite(controles: list[Controle]) -> dict:
    """Agrège les contrôles en un rapport résumé."""
    par_niveau = {n: [] for n in Niveau}
    for c in controles:
        par_niveau[c.niveau].append(c)
    return {
        "niveau_global": (
            Niveau.BLOQUANT if par_niveau[Niveau.BLOQUANT]
            else Niveau.AVERTISSEMENT if par_niveau[Niveau.AVERTISSEMENT]
            else Niveau.OK
        ),
        "nb_ok": len(par_niveau[Niveau.OK]),
        "nb_avertissements": len(par_niveau[Niveau.AVERTISSEMENT]),
        "nb_bloquants": len(par_niveau[Niveau.BLOQUANT]),
        "details": controles,
    }
