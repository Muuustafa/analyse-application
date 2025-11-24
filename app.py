import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_and_clean_uploaded_data
from analysis.bid_analysis import BidAnalyzer

# Configuration de la page
st.set_page_config(
    page_title="Analyse Stratégique des Appels d'Offres Médicaux",
    page_icon="🏥",
    layout="wide"
)

# Titre principal
st.title("🏥 Analyse Stratégique des Appels d'Offres Médicaux")
st.markdown("**Outil d'aide à la décision pour Technologies Services**")
st.markdown("---")

# Section d'upload des fichiers
st.sidebar.header("📁 Chargement des données")

uploaded_files = st.sidebar.file_uploader(
    "Choisissez les fichiers Excel",
    type=["xlsx", "xls"],
    accept_multiple_files=True,
    help="Sélectionnez un ou plusieurs fichiers Excel avec les colonnes requises"
)

# Instructions si aucun fichier
if not uploaded_files:
    st.info("""
    ### 📋 Instructions pour l'upload
    
    Veuillez uploader les fichiers Excel contenant les données d'appels d'offres avec les colonnes:
    - **catégorie, gamme, modele, marque, distributeur, montant soumission**
    
    L'application analysera automatiquement les opportunités pour Technologies Services.
    """)
    st.stop()

# Chargement des données
try:
    with st.spinner("🔍 Chargement et analyse des données en cours..."):
        combined_data = load_and_clean_uploaded_data(uploaded_files)
        
        if combined_data.empty:
            st.error("❌ Aucune donnée valide n'a pu être chargée.")
            st.stop()
        
        # Appliquer la catégorisation si nécessaire
        from utils.data_loader import categorize_gamme
        if 'catégorie' not in combined_data.columns or combined_data['catégorie'].isna().all():
            combined_data['catégorie'] = combined_data['gamme'].apply(categorize_gamme)
        
        # Initialiser l'analyseur
        analyzer = BidAnalyzer(combined_data)
        
        st.success(f"✅ Données chargées avec succès! {len(combined_data)} soumissions analysées.")

except Exception as e:
    st.error(f"❌ Erreur lors du chargement: {e}")
    st.stop()

# Navigation
st.sidebar.header("📊 Navigation Analytique")
section = st.sidebar.radio(
    "Sélectionnez une analyse:",
    ["🎯 Tableau de Bord Stratégique", "📈 Analyse du Marché", "🔍 Performance TS", 
     "💰 Opportunités Non-Pourvues", "⚔️ Analyse Concurrentielle", "📋 Données Brutes"]
)

# Afficher les fichiers chargés
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Fichiers Chargés")
for i, file in enumerate(uploaded_files, 1):
    st.sidebar.write(f"{i}. {file.name}")

# ==================== SECTION 1: TABLEAU DE BORD STRATÉGIQUE ====================
if section == "🎯 Tableau de Bord Stratégique":
    st.header("🎯 Tableau de Bord Stratégique - Technologies Services")
    
    # Métriques KPIs principaux
    market_overview = analyzer.get_market_overview()
    growth_potential = analyzer.get_ts_growth_potential()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Part de Marché TS", 
            f"{market_overview['part_marche_ts']:.1f}%",
            delta=f"{market_overview['participation_ts']} soumissions"
        )
    
    with col2:
        st.metric(
            "Opportunités Identifiées", 
            f"{growth_potential['opportunites_identifiees']}",
            delta=f"{growth_potential['opportunites_haute_priorite']} haute priorité"
        )
    
    with col3:
        st.metric(
            "Potentiel de Croissance", 
            f"{growth_potential['montant_total_opportunites']:,.0f} FCFA"
        )
    
    with col4:
        st.metric(
            "Gammes Non-Pourvues", 
            f"{market_overview['gammes_sans_soumissionnaires']}"
        )
    
    # Tableau de bord visuel
    st.subheader("📊 Vue Stratégique Globale")
    strategic_dashboard = analyzer.create_strategic_dashboard()
    st.plotly_chart(strategic_dashboard, use_container_width=True)
    
    # Recommandations stratégiques
    st.subheader("🚀 Plan d'Action Recommandé")
    
    if growth_potential['recommandations']:
        for i, recommandation in enumerate(growth_potential['recommandations'], 1):
            st.success(f"{i}. {recommandation}")
    
    # Alertes stratégiques
    st.subheader("⚠️ Points de Vigilance")
    ts_position = analyzer.get_ts_competitive_position()
    
    if not ts_position.empty:
        marginal_positions = ts_position[ts_position['position_concurrentielle'] == 'Marginal']
        if not marginal_positions.empty:
            for _, position in marginal_positions.iterrows():
                st.warning(
                    f"Position marginale détectée dans **{position['catégorie']}** "
                    f"({position['part_marche_montant']}% de part de marché)"
                )

