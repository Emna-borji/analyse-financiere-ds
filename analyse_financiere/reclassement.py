"""Moteur de reclassement déclaratif (ch.2, lot 2).

Prend un `EtatsFinanciers` et un fichier de règles YAML, retourne un bilan
fonctionnel avec lineage : chaque masse conserve la liste des postes
sources, leur montant, et les retraitements qui les ont modifiés.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from .pivot import EtatsFinanciers


@dataclass
class LignePostee:
    """Une contribution d'un poste source vers une masse fonctionnelle."""
    poste_source: str
    montant: float
    retraitement: Optional[str] = None  # nom du retraitement si issu d'un retraitement


@dataclass
class Masse:
    """Une masse fonctionnelle avec son lineage."""
    nom: str
    total: float = 0.0
    lignes: list[LignePostee] = field(default_factory=list)

    def ajouter(self, poste: str, montant: float, retraitement: Optional[str] = None) -> None:
        if montant == 0:
            return
        self.lignes.append(LignePostee(poste, montant, retraitement))
        self.total += montant


@dataclass
class BilanFonctionnel:
    """Un bilan fonctionnel complet avec ses grandeurs dérivées."""
    annee: int
    emplois_stables: Masse
    ressources_stables: Masse
    actif_circulant_exploitation: Masse
    actif_circulant_hors_exploitation: Masse
    passif_circulant_exploitation: Masse
    passif_circulant_hors_exploitation: Masse
    tresorerie_active: Masse
    tresorerie_passive: Masse
    retraitements_appliques: list[str] = field(default_factory=list)
    retraitements_non_appliques: list[str] = field(default_factory=list)
    postes_non_reconnus: list[str] = field(default_factory=list)

    @property
    def frng(self) -> float:
        """Fonds de roulement net global = RS − ES."""
        return self.ressources_stables.total - self.emplois_stables.total

    @property
    def bfre(self) -> float:
        """BFR d'exploitation = ACE − PCE."""
        return self.actif_circulant_exploitation.total - self.passif_circulant_exploitation.total

    @property
    def bfrhe(self) -> float:
        """BFR hors exploitation = ACHE − PCHE."""
        return self.actif_circulant_hors_exploitation.total - self.passif_circulant_hors_exploitation.total

    @property
    def bfr(self) -> float:
        """BFR total."""
        return self.bfre + self.bfrhe

    @property
    def tn(self) -> float:
        """Trésorerie nette = TA − TP."""
        return self.tresorerie_active.total - self.tresorerie_passive.total

    @property
    def taux_couverture_es(self) -> Optional[float]:
        """Taux de couverture des emplois stables = RS / ES (repère > 1)."""
        if not self.emplois_stables.total:
            return None
        return self.ressources_stables.total / self.emplois_stables.total

    def en_jours_de_ca(self, ca: float) -> dict[str, float]:
        """FRNG / BFR / TN en jours de CA (base 360, convention ch.2)."""
        if not ca:
            return {}
        return {
            "frng_jours": self.frng / ca * 360,
            "bfr_jours": self.bfr / ca * 360,
            "tn_jours": self.tn / ca * 360,
        }


# -------------------------------------------------- Construction du bilan ----
def _nouvelles_masses() -> dict[str, Masse]:
    return {nom: Masse(nom=nom) for nom in [
        "emplois_stables",
        "ressources_stables",
        "actif_circulant_exploitation",
        "actif_circulant_hors_exploitation",
        "passif_circulant_exploitation",
        "passif_circulant_hors_exploitation",
        "tresorerie_active",
        "tresorerie_passive",
    ]}


def _appliquer_regle_simple(
    masses: dict[str, Masse],
    nom_masse: str,
    poste: str,
    montant: Optional[float],
) -> None:
    if montant is None or montant == 0:
        return
    masses[nom_masse].ajouter(poste, montant)


def _appliquer_ventilation(
    masses: dict[str, Masse],
    poste: str,
    montant_total: Optional[float],
    ventilation: list[dict],
    e: EtatsFinanciers,
    avec_ventilation_hors_expl: bool,
) -> None:
    """Ventile un poste mixte entre plusieurs masses selon la liste de sources.

    Si `avec_ventilation_hors_expl=False`, tout le montant va dans la masse
    "reste" (l'exploitation), comme dans le bilan fonctionnel condensé du
    corrigé C4 (ch.2). La ventilation complète (prêt société sœur → ACHE,
    dettes acq. immos → PCHE) n'est appliquée qu'au niveau C5 (retraité).
    """
    if montant_total is None:
        return
    reste = montant_total
    if avec_ventilation_hors_expl:
        for item in ventilation:
            source = item["source"]
            masse = item["masse"]
            if source == "reste":
                continue
            part = getattr(e, source, None)
            if part is not None and part != 0:
                masses[masse].ajouter(f"{poste}→{source}", part)
                reste -= part
    # L'entrée "reste" reçoit ce qui n'a pas été attribué
    for item in ventilation:
        if item["source"] == "reste":
            if reste != 0:
                masses[item["masse"]].ajouter(f"{poste}(reste)", reste)
            break


def construire_bilan_fonctionnel(
    e: EtatsFinanciers,
    chemin_yaml: str | Path,
    avec_retraitements: bool = False,
) -> BilanFonctionnel:
    """Construit le bilan fonctionnel pour un exercice.

    Si `avec_retraitements=True`, applique le crédit-bail et les EENE.
    """
    with Path(chemin_yaml).open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    masses = _nouvelles_masses()
    retraitements_appliques: list[str] = []
    retraitements_non_appliques: list[str] = []

    # --- 1. Règles de base ---
    for champ, regle in config["regles"].items():
        montant = getattr(e, champ, None)
        if montant is None:
            continue
        if "masse" in regle:
            _appliquer_regle_simple(masses, regle["masse"], champ, montant)
        elif "ventilation" in regle:
            _appliquer_ventilation(
                masses, champ, montant, regle["ventilation"], e,
                avec_ventilation_hors_expl=avec_retraitements,
            )

    # --- 2. Retraitements ---
    if avec_retraitements:
        for nom, bloc in config.get("retraitements", {}).items():
            applique = False
            for op in bloc["operations"]:
                source = op["source"]
                signe = op.get("signe", 1)
                # La dette résiduelle de crédit-bail est une propriété dérivée
                if source == "credit_bail_dette_residuelle":
                    montant = e.credit_bail_dette_residuelle
                else:
                    montant = getattr(e, source, None)
                if montant is None or montant == 0:
                    continue
                masses[op["masse"]].ajouter(
                    f"{nom}:{source}", signe * montant, retraitement=nom,
                )
                applique = True
            if applique:
                retraitements_appliques.append(nom)
            else:
                retraitements_non_appliques.append(nom)

    return BilanFonctionnel(
        annee=e.annee,
        emplois_stables=masses["emplois_stables"],
        ressources_stables=masses["ressources_stables"],
        actif_circulant_exploitation=masses["actif_circulant_exploitation"],
        actif_circulant_hors_exploitation=masses["actif_circulant_hors_exploitation"],
        passif_circulant_exploitation=masses["passif_circulant_exploitation"],
        passif_circulant_hors_exploitation=masses["passif_circulant_hors_exploitation"],
        tresorerie_active=masses["tresorerie_active"],
        tresorerie_passive=masses["tresorerie_passive"],
        retraitements_appliques=retraitements_appliques,
        retraitements_non_appliques=retraitements_non_appliques,
    )
