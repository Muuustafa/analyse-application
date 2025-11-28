import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Configuration de la page
st.set_page_config(
    page_title="Dashboard DG - Technologies Services",
    page_icon="🏥",
    layout="wide"
)

# Fonction pour formater les montants avec séparateurs
def format_montant(montant):
    """Formate un montant avec des séparateurs de milliers"""
    try:
        return f"{montant:,.0f}".replace(",", " ").replace(".", " ") + " FCFA"
    except:
        return "0 FCFA"

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
        text_columns = ['paillasse', 'lot', 'modele', 'marque', 'distributeur', 'attribution', 'reference', 'famille']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.upper().str.strip()
        
        # Nettoyer les montants
        if 'montant soumission' in df.columns:
            df['montant soumission'] = pd.to_numeric(df['montant soumission'], errors='coerce').fillna(0)
        
        # Ajouter la colonne commentaires si elle n'existe pas
        if 'commentaires_dg' not in df.columns:
            df['commentaires_dg'] = ''
        
        return df
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")
        return pd.DataFrame()

# Fonction pour sauvegarder les commentaires dans le DataFrame
def save_comment_to_dataframe(df, paillasse, commentaire, reference):
    """Sauvegarde le commentaire dans le DataFrame"""
    try:
        # Créer une clé unique pour identifier le commentaire
        condition = (df['paillasse'] == paillasse) & (df['reference'] == reference)
        
        if condition.any():
            # Mettre à jour le commentaire pour toutes les lignes correspondantes
            df.loc[condition, 'commentaires_dg'] = commentaire
        else:
            # Si aucune ligne ne correspond, créer une nouvelle ligne
            new_row = {
                'paillasse': paillasse,
                'reference': reference,
                'commentaires_dg': commentaire,
                'lot': 'COMMENTAIRE_DG',
                'distributeur': 'SYSTEME',
                'montant soumission': 0
            }
            # Ajouter les autres colonnes nécessaires avec des valeurs par défaut
            for col in df.columns:
                if col not in new_row:
                    new_row[col] = ''
            
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        return df
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde du commentaire: {e}")
        return df

# Fonction pour récupérer le commentaire d'une paillasse
def get_comment_from_dataframe(df, paillasse, reference):
    """Récupère le commentaire d'une paillasse depuis le DataFrame"""
    try:
        condition = (df['paillasse'] == paillasse) & (df['reference'] == reference)
        if condition.any():
            commentaires = df.loc[condition, 'commentaires_dg'].dropna()
            if not commentaires.empty:
                return commentaires.iloc[0]
        return ""
    except:
        return ""

# Fonction pour détecter le nom de l'hôpital depuis le nom du fichier
def detect_hospital_name(filename):
    """Détecte le nom de l'hôpital depuis le nom du fichier"""
    # Nettoyer le nom du fichier
    name = os.path.splitext(filename)[0]
    
    # Mapping des noms d'hôpitaux courants
    hospital_keywords = {
        'DALAL': 'Hôpital Dalal Jamm',
        'JAMM': 'Hôpital Dalal Jamm', 
        'FANN': 'Hôpital Fann',
        'PRINCIPAL': 'Hôpital Principal',
        'LE_DANTEC': 'Hôpital Aristide Le Dantec',
        'DANTEC': 'Hôpital Aristide Le Dantec',
        'ALBERT_ROYER': 'Hôpital Albert Royer',
        'ENFANTS': 'Hôpital d\'Enfants',
        'GRAND_YOFF': 'Hôpital Grand Yoff',
        'ABASS': 'Hôpital Abass Ndao'
    }
    
    # Chercher des mots-clés dans le nom du fichier
    for keyword, hospital_name in hospital_keywords.items():
        if keyword in name.upper():
            return hospital_name
    
    # Si aucun mot-clé n'est trouvé, retourner le nom du fichier formaté
    return name.replace('_', ' ').title()

# Section d'upload
st.sidebar.header("📁 Chargement des données")
uploaded_file = st.sidebar.file_uploader(
    "Choisissez le fichier Excel des appels d'offres",
    type=["xlsx", "xls"],
    help="Fichier avec les colonnes: paillasse, lot, modele, marque, distributeur, montant soumission, attribution, reference, famille"
)

# Charger les données d'exemple si aucun fichier uploadé
if not uploaded_file:
    st.info("""
    ### 📋 Instructions
    Veuillez uploader un fichier Excel avec les colonnes suivantes:
    - **paillasse, lot, modele, marque, distributeur, montant soumission, attribution, reference, famille**
    
    L'analyse présentera les indicateurs clés pour Technologies Services.
    """)
    st.stop()

