import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

# Fonction pour charger et nettoyer les données
def load_and_clean_data(uploaded_file):
    """
    Charge et nettoie les données du fichier Excel uploadé
    """
    try:
        # Charger le fichier Excel
        df = pd.read_excel(uploaded_file)
        
        # Nettoyer les noms de colonnes
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Standardiser les textes en majuscules
        text_columns = ['paillasse', 'gamme', 'modele', 'marque', 'distributeur']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.upper().str.strip()
        
        # Nettoyer les montants
        if 'montant soumission' in df.columns:
            df['montant soumission'] = pd.to_numeric(df['montant soumission'], errors='coerce').fillna(0)
        
        # Supprimer les lignes sans distributeur ou sans montant
        df = df[df['distributeur'].notna() & (df['distributeur'] != 'NAN')]
        df = df[df['montant soumission'] > 0]
        
        return df
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")
        return pd.DataFrame()

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

# Importer BidAnalyzer après le chargement des données pour éviter les erreurs circulaires
from analysis.bid_analysis import BidAnalyzer

# Initialiser l'analyseur
analyzer = BidAnalyzer(df)

# Navigation
st.sidebar.header("📊 Navigation")
section = st.sidebar.radio(
    "Sélectionnez une analyse:",
    ["🎯 Vue d'Ensemble", "📊 Par Paillasse", "⚔️ Analyse Concurrentielle", "📈 Performance TS", "📋 Données Brutes"]
)

# ==================== FONCTIONS D'ANALYSE ====================

def calculate_market_share(data):
    """Calcule la part de marché globale"""
    total_market = data['montant soumission'].sum()
    ts_data = data[data['distributeur'] == 'TECHNOLOGIES SERVICES']
    ts_total = ts_data['montant soumission'].sum()
    
    ts_market_share = (ts_total / total_market * 100) if total_market > 0 else 0
    
    return {
        'total_marche': total_market,
        'total_ts': ts_total,
        'part_marche_ts': ts_market_share,
        'nombre_soumissions_ts': len(ts_data),
        'nombre_soumissions_total': len(data)
    }

def analyze_by_paillasse(data):
    """Analyse détaillée par paillasse"""
    analysis = data.groupby('paillasse').agg({
        'montant soumission': ['sum', 'count', 'mean'],
        'distributeur': 'nunique'
    }).round(2)
    
    analysis.columns = ['montant_total', 'nombre_soumissions', 'montant_moyen', 'nombre_distributeurs']
    
    # Calcul de la part de TS par paillasse
    ts_by_paillasse = data[data['distributeur'] == 'TECHNOLOGIES SERVICES'].groupby('paillasse').agg({
        'montant soumission': 'sum',
        'gamme': 'count'
    })
    
    ts_by_paillasse.columns = ['montant_ts', 'soumissions_ts']
    
    analysis = analysis.merge(ts_by_paillasse, on='paillasse', how='left').fillna(0)
    analysis['part_marche_ts'] = (analysis['montant_ts'] / analysis['montant_total'] * 100).round(2)
    
    return analysis.reset_index()

def get_competitors_analysis(data):
    """Analyse des concurrents principaux"""
    competitors = data[data['distributeur'] != 'TECHNOLOGIES SERVICES']
    competitor_stats = competitors.groupby('distributeur').agg({
        'montant soumission': ['sum', 'count'],
        'paillasse': 'nunique',
        'gamme': 'nunique'
    }).round(2)
    
    competitor_stats.columns = ['montant_total', 'nombre_soumissions', 'paillasses_couvertes', 'gammes_couvertes']
    competitor_stats['part_marche'] = (competitor_stats['montant_total'] / data['montant soumission'].sum() * 100).round(2)
    
    return competitor_stats.reset_index().sort_values('montant_total', ascending=False)

def get_ts_performance_details(data):
    """Détails de performance de TS"""
    ts_data = data[data['distributeur'] == 'TECHNOLOGIES SERVICES']
    
    if ts_data.empty:
        return pd.DataFrame()
    
    performance = ts_data.groupby('paillasse').agg({
        'montant soumission': ['sum', 'count', 'mean'],
        'gamme': 'nunique'
    }).round(2)
    
    performance.columns = ['montant_total', 'nombre_soumissions', 'montant_moyen', 'gammes_couvertes']
    
    # Comparaison avec le marché
    market_by_paillasse = data.groupby('paillasse')['montant soumission'].sum()
    performance = performance.merge(market_by_paillasse, on='paillasse', suffixes=('_ts', '_marche'))
    performance['part_marche'] = (performance['montant_total_ts'] / performance['montant soumission'] * 100).round(2)
    
    return performance.reset_index()

