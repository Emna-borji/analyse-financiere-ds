"""Moteur de ratios déclaratif avec AST restreint (lot 4 du ch.1).

Les formules sont lues depuis `config/ratios.yaml` et évaluées par un
visiteur AST qui n'autorise que : opérations arithmétiques, comparaisons,
noms de variables (champs du pivot), littéraux numériques, et quelques
fonctions sûres (abs, min, max). Pas de `eval()` libre, pas d'import,
pas d'appel arbitraire.

Garde-fous :
- division par zéro → ratio = None
- capitaux propres négatifs → ratios qui le réclament → None + note
  'non_significatif'
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from .pivot import EtatsFinanciers


# ------------------------------------------------------------------- AST ----
_OP_BINAIRES = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a ** b,
    ast.Mod: lambda a, b: a % b,
}

_OP_UNAIRES = {
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a,
}

_FONCTIONS_AUTORISEES = {
    "abs": abs,
    "min": min,
    "max": max,
}


class EvaluationError(Exception):
    """Erreur contrôlée pendant l'évaluation d'une formule."""


def evaluer_formule(formule: str, variables: dict[str, Any]) -> float:
    """Évalue une formule arithmétique restreinte dans un contexte donné.

    Lève EvaluationError en cas de division par zéro ou de variable
    manquante (valeur None). Les callers interceptent pour produire un
    ratio 'non calculable'.
    """
    arbre = ast.parse(formule, mode="eval")
    return _visiter(arbre.body, variables, formule)


def _visiter(noeud: ast.AST, variables: dict[str, Any], formule: str) -> float:
    if isinstance(noeud, ast.Constant):
        if not isinstance(noeud.value, (int, float)):
            raise EvaluationError(f"Constante non numérique dans '{formule}'")
        return float(noeud.value)
    if isinstance(noeud, ast.Name):
        if noeud.id not in variables:
            raise EvaluationError(f"Variable '{noeud.id}' absente")
        val = variables[noeud.id]
        if val is None:
            raise EvaluationError(f"Variable '{noeud.id}' vaut None")
        return float(val)
    if isinstance(noeud, ast.BinOp):
        g = _visiter(noeud.left, variables, formule)
        d = _visiter(noeud.right, variables, formule)
        op = _OP_BINAIRES.get(type(noeud.op))
        if op is None:
            raise EvaluationError(f"Opérateur binaire interdit : {type(noeud.op).__name__}")
        try:
            return op(g, d)
        except ZeroDivisionError:
            raise EvaluationError("Division par zéro")
    if isinstance(noeud, ast.UnaryOp):
        v = _visiter(noeud.operand, variables, formule)
        op = _OP_UNAIRES.get(type(noeud.op))
        if op is None:
            raise EvaluationError(f"Opérateur unaire interdit : {type(noeud.op).__name__}")
        return op(v)
    if isinstance(noeud, ast.Call):
        if not isinstance(noeud.func, ast.Name):
            raise EvaluationError("Appel de fonction indirect interdit")
        nom = noeud.func.id
        if nom not in _FONCTIONS_AUTORISEES:
            raise EvaluationError(f"Fonction non autorisée : {nom}")
        args = [_visiter(a, variables, formule) for a in noeud.args]
        return float(_FONCTIONS_AUTORISEES[nom](*args))
    raise EvaluationError(f"Nœud AST interdit : {type(noeud).__name__}")


# ------------------------------------------------------ MOTEUR DE RATIOS ----
@dataclass
class ResultatRatio:
    id: str
    famille: str
    valeur: Optional[float]
    unite: str
    sens_favorable: str
    repere: Optional[dict] = None
    note: Optional[str] = None
    formule: Optional[str] = None


def _construire_contexte(e: EtatsFinanciers) -> dict[str, Any]:
    """Toutes les variables des formules. Dérive la TVA 19 % pour DPO."""
    ctx = e.model_dump()
    # Variable dérivée du cours : achats TTC = (achats + autres charges) × 1.19
    achats = (e.achats_approvisionnements or 0) + (e.autres_charges_exploitation or 0)
    ctx["achats_ttc"] = achats * 1.19 if achats else None
    return ctx


def charger_ratios(chemin_yaml: str | Path) -> list[dict]:
    """Charge la configuration des ratios depuis le YAML."""
    with Path(chemin_yaml).open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def calculer_ratios(
    e: EtatsFinanciers,
    chemin_yaml: str | Path,
) -> list[ResultatRatio]:
    """Calcule tous les ratios du YAML pour un exercice donné."""
    config = charger_ratios(chemin_yaml)
    ctx = _construire_contexte(e)
    resultats: list[ResultatRatio] = []

    for r in config:
        rid = r["id"]
        famille = r["famille"]
        formule = r["formule"]
        unite = r.get("unite", "ratio")
        sens = r.get("sens_favorable", "neutre")
        repere = r.get("repere")
        garde_fou = r.get("garde_fou", {})

        # Garde-fou capitaux propres négatifs
        if (
            garde_fou.get("capitaux_propres_negatifs") == "non_significatif"
            and e.capitaux_propres is not None
            and e.capitaux_propres < 0
        ):
            resultats.append(ResultatRatio(
                id=rid, famille=famille, valeur=None, unite=unite,
                sens_favorable=sens, repere=repere, formule=formule,
                note="Non significatif : capitaux propres négatifs",
            ))
            continue

        # Garde-fou stocks nuls (ex. DIO Société X)
        if (
            garde_fou.get("stocks_nuls") == "non_applicable"
            and (e.stocks is None or e.stocks == 0)
        ):
            resultats.append(ResultatRatio(
                id=rid, famille=famille, valeur=None, unite=unite,
                sens_favorable=sens, repere=repere, formule=formule,
                note="Non applicable : pas de stocks",
            ))
            continue

        try:
            val = evaluer_formule(formule, ctx)
            resultats.append(ResultatRatio(
                id=rid, famille=famille, valeur=val, unite=unite,
                sens_favorable=sens, repere=repere, formule=formule,
            ))
        except EvaluationError as exc:
            resultats.append(ResultatRatio(
                id=rid, famille=famille, valeur=None, unite=unite,
                sens_favorable=sens, repere=repere, formule=formule,
                note=f"Non calculable : {exc}",
            ))

    return resultats


def common_size(e: EtatsFinanciers) -> dict[str, float]:
    """Lecture verticale : chaque poste du bilan en pourcentage du total.

    Renvoie un dict des parts (entre 0 et 1) pour les grandeurs clés.
    Utile pour la lecture C1 du corrigé ch.1.
    """
    if not e.actif_total:
        return {}
    at = e.actif_total
    tp = e.total_passif or at
    return {
        "actifs_non_courants_pct": (e.actifs_non_courants or 0) / at,
        "actifs_courants_pct": (e.actifs_courants or 0) / at,
        "liquidites_pct": (e.liquidites or 0) / at,
        "capitaux_propres_pct": (e.capitaux_propres or 0) / tp,
        "passifs_non_courants_pct": (e.passifs_non_courants or 0) / tp,
        "passifs_courants_pct": (e.passifs_courants or 0) / tp,
    }
