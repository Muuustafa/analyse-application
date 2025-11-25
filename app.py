import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_and_clean_data
from analysis.bid_analysis import BidAnalyzer

# Configuration de la page
st.set_page_config(
    page_title="Analyse Part de Marché - Technologies Services",
    page_icon="🏥",
    layout="wide"
)

# Titre principal
st.title("🏥 Analyse Stratégique - Technologies Services")
st.markdown("**Part de Marché et Positionnement Concurrentiel**")
st.markdown("---")

# Section d'upload
st.sidebar.header("📁 Chargement des données")
uploaded_file = st.sidebar.file_uploader(
    "Choisissez le fichier Excel",
    type=["xlsx", "xls"],
    help="Fichier avec les colonnes: paillasse, gamme, modele, marque, distributeur, montant soumission"
)

# Charger les données d'exemple si aucun fichier uploadé
if not uploaded_file:
    st.info("""
    ### 📋 Instructions
    Veuillez uploader un fichier Excel avec les colonnes suivantes:
    - **paillasse, gamme, modele, marque, distributeur, montant soumission**
    
    L'analyse se concentrera sur Technologies Services et ses concurrents.
    """)
    st.stop()

# Chargement des données
with st.spinner("Chargement et analyse des données..."):
    df = load_and_clean_data(uploaded_file)
    
    if df.empty:
        st.error("❌ Aucune donnée valide n'a pu être chargée.")
        st.stop()

# Vérification des colonnes requises
required_columns = ['paillasse', 'gamme', 'distributeur', 'montant soumission']
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    st.error(f"❌ Colonnes manquantes: {', '.join(missing_columns)}")
    st.stop()

# Initialiser l'analyseur
analyzer = BidAnalyzer(df)

# Navigation
st.sidebar.header("📊 Navigation")
section = st.sidebar.radio(
    "Sélectionnez une analyse:",
    ["🎯 Vue d'Ensemble", "📊 Par Paillasse", "⚔️ Analyse Concurrentielle", "📈 Performance TS", "📋 Données Brutes"]
)

# ==================== SECTIONS D'ANALYSE ====================

if section == "🎯 Vue d'Ensemble":
    st.header("🎯 Vue d'Ensemble du Marché")
    
    # Calcul des indicateurs clés
    market_share = analyzer.calculate_market_share()
    
    # KPIs principaux
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Part de Marché TS",
            f"{market_share['part_marche_ts']:.1f}%",
            help="Part du chiffre d'affaires total détenue par Technologies Services"
        )
    
    with col2:
        st.metric(
            "Chiffre d'Affaires TS",
            f"{market_share['total_ts']:,.0f} FCFA"
        )
    
    with col3:
        st.metric(
            "Soumissions TS",
            f"{market_share['nombre_soumissions_ts']}",
            delta=f"{market_share['nombre_soumissions_ts']} soumissions"
        )
    
    with col4:
        participation_rate = (market_share['nombre_soumissions_ts'] / market_share['nombre_soumissions_total'] * 100)
        st.metric(
            "Taux de Participation",
            f"{participation_rate:.1f}%"
        )
    
    # Graphiques
    st.subheader("📊 Répartition du Marché")
    
    market_distribution = analyzer.get_market_distribution()
    fig_market_share = px.pie(
        market_distribution,
        values='montant soumission',
        names='distributeur',
        title="Répartition du Marché par Distributeur"
    )
    st.plotly_chart(fig_market_share, use_container_width=True)
    
    # Performance TS vs marché
    st.subheader("📈 Performance TS vs Marché Global")
    
    col1, col2 = st.columns(2)
    
    with col1:
        top_paillasses = analyzer.get_top_paillasses()
        fig_top_paillasses = px.bar(
            top_paillasses,
            x='paillasse',
            y='montant_total',
            title="Top 10 Paillasses par Montant Total"
        )
        st.plotly_chart(fig_top_paillasses, use_container_width=True)
    
    with col2:
        ts_paillasse = analyzer.get_ts_paillasse_performance()
        if not ts_paillasse.empty:
            fig_ts_share = px.bar(
                ts_paillasse.nlargest(10, 'part_marche_ts'),
                x='paillasse',
                y='part_marche_ts',
                title="Top 10 Paillasses - Part de Marché TS"
            )
            st.plotly_chart(fig_ts_share, use_container_width=True)

elif section == "📊 Par Paillasse":
    st.header("📊 Analyse Détailée par Paillasse")
    
    paillasse_analysis = analyzer.analyze_by_paillasse()
    
    # Sélection de paillasse
    selected_paillasse = st.selectbox(
        "Sélectionnez une paillasse:",
        options=paillasse_analysis['paillasse'].unique()
    )
    
    if selected_paillasse:
        # Données de la paillasse sélectionnée
        paillasse_stats = paillasse_analysis[paillasse_analysis['paillasse'] == selected_paillasse].iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Montant Total", f"{paillasse_stats['montant_total']:,.0f} FCFA")
        
        with col2:
            st.metric("Part de Marché TS", f"{paillasse_stats['part_marche_ts']:.1f}%")
        
        with col3:
            st.metric("Nombre de Soumissions", f"{int(paillasse_stats['nombre_soumissions'])}")
        
        with col4:
            st.metric("Distributeurs Actifs", f"{int(paillasse_stats['nombre_distributeurs'])}")
        
        # Répartition par distributeur
        st.subheader(f"📊 Répartition par Distributeur - {selected_paillasse}")
        distributor_share = analyzer.get_paillasse_distributors(selected_paillasse)
        
        fig_distributor = px.pie(
            distributor_share,
            values='montant soumission',
            names='distributeur',
            title=f"Répartition {selected_paillasse} par Distributeur"
        )
        st.plotly_chart(fig_distributor, use_container_width=True)
        
        # Gammes de la paillasse
        st.subheader(f"🎯 Gammes - {selected_paillasse}")
        gammes_analysis = analyzer.get_paillasse_gammes(selected_paillasse)
        st.dataframe(gammes_analysis, use_container_width=True)

