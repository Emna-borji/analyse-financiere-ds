"""Typologie des 6 situations financières (ch.2, partie A §5)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Situation:
    numero: int
    nom: str
    lecture: str


_SITUATIONS = {
    (True, True, True): Situation(1, "Équilibre",
        "Le FRNG finance tout le BFR et dégage un excédent de trésorerie. "
        "Attention à l'excès de trésorerie oisive."),
    (True, True, False): Situation(2, "FRNG insuffisant",
        "Une partie du BFR est financée par des concours bancaires. "
        "Situation fréquente mais à surveiller."),
    (True, False, True): Situation(3, "Très confortable",
        "L'exploitation dégage des ressources et le FRNG est positif."),
    (False, False, True): Situation(4, "Grande distribution",
        "Typique de la grande distribution : les ressources d'exploitation "
        "financent une partie des immobilisations. Risquée si l'activité baisse."),
    (False, False, False): Situation(5, "Déséquilibre grave",
        "Même les ressources d'exploitation ne suffisent pas."),
    (False, True, False): Situation(6, "Critique",
        "Les immobilisations et le BFR sont financés par la banque à court terme."),
}


def classer(frng: float, bfr: float, tn: float) -> Situation:
    """Retourne la situation typologique d'un bilan fonctionnel.

    Convention : seuil strict à 0 pour chaque grandeur.
    """
    cle = (frng > 0, bfr > 0, tn > 0)
    if cle in _SITUATIONS:
        return _SITUATIONS[cle]
    # Cas limite non répertorié (ex. FRNG > 0, BFR < 0, TN < 0 impossible
    # si FRNG = BFR + TN). On renvoie la situation la plus proche par
    # cohérence TN = FRNG − BFR.
    return Situation(0, "Non classée",
        f"Cas non prévu dans la typologie : FRNG={frng:.0f}, BFR={bfr:.0f}, TN={tn:.0f}")
