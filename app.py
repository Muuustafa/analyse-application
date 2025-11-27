import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Dashboard - Technologies Services",
    page_icon="🏥",
    layout="wide"
)

# Titre principal
st.title("🏥 Tableau de Bord")
st.markdown("**Technologies Services - Analyse des Appels d'Offres**")
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
        text_columns = ['paillasse', 'gamme', 'modele', 'marque', 'distributeur', 'attribution', 'reference']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.upper().str.strip()
        
        # Nettoyer les montants
        if 'montant soumission' in df.columns:
            df['montant soumission'] = pd.to_numeric(df['montant soumission'], errors='coerce').fillna(0)
        
        return df
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")
        return pd.DataFrame()

# Section d'upload
st.sidebar.header("📁 Chargement des données")
uploaded_file = st.sidebar.file_uploader(
    "Choisissez le fichier Excel des appels d'offres",
    type=["xlsx", "xls"],
    help="Fichier avec les colonnes: paillasse, gamme, modele, marque, distributeur, montant soumission, attribution, reference"
)

# Charger les données d'exemple si aucun fichier uploadé
if not uploaded_file:
    st.info("""
    ### 📋 Instructions
    Veuillez uploader un fichier Excel avec les colonnes suivantes:
    - **paillasse, gamme, modele, marque, distributeur, montant soumission, attribution, reference**
    
    L'analyse présentera les indicateurs clés pour Technologies Services.
    """)
    st.stop()

# Chargement des données
with st.spinner("Chargement et analyse des données..."):
    df = load_and_clean_data(uploaded_file)
    
    if df.empty:
        st.error("❌ Aucune donnée valide n'a pu être chargée.")
        st.stop()

# Vérification des colonnes requises
required_columns = ['paillasse', 'gamme', 'distributeur', 'montant soumission', 'attribution', 'reference']
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    st.error(f"❌ Colonnes manquantes: {', '.join(missing_columns)}")
    st.stop()

# Initialisation
TS_NAME = "TECHNOLOGIES SERVICES"

# ==================== CALCULS DES INDICATEURS CLÉS ====================

def calculate_kpis(data):
    """Calcule tous les indicateurs clés demandés par le DG"""
    
    # Indicateurs généraux
    total_soumissionnaires = data['distributeur'].nunique()
    montant_total_marche = data['montant soumission'].sum()
    
    # Données TS
    ts_data = data[data['distributeur'] == TS_NAME]
    montant_total_ts = ts_data['montant soumission'].sum()
    
    # Calcul du rang de TS
    distributeurs_montant = data.groupby('distributeur')['montant soumission'].sum().sort_values(ascending=False)
    distributeurs_count = data.groupby('distributeur')['gamme'].count().sort_values(ascending=False)
    
    rang_montant_ts = distributeurs_montant.index.get_loc(TS_NAME) + 1 if TS_NAME in distributeurs_montant.index else 0
    rang_nombre_ts = distributeurs_count.index.get_loc(TS_NAME) + 1 if TS_NAME in distributeurs_count.index else 0
    
    # Lots et sous-lots
    total_lots = data['gamme'].nunique()
    lots_ts_soumissionne = ts_data['gamme'].nunique()
    
    # Lots attribués à TS
    lots_attribues_ts = data[data['attribution'] == TS_NAME]['gamme'].nunique()
    pourcentage_attribution_ts = (lots_attribues_ts / total_lots * 100) if total_lots > 0 else 0
    
    # Lots non positionnés par TS
    tous_les_lots = set(data['gamme'].unique())
    lots_ts = set(ts_data['gamme'].unique())
    lots_non_positionnes_ts = tous_les_lots - lots_ts
    
    # Lots sans soumissionnaires
    lots_avec_soumission = set(data[data['distributeur'] != 'Pas de soumissionnaires']['gamme'].unique())
    lots_sans_soumission = tous_les_lots - lots_avec_soumission
    
    return {
        'total_soumissionnaires': total_soumissionnaires,
        'montant_total_marche': montant_total_marche,
        'montant_total_ts': montant_total_ts,
        'rang_montant_ts': rang_montant_ts,
        'rang_nombre_ts': rang_nombre_ts,
        'total_lots': total_lots,
        'lots_ts_soumissionne': lots_ts_soumissionne,
        'lots_attribues_ts': lots_attribues_ts,
        'pourcentage_attribution_ts': pourcentage_attribution_ts,
        'lots_non_positionnes_ts': len(lots_non_positionnes_ts),
        'lots_sans_soumission': len(lots_sans_soumission),
        'distributeurs_montant': distributeurs_montant,
        'distributeurs_count': distributeurs_count
    }