# Chargement des données
with st.spinner("Chargement et analyse des données..."):
    df_original = load_and_clean_data(uploaded_file)
    
    if df_original.empty:
        st.error("❌ Aucune donnée valide n'a pu être chargée.")
        st.stop()

# Vérification des colonnes requises
required_columns = ['paillasse', 'lot', 'distributeur', 'montant soumission', 'attribution', 'reference', 'famille']
missing_columns = [col for col in required_columns if col not in df_original.columns]
if missing_columns:
    st.error(f"❌ Colonnes manquantes: {', '.join(missing_columns)}")
    st.stop()

# Initialisation
TS_NAME = "TECHNOLOGIES SERVICES"

# Détection du nom de l'hôpital
hospital_name = detect_hospital_name(uploaded_file.name)

# ==================== FILTRE PAR APPEL D'OFFRE ====================

st.sidebar.header("🎯 Filtre par Appel d'Offre")
references = df_original['reference'].unique()
selected_reference = st.sidebar.selectbox(
    "Sélectionnez un appel d'offre:",
    options=["TOUS LES APPELS D'OFFRE"] + list(references)
)

# Appliquer le filtre si un appel d'offre spécifique est sélectionné
if selected_reference != "TOUS LES APPELS D'OFFRE":
    df_filtered = df_original[df_original['reference'] == selected_reference]
    st.sidebar.success(f"📋 Appel d'offre: {selected_reference}")
else:
    df_filtered = df_original
    st.sidebar.info("📊 Tous les appels d'offre")

# ==================== TITRE DYNAMIQUE ====================

# Titre principal dynamique
if selected_reference != "TOUS LES APPELS D'OFFRE":
    st.title(f"🏥 {hospital_name}")
    st.markdown(f"**Appel d'Offre: {selected_reference} - Technologies Services**")
else:
    st.title(f"🏥 {hospital_name}")
    st.markdown("**Analyse Globale - Technologies Services**")

st.markdown("---")

# ==================== CALCULS DES INDICATEURS CLÉS ====================

def calculate_kpis(data):
    """Calcule tous les indicateurs clés demandés par le DG"""
    
    # Indicateurs généraux
    total_soumissionnaires = data['distributeur'].nunique()
    montant_total_marche = data['montant soumission'].sum()
    
    # Données TS
    ts_data = data[data['distributeur'] == TS_NAME]
    montant_total_ts = ts_data['montant soumission'].sum()
    
    # NOUVEL INDICATEUR : Pourcentage de TS dans le marché
    pourcentage_marche_ts = (montant_total_ts / montant_total_marche * 100) if montant_total_marche > 0 else 0
    
    # Calcul du rang de TS
    distributeurs_montant = data.groupby('distributeur')['montant soumission'].sum().sort_values(ascending=False)
    distributeurs_count = data.groupby('distributeur')['lot'].count().sort_values(ascending=False)
    
    rang_montant_ts = distributeurs_montant.index.get_loc(TS_NAME) + 1 if TS_NAME in distributeurs_montant.index else 0
    rang_nombre_ts = distributeurs_count.index.get_loc(TS_NAME) + 1 if TS_NAME in distributeurs_count.index else 0
    
    # Lots et sous-lots
    total_lots = data['lot'].nunique()
    lots_ts_soumissionne = ts_data['lot'].nunique()
    
    # Lots attribués à TS
    lots_attribues_ts = data[data['attribution'] == TS_NAME]['lot'].nunique()
    pourcentage_attribution_ts = (lots_attribues_ts / total_lots * 100) if total_lots > 0 else 0
    
    # Lots non positionnés par TS
    tous_les_lots = set(data['lot'].unique())
    lots_ts = set(ts_data['lot'].unique())
    lots_non_positionnes_ts = tous_les_lots - lots_ts
    
    # Lots sans soumissionnaires
    lots_avec_soumission = set(data[data['distributeur'] != 'PAS DE SOUMISSIONNAIRE']['lot'].unique())
    lots_sans_soumission = tous_les_lots - lots_avec_soumission
    
    return {
        'total_soumissionnaires': total_soumissionnaires,
        'montant_total_marche': montant_total_marche,
        'montant_total_ts': montant_total_ts,
        'pourcentage_marche_ts': pourcentage_marche_ts,
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
        'lot': 'nunique',
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
        'lot': 'nunique'
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
        'lot': 'count',
        'marque': lambda x: ', '.join(x.unique()),
        'famille': lambda x: ', '.join(x.unique())
    }).reset_index()
    
    distributeurs.columns = ['distributeur', 'montant_total', 'nombre_lots', 'marques', 'familles']
    distributeurs = distributeurs.sort_values('montant_total', ascending=False)
    
    return distributeurs

