"""Schéma pivot — Pydantic v2, libellés français.

Reprend les noms de champs du lot 1 du chapitre 1 (ca, ebit, actif_total,
clients, dettes_financieres_lt, dettes_financieres_ct, passifs_courants…)
et les étend pour le chapitre 2 (valeurs brutes, amortissements, SIG,
CAF, hors bilan, affectation du résultat).

La devise et l'unité d'origine sont conservées : la conversion éventuelle
(ex. milliers → unités, USD → TND) est une étape explicite du pipeline,
pas une transformation implicite à l'ingestion.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


Devise = Literal["TND", "USD", "EUR", "MAD", "GBP", "CHF"]
Unite = Literal["unite", "millier", "million"]
Referentiel = Literal["SCE", "IFRS", "US_GAAP", "PCG"]


class EtatsFinanciers(BaseModel):
    """États financiers d'une entreprise pour un exercice.

    Les montants sont stockés dans la devise et l'unité d'origine. Les
    charges (charges_financieres, impot_benefices, autres_pertes_ordinaires,
    cout_achat_marchandises…) sont stockées en valeur ABSOLUE (positive),
    même si le fichier source les affiche en négatif.
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    # --- Identité de l'enregistrement -------------------------------------
    entreprise: str
    secteur: Optional[str] = None
    annee: int = Field(ge=1900, le=2100)
    devise: Devise = "TND"
    unite: Unite = "unite"
    referentiel: Referentiel = "SCE"
    source: Optional[str] = None  # fichier d'origine

    # --- BILAN — ACTIF (valeurs nettes, schéma ch.1) ----------------------
    actifs_non_courants: Optional[float] = None
    immobilisations_incorporelles: Optional[float] = None
    immobilisations_corporelles: Optional[float] = None
    immobilisations_financieres: Optional[float] = None
    autres_actifs_non_courants: Optional[float] = None

    # Valeurs brutes et amortissements (schéma ch.2, bilan fonctionnel)
    immobilisations_incorporelles_brutes: Optional[float] = None
    immobilisations_corporelles_brutes: Optional[float] = None
    amortissements_incorporelles: Optional[float] = None  # en valeur absolue
    amortissements_corporelles: Optional[float] = None
    amortissements_cumules: Optional[float] = None  # somme des amorts

    actifs_courants: Optional[float] = None
    stocks: Optional[float] = None
    clients: Optional[float] = None  # net (ch.1)
    clients_bruts: Optional[float] = None  # ch.2 — DSO le réclame
    provisions_clients: Optional[float] = None  # en valeur absolue
    autres_actifs_courants: Optional[float] = None
    liquidites: Optional[float] = None
    actif_total: Optional[float] = None

    # --- BILAN — CAPITAUX PROPRES ET PASSIFS ------------------------------
    capitaux_propres: Optional[float] = None
    capital: Optional[float] = None
    reserves: Optional[float] = None
    resultats_reportes: Optional[float] = None
    resultat_net_capitaux: Optional[float] = None  # ligne RN du bilan

    dettes_financieres_lt: Optional[float] = None  # emprunts > 1 an
    provisions_risques_charges: Optional[float] = None
    passifs_non_courants: Optional[float] = None

    fournisseurs: Optional[float] = None
    dettes_financieres_ct: Optional[float] = None  # concours bancaires
    autres_passifs_courants: Optional[float] = None
    passifs_courants: Optional[float] = None

    total_dettes: Optional[float] = None
    total_passif: Optional[float] = None  # CP + dettes totales

    # --- ÉTAT DE RÉSULTAT -------------------------------------------------
    ca: Optional[float] = None  # revenus = chiffre d'affaires
    ventes_marchandises: Optional[float] = None  # SIG marge commerciale
    cout_achat_marchandises: Optional[float] = None  # idem, valeur absolue
    production_vendue: Optional[float] = None
    production_stockee: Optional[float] = None
    production_immobilisee: Optional[float] = None
    autres_produits_exploitation: Optional[float] = None
    subventions_exploitation: Optional[float] = None

    achats_matieres: Optional[float] = None
    achats_approvisionnements: Optional[float] = None
    variation_stocks_mp: Optional[float] = None
    autres_charges_exploitation: Optional[float] = None  # services tiers
    impots_taxes: Optional[float] = None
    charges_personnel: Optional[float] = None
    dotations: Optional[float] = None
    reprises: Optional[float] = None

    ebit: Optional[float] = None  # résultat d'exploitation

    charges_financieres: Optional[float] = None  # nettes, valeur absolue
    autres_gains_ordinaires: Optional[float] = None
    autres_pertes_ordinaires: Optional[float] = None  # valeur absolue
    rcai: Optional[float] = None  # résultat avant impôt
    impot_benefices: Optional[float] = None  # valeur absolue
    elements_extraordinaires: Optional[float] = None
    resultat_net: Optional[float] = None

    # --- Hors bilan et retraitements (ch.2) -------------------------------
    eene: Optional[float] = None  # effets escomptés non échus
    credit_bail_valeur_origine: Optional[float] = None
    credit_bail_amort_cumules: Optional[float] = None
    credit_bail_duree_annees: Optional[int] = None

    # --- Reclassement hors exploitation (ch.2) ----------------------------
    pret_societe_soeur: Optional[float] = None
    dettes_acquisitions_immos: Optional[float] = None

    # --- Affectation du résultat (ch.2, reconstitution dividendes) --------
    dividendes: Optional[float] = None  # reconstitués via variation CP

    # --- Hygiène et métadonnées ------------------------------------------
    postes_manquants: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)

    @property
    def credit_bail_dette_residuelle(self) -> Optional[float]:
        """Dette résiduelle du crédit-bail = valeur origine − amort cumulés.

        Hypothèse du cours : la part non encore amortie reste à rembourser
        et constitue une dette financière pour le bilan fonctionnel retraité.
        """
        v = self.credit_bail_valeur_origine
        a = self.credit_bail_amort_cumules
        if v is None or a is None:
            return None
        return v - a
