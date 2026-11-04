"""Dashboard Streamlit — diagnostic d'une entreprise.

Lancer avec : streamlit run app.py

Permet de :
- charger un fichier SCE Excel + un YAML de retraitements,
- visualiser les ratios avec feux,
- parcourir la cascade des SIG,
- consulter le bilan fonctionnel (condensé et retraité),
- lire le commentaire automatique.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from analyse_financiere.adapters.sce_excel import charger_societe_x
from analyse_financiere.benchmark import charger_benchmark_csv
from analyse_financiere.commentaire import commenter, regles_expertes
from analyse_financiere.quality import controler, Niveau
from analyse_financiere.ratios import calculer_ratios
from analyse_financiere.reclassement import construire_bilan_fonctionnel
from analyse_financiere.restitution import feu
from analyse_financiere.scoring import calculer_score, donnees_radar
from analyse_financiere.sig_caf import calculer_caf, calculer_sig
from analyse_financiere.typologie import classer
from analyse_financiere.visualisations import (
    donnees_evolution_temporelle,
    donnees_heatmap_centiles,
    donnees_sankey,
    exporter_lineage_csv,
)


RACINE = Path(__file__).resolve().parent


st.set_page_config(page_title="Analyse financière — DS", layout="wide")
st.title("FinRatio Engine + FuncBalance")
st.caption("Master Data Science — Analyse financière. Données Société X par défaut ; cas réels à venir.")


@st.cache_data
def charger_defaut():
    etats = charger_societe_x(
        RACINE / "data" / "ch1" / "CAS_1_Societe_X_SCE_2023_2022.xlsx",
        RACINE / "data" / "ch2" / "societe_x_retraitements.yaml",
    )
    return {e.annee: e for e in etats}


etats = charger_defaut()
annees = sorted(etats)

# Sélection d'exercice
st.sidebar.header("Paramètres")
annee = st.sidebar.selectbox("Exercice", annees, index=len(annees) - 1)
e = etats[annee]

st.sidebar.write(f"**Entreprise :** {e.entreprise}")
st.sidebar.write(f"**Secteur :** {e.secteur}")
st.sidebar.write(f"**Devise :** {e.devise}")
st.sidebar.write(f"**Référentiel :** {e.referentiel}")
st.sidebar.write(f"**Source :** {e.source}")

# Contrôles qualité
with st.expander("Contrôles qualité", expanded=False):
    controles = controler(e)
    for c in controles:
        icone = {"OK": "✅", "Avertissement": "⚠️", "Bloquant": "❌"}.get(c.niveau.value, "")
        st.write(f"{icone} **{c.nom}** : {c.message}")

# Calculs pipelines
ratios = calculer_ratios(e, RACINE / "config" / "ratios.yaml")
sig = calculer_sig(e)
caf = calculer_caf(e, sig)
bf = construire_bilan_fonctionnel(e, RACINE / "config" / "reclassement.yaml")
bf_r = construire_bilan_fonctionnel(e, RACINE / "config" / "reclassement.yaml", avec_retraitements=True)
situation = classer(bf_r.frng, bf_r.bfr, bf_r.tn)

# Onglets
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["Ratios", "SIG & CAF", "Bilan fonctionnel",
     "Typologie & diagnostic", "Visualisations", "Données brutes"]
)

with tab1:
    st.header("Ratios et feux tricolores")
    lignes = []
    for r in ratios:
        couleur = feu(r)
        emoji = {"vert": "🟢", "orange": "🟠", "rouge": "🔴", "gris": "⚪"}[couleur]
        val = (
            f"{r.valeur*100:.1f} %" if r.valeur is not None and r.unite == "pourcentage"
            else f"{r.valeur:.0f} j" if r.valeur is not None and r.unite == "jours"
            else f"{r.valeur:.2f}" if r.valeur is not None
            else r.note or "n/c"
        )
        lignes.append({
            "Famille": r.famille,
            "Ratio": r.id,
            "Valeur": val,
            "Feu": emoji,
            "Formule": r.formule,
        })
    st.dataframe(pd.DataFrame(lignes), use_container_width=True, hide_index=True)

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cascade des SIG")
        df_sig = pd.DataFrame([
            {"Solde": "Production de l'exercice", "Montant": sig.production_exercice},
            {"Solde": "Consommations intermédiaires", "Montant": -sig.consommations_intermediaires},
            {"Solde": "Valeur ajoutée", "Montant": sig.valeur_ajoutee},
            {"Solde": "− Charges de personnel", "Montant": -(sig.valeur_ajoutee - sig.ebe)},
            {"Solde": "EBE", "Montant": sig.ebe},
            {"Solde": "− Dotations", "Montant": -(sig.ebe - sig.rex)},
            {"Solde": "REX", "Montant": sig.rex},
            {"Solde": "RCAI", "Montant": sig.rcai},
            {"Solde": "Résultat net", "Montant": sig.resultat_net},
        ])
        st.dataframe(df_sig, use_container_width=True, hide_index=True)
        if sig.taux_valeur_ajoutee:
            st.metric("Taux de valeur ajoutée", f"{sig.taux_valeur_ajoutee*100:.1f} %")
        if sig.taux_ebe:
            st.metric("Taux d'EBE", f"{sig.taux_ebe*100:.1f} %")

    with col2:
        st.subheader("Capacité d'autofinancement")
        st.metric("CAF (soustractive)", f"{caf.caf_soustractive:,.0f} TND".replace(",", " "))
        st.metric("CAF (additive)", f"{caf.caf_additive:,.0f} TND".replace(",", " "))
        st.metric(
            "Concordance",
            "✅ OK" if caf.concordance_ok else f"⚠️ écart {caf.ecart:.2f} TND",
        )
        if caf.capacite_remboursement is not None:
            st.metric("Capacité de remboursement", f"{caf.capacite_remboursement:.2f} années")
        if caf.autofinancement is not None:
            st.metric("Autofinancement", f"{caf.autofinancement:,.0f} TND".replace(",", " "))
        if e.dividendes:
            st.metric("Dividendes reconstitués", f"{e.dividendes:,.0f} TND".replace(",", " "))

with tab3:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Sans retraitement")
        df_bf = pd.DataFrame([
            {"Masse": "Emplois stables", "Montant": bf.emplois_stables.total},
            {"Masse": "Ressources stables", "Montant": bf.ressources_stables.total},
            {"Masse": "FRNG = RS − ES", "Montant": bf.frng},
            {"Masse": "ACE", "Montant": bf.actif_circulant_exploitation.total},
            {"Masse": "PCE", "Montant": bf.passif_circulant_exploitation.total},
            {"Masse": "BFR", "Montant": bf.bfr},
            {"Masse": "TA", "Montant": bf.tresorerie_active.total},
            {"Masse": "TP", "Montant": bf.tresorerie_passive.total},
            {"Masse": "TN = TA − TP", "Montant": bf.tn},
        ])
        st.dataframe(df_bf, use_container_width=True, hide_index=True)
        st.caption(f"Invariant FRNG − BFR − TN = {bf.frng - bf.bfr - bf.tn:.2f}")

    with col2:
        st.subheader("Retraité (crédit-bail + EENE + hors expl.)")
        df_bfr = pd.DataFrame([
            {"Masse": "Emplois stables (retraité)", "Montant": bf_r.emplois_stables.total},
            {"Masse": "Ressources stables (retraité)", "Montant": bf_r.ressources_stables.total},
            {"Masse": "FRNG (retraité)", "Montant": bf_r.frng},
            {"Masse": "ACE", "Montant": bf_r.actif_circulant_exploitation.total},
            {"Masse": "ACHE", "Montant": bf_r.actif_circulant_hors_exploitation.total},
            {"Masse": "PCE", "Montant": bf_r.passif_circulant_exploitation.total},
            {"Masse": "PCHE", "Montant": bf_r.passif_circulant_hors_exploitation.total},
            {"Masse": "BFRE", "Montant": bf_r.bfre},
            {"Masse": "BFRHE", "Montant": bf_r.bfrhe},
            {"Masse": "BFR total", "Montant": bf_r.bfr},
            {"Masse": "TN", "Montant": bf_r.tn},
        ])
        st.dataframe(df_bfr, use_container_width=True, hide_index=True)
        if e.ca:
            jours = bf_r.en_jours_de_ca(e.ca)
            st.metric("FRNG en jours de CA", f"{jours['frng_jours']:.1f} j")
            st.metric("BFR en jours de CA", f"{jours['bfr_jours']:.1f} j")
            st.metric("TN en jours de CA", f"{jours['tn_jours']:.1f} j")

with tab4:
    st.subheader(f"Situation {situation.numero} : {situation.nom}")
    st.info(situation.lecture)

    st.subheader("Diagnostic rédigé")
    md = commenter(e, ratios, sig, caf, bf_r, situation)
    st.markdown(md)

with tab5:
    st.subheader("Visualisations avancées")
    # Charger le benchmark EDGAR
    bench_path = RACINE / "data" / "ch1" / "benchmark_edgar_frames_2023.csv"
    if bench_path.exists():
        bench = charger_benchmark_csv(bench_path)
    else:
        bench = {}

    # ---- Radar (score par famille) ----
    st.markdown("### Radar par famille (vs. benchmark EDGAR)")
    ratios_map = {r.id: r.valeur for r in ratios}
    try:
        score = calculer_score(ratios_map, bench, e.entreprise, e.annee)
        radar = donnees_radar(score)
        import plotly.graph_objects as go

        axes = list(radar.keys())
        valeurs = [radar[a]["score"] for a in axes]
        valeurs_fermes = valeurs + [valeurs[0]]
        axes_fermes = axes + [axes[0]]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=valeurs_fermes, theta=axes_fermes, fill="toself",
                                      name=e.entreprise))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            f"Score global pondéré : **{score.score_global:.1f}/100**  "
            f"(rentabilité 40 % + solvabilité 30 % + liquidité 30 %)"
        )
    except Exception as exc:
        st.warning(f"Radar indisponible : {exc}")

    # ---- Heatmap centiles ----
    st.markdown("### Heatmap centiles (ratio × exercice)")
    ratios_par_annee = {}
    for an, et in etats.items():
        ratios_par_annee[an] = {
            r.id: r.valeur for r in calculer_ratios(et, RACINE / "config" / "ratios.yaml")
        }
    df_heat = donnees_heatmap_centiles(ratios_par_annee, bench)
    if not df_heat.empty:
        # Heatmap via plotly (pas de dependance matplotlib)
        import plotly.express as px
        fig_heat = px.imshow(
            df_heat, text_auto=".0f", aspect="auto",
            color_continuous_scale="RdYlGn",
            zmin=0, zmax=100, labels={"color": "centile"},
        )
        fig_heat.update_layout(height=400)
        st.plotly_chart(fig_heat, use_container_width=True)

    # ---- Evolution temporelle ----
    st.markdown("### Évolution temporelle")
    bilans = {
        an: construire_bilan_fonctionnel(et, RACINE / "config" / "reclassement.yaml")
        for an, et in etats.items()
    }
    df_evo = donnees_evolution_temporelle(etats, bilans)
    st.line_chart(df_evo[["ca", "frng", "bfr", "tn"]])

    # ---- Sankey (flux postes -> masses) ----
    st.markdown("### Sankey (postes sources → masses fonctionnelles)")
    s = donnees_sankey(bf_r)
    import plotly.graph_objects as go
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(label=s["nodes"], pad=15, thickness=12),
        link=dict(source=[l["source"] for l in s["links"]],
                  target=[l["target"] for l in s["links"]],
                  value=[l["value"] for l in s["links"]]),
    )])
    fig_sankey.update_layout(height=500)
    st.plotly_chart(fig_sankey, use_container_width=True)

    # ---- Export CSV lineage ----
    st.markdown("### Export CSV du lineage")
    import io, csv as _csv
    buf = io.StringIO()
    writer = _csv.DictWriter(
        buf, fieldnames=["annee", "masse", "poste_source", "montant", "retraitement"],
    )
    writer.writeheader()
    for nom_masse in ["emplois_stables", "ressources_stables",
                      "actif_circulant_exploitation", "actif_circulant_hors_exploitation",
                      "passif_circulant_exploitation", "passif_circulant_hors_exploitation",
                      "tresorerie_active", "tresorerie_passive"]:
        masse = getattr(bf_r, nom_masse)
        for l in masse.lignes:
            writer.writerow({
                "annee": bf_r.annee, "masse": nom_masse,
                "poste_source": l.poste_source, "montant": l.montant,
                "retraitement": l.retraitement or "",
            })
    st.download_button(
        "Télécharger le lineage CSV",
        buf.getvalue().encode("utf-8"),
        file_name=f"lineage_{e.entreprise}_{e.annee}.csv",
        mime="text/csv",
    )


with tab6:
    st.subheader("Pivot (JSON)")
    st.json(e.model_dump())