# ==================== SECTION 2: ANALYSE DU MARCHÉ ====================
elif section == "📈 Analyse du Marché":
    st.header("📈 Analyse Globale du Marché")
    
    # Vue d'ensemble du marché
    market_overview = analyzer.get_market_overview()
    category_analysis = analyzer.get_category_analysis()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Répartition du Marché")
        fig_market_pie = px.pie(
            category_analysis,
            values='montant_total',
            names='catégorie',
            title="Répartition du Chiffre d'Affaires par Catégorie"
        )
        st.plotly_chart(fig_market_pie, use_container_width=True)
    
    with col2:
        st.subheader("🏆 Catégories les Plus Actives")
        fig_category_bar = px.bar(
            category_analysis.nlargest(10, 'nombre_soumissions'),
            x='catégorie',
            y='nombre_soumissions',
            title="Top 10 Catégories par Nombre de Soumissions"
        )
        st.plotly_chart(fig_category_bar, use_container_width=True)
    
    # Analyse de la densité concurrentielle
    st.subheader("🎯 Attractivité des Catégories")
    
    fig_attractiveness = px.scatter(
        category_analysis,
        x='densite_concurrentielle',
        y='montant_total',
        size='nombre_soumissions',
        color='catégorie',
        hover_data=['nombre_distributeurs'],
        title="Attractivité vs Potentiel du Marché",
        labels={
            'densite_concurrentielle': 'Densité Concurrentielle (faible = meilleur)',
            'montant_total': 'Potentiel du Marché (FCFA)'
        }
    )
    st.plotly_chart(fig_attractiveness, use_container_width=True)
    
    # Tableau détaillé
    st.subheader("📋 Analyse Détailée par Catégorie")
    display_columns = ['catégorie', 'nombre_soumissions', 'montant_total', 'prix_moyen', 'nombre_distributeurs', 'densite_concurrentielle']
    st.dataframe(category_analysis[display_columns], use_container_width=True)

# ==================== SECTION 3: PERFORMANCE TS ====================
elif section == "🔍 Performance TS":
    st.header("🔍 Analyse de Performance - Technologies Services")
    
    ts_performance = analyzer.get_ts_performance()
    ts_position = analyzer.get_ts_competitive_position()
    
    if ts_performance.empty:
        st.warning("ℹ️ Technologies Services n'apparaît pas dans les données analysées.")
    else:
        # KPIs TS
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_ts_submissions = ts_performance['soumissions_ts'].sum()
            st.metric("Soumissions TS", f"{total_ts_submissions}")
        
        with col2:
            total_ts_amount = ts_performance['montant_ts'].sum()
            st.metric("Chiffre d'Affaires TS", f"{total_ts_amount:,.0f} FCFA")
        
        with col3:
            avg_market_share = ts_performance['part_marche_montant'].mean()
            st.metric("Part de Marché Moyenne", f"{avg_market_share:.1f}%")
        
        with col4:
            categories_covered = len(ts_performance)
            st.metric("Catégories Couvertes", f"{categories_covered}")
        
        # Graphiques de performance
        col1, col2 = st.columns(2)
        
        with col1:
            fig_ts_performance = px.bar(
                ts_performance,
                x='catégorie',
                y=['part_marche_volume', 'part_marche_montant'],
                title="Parts de Marché TS par Catégorie",
                barmode='group'
            )
            st.plotly_chart(fig_ts_performance, use_container_width=True)
        
        with col2:
            fig_ts_position = px.pie(
                ts_position,
                values='soumissions_ts',
                names='position_concurrentielle',
                title="Position Concurrentielle de TS"
            )
            st.plotly_chart(fig_ts_position, use_container_width=True)
        
        # Points forts et axes d'amélioration
        st.subheader("📈 Analyse des Performances")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("**✅ Points Forts**")
            strong_categories = ts_position[ts_position['position_concurrentielle'].isin(['Leader', 'Compétiteur fort'])]
            if not strong_categories.empty:
                for _, cat in strong_categories.iterrows():
                    st.write(f"• **{cat['catégorie']}** : {cat['part_marche_montant']}% de part de marché")
        
        with col2:
            st.warning("**📈 Axes d'Amélioration**")
            weak_categories = ts_position[ts_position['position_concurrentielle'].isin(['Marginal'])]
            if not weak_categories.empty:
                for _, cat in weak_categories.iterrows():
                    st.write(f"• **{cat['catégorie']}** : {cat['part_marche_montant']}% de part de marché")