# ==================== SECTION 1: VUE D'ENSEMBLE ====================

if section == "🎯 Vue d'Ensemble":
    st.header("🎯 Vue d'Ensemble du Marché")
    
    # Calcul des indicateurs clés
    market_share = calculate_market_share(df)
    ts_data = df[df['distributeur'] == 'TECHNOLOGIES SERVICES']
    
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
            f"{market_share['total_ts']:,.0f} FCFA",
            help="Montant total des soumissions de Technologies Services"
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
            f"{participation_rate:.1f}%",
            help="Pourcentage des soumissions auxquelles TS a participé"
        )
    
    # Graphique de part de marché
    st.subheader("📊 Répartition du Marché")
    
    market_distribution = df.groupby('distributeur')['montant soumission'].sum().reset_index()
    market_distribution = market_distribution.sort_values('montant soumission', ascending=False)
    
    # Grouper les petits distributeurs
    top_distributors = market_distribution.head(8)
    others = market_distribution[8:]['montant soumission'].sum()
    
    if others > 0:
        top_distributors = pd.concat([
            top_distributors,
            pd.DataFrame([{'distributeur': 'AUTRES', 'montant soumission': others}])
        ])
    
    fig_market_share = px.pie(
        top_distributors,
        values='montant soumission',
        names='distributeur',
        title="Répartition du Marché par Distributeur"
    )
    st.plotly_chart(fig_market_share, use_container_width=True)
    
    # Performance TS vs marché
    st.subheader("📈 Performance TS vs Marché Global")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top paillasses par montant
        paillasse_analysis = analyze_by_paillasse(df)
        top_paillasses = paillasse_analysis.nlargest(10, 'montant_total')
        
        fig_top_paillasses = px.bar(
            top_paillasses,
            x='paillasse',
            y='montant_total',
            title="Top 10 Paillasses par Montant Total"
        )
        st.plotly_chart(fig_top_paillasses, use_container_width=True)
    
    with col2:
        # Part de marché TS par paillasse (top 10)
        ts_paillasse = paillasse_analysis[paillasse_analysis['montant_ts'] > 0]
        if not ts_paillasse.empty:
            fig_ts_share = px.bar(
                ts_paillasse.nlargest(10, 'part_marche_ts'),
                x='paillasse',
                y='part_marche_ts',
                title="Top 10 Paillasses - Part de Marché TS"
            )
            st.plotly_chart(fig_ts_share, use_container_width=True)

# ==================== SECTION 2: PAR PAILLASSE ====================

elif section == "📊 Par Paillasse":
    st.header("📊 Analyse Détailée par Paillasse")
    
    paillasse_analysis = analyze_by_paillasse(df)
    
    # Sélection de paillasse
    selected_paillasse = st.selectbox(
        "Sélectionnez une paillasse:",
        options=paillasse_analysis['paillasse'].unique()
    )
    
    if selected_paillasse:
        # Données de la paillasse sélectionnée
        paillasse_data = df[df['paillasse'] == selected_paillasse]
        paillasse_stats = paillasse_analysis[paillasse_analysis['paillasse'] == selected_paillasse].iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Montant Total",
                f"{paillasse_stats['montant_total']:,.0f} FCFA"
            )
        
        with col2:
            st.metric(
                "Part de Marché TS",
                f"{paillasse_stats['part_marche_ts']:.1f}%"
            )
        
        with col3:
            st.metric(
                "Nombre de Soumissions",
                f"{int(paillasse_stats['nombre_soumissions'])}"
            )
        
        with col4:
            st.metric(
                "Distributeurs Actifs",
                f"{int(paillasse_stats['nombre_distributeurs'])}"
            )
        
        # Répartition par distributeur
        st.subheader(f"📊 Répartition par Distributeur - {selected_paillasse}")
        
        distributor_share = paillasse_data.groupby('distributeur')['montant soumission'].sum().reset_index()
        distributor_share = distributor_share.sort_values('montant soumission', ascending=False)
        
        fig_distributor = px.pie(
            distributor_share,
            values='montant soumission',
            names='distributeur',
            title=f"Répartition {selected_paillasse} par Distributeur"
        )
        st.plotly_chart(fig_distributor, use_container_width=True)
        
        # Gammes de la paillasse
        st.subheader(f"🎯 Gammes - {selected_paillasse}")
        
        gammes_analysis = paillasse_data.groupby('gamme').agg({
            'montant soumission': ['sum', 'count'],
            'distributeur': 'nunique'
        }).round(2)
        
        gammes_analysis.columns = ['montant_total', 'nombre_soumissions', 'nombre_distributeurs']
        gammes_analysis = gammes_analysis.reset_index().sort_values('montant_total', ascending=False)
        
        st.dataframe(gammes_analysis, use_container_width=True)

