"""Correspondance sémantique des libellés (ch.1 lot 2).

Deux niveaux :
1. YAML d'alias + regex : rapide et déterministe.
2. Fuzzy matching (rapidfuzz, score ≥ 85) pour les libellés hors alias.

Les postes non reconnus sont journalisés. Un rapport précision/rappel
est produit à partir d'un jeu annoté.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from rapidfuzz import fuzz, process


def normaliser(texte: str) -> str:
    """Minuscule, sans accents, espaces compactés, apostrophes unifiées."""
    if not isinstance(texte, str):
        return ""
    t = unicodedata.normalize("NFD", texte)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.lower().strip().replace("’", "'")
    return " ".join(t.split())


@dataclass
class ResultatMapping:
    libelle_source: str
    champ_pivot: Optional[str]
    methode: str  # "alias", "regex", "fuzzy", "aucun"
    score: Optional[float] = None


@dataclass
class RapportMapping:
    resultats: list[ResultatMapping] = field(default_factory=list)
    non_reconnus: list[str] = field(default_factory=list)

    def precision_rappel(self, verite: dict[str, str]) -> dict:
        """Calcule précision et rappel sur un dict {libellé: champ_attendu}."""
        vp = fp = fn = 0
        for libelle, champ_attendu in verite.items():
            trouve = next(
                (r for r in self.resultats if r.libelle_source == libelle),
                None,
            )
            if trouve and trouve.champ_pivot == champ_attendu:
                vp += 1
            elif trouve and trouve.champ_pivot:
                fp += 1
            else:
                fn += 1
        precision = vp / (vp + fp) if (vp + fp) else 0
        rappel = vp / (vp + fn) if (vp + fn) else 0
        return {"vp": vp, "fp": fp, "fn": fn, "precision": precision, "rappel": rappel}


class MapperLibelles:
    """Mappe des libellés comptables vers les champs du pivot."""

    def __init__(self, chemin_yaml: str | Path, seuil_fuzzy: int = 85):
        with Path(chemin_yaml).open(encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.seuil_fuzzy = seuil_fuzzy
        self._index_alias: dict[str, str] = {}
        self._regex: list[tuple[re.Pattern, str]] = []
        self._tous_alias_normalises: list[tuple[str, str]] = []  # (alias_norm, champ)
        for champ, config in self.config["mapping"].items():
            for alias in config.get("alias", []):
                a = normaliser(alias)
                self._index_alias[a] = champ
                self._tous_alias_normalises.append((a, champ))
            for pattern in config.get("regex", []):
                self._regex.append((re.compile(pattern, re.IGNORECASE), champ))

    def mapper(self, libelle: str) -> ResultatMapping:
        norm = normaliser(libelle)
        if not norm:
            return ResultatMapping(libelle, None, "aucun")

        # 1. Alias exact
        if norm in self._index_alias:
            return ResultatMapping(libelle, self._index_alias[norm], "alias", 100.0)

        # 2. Regex
        for pat, champ in self._regex:
            if pat.search(libelle):
                return ResultatMapping(libelle, champ, "regex", 100.0)

        # 3. Fuzzy sur les alias
        if self._tous_alias_normalises:
            candidats = [a for a, _ in self._tous_alias_normalises]
            best = process.extractOne(
                norm, candidats, scorer=fuzz.token_sort_ratio,
            )
            if best and best[1] >= self.seuil_fuzzy:
                champ = dict(self._tous_alias_normalises)[best[0]]
                return ResultatMapping(libelle, champ, "fuzzy", float(best[1]))

        return ResultatMapping(libelle, None, "aucun")

    def mapper_liste(self, libelles: list[str]) -> RapportMapping:
        resultats = [self.mapper(l) for l in libelles]
        non_rec = [r.libelle_source for r in resultats if r.champ_pivot is None]
        return RapportMapping(resultats=resultats, non_reconnus=non_rec)