# ==================== SECTION 4: OPPORTUNITÉS NON-POURVUES ====================
elif section == "💰 Opportunités Non-Pourvues":
    st.header("💰 Opportunités des Marchés Non-Pourvus")
    
    opportunities = analyzer.get_strategic_opportunities()
    growth_potential = analyzer.get_ts_growth_potential()
    
    if opportunities.empty:
        st.info("🎉 Aucune opportunité non-pourvue identifiée dans les données actuelles.")
    else:
        # Métriques des opportunités
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Potentiel Total Estimé", 
                f"{growth_potential['montant_total_opportunites']:,.0f} FCFA"
            )
        
        with col2:
            st.metric(
                "Opportunités Haute Priorité", 
                f"{growth_potential['opportunites_haute_priorite']}"
            )
        
        with col3:
            high_confidence_opps = len(opportunities[opportunities['niveau_confiance'] == 'Élevé'])
            st.metric(
                "Estimations Haute Confiance", 
                f"{high_confidence_opps}"
            )
        
        # Top 10 des meilleures opportunités
        st.subheader("🎯 Top 10 des Opportunités à Haut Potentiel")
        top_10_opportunities = opportunities.head(10)
        
        fig_top_opportunities = px.bar(
            top_10_opportunities,
            x='score_opportunite',
            y='gamme',
            color='niveau_confiance',
            orientation='h',
            title="Top 10 des Opportunités par Score Stratégique",
            labels={'score_opportunite': 'Score Opportunité', 'gamme': 'Gamme'}
        )
        st.plotly_chart(fig_top_opportunities, use_container_width=True)
        
        # Analyse par catégorie
        st.subheader("📊 Répartition des Opportunités par Catégorie")
        
        col1, col2 = st.columns(2)
        
        with col1:
            opp_by_category = opportunities.groupby('catégorie').agg({
                'montant_estime': 'sum',
                'opportunite_id': 'count'
            }).reset_index()
            opp_by_category.columns = ['catégorie', 'montant_total', 'nombre_opportunites']
            
            fig_opp_category = px.pie(
                opp_by_category,
                values='montant_total',
                names='catégorie',
                title="Potentiel par Catégorie"
            )
            st.plotly_chart(fig_opp_category, use_container_width=True)
        
        with col2:
            fig_opp_confidence = px.bar(
                opportunities.groupby('niveau_confiance')['montant_estime'].sum().reset_index(),
                x='niveau_confiance',
                y='montant_estime',
                title="Potentiel par Niveau de Confiance",
                color='niveau_confiance'
            )
            st.plotly_chart(fig_opp_confidence, use_container_width=True)
        
        # Tableau détaillé des opportunités
        st.subheader("📋 Détail des Opportunités Identifiées")
        
        display_columns = ['catégorie', 'gamme', 'montant_estime', 'niveau_confiance', 'methode_estimation', 'priorite']
        opportunities_display = opportunities[display_columns].copy()
        opportunities_display['montant_estime'] = opportunities_display['montant_estime'].apply(lambda x: f"{x:,.0f} FCFA")
        
        st.dataframe(opportunities_display, use_container_width=True)
        
        # Recommandations d'action
        st.subheader("💡 Plan d'Action Immédiat")
        
        high_priority_opps = opportunities[opportunities['priorite'] == 'Haute']
        if not high_priority_opps.empty:
            st.success("**🚀 Actions Prioritaires Recommandées:**")
            for i, (_, opp) in enumerate(high_priority_opps.head(3).iterrows(), 1):
                st.write(f"""
                **{i}. {opp['gamme']}**
                - **Catégorie**: {opp['catégorie']}
                - **Potentiel estimé**: {opp['montant_estime']:,.0f} FCFA
                - **Confiance**: {opp['niveau_confiance']}
                - **Action**: Contacter 3 fournisseurs pour validation de prix
                """)