def get_distributeur_paillasse_details(data, distributeur_selectionne):
    """Détail des paillasses pour un distributeur avec les lots"""
    dist_data = data[data['distributeur'] == distributeur_selectionne]
    
    # Grouper par paillasse et agréger les lots avec marque, modèle et famille
    detail_paillasse = dist_data.groupby('paillasse').agg({
        'montant soumission': 'sum',
        'lot': lambda x: '<br>• '.join([''] + list(x.unique())),
        'marque': lambda x: '<br>• '.join([''] + list(x.unique())),
        'modele': lambda x: '<br>• '.join([''] + list(x.unique())),
        'famille': lambda x: '<br>• '.join([''] + list(x.unique()))
    }).reset_index()
    
    detail_paillasse.columns = ['paillasse', 'montant_total', 'lots', 'marques', 'modeles', 'familles']
    detail_paillasse = detail_paillasse.sort_values('montant_total', ascending=False)
    
    return detail_paillasse

def get_lots_non_positionnes_ts(data):
    """Lots où TS ne s'est pas positionné"""
    tous_les_lots = set(data['lot'].unique())
    lots_ts = set(data[data['distributeur'] == TS_NAME]['lot'].unique())
    lots_non_positionnes = tous_les_lots - lots_ts
    
    # Récupérer les données de ces lots
    lots_data = data[data['lot'].isin(lots_non_positionnes)]
    
    # Garder une ligne par lot avec le distributeur principal
    analysis = lots_data.groupby('lot').agg({
        'paillasse': 'first',
        'distributeur': lambda x: ', '.join(x.unique()),
        'montant soumission': 'sum',
        'attribution': 'first'
    }).reset_index()
    
    return analysis

def get_detail_distributeurs_lot(data, lot_selectionne):
    """Détail des distributeurs pour un lot spécifique avec marque, modèle et famille"""
    lot_data = data[data['lot'] == lot_selectionne]
    
    # Analyse par distributeur pour ce lot
    distributeurs_detail = lot_data.groupby('distributeur').agg({
        'montant soumission': 'sum',
        'marque': 'first',
        'modele': 'first',
        'famille': 'first'
    }).reset_index()
    
    distributeurs_detail = distributeurs_detail.sort_values('montant soumission', ascending=False)
    
    # Calcul du total
    total_montant = distributeurs_detail['montant soumission'].sum()
    
    return distributeurs_detail, total_montant

# ==================== CALCUL DES INDICATEURS ====================

kpis = calculate_kpis(df_filtered)
distributeurs_analysis = get_distributeurs_analysis(df_filtered)
ts_paillasse_analysis = get_ts_paillasse_analysis(df_filtered)

# Navigation
st.sidebar.header("📊 Navigation")
section = st.sidebar.radio(
    "Sélectionnez une vue:",
    ["🎯 Tableau de Bord", "📊 Analyse par Distributeur", "🏥 Positionnement TS par Paillasse", 
     "🔍 Lots Non Soumissionnés", "📋 Données Brutes"]
)

# ==================== SECTION 1: TABLEAU DE BORD ====================