# ==================== FONCTIONS D'ANALYSE ====================

def get_distributeurs_analysis(data):
    """Analyse détaillée par distributeur"""
    analysis = data.groupby('distributeur').agg({
        'montant soumission': ['sum', 'count'],
        'gamme': 'nunique',
        'paillasse': 'nunique'
    }).round(0)
    
    analysis.columns = ['montant_total', 'nombre_soumissions', 'lots_couverts', 'paillasses_couvertes']
    analysis = analysis.reset_index()
    
    # Calcul des pourcentages
    total_montant = data['montant soumission'].sum()
    analysis['pourcentage_montant'] = (analysis['montant_total'] / total_montant * 100).round(2)
    
    return analysis.sort_values('montant_total', ascending=False)

def get_ts_paillasse_analysis(data):
    """Analyse des paillasses où TS s'est positionné"""
    ts_data = data[data['distributeur'] == TS_NAME]
    
    if ts_data.empty:
        return pd.DataFrame()
    
    analysis = ts_data.groupby('paillasse').agg({
        'montant soumission': ['sum', 'count'],
        'gamme': 'nunique'
    }).round(0)
    
    analysis.columns = ['montant_total', 'nombre_soumissions', 'lots_couverts']
    analysis = analysis.reset_index()
    
    # Calcul du pourcentage par rapport au total TS
    total_ts = ts_data['montant soumission'].sum()
    analysis['pourcentage_ts'] = (analysis['montant_total'] / total_ts * 100).round(2)
    
    return analysis.sort_values('montant_total', ascending=False)

def get_paillasse_detail(data, paillasse_selectionnee):
    """Détail d'une paillasse spécifique"""
    paillasse_data = data[data['paillasse'] == paillasse_selectionnee]
    
    # Analyse par distributeur
    distributeurs = paillasse_data.groupby('distributeur').agg({
        'montant soumission': 'sum',
        'gamme': 'count',
        'marque': lambda x: ', '.join(x.unique())
    }).reset_index()
    
    distributeurs.columns = ['distributeur', 'montant_total', 'nombre_lots', 'marques']
    distributeurs = distributeurs.sort_values('montant_total', ascending=False)
    
    return distributeurs

def get_lots_non_positionnes_ts(data):
    """Lots où TS ne s'est pas positionné"""
    tous_les_lots = set(data['gamme'].unique())
    lots_ts = set(data[data['distributeur'] == TS_NAME]['gamme'].unique())
    lots_non_positionnes = tous_les_lots - lots_ts
    
    # Récupérer les données de ces lots
    lots_data = data[data['gamme'].isin(lots_non_positionnes)]
    
    # Garder une ligne par lot avec le distributeur principal
    analysis = lots_data.groupby('gamme').agg({
        'paillasse': 'first',
        'distributeur': lambda x: ', '.join(x.unique()),
        'montant soumission': 'sum',
        'attribution': 'first'
    }).reset_index()
    
    return analysis

# ==================== SESSION STATE POUR LES COMMENTAIRES ====================

if 'commentaires' not in st.session_state:
    st.session_state.commentaires = {}

# ==================== CALCUL DES INDICATEURS ====================

kpis = calculate_kpis(df)
distributeurs_analysis = get_distributeurs_analysis(df)
ts_paillasse_analysis = get_ts_paillasse_analysis(df)

# Navigation
st.sidebar.header("📊 Navigation")
section = st.sidebar.radio(
    "Sélectionnez une vue:",
    ["🎯 Tableau de Bord", "📊 Analyse par Distributeur", "🏥 Positionnement TS par Paillasse", 
     "🔍 Lots Non Positionnés", "📋 Données Brutes"]
)

# ==================== SECTION 1: TABLEAU DE BORD ====================

