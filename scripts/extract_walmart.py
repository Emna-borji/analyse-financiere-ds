"""Extrait les grandeurs cles de Walmart depuis SEC EDGAR companyfacts.

Demonstration :
1. Deduplication : pour un meme (concept, end-date), plusieurs valeurs
   peuvent exister (depot original 10-K, amendement 10-K/A, comparatif 10-Q).
   Le script retient la plus recente (filed).
2. Conversion USD -> TND avec taux documente (BCT USD/TND au 31/01/2024).

Walmart cloture son exercice fiscal au 31 janvier (exercice decale) :
l'exercice 2023 (FY2024 Walmart) se termine au 31 janvier 2024.

Usage : python -m scripts.extract_walmart
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path


RACINE = Path(__file__).resolve().parent.parent
FICHIER = RACINE / "data" / "ch1" / "edgar_companyfacts" / "CIK0000104169_walmart.json"

# Taux de change BCT au 31 janvier 2024 (reference publique :
# https://www.bct.gov.tn/bct/siteprod/cours_archiv.jsp)
# 1 USD = 3,1217 TND (taux officiel de cloture).
TAUX_USD_TND_31_01_2024 = 3.1217
DATE_TAUX = "2024-01-31"
SOURCE_TAUX = "Banque Centrale de Tunisie (BCT), cours de reference, 31/01/2024"

CONCEPTS = {
    "Assets": "actif_total",
    "StockholdersEquity": "capitaux_propres",
    "AssetsCurrent": "actifs_courants",
    "LiabilitiesCurrent": "passifs_courants",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "ca",
    "NetIncomeLoss": "resultat_net",
}


def extraire_concept(facts: dict, concept: str, end_cible: str) -> float | None:
    """Pour un concept XBRL et une date de fin, retourne la valeur la plus
    recente (plus grand `filed`) — gere donc la deduplication si plusieurs
    depots ont rapporte la meme date (10-K + 10-K/A + 10-Q comparatifs).
    """
    unit_data = facts.get("facts", {}).get("us-gaap", {}).get(concept, {}).get("units", {})
    rows_usd = unit_data.get("USD", [])
    rows_matching = [r for r in rows_usd if r.get("end") == end_cible]
    if not rows_matching:
        return None
    # Deduplication : plus recent `filed` l'emporte
    plus_recent = max(rows_matching, key=lambda r: r.get("filed", ""))
    return plus_recent.get("val")


def main() -> None:
    if not FICHIER.exists():
        raise FileNotFoundError(f"companyfacts manquant : {FICHIER}")
    with FICHIER.open(encoding="utf-8") as f:
        facts = json.load(f)
    print(f"Societe : {facts.get('entityName')}")
    print(f"CIK     : {facts.get('cik')}")
    print()

    end_cible = "2024-01-31"  # exercice 2024 Walmart (cloture janvier 2024)
    print(f"Grandeurs cles au {end_cible} (deduplication appliquee) :")
    print(f"{'Concept XBRL':<60s} {'USD (M)':>12s} {'TND (M)':>12s}")
    print("-" * 90)
    for concept, nom_pivot in CONCEPTS.items():
        val_usd = extraire_concept(facts, concept, end_cible)
        if val_usd is None:
            print(f"{concept:<60s} {'manquant':>12s} {'manquant':>12s}")
            continue
        val_tnd = val_usd * TAUX_USD_TND_31_01_2024
        print(
            f"{concept:<60s} {val_usd / 1e6:>12,.1f} {val_tnd / 1e6:>12,.1f}"
        )
    print()
    print(f"Taux USD/TND utilise : {TAUX_USD_TND_31_01_2024} au {DATE_TAUX}")
    print(f"Source : {SOURCE_TAUX}")


if __name__ == "__main__":
    main()
