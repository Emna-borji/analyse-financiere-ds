"""Règles expertes et commentaire automatique (ch.1 lot 6).

Produit un diagnostic rédigé en français simple, basé sur des règles
expertes (sans LLM, sans heuristique opaque). Chaque alerte renvoie une
justification chiffrée que l'utilisateur peut tracer dans les données.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from jinja2 import Template

from .pivot import EtatsFinanciers
from .ratios import ResultatRatio
from .sig_caf import CAF, SIG
from .reclassement import BilanFonctionnel
from .typologie import Situation


@dataclass
class Alerte:
    niveau: str  # "force", "attention", "risque"
    message: str


def _get(ratios: list[ResultatRatio], rid: str) -> Optional[float]:
    for r in ratios:
        if r.id == rid:
            return r.valeur
    return None


def regles_expertes(
    e: EtatsFinanciers,
    ratios: list[ResultatRatio],
    sig: SIG,
    caf: CAF,
    bilan_fonctionnel: BilanFonctionnel,
    situation: Situation,
) -> list[Alerte]:
    """Appliquer les règles du cours et renvoyer les alertes."""
    alertes: list[Alerte] = []

    # --- Liquidité ---
    lg = _get(ratios, "liquidite_generale")
    li = _get(ratios, "liquidite_immediate")
    if lg is not None and lg < 1:
        alertes.append(Alerte("risque",
            f"Liquidité générale {lg:.2f} < 1 : les actifs courants ne couvrent pas les dettes à court terme."))
    elif lg is not None and lg > 1.5:
        alertes.append(Alerte("force",
            f"Liquidité générale {lg:.2f} > 1,5 : marge de sécurité confortable sur le court terme."))
    if li is not None and li < 0.2:
        alertes.append(Alerte("risque",
            f"Liquidité immédiate {li:.2f} < 0,2 : seulement {li*100:.0f} % des dettes à CT sont payables immédiatement."))

    # --- Structure / endettement ---
    af = _get(ratios, "autonomie_financiere")
    gearing = _get(ratios, "gearing")
    dn_ebitda = _get(ratios, "dette_nette_ebitda")
    cov = _get(ratios, "couverture_interets")
    if af is not None and af < 0.33:
        alertes.append(Alerte("risque",
            f"Autonomie financière {af*100:.1f} % < 33 % : forte dépendance aux financements externes."))
    if gearing is not None and gearing > 1:
        alertes.append(Alerte("attention",
            f"Gearing {gearing:.2f} > 1 : dette nette supérieure aux capitaux propres."))
    if dn_ebitda is not None and dn_ebitda > 3:
        alertes.append(Alerte("risque",
            f"Dette nette / EBITDA = {dn_ebitda:.2f} > 3 : covenant bancaire usuel franchi."))
    if cov is not None and cov < 3:
        alertes.append(Alerte("attention",
            f"Couverture des intérêts {cov:.2f} < 3 : marge de sécurité faible pour servir la dette."))

    # --- Rentabilité ---
    marge_n = _get(ratios, "marge_nette")
    roe = _get(ratios, "roe")
    if marge_n is not None and marge_n > 0.2:
        alertes.append(Alerte("force",
            f"Marge nette {marge_n*100:.1f} % : rentabilité très au-dessus de la médiane sectorielle usuelle."))
    if roe is not None and roe > 0.2:
        alertes.append(Alerte("force", f"ROE {roe*100:.1f} % : excellente rémunération des actionnaires."))
    if marge_n is not None and marge_n < 0:
        alertes.append(Alerte("risque", f"Marge nette négative ({marge_n*100:.1f} %) : l'activité détruit de la valeur."))

    # --- Activité ---
    dso = _get(ratios, "dso")
    dpo = _get(ratios, "dpo")
    if dso is not None and dpo is not None and dpo > dso + 15:
        alertes.append(Alerte("attention",
            f"DPO {dpo:.0f} j largement supérieur au DSO {dso:.0f} j : signe possible de tension de trésorerie (l'entreprise paie ses fournisseurs plus lentement qu'elle n'est payée)."))

    # --- CAF / autofinancement ---
    if caf.capacite_remboursement is not None and caf.capacite_remboursement > 4:
        alertes.append(Alerte("risque",
            f"Capacité de remboursement {caf.capacite_remboursement:.1f} années > 4 : la CAF ne suffit pas à rembourser la dette dans un horizon raisonnable."))
    if caf.autofinancement is not None and e.dividendes and e.dividendes > 0.5 * caf.caf_soustractive:
        pct = e.dividendes / caf.caf_soustractive * 100
        alertes.append(Alerte("attention",
            f"Dividendes distribués = {pct:.0f} % de la CAF : l'autofinancement est faible malgré une CAF suffisante."))

    # --- Équilibre fonctionnel ---
    if situation.numero == 2:
        alertes.append(Alerte("attention",
            f"Situation {situation.numero} ({situation.nom}) : {situation.lecture}"))
    elif situation.numero in (5, 6):
        alertes.append(Alerte("risque",
            f"Situation {situation.numero} ({situation.nom}) : {situation.lecture}"))

    # Combinaison classique : liquidité immédiate faible ET DPO en forte hausse
    if li is not None and li < 0.2 and dpo is not None and dpo > 60:
        alertes.append(Alerte("risque",
            "Combinaison liquidité immédiate faible + DPO élevé : forte probabilité de tension de trésorerie à surveiller."))

    return alertes


# Gabarit Jinja2 pour le commentaire rédigé
_GABARIT = Template("""
## Diagnostic financier — {{ entreprise }} ({{ annee }})

