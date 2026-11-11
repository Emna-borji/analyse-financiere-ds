"""Calcule FRNG, BFR, TN et la situation typologique pour chaque exercice
Monoprix disponible (2021-2024).

Enchaine : adaptateur PDF -> moteur de reclassement declaratif (YAML) ->
classification des 6 situations.

Usage :
    python -m scripts.monoprix_typologie
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from analyse_financiere.adapters.monoprix_pdf import charger_monoprix
from analyse_financiere.reclassement import construire_bilan_fonctionnel
from analyse_financiere.typologie import Situation, classer


RACINE = Path(__file__).resolve().parent.parent
PDFS_PAR_DEFAUT = [
    RACINE / "data" / "ch1" / "monoprix_pdfs" / "mnp-etats-financiers-annuels-individuels-31-12-2022.pdf",
    RACINE / "data" / "ch1" / "monoprix_pdfs" / "mnp-etats-financiers-annuels-individuels-31-12-2023.pdf",
    RACINE / "data" / "ch1" / "monoprix_pdfs" / "mnp-etats-financiers-annuels-individuels-31-12-2024.pdf",
]
REGLES_DEFAUT = RACINE / "config" / "reclassement.yaml"


@dataclass
class ResultatMonoprix:
    annee: int
    frng: float
    bfr: float
    tn: float
    situation: Situation


def calculer_monoprix_typologie(
    pdfs: list[Path] | None = None,
    regles_yaml: Path | None = None,
) -> list[ResultatMonoprix]:
    """Calcule FRNG, BFR, TN et la situation pour chaque exercice Monoprix.

    Retourne la liste triee par annee.
    """
    pdfs = pdfs or PDFS_PAR_DEFAUT
    regles_yaml = regles_yaml or REGLES_DEFAUT
    etats = {e.annee: e for e in charger_monoprix([str(p) for p in pdfs])}
    resultats = []
    for annee in sorted(etats):
        bf = construire_bilan_fonctionnel(etats[annee], str(regles_yaml))
        situation = classer(bf.frng, bf.bfr, bf.tn)
        resultats.append(ResultatMonoprix(
            annee=annee, frng=bf.frng, bfr=bf.bfr, tn=bf.tn, situation=situation,
        ))
    return resultats


def main() -> None:
    resultats = calculer_monoprix_typologie()
    print(f"{'Annee':<6}{'FRNG':>18}{'BFR':>18}{'TN':>18}  Situation")
    print("-" * 90)
    for r in resultats:
        print(
            f"{r.annee:<6}{r.frng:>18,.0f}{r.bfr:>18,.0f}{r.tn:>18,.0f}"
            f"  {r.situation.numero} {r.situation.nom}"
        )
        identite = r.frng - r.bfr - r.tn
        print(f"       (identite FRNG - BFR - TN = {identite:+.2f} TND)")


if __name__ == "__main__":
    main()
