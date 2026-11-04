"""Restitution HTML autonome d'un diagnostic (ch.1 lot 7).

Produit un fichier HTML avec :
- tableau des ratios + feux (vert/orange/rouge selon seuils du cours),
- cascade des SIG,
- bilan fonctionnel condensé et retraité,
- commentaire rédigé.

Utilise des SVG inline pour les graphiques (waterfall SIG, feux). Pas de
dépendance externe au-delà de Jinja2 et pandas.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from jinja2 import Template

from .commentaire import commenter
from .pivot import EtatsFinanciers
from .ratios import ResultatRatio
from .reclassement import BilanFonctionnel
from .sig_caf import CAF, SIG
from .typologie import Situation


def feu(ratio: ResultatRatio) -> str:
    """Retourne la couleur du feu (vert / orange / rouge / gris)."""
    if ratio.valeur is None:
        return "gris"
    rep = ratio.repere
    if not rep:
        return "gris"
    seuil = rep.get("seuil")
    op = rep.get("operateur", "~")
    v = ratio.valeur
    if seuil is None:
        return "gris"
    if op == ">":
        if v >= seuil:
            return "vert"
        if v >= 0.8 * seuil:
            return "orange"
        return "rouge"
    if op == "<":
        if v <= seuil:
            return "vert"
        if v <= 1.2 * seuil:
            return "orange"
        return "rouge"
    if op == "~":
        if 0.9 * seuil <= v <= 1.1 * seuil:
            return "vert"
        return "orange"
    return "gris"


def _fmt_valeur(r: ResultatRatio) -> str:
    if r.valeur is None:
        return "n/c"
    if r.unite == "pourcentage":
        return f"{r.valeur*100:.1f} %"
    if r.unite == "jours":
        return f"{r.valeur:.0f} j"
    if r.unite == "annees":
        return f"{r.valeur:.2f} ans"
    return f"{r.valeur:.2f}"


def _svg_waterfall_sig(sig: SIG) -> str:
    """Rend un petit waterfall SVG des SIG (CA → RN)."""
    etapes = [
        ("Revenus", sig.production_exercice, "#4caf50"),
        ("− Conso.", -sig.consommations_intermediaires, "#f44336"),
        ("= VA", sig.valeur_ajoutee, "#2196f3"),
        ("− Personnel", -(sig.valeur_ajoutee - sig.ebe), "#f44336"),
        ("= EBE", sig.ebe, "#2196f3"),
        ("− Dotations", -(sig.ebe - sig.rex), "#f44336"),
        ("= REX", sig.rex, "#2196f3"),
        ("± Fin./autres", sig.rcai - sig.rex, "#9e9e9e"),
        ("= RCAI", sig.rcai, "#2196f3"),
        ("− Impôt", sig.rcai - sig.resultat_net, "#f44336"),
        ("= RN", sig.resultat_net, "#1976d2"),
    ]
    hauteur = 300
    largeur = 700
    marge_g = 90
    marge_b = 40
    plage_x = largeur - marge_g - 20
    max_abs = max(abs(sig.production_exercice), 1)
    pas_x = plage_x / len(etapes)
    bars = []
    for i, (nom, val, couleur) in enumerate(etapes):
        x = marge_g + i * pas_x
        base_y = hauteur - marge_b
        h = abs(val) / max_abs * (hauteur - marge_b - 20)
        y = base_y - h if val >= 0 else base_y
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{pas_x*0.8:.1f}" height="{h:.1f}" fill="{couleur}" />'
            f'<text x="{x + pas_x*0.4:.1f}" y="{hauteur - 10:.1f}" font-size="10" text-anchor="middle">{nom}</text>'
            f'<text x="{x + pas_x*0.4:.1f}" y="{y - 4:.1f}" font-size="9" text-anchor="middle">{val:,.0f}</text>'
        )
    return (
        f'<svg viewBox="0 0 {largeur} {hauteur}" width="100%" style="max-width:800px">'
        + "".join(bars).replace(",", " ")
        + "</svg>"
    )


_GABARIT_HTML = Template("""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>{{ entreprise }} — Diagnostic {{ annee }}</title>
  <style>
    body { font-family: -apple-system, system-ui, 'Segoe UI', sans-serif;
           max-width: 980px; margin: 2em auto; padding: 0 1em; color: #222; }
    h1, h2 { color: #1a3a6a; }
    h1 { border-bottom: 2px solid #1a3a6a; padding-bottom: 0.3em; }
    h2 { margin-top: 2em; }
    table { border-collapse: collapse; width: 100%; margin: 1em 0; }
    th, td { padding: 6px 10px; border: 1px solid #ddd; text-align: left; }
    th { background: #f5f5f5; }
    .feu { display: inline-block; width: 12px; height: 12px; border-radius: 50%;
           vertical-align: middle; margin-right: 6px; }
    .vert { background: #4caf50; }
    .orange { background: #ff9800; }
    .rouge { background: #f44336; }
    .gris { background: #9e9e9e; }
    .encart { background: #fff8e1; border-left: 4px solid #ff9800;
              padding: 0.8em 1.2em; margin: 1em 0; }
    .force { background: #e8f5e9; border-left: 4px solid #4caf50;
             padding: 0.5em 1em; margin: 0.5em 0; }
    .risque { background: #ffebee; border-left: 4px solid #f44336;
              padding: 0.5em 1em; margin: 0.5em 0; }
    .meta { color: #666; font-size: 0.9em; }
  </style>
</head>
<body>
  <h1>{{ entreprise }} — Diagnostic financier {{ annee }}</h1>
  <p class="meta">Référentiel : {{ referentiel }} · Devise : {{ devise }} · Source : {{ source }}</p>

  <h2>1. Chiffres clés</h2>
  <table>
    <tr><td>Chiffre d'affaires</td><td>{{ fmt(e.ca) }} TND</td></tr>
    <tr><td>EBE</td><td>{{ fmt(sig.ebe) }} TND</td></tr>
    <tr><td>Résultat net</td><td>{{ fmt(sig.resultat_net) }} TND</td></tr>
    <tr><td>Total actif</td><td>{{ fmt(e.actif_total) }} TND</td></tr>
    <tr><td>Capitaux propres</td><td>{{ fmt(e.capitaux_propres) }} TND</td></tr>
  </table>

  <h2>2. Ratios et feux</h2>
  <table>
    <tr><th>Famille</th><th>Ratio</th><th>Valeur</th><th>Repère</th><th></th></tr>
    {% for r in ratios %}
    <tr>
      <td>{{ r.famille }}</td>
      <td>{{ r.id }}</td>
      <td>{{ fmt_r(r) }}</td>
      <td>{{ repere(r) }}</td>
      <td><span class="feu {{ feu(r) }}"></span></td>
    </tr>
    {% endfor %}
  </table>

  <h2>3. Soldes intermédiaires de gestion</h2>
  {{ waterfall|safe }}

  <h2>4. CAF</h2>
  <table>
    <tr><td>CAF méthode soustractive</td><td>{{ fmt(caf.caf_soustractive) }} TND</td></tr>
    <tr><td>CAF méthode additive</td><td>{{ fmt(caf.caf_additive) }} TND</td></tr>
    <tr><td>Concordance</td><td>{{ "OK" if caf.concordance_ok else "écart %.2f"|format(caf.ecart) }}</td></tr>
    <tr><td>Capacité de remboursement</td><td>{{ "%.2f"|format(caf.capacite_remboursement) if caf.capacite_remboursement else "n/c" }} années</td></tr>
    {% if caf.autofinancement %}<tr><td>Autofinancement</td><td>{{ fmt(caf.autofinancement) }} TND</td></tr>{% endif %}
  </table>

  <h2>5. Bilan fonctionnel</h2>
  <table>
    <tr><th></th><th>Sans retraitement</th><th>Retraité (crédit-bail + EENE + hors expl.)</th></tr>
    <tr><td>Emplois stables</td><td>{{ fmt(bf.emplois_stables.total) }}</td><td>{{ fmt(bf_r.emplois_stables.total) }}</td></tr>
    <tr><td>Ressources stables</td><td>{{ fmt(bf.ressources_stables.total) }}</td><td>{{ fmt(bf_r.ressources_stables.total) }}</td></tr>
    <tr><td><b>FRNG</b></td><td><b>{{ fmt(bf.frng) }}</b></td><td><b>{{ fmt(bf_r.frng) }}</b></td></tr>
    <tr><td>BFR</td><td>{{ fmt(bf.bfr) }}</td><td>{{ fmt(bf_r.bfr) }}</td></tr>
    <tr><td>Trésorerie nette</td><td>{{ fmt(bf.tn) }}</td><td>{{ fmt(bf_r.tn) }}</td></tr>
  </table>
  <div class="encart">
    <b>Situation typologique :</b> {{ situation.numero }} — {{ situation.nom }}.<br>
    {{ situation.lecture }}
  </div>

  <h2>6. Diagnostic</h2>
  {% for a in forces %}<div class="force"><b>Force :</b> {{ a.message }}</div>{% endfor %}
  {% for a in attentions %}<div class="encart"><b>Attention :</b> {{ a.message }}</div>{% endfor %}
  {% for a in risques %}<div class="risque"><b>Risque :</b> {{ a.message }}</div>{% endfor %}

  <p class="meta">Rapport généré par <code>analyse-financiere-ds</code>. Références : PDF Chapitre 1 et Chapitre 2 (Master Data Science — Analyse Financière).</p>
</body>
</html>""")


def _fmt_nombre(v: Optional[float]) -> str:
    if v is None:
        return "n/c"
    return f"{v:,.0f}".replace(",", " ")


def _repere(r: ResultatRatio) -> str:
    rep = r.repere
    if not rep:
        return "—"
    s, op = rep.get("seuil"), rep.get("operateur", "~")
    return f"{op} {s}"


def rendre_rapport_html(
    e: EtatsFinanciers,
    ratios: list[ResultatRatio],
    sig: SIG,
    caf: CAF,
    bf: BilanFonctionnel,
    bf_retraite: BilanFonctionnel,
    situation: Situation,
    chemin_sortie: str | Path,
) -> Path:
    """Génère le rapport HTML et retourne le chemin produit."""
    from .commentaire import regles_expertes

    alertes = regles_expertes(e, ratios, sig, caf, bf_retraite, situation)
    forces = [a for a in alertes if a.niveau == "force"]
    attentions = [a for a in alertes if a.niveau == "attention"]
    risques = [a for a in alertes if a.niveau == "risque"]

    html = _GABARIT_HTML.render(
        entreprise=e.entreprise, annee=e.annee,
        referentiel=e.referentiel, devise=e.devise, source=e.source,
        e=e, sig=sig, caf=caf, bf=bf, bf_r=bf_retraite,
        situation=situation, ratios=ratios,
        waterfall=_svg_waterfall_sig(sig),
        forces=forces, attentions=attentions, risques=risques,
        fmt=_fmt_nombre, fmt_r=_fmt_valeur, feu=feu, repere=_repere,
    )
    chemin = Path(chemin_sortie)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(html, encoding="utf-8")
    return chemin


def diagnostic_complet(
    e: EtatsFinanciers,
    chemin_ratios_yaml: str | Path,
    chemin_reclassement_yaml: str | Path,
    chemin_sortie_html: str | Path,
) -> dict:
    """Pipeline complet pour un exercice : ratios, SIG, CAF, bilans, situation, rapport HTML."""
    from .ratios import calculer_ratios
    from .sig_caf import calculer_sig, calculer_caf
    from .reclassement import construire_bilan_fonctionnel
    from .typologie import classer

    ratios = calculer_ratios(e, chemin_ratios_yaml)
    sig = calculer_sig(e)
    caf = calculer_caf(e, sig)
    bf = construire_bilan_fonctionnel(e, chemin_reclassement_yaml, avec_retraitements=False)
    bf_r = construire_bilan_fonctionnel(e, chemin_reclassement_yaml, avec_retraitements=True)
    situation = classer(bf_r.frng, bf_r.bfr, bf_r.tn)

    chemin = rendre_rapport_html(e, ratios, sig, caf, bf, bf_r, situation, chemin_sortie_html)
    return {
        "ratios": ratios, "sig": sig, "caf": caf,
        "bilan": bf, "bilan_retraite": bf_r,
        "situation": situation, "chemin_html": chemin,
    }
