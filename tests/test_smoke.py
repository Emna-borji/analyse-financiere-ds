"""Tests de fumée du lot 0.

Vérifient que l'ossature du projet est en place : les fichiers YAML
reconstruits se chargent correctement et contiennent les clés attendues.
Ces tests ne couvrent aucune logique métier — ils garantissent juste que
la CI est verte dès le lot 0 et que les futures régressions de
reconstitution de données seront attrapées tôt.
"""
from pathlib import Path

import yaml


RACINE = Path(__file__).resolve().parent.parent


def test_societe_x_retraitements_yaml_chargeable():
    chemin = RACINE / "data" / "ch2" / "societe_x_retraitements.yaml"
    with chemin.open(encoding="utf-8") as f:
        donnees = yaml.safe_load(f)

    # Les deux exercices du corrigé doivent être présents.
    assert set(donnees["exercices"].keys()) == {"2022", "2023"}

    # Les montants qui alimentent le corrigé C2 (CAF 2023) doivent être exacts.
    e2023 = donnees["exercices"]["2023"]
    assert e2023["charges_financieres_nettes"] == 221611
    assert e2023["autres_gains_ordinaires"] == 15198
    assert e2023["autres_pertes_ordinaires"] == 787
    assert e2023["credit_bail_valeur_origine"] == 600000
    assert e2023["credit_bail_amort_cumules"] == 240000