if section == "🎯 Tableau de Bord":
    st.header("🎯 Tableau de Bord Direction Générale")
    
    # Affichage de l'appel d'offre sélectionné
    if selected_reference != "TOUS LES APPELS D'OFFRE":
        st.info(f"**📋 Appel d'offre analysé :** {selected_reference}")
    else:
        st.info("**📊 Analyse globale de tous les appels d'offre**")
    
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
            format_montant(kpis['montant_total_marche']),
            help="Montant total de toutes les soumissions"
        )
    
    with col3:
        st.metric(
            "Montant Total TS",
            format_montant(kpis['montant_total_ts']),
            help="Montant total des soumissions de Technologies Services"
        )
    
    with col4:
        st.metric(
            "Part de Marché TS",
            f"{kpis['pourcentage_marche_ts']:.1f}%",
            help="Pourcentage du marché détenu par Technologies Services"
        )
    
    # Deuxième ligne de métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Rang TS (Montant)",
            f"{kpis['rang_montant_ts']}ème",
            help="Classement de TS par montant de soumission"
        )
    
    with col2:
        st.metric(
            "Total Lots/Sous-lots",
            f"{kpis['total_lots']}",
            help="Nombre total de lots et sous-lots dans l'appel d'offre"
        )
    
    with col3:
        st.metric(
            "Lots Soumissionnés TS",
            f"{kpis['lots_ts_soumissionne']}",
            help="Nombre de lots où TS a soumissionné"
        )
    
    with col4:
        st.metric(
            "Lots Attribués à TS",
            f"{kpis['lots_attribues_ts']}",
            delta=f"{kpis['pourcentage_attribution_ts']:.1f}%",
            help="Lots attribués à Technologies Services"
        )
    
    # Troisième ligne de métriques
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Lots Non Positionnés TS",
            f"{kpis['lots_non_positionnes_ts']}",
            help="Lots où TS ne s'est pas positionné"
        )
    
    with col2:
        st.metric(
            "Rang TS (Nombre)",
            f"{kpis['rang_nombre_ts']}ème",
            help="Classement de TS par nombre de soumissions"
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
        fig_montant.update_layout(yaxis_tickformat=',')
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
    
    references = df_original['reference'].unique()
    st.write(f"**Appels d'offres disponibles :** {len(references)}")
    for i, ref in enumerate(references[:5], 1):  # Afficher les 5 premiers
        st.write(f"{i}. {ref}")
    
    if len(references) > 5:
        st.write(f"... et {len(references) - 5} autres")

# ==================== SECTION 2: ANALYSE PAR DISTRIBUTEUR ====================

elif section == "📊 Analyse par Distributeur":
    st.header("📊 Analyse Détailée par Distributeur")
    
    if selected_reference != "TOUS LES APPELS D'OFFRE":
        st.info(f"**📋 Appel d'offre analysé :** {selected_reference}")
    
    # Créer une copie pour l'affichage avec montants formatés
    display_distributeurs = distributeurs_analysis.copy()
    display_distributeurs['montant_total_format'] = display_distributeurs['montant_total'].apply(format_montant)
    
    st.dataframe(
        display_distributeurs[['distributeur', 'montant_total_format', 'nombre_soumissions', 'lots_couverts', 'paillasses_couvertes', 'pourcentage_montant']],
        column_config={
            'distributeur': 'Distributeur',
            'montant_total_format': 'Montant Total',
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
        dist_data = df_filtered[df_filtered['distributeur'] == selected_distributeur]
        
        st.subheader(f"🔍 Détail pour {selected_distributeur}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Montant Total", format_montant(dist_data['montant soumission'].sum()))
        
        with col2:
            st.metric("Nombre de Lots", f"{dist_data['lot'].nunique()}")
        
        with col3:
            st.metric("Paillasses Couvertes", f"{dist_data['paillasse'].nunique()}")
        
        # Détail par paillasse avec lots, marques, modèles et familles
        st.subheader("📋 Détail par Paillasse")
        
        detail_paillasse = get_distributeur_paillasse_details(df_filtered, selected_distributeur)
        
        # Afficher avec formatage pour les informations détaillées
        for _, row in detail_paillasse.iterrows():
            with st.expander(f"🏥 {row['paillasse']} - {format_montant(row['montant_total'])}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Montant total :** {format_montant(row['montant_total'])}")
                    st.write("**Lots :**")
                    lots_html = f"<div style='max-height: 150px; overflow-y: auto; font-size: 0.9em;'>{row['lots']}</div>"
                    st.markdown(lots_html, unsafe_allow_html=True)
                
                with col2:
                    st.write("**Marques :**")
                    marques_html = f"<div style='max-height: 100px; overflow-y: auto; font-size: 0.9em;'>{row['marques']}</div>"
                    st.markdown(marques_html, unsafe_allow_html=True)
                    
                    st.write("**Modèles :**")
                    modeles_html = f"<div style='max-height: 100px; overflow-y: auto; font-size: 0.9em;'>{row['modeles']}</div>"
                    st.markdown(modeles_html, unsafe_allow_html=True)
                    
                    st.write("**Familles :**")
                    familles_html = f"<div style='max-height: 100px; overflow-y: auto; font-size: 0.9em;'>{row['familles']}</div>"
                    st.markdown(familles_html, unsafe_allow_html=True)

# ==================== SECTION 3: POSITIONNEMENT TS PAR PAILLASSE ====================

elif section == "🏥 Positionnement TS par Paillasse":
    st.header("🏥 Positionnement de TS par Paillasse")
    
    if selected_reference != "TOUS LES APPELS D'OFFRE":
        st.info(f"**📋 Appel d'offre analysé :** {selected_reference}")
    
    if ts_paillasse_analysis.empty:
        st.warning("Technologies Services n'apparaît pas dans les données analysées.")
    else:
        # Métriques TS
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("CA Total TS", format_montant(ts_paillasse_analysis['montant_total'].sum()))
        
        with col2:
            st.metric("Lots Soumissionnés", f"{ts_paillasse_analysis['lots_couverts'].sum()}")
        
        with col3:
            st.metric("Paillasses Couvertes", f"{len(ts_paillasse_analysis)}")
        
        # Tableau des paillasses avec montants formatés
        st.subheader("📊 Performance par Paillasse")
        
        display_ts_paillasse = ts_paillasse_analysis.copy()
        display_ts_paillasse['montant_total_format'] = display_ts_paillasse['montant_total'].apply(format_montant)
        
        st.dataframe(
            display_ts_paillasse[['paillasse', 'montant_total_format', 'nombre_soumissions', 'lots_couverts', 'pourcentage_ts']],
            column_config={
                'paillasse': 'Paillasse',
                'montant_total_format': 'Montant TS',
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
            detail_paillasse = get_paillasse_detail(df_filtered, selected_paillasse)
            
            # Formater les montants pour l'affichage
            detail_paillasse_display = detail_paillasse.copy()
            detail_paillasse_display['montant_total_format'] = detail_paillasse_display['montant_total'].apply(format_montant)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Répartition par Distributeur:**")
                st.dataframe(
                    detail_paillasse_display[['distributeur', 'montant_total_format', 'nombre_lots', 'marques', 'familles']],
                    use_container_width=True
                )
            
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
            st.subheader("💬 Commentaires")
            
            # Récupérer le commentaire existant depuis le DataFrame
            commentaire_existant = get_comment_from_dataframe(df_original, selected_paillasse, selected_reference if selected_reference != "TOUS LES APPELS D'OFFRE" else "")
            
            # Éditeur de commentaires
            commentaire = st.text_area(
                f"Commentaires pour {selected_paillasse}:",
                value=commentaire_existant,
                height=150,
                key=f"comment_{selected_paillasse}_{selected_reference}"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Sauvegarder le commentaire
                if st.button("💾 Sauvegarder le commentaire", key=f"save_{selected_paillasse}_{selected_reference}"):
                    # Sauvegarder dans le DataFrame global
                    updated_df = save_comment_to_dataframe(df_original, selected_paillasse, commentaire, selected_reference if selected_reference != "TOUS LES APPELS D'OFFRE" else "")
                    
                    # Mettre à jour le DataFrame original
                    st.session_state.df_original = updated_df
                    st.success("Commentaire sauvegardé dans le fichier!")
            
            with col2:
                # Télécharger le fichier mis à jour
                if 'df_original' in st.session_state:
                    csv_data = st.session_state.df_original.to_csv(index=False).encode('utf-8')
                else:
                    csv_data = df_original.to_csv(index=False).encode('utf-8')
                    
                st.download_button(
                    label="📥 Télécharger avec commentaires",
                    data=csv_data,
                    file_name=f"commentaires_{hospital_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    help="Téléchargez le fichier avec tous les commentaires sauvegardés"
                )
            
            # Afficher le commentaire sauvegardé
            if commentaire_existant:
                st.info(f"**Commentaire sauvegardé:** {commentaire_existant}")

# ==================== SECTION 4: LOTS NON POSITIONNÉS ====================

elif section == "🔍 Lots Non Positionnés":
    st.header("🔍 Lots Non Positionnés par TS")
    
    if selected_reference != "TOUS LES APPELS D'OFFRE":
        st.info(f"**📋 Appel d'offre analysé :** {selected_reference}")
    
    lots_non_positionnes = get_lots_non_positionnes_ts(df_filtered)
    
    if lots_non_positionnes.empty:
        st.success("🎉 TS s'est positionné sur tous les lots!")
    else:
        st.metric(
            "Lots Non Positionnés par TS",
            f"{len(lots_non_positionnes)}",
            help="Lots où Technologies Services ne s'est pas positionné"
        )
        
        st.subheader("📋 Liste des Lots Non Soumissionnés")
        
        # Afficher chaque lot avec le détail des distributeurs
        for _, lot in lots_non_positionnes.iterrows():
            with st.expander(f"📦 {lot['lot']} - {format_montant(lot['montant soumission'])} - {lot['paillasse']}"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Paillasse :** {lot['paillasse']}")
                    st.write(f"**Attribué à :** {lot['attribution']}")
                    st.write(f"**Montant total du lot :** {format_montant(lot['montant soumission'])}")
                
                with col2:
                    # Récupérer le détail des distributeurs pour ce lot
                    distributeurs_detail, total_montant = get_detail_distributeurs_lot(df_filtered, lot['lot'])
                    
                    st.write("**Détail par distributeur :**")
                    
                    # Afficher le tableau des distributeurs avec marque, modèle et famille
                    for _, dist in distributeurs_detail.iterrows():
                        st.write(f"• **{dist['distributeur']}** : {format_montant(dist['montant soumission'])}")
                        if pd.notna(dist['marque']) and dist['marque'] != 'NAN':
                            st.write(f"  _Marque : {dist['marque']}_")
                        if pd.notna(dist['modele']) and dist['modele'] != 'NAN':
                            st.write(f"  _Modèle : {dist['modele']}_")
                        if pd.notna(dist['famille']) and dist['famille'] != 'NAN':
                            st.write(f"  _Famille : {dist['famille']}_")
                        st.write("")  # Ligne vide pour la séparation
                    
                    st.write(f"**Total des soumissions :** {format_montant(total_montant)}")
        
        # Analyse des opportunités manquées
        st.subheader("💡 Analyse des Opportunités")
        
        montant_opportunites = lots_non_positionnes['montant soumission'].sum()
        st.write(f"**Potentiel manqué estimé :** {format_montant(montant_opportunites)}")
        
        # Lots sans soumissionnaires
        lots_sans_soumission = df_filtered[df_filtered['distributeur'] == 'PAS DE SOUMISSIONNAIRES']
        if not lots_sans_soumission.empty:
            st.warning(f"⚠️ {len(lots_sans_soumission)} lots sans soumissionnaires identifiés")
            
            st.write("**Lots sans soumissionnaires:**")
            lots_sans_soumission_display = lots_sans_soumission.copy()
            lots_sans_soumission_display['montant_format'] = lots_sans_soumission_display['montant soumission'].apply(format_montant)
            
            st.dataframe(
                lots_sans_soumission_display[['lot', 'paillasse', 'montant_format']],
                use_container_width=True
            )

# ==================== SECTION 5: DONNÉES BRUTES ====================

elif section == "📋 Données Brutes":
    st.header("📋 Données Brutes et Export")
    
    if selected_reference != "TOUS LES APPELS D'OFFRE":
        st.info(f"**📋 Appel d'offre analysé :** {selected_reference}")
    
    st.subheader("Aperçu des Données")
    
    # Créer une copie avec montants formatés pour l'affichage
    df_display = df_filtered.copy()
    df_display['montant_format'] = df_display['montant soumission'].apply(format_montant)
    
    st.dataframe(
        df_display[['reference', 'paillasse', 'lot', 'marque', 'modele', 'famille', 'distributeur', 'montant_format', 'attribution', 'commentaires_dg']],
        use_container_width=True
    )
    
    # Statistiques descriptives
    st.subheader("Statistiques Descriptives")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Description des montants:**")
        st.dataframe(df_filtered['montant soumission'].describe(), use_container_width=True)
    
    with col2:
        st.write("**Répartition par référence:**")
        reference_counts = df_original['reference'].value_counts()
        st.dataframe(reference_counts, use_container_width=True)
    
    # Export des données
    st.subheader("📤 Export des Données")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export des données filtrées
        csv_data_filtered = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Données Filtrees (CSV)",
            data=csv_data_filtered,
            file_name=f"donnees_filtrees_{hospital_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Export de toutes les données avec commentaires
        if 'df_original' in st.session_state:
            csv_data_all = st.session_state.df_original.to_csv(index=False).encode('utf-8')
        else:
            csv_data_all = df_original.to_csv(index=False).encode('utf-8')
            
        st.download_button(
            label="📥 Toutes Donnees avec Commentaires",
            data=csv_data_all,
            file_name=f"toutes_donnees_commentaires_{hospital_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.markdown(
    f"**🏥 {hospital_name} - Dashboard Direction Générale - Technologies Services** • "
    f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}"
)
