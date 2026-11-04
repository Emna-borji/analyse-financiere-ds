"""Génère les rapports HTML pour toutes les entreprises disponibles."""
from pathlib import Path

from analyse_financiere.adapters.sce_excel import charger_societe_x
from analyse_financiere.restitution import diagnostic_complet


RACINE = Path(__file__).resolve().parent.parent


def main() -> None:
    # Société X
    etats = charger_societe_x(
        RACINE / "data" / "ch1" / "CAS_1_Societe_X_SCE_2023_2022.xlsx",
        RACINE / "data" / "ch2" / "societe_x_retraitements.yaml",
    )
    sortie = RACINE / "reports"
    sortie.mkdir(exist_ok=True)
    for e in etats:
        out = sortie / f"{e.entreprise}_{e.annee}.html"
        res = diagnostic_complet(
            e,
            RACINE / "config" / "ratios.yaml",
            RACINE / "config" / "reclassement.yaml",
            out,
        )
        print(f"{e.annee}: {out.name} — Situation {res['situation'].numero} ({res['situation'].nom})")


if __name__ == "__main__":
    main()
