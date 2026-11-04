"""Soldes intermédiaires de gestion (SIG) et CAF — ch.2, lot 3.

Deux méthodes de CAF, test d'égalité intégré. Adapté au modèle SCE
(sociétés sans activité de négoce : la marge commerciale est nulle, la
production vendue = revenus).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .pivot import EtatsFinanciers


@dataclass
class SIG:
    """Cascade des soldes intermédiaires de gestion."""
    marge_commerciale: float
    production_exercice: float
    consommations_intermediaires: float
    valeur_ajoutee: float
    ebe: float
    rex: float
    rcai: float
    resultat_net: float

    # Ratios de répartition
    taux_valeur_ajoutee: Optional[float]  # VA / CA
    part_personnel: Optional[float]  # charges_personnel / VA
    taux_ebe: Optional[float]  # EBE / CA
    poids_frais_financiers: Optional[float]  # CF / EBE


@dataclass
class CAF:
    """Capacité d'autofinancement par les deux méthodes."""
    caf_soustractive: float
    caf_additive: float
    ecart: float
    concordance_ok: bool
    autofinancement: Optional[float]  # CAF − dividendes
    capacite_remboursement: Optional[float]  # dettes_fin / CAF, en années
    taux_caf: Optional[float]  # CAF / CA


def calculer_sig(e: EtatsFinanciers) -> SIG:
    """Construit la cascade des SIG à partir d'un exercice.

    Hypothèses du cours (Société X, services) :
    - Pas de marchandises (ventes_marchandises = 0 par défaut).
    - Production de l'exercice ≈ revenus (pas de variation de stocks pf,
      pas d'immobilisée dans ce cas).
    - Consommations intermédiaires = achats approvisionnements + autres
      charges d'exploitation (= services extérieurs, conformément à la
      note p.6 du ch.2).
    """
    ventes_m = e.ventes_marchandises or 0
    cout_m = e.cout_achat_marchandises or 0
    marge_com = ventes_m - cout_m

    revenus = e.ca or 0
    prod_stockee = e.production_stockee or 0
    prod_immo = e.production_immobilisee or 0
    production = revenus + prod_stockee + prod_immo

    achats_m = e.achats_matieres or 0
    achats_a = e.achats_approvisionnements or 0
    autres_ch = e.autres_charges_exploitation or 0
    conso = achats_m + achats_a + autres_ch

    va = marge_com + production - conso

    subventions = e.subventions_exploitation or 0
    impots_taxes = e.impots_taxes or 0
    personnel = e.charges_personnel or 0
    ebe = va + subventions - impots_taxes - personnel

    dotations = e.dotations or 0
    reprises = e.reprises or 0
    rex = ebe - dotations + reprises

    # Si l'état de résultat fournit déjà le REX, on l'utilise comme oracle
    # (évite les décalages de convention).
    if e.ebit is not None:
        rex = e.ebit

    cf = e.charges_financieres or 0
    gains = e.autres_gains_ordinaires or 0
    pertes = e.autres_pertes_ordinaires or 0
    rcai = rex - cf + gains - pertes
    if e.rcai is not None:
        rcai = e.rcai

    impot = e.impot_benefices or 0
    extra = e.elements_extraordinaires or 0
    rn = rcai - impot + extra
    if e.resultat_net is not None:
        rn = e.resultat_net

    # Ratios de répartition
    taux_va = va / revenus if revenus else None
    part_perso = personnel / va if va else None
    taux_ebe = ebe / revenus if revenus else None
    poids_cf = cf / ebe if ebe else None

    return SIG(
        marge_commerciale=marge_com,
        production_exercice=production,
        consommations_intermediaires=conso,
        valeur_ajoutee=va,
        ebe=ebe,
        rex=rex,
        rcai=rcai,
        resultat_net=rn,
        taux_valeur_ajoutee=taux_va,
        part_personnel=part_perso,
        taux_ebe=taux_ebe,
        poids_frais_financiers=poids_cf,
    )


def calculer_caf(e: EtatsFinanciers, sig: Optional[SIG] = None) -> CAF:
    """CAF par les deux méthodes + indicateurs dérivés.

    Méthode soustractive : EBE − CF + autres gains − autres pertes − impôt.
    Méthode additive : RN + dotations − reprises − produits_cession + VNC_cedees
                       − quote_part_subventions.
    Dans le cas de la Société X, on n'a pas de cessions d'actifs : la
    méthode additive se réduit à RN + dotations.
    """
    if sig is None:
        sig = calculer_sig(e)

    cf = e.charges_financieres or 0
    gains = e.autres_gains_ordinaires or 0
    pertes = e.autres_pertes_ordinaires or 0
    impot = e.impot_benefices or 0

    caf_sous = sig.ebe - cf + gains - pertes - impot
    caf_add = (e.resultat_net or 0) + (e.dotations or 0) - (e.reprises or 0)

    ecart = abs(caf_sous - caf_add)
    concordance = ecart < 1.0  # tolerance 1 TND

    # Dividendes (reconstitués via l'adaptateur, si disponibles)
    auto = None
    if e.dividendes is not None:
        auto = caf_sous - e.dividendes

    # Capacité de remboursement
    dettes_fin = (e.dettes_financieres_lt or 0) + (e.dettes_financieres_ct or 0)
    cap_remb = dettes_fin / caf_sous if caf_sous else None

    taux_caf = caf_sous / e.ca if e.ca else None

    return CAF(
        caf_soustractive=caf_sous,
        caf_additive=caf_add,
        ecart=ecart,
        concordance_ok=concordance,
        autofinancement=auto,
        capacite_remboursement=cap_remb,
        taux_caf=taux_caf,
    )