if section == "🎯 Tableau de Bord":
    st.header("🎯 Tableau de Bord Direction Générale")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Soumissionnaires Total",
            f"{kpis['total_soumissionnaires']}",
            help="Nombre total de distributeurs ayant soumissionné"
        )
    
    with col2:
        st.metric(
            "Montant Total Marché",
            f"{kpis['montant_total_marche']:,.0f} FCFA",
            help="Montant total de toutes les soumissions"
        )
    
    with col3:
        st.metric(
            "Montant Total TS",
            f"{kpis['montant_total_ts']:,.0f} FCFA",
            help="Montant total des soumissions de Technologies Services"
        )
    
    with col4:
        st.metric(
            "Rang TS (Montant)",
            f"{kpis['rang_montant_ts']}ème",
            help="Classement de TS par montant de soumission"
        )
    
    # Deuxième ligne de métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Lots/Sous-lots",
            f"{kpis['total_lots']}",
            help="Nombre total de lots et sous-lots dans l'appel d'offre"
        )
    
    with col2:
        st.metric(
            "Lots Soumissionnés TS",
            f"{kpis['lots_ts_soumissionne']}",
            help="Nombre de lots où TS a soumissionné"
        )
    
    with col3:
        st.metric(
            "Lots Attribués à TS",
            f"{kpis['lots_attribues_ts']}",
            delta=f"{kpis['pourcentage_attribution_ts']:.1f}%",
            help="Lots attribués à Technologies Services"
        )
    
    with col4:
        st.metric(
            "Lots Non Positionnés TS",
            f"{kpis['lots_non_positionnes_ts']}",
            help="Lots où TS ne s'est pas positionné"
        )
    
    # Visualisations
    st.subheader("📈 Vue d'Ensemble du Marché")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top 10 distributeurs par montant
        top_distributeurs = distributeurs_analysis.head(10)
        fig_montant = px.bar(
            top_distributeurs,
            x='distributeur',
            y='montant_total',
            title="Top 10 Distributeurs par Montant",
            color='montant_total'
        )
        st.plotly_chart(fig_montant, use_container_width=True)
    
    with col2:
        # Répartition du marché
        fig_pie = px.pie(
            distributeurs_analysis,
            values='montant_total',
            names='distributeur',
            title="Répartition du Marché par Distributeur"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Informations sur les appels d'offres
    st.subheader("📋 Informations des Appels d'Offres")
    
    references = df['reference'].unique()
    st.write(f"**Appels d'offres analysés :** {len(references)}")
    for i, ref in enumerate(references[:5], 1):  # Afficher les 5 premiers
        st.write(f"{i}. {ref}")
    
    if len(references) > 5:
        st.write(f"... et {len(references) - 5} autres")

# ==================== SECTION 2: ANALYSE PAR DISTRIBUTEUR ====================

elif section == "📊 Analyse par Distributeur":
    st.header("📊 Analyse Détailée par Distributeur")
    
    st.dataframe(
        distributeurs_analysis,
        column_config={
            'distributeur': 'Distributeur',
            'montant_total': st.column_config.NumberColumn('Montant Total (FCFA)', format='%d FCFA'),
            'nombre_soumissions': 'Nombre de Soumissions',
            'lots_couverts': 'Lots Couverts',
            'paillasses_couvertes': 'Paillasses Couvertes',
            'pourcentage_montant': st.column_config.NumberColumn('% du Marché', format='%.2f%%')
        },
        use_container_width=True
    )
    
    # Filtre par distributeur
    selected_distributeur = st.selectbox(
        "Sélectionnez un distributeur pour voir le détail:",
        options=distributeurs_analysis['distributeur'].unique()
    )
    
    if selected_distributeur:
        dist_data = df[df['distributeur'] == selected_distributeur]
        
        st.subheader(f"🔍 Détail pour {selected_distributeur}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Montant Total", f"{dist_data['montant soumission'].sum():,.0f} FCFA")
        
        with col2:
            st.metric("Nombre de Lots", f"{dist_data['gamme'].nunique()}")
        
        with col3:
            st.metric("Paillasses Couvertes", f"{dist_data['paillasse'].nunique()}")
        
        # Détail par paillasse
        st.write("**Détail par Paillasse:**")
        detail_paillasse = dist_data.groupby('paillasse').agg({
            'montant soumission': 'sum',
            'gamme': 'count'
        }).reset_index()
        
        st.dataframe(detail_paillasse, use_container_width=True)

# ==================== SECTION 3: POSITIONNEMENT TS PAR PAILLASSE ====================

elif section == "🏥 Positionnement TS par Paillasse":
    st.header("🏥 Positionnement de TS par Paillasse")
    
    if ts_paillasse_analysis.empty:
        st.warning("Technologies Services n'apparaît pas dans les données analysées.")
    else:
        # Métriques TS
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("CA Total TS", f"{ts_paillasse_analysis['montant_total'].sum():,.0f} FCFA")
        
        with col2:
            st.metric("Lots Soumissionnés", f"{ts_paillasse_analysis['lots_couverts'].sum()}")
        
        with col3:
            st.metric("Paillasses Couvertes", f"{len(ts_paillasse_analysis)}")
        
        # Tableau des paillasses
        st.subheader("📊 Performance par Paillasse")
        
        st.dataframe(
            ts_paillasse_analysis,
            column_config={
                'paillasse': 'Paillasse',
                'montant_total': st.column_config.NumberColumn('Montant TS (FCFA)', format='%d FCFA'),
                'nombre_soumissions': 'Soumissions',
                'lots_couverts': 'Lots Couverts',
                'pourcentage_ts': st.column_config.NumberColumn('% du CA TS', format='%.2f%%')
            },
            use_container_width=True
        )
        
        # Sélection de paillasse pour le détail
        selected_paillasse = st.selectbox(
            "Sélectionnez une paillasse pour voir le détail:",
            options=ts_paillasse_analysis['paillasse'].unique()
        )
        
        if selected_paillasse:
            st.subheader(f"🔍 Détail de la Paillasse: {selected_paillasse}")
            
            # Détail des distributeurs pour cette paillasse
            detail_paillasse = get_paillasse_detail(df, selected_paillasse)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Répartition par Distributeur:**")
                st.dataframe(detail_paillasse, use_container_width=True)
            
            with col2:
                # Graphique de répartition
                fig = px.pie(
                    detail_paillasse,
                    values='montant_total',
                    names='distributeur',
                    title=f"Répartition {selected_paillasse}"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Section commentaires pour le DG
            st.subheader("💬 Commentaires du DG")
            
            # Initialiser le commentaire s'il n'existe pas
            if selected_paillasse not in st.session_state.commentaires:
                st.session_state.commentaires[selected_paillasse] = ""
            
            # Éditeur de commentaires
            commentaire = st.text_area(
                f"Commentaires pour {selected_paillasse}:",
                value=st.session_state.commentaires[selected_paillasse],
                height=150,
                key=f"comment_{selected_paillasse}"
            )
            
            # Sauvegarder le commentaire
            if st.button("💾 Sauvegarder le commentaire", key=f"save_{selected_paillasse}"):
                st.session_state.commentaires[selected_paillasse] = commentaire
                st.success("Commentaire sauvegardé!")
            
            # Afficher le commentaire sauvegardé
            if st.session_state.commentaires[selected_paillasse]:
                st.info(f"**Commentaire sauvegardé:** {st.session_state.commentaires[selected_paillasse]}")

# ==================== SECTION 4: LOTS NON POSITIONNÉS ====================

elif section == "🔍 Lots Non Positionnés":
    st.header("🔍 Lots Non Positionnés par TS")
    
    lots_non_positionnes = get_lots_non_positionnes_ts(df)
    
    if lots_non_positionnes.empty:
        st.success("🎉 TS s'est positionné sur tous les lots!")
    else:
        st.metric(
            "Lots Non Positionnés par TS",
            f"{len(lots_non_positionnes)}",
            help="Lots où Technologies Services ne s'est pas positionné"
        )
        
        st.subheader("📋 Liste des Lots Non Positionnés")
        
        st.dataframe(
            lots_non_positionnes,
            column_config={
                'gamme': 'Lot/Sous-lot',
                'paillasse': 'Paillasse',
                'distributeur': 'Distributeurs Présents',
                'montant soumission': st.column_config.NumberColumn('Montant (FCFA)', format='%d FCFA'),
                'attribution': 'Attribué à'
            },
            use_container_width=True
        )
        
        # Analyse des opportunités manquées
        st.subheader("💡 Analyse des Opportunités")
        
        montant_opportunites = lots_non_positionnes['montant soumission'].sum()
        st.write(f"**Potentiel manqué estimé :** {montant_opportunites:,.0f} FCFA")
        
        # Lots sans soumissionnaires
        lots_sans_soumission = df[df['distributeur'] == 'PAS DE SOUMISSIONNAIRE']
        if not lots_sans_sans_soumission.empty:
            st.warning(f"⚠️ {len(lots_sans_soumission)} lots sans soumissionnaires identifiés")
            
            st.write("**Lots sans soumissionnaires:**")
            st.dataframe(
                lots_sans_soumission[['gamme', 'paillasse', 'montant soumission']],
                use_container_width=True
            )

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
        st.write("**Répartition par référence:**")
        reference_counts = df['reference'].value_counts()
        st.dataframe(reference_counts, use_container_width=True)
    
    # Export des données
    st.subheader("📤 Export des Données")
    
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger Données Brutes (CSV)",
        data=csv_data,
        file_name=f"analyse_ts_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown(
    "**🏥 Dashboard Direction Générale - Technologies Services** • "
    f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}"
)