elif section == "⚔️ Analyse Concurrentielle":
    st.header("⚔️ Analyse du Paysage Concurrentiel")
    
    competitors = analyzer.get_competitors_analysis()
    
    # Top concurrents
    st.subheader("🏆 Classement des Concurrents")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_competitors_volume = px.bar(
            competitors.head(10),
            x='distributeur',
            y='nombre_soumissions',
            title="Top 10 Concurrents par Volume de Soumissions"
        )
        st.plotly_chart(fig_competitors_volume, use_container_width=True)
    
    with col2:
        fig_competitors_amount = px.bar(
            competitors.head(10),
            x='distributeur',
            y='montant_total',
            title="Top 10 Concurrents par Chiffre d'Affaires"
        )
        st.plotly_chart(fig_competitors_amount, use_container_width=True)
    
    # Comparaison TS vs Concurrents
    st.subheader("🔍 Comparaison TS vs Principaux Concurrents")
    comparison_df = analyzer.get_ts_vs_competitors_comparison()
    
    if not comparison_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig_comp_amount = px.bar(
                comparison_df,
                x='distributeur',
                y='montant_total',
                title="Comparaison Chiffre d'Affaires",
                color='type'
            )
            st.plotly_chart(fig_comp_amount, use_container_width=True)
        
        with col2:
            fig_comp_volume = px.bar(
                comparison_df,
                x='distributeur',
                y='nombre_soumissions',
                title="Comparaison Volume de Soumissions",
                color='type'
            )
            st.plotly_chart(fig_comp_volume, use_container_width=True)

elif section == "📈 Performance TS":
    st.header("📈 Analyse de Performance - Technologies Services")
    
    ts_performance = analyzer.get_ts_performance_details()
    
    if ts_performance.empty:
        st.warning("ℹ️ Technologies Services n'apparaît pas dans les données analysées.")
    else:
        # KPIs TS
        total_ts_amount = ts_performance['montant_total_ts'].sum()
        total_ts_submissions = ts_performance['nombre_soumissions'].sum()
        avg_market_share = ts_performance['part_marche'].mean()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("CA Total TS", f"{total_ts_amount:,.0f} FCFA")
        
        with col2:
            st.metric("Soumissions Total TS", f"{total_ts_submissions}")
        
        with col3:
            st.metric("Part de Marché Moyenne", f"{avg_market_share:.1f}%")
        
        # Performance par paillasse
        st.subheader("📊 Performance par Paillasse")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_ts_performance = px.bar(
                ts_performance.nlargest(10, 'montant_total_ts'),
                x='paillasse',
                y='montant_total_ts',
                title="Top 10 Paillasses par CA TS"
            )
            st.plotly_chart(fig_ts_performance, use_container_width=True)
        
        with col2:
            fig_ts_market_share = px.bar(
                ts_performance.nlargest(10, 'part_marche'),
                x='paillasse',
                y='part_marche',
                title="Top 10 Paillasses par Part de Marché TS"
            )
            st.plotly_chart(fig_ts_market_share, use_container_width=True)
        
        # Points forts et axes d'amélioration
        st.subheader("🎯 Analyse Stratégique")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("**✅ Points Forts**")
            strong_categories = analyzer.get_ts_strong_points()
            if not strong_categories.empty:
                for _, cat in strong_categories.iterrows():
                    st.write(f"• **{cat['paillasse']}** : {cat['part_marche']}% de part de marché")
            else:
                st.write("Aucune catégorie avec part de marché ≥ 20%")
        
        with col2:
            st.warning("**📈 Axes d'Amélioration**")
            weak_categories = analyzer.get_ts_improvement_areas()
            if not weak_categories.empty:
                for _, cat in weak_categories.iterrows():
                    st.write(f"• **{cat['paillasse']}** : {cat['part_marche']}% de part de marché")
            else:
                st.write("Toutes les catégories ont une part de marché ≥ 10%")

elif section == "📋 Données Brutes":
    st.header("📋 Données Brutes et Export")
    
    st.subheader("Aperçu des Données")
    st.dataframe(df, use_container_width=True)
    
    # Statistiques descriptives
    st.subheader("Statistiques Descriptives")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Description des montants:**")
        st.dataframe(df['montant soumission'].describe(), use_container_width=True)
    
    with col2:
        st.write("**Répartition par paillasse:**")
        paillasse_counts = df['paillasse'].value_counts()
        st.dataframe(paillasse_counts, use_container_width=True)
    
    # Export des données
    st.subheader("📤 Export des Données")
    
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger Données Brutes (CSV)",
        data=csv_data,
        file_name="analyse_technologies_services.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("**📊 Analyse Stratégique Technologies Services** • Focus sur la part de marché et le positionnement concurrentiel")