# ==================== SECTION 3: ANALYSE CONCURRENTIELLE ====================

elif section == "⚔️ Analyse Concurrentielle":
    st.header("⚔️ Analyse du Paysage Concurrentiel")
    
    competitors = get_competitors_analysis(df)
    ts_market_share = calculate_market_share(df)
    
    # Top concurrents
    st.subheader("🏆 Classement des Concurrents")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_competitors_volume = px.bar(
            competitors.head(10),
            x='distributeur',
            y='nombre_soumissions',
            title="Top 10 Concurrents par Volume de Soumissions",
            color='nombre_soumissions'
        )
        st.plotly_chart(fig_competitors_volume, use_container_width=True)
    
    with col2:
        fig_competitors_amount = px.bar(
            competitors.head(10),
            x='distributeur',
            y='montant_total',
            title="Top 10 Concurrents par Chiffre d'Affaires",
            color='montant_total'
        )
        st.plotly_chart(fig_competitors_amount, use_container_width=True)
    
    # Comparaison TS vs Concurrents
    st.subheader("🔍 Comparaison TS vs Principaux Concurrents")
    
    top_competitors = competitors.head(5)
    comparison_data = []
    
    # Ajouter TS
    comparison_data.append({
        'distributeur': 'TECHNOLOGIES SERVICES',
        'montant_total': ts_market_share['total_ts'],
        'nombre_soumissions': ts_market_share['nombre_soumissions_ts'],
        'type': 'TS'
    })
    
    # Ajouter top concurrents
    for _, comp in top_competitors.iterrows():
        comparison_data.append({
            'distributeur': comp['distributeur'],
            'montant_total': comp['montant_total'],
            'nombre_soumissions': comp['nombre_soumissions'],
            'type': 'Concurrent'
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
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

# ==================== SECTION 4: PERFORMANCE TS ====================

elif section == "📈 Performance TS":
    st.header("📈 Analyse de Performance - Technologies Services")
    
    ts_performance = get_ts_performance_details(df)
    
    if ts_performance.empty:
        st.warning("ℹ️ Technologies Services n'apparaît pas dans les données analysées.")
    else:
        # KPIs TS
        total_ts_amount = ts_performance['montant_total'].sum()
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
                ts_performance.nlargest(10, 'montant_total'),
                x='paillasse',
                y='montant_total',
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
            strong_categories = ts_performance[ts_performance['part_marche'] >= 20]
            if not strong_categories.empty:
                for _, cat in strong_categories.iterrows():
                    st.write(f"• **{cat['paillasse']}** : {cat['part_marche']}% de part de marché")
            else:
                st.write("Aucune catégorie avec part de marché ≥ 20%")
        
        with col2:
            st.warning("**📈 Axes d'Amélioration**")
            weak_categories = ts_performance[ts_performance['part_marche'] < 10]
            if not weak_categories.empty:
                for _, cat in weak_categories.iterrows():
                    st.write(f"• **{cat['paillasse']}** : {cat['part_marche']}% de part de marché")
            else:
                st.write("Toutes les catégories ont une part de marché ≥ 10%")

# ==================== SECTION 5: DONNÉES BRUTES ====================

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
st.markdown(
    "**📊 Analyse Stratégique Technologies Services** • "
    "Focus sur la part de marché et le positionnement concurrentiel"
)
