"""Actualise le benchmark reel EDGAR pour une annee donnee.

Usage :
    export EDGAR_USER_AGENT="Mon Nom (mon.email@exemple.com)"
    python -m scripts.actualiser_benchmark_edgar 2023

Produit `data/ch1/benchmark_edgar_frames_YYYY.csv`. Les requetes sont
mises en cache dans `.cache/edgar/` (gitignore) pour ne pas retelecharger.
"""
import argparse
from datetime import date
from pathlib import Path

from analyse_financiere.benchmark_edgar import (
    construire_benchmark_edgar, exporter_csv,
)


RACINE = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("annee", type=int, help="Exercice fiscal (ex. 2023)")
    args = parser.parse_args()

    cache = RACINE / ".cache" / "edgar"
    bench = construire_benchmark_edgar(args.annee, cache_dir=cache)

    source = f"SEC EDGAR Frames API (us-gaap), telecharge {date.today().isoformat()}"
    chemin = exporter_csv(
        bench,
        RACINE / "data" / "ch1" / f"benchmark_edgar_frames_{args.annee}.csv",
        source,
    )
    print(f"OK : benchmark EDGAR {args.annee} - {bench.n_entreprises} societes - {chemin}")


if __name__ == "__main__":
    main()