**Chiffre d'affaires** : {{ ca_fmt }} TND
**Résultat net** : {{ rn_fmt }} TND
**Structure fonctionnelle** : {{ situation.nom }} (situation {{ situation.numero }}/6)

### Soldes intermédiaires de gestion
- Valeur ajoutée : {{ va_fmt }} TND ({{ taux_va }} % du CA)
- EBE : {{ ebe_fmt }} TND
- REX : {{ rex_fmt }} TND
- Résultat net : {{ rn_fmt }} TND

### Capacité d'autofinancement
- CAF : {{ caf_fmt }} TND
- Capacité de remboursement : {{ cap_remb }} années
{% if autofinancement %}- Autofinancement (CAF − dividendes) : {{ autofinancement }} TND{% endif %}

### Équilibre fonctionnel
- FRNG : {{ frng_fmt }} TND
- BFR : {{ bfr_fmt }} TND
- Trésorerie nette : {{ tn_fmt }} TND
- Situation : **{{ situation.nom }}** — {{ situation.lecture }}

### Forces
{% for a in forces %}- {{ a.message }}
{% endfor %}

### Points d'attention
{% for a in attentions %}- {{ a.message }}
{% endfor %}

### Risques
{% for a in risques %}- {{ a.message }}
{% endfor %}
""".strip())


def _fmt(val: Optional[float]) -> str:
    if val is None:
        return "n/c"
    return f"{val:,.0f}".replace(",", " ")


def commenter(
    e: EtatsFinanciers,
    ratios: list[ResultatRatio],
    sig: SIG,
    caf: CAF,
    bf: BilanFonctionnel,
    situation: Situation,
) -> str:
    """Rend un commentaire Markdown complet pour un exercice."""
    alertes = regles_expertes(e, ratios, sig, caf, bf, situation)
    forces = [a for a in alertes if a.niveau == "force"]
    attentions = [a for a in alertes if a.niveau == "attention"]
    risques = [a for a in alertes if a.niveau == "risque"]

    return _GABARIT.render(
        entreprise=e.entreprise,
        annee=e.annee,
        ca_fmt=_fmt(e.ca),
        rn_fmt=_fmt(sig.resultat_net),
        va_fmt=_fmt(sig.valeur_ajoutee),
        taux_va=f"{sig.taux_valeur_ajoutee*100:.1f}" if sig.taux_valeur_ajoutee else "n/c",
        ebe_fmt=_fmt(sig.ebe),
        rex_fmt=_fmt(sig.rex),
        caf_fmt=_fmt(caf.caf_soustractive),
        cap_remb=f"{caf.capacite_remboursement:.2f}" if caf.capacite_remboursement else "n/c",
        autofinancement=_fmt(caf.autofinancement) if caf.autofinancement else None,
        frng_fmt=_fmt(bf.frng),
        bfr_fmt=_fmt(bf.bfr),
        tn_fmt=_fmt(bf.tn),
        situation=situation,
        forces=forces,
        attentions=attentions,
        risques=risques,
    )