# ==================== SECTION 5: ANALYSE CONCURRENTIELLE ====================
elif section == "⚔️ Analyse Concurrentielle":
    st.header("⚔️ Analyse du Paysage Concurrentiel")
    
    competitors = analyzer.get_competitive_landscape()
    ts_vs_competitors = analyzer.get_ts_vs_competitors()
    
    # Top concurrents
    st.subheader("🏆 Classement des Distributeurs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_competitor_ranking = px.bar(
            competitors.nlargest(10, 'nombre_soumissions'),
            x='distributeur',
            y='nombre_soumissions',
            title="Top 10 Distributeurs par Volume de Soumissions",
            color='nombre_soumissions'
        )
        st.plotly_chart(fig_competitor_ranking, use_container_width=True)
    
    with col2:
        fig_market_share = px.pie(
            competitors.nlargest(8, 'part_marche_montant'),
            values='part_marche_montant',
            names='distributeur',
            title="Répartition des Parts de Marché (Top 8)"
        )
        st.plotly_chart(fig_market_share, use_container_width=True)
    
    # Comparaison TS vs Concurrents
    if not ts_vs_competitors.empty:
        st.subheader("🔍 Comparaison TS vs Principaux Concurrents")
        
        metrics_to_compare = ['nombre_soumissions', 'montant_total', 'categories_couvertes', 'gammes_couvertes']
        
        for metric in metrics_to_compare:
            fig_comparison = px.bar(
                ts_vs_competitors,
                x='distributeur',
                y=metric,
                title=f"Comparaison: {metric.replace('_', ' ').title()}",
                color='distributeur'
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Stratégies concurrentielles
    st.subheader("🎯 Analyse des Stratégies Concurrentes")
    
    if not competitors.empty:
        # Identifier les concurrents spécialisés
        specialized_competitors = competitors[
            (competitors['categories_couvertes'] <= 3) & 
            (competitors['nombre_soumissions'] >= 5)
        ]
        
        if not specialized_competitors.empty:
            st.info("**🏢 Concurrents Spécialisés Identifiés:**")
            for _, competitor in specialized_competitors.iterrows():
                st.write(f"• **{competitor['distributeur']}** : {competitor['categories_couvertes']} catégories, {competitor['nombre_soumissions']} soumissions")

# ==================== SECTION 6: DONNÉES BRUTES ====================
elif section == "📋 Données Brutes":
    st.header("📋 Données Brutes et Export")
    
    st.subheader("Aperçu des Données Chargées")
    st.dataframe(combined_data, use_container_width=True)
    
    # Statistiques descriptives
    st.subheader("Statistiques Descriptives")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Description des montants de soumission:**")
        st.dataframe(combined_data['montant soumission'].describe(), use_container_width=True)
    
    with col2:
        st.write("**Répartition par catégorie:**")
        category_counts = combined_data['catégorie'].value_counts()
        st.dataframe(category_counts, use_container_width=True)
    
    # Export des données
    st.subheader("📤 Export des Analyses")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export données brutes
        csv_raw = combined_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger Données Brutes (CSV)",
            data=csv_raw,
            file_name="donnees_appels_offres_brutes.csv",
            mime="text/csv"
        )
    
    with col2:
        # Export des opportunités
        opportunities = analyzer.get_strategic_opportunities()
        if not opportunities.empty:
            csv_opp = opportunities.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Télécharger Opportunités (CSV)",
                data=csv_opp,
                file_name="opportunites_strategiques_ts.csv",
                mime="text/csv"
            )

# Footer
st.markdown("---")
st.markdown(
    "**📊 Application d'Aide à la Décision Stratégique** • "
    "Développée pour optimiser le positionnement de Technologies Services sur le marché des appels d'offres médicaux."
)