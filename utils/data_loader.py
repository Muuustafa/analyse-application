import pandas as pd
import streamlit as st

def load_and_clean_uploaded_data(uploaded_files):
    """
    Charge et nettoie les données des fichiers Excel uploadés
    """
    all_data = []
    
    for uploaded_file in uploaded_files:
        try:
            # Charger le fichier Excel
            df = pd.read_excel(uploaded_file)
            
            # Standardiser les noms de colonnes
            df.columns = [col.strip().lower() for col in df.columns]
            
            # Vérifier que les colonnes requises sont présentes
            required_columns = ['catégorie', 'gamme', 'modele', 'marque', 'distributeur', 'montant soumission']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.warning(f"Colonnes manquantes dans {uploaded_file.name}: {missing_columns}")
                continue
            
            # Nettoyer les données
            df = clean_dataframe(df)
            
            # Ajouter le nom du fichier source
            df['source_fichier'] = uploaded_file.name
            
            all_data.append(df)
            
        except Exception as e:
            st.error(f"Erreur lors du chargement de {uploaded_file.name}: {str(e)}")
    
    if not all_data:
        st.error("Aucune donnée valide n'a pu être chargée.")
        return pd.DataFrame()
    
    # Fusionner toutes les données
    combined_data = pd.concat(all_data, ignore_index=True)
    
    return combined_data

def clean_dataframe(df):
    """
    Nettoie et standardise le dataframe
    """
    # Faire une copie pour éviter les warnings
    df_clean = df.copy()
    
    # Nettoyer les colonnes texte
    text_columns = ['catégorie', 'gamme', 'modele', 'marque', 'distributeur']
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()
    
    # Nettoyer la colonne montant
    if 'montant soumission' in df_clean.columns:
        df_clean['montant soumission'] = (
            df_clean['montant soumission']
            .astype(str)
            .str.replace(' FCFA', '', regex=False)
            .str.replace(' ', '')
            .str.replace(',', '')
            .replace('nan', '0')
            .replace('None', '0')
            .fillna('0')
            .astype(float)
        )
    
    # Standardiser les noms de distributeurs
    if 'distributeur' in df_clean.columns:
        df_clean['distributeur'] = df_clean['distributeur'].str.upper().str.strip()
    
    return df_clean

def categorize_gamme(gamme):
    """
    Catégorise les gammes selon les 3 catégories principales
    """
    if pd.isna(gamme) or gamme == 'nan':
        return 'Non classifié'
    
    gamme_lower = str(gamme).lower()
    
    if any(word in gamme_lower for word in ['biologie', 'bactério', 'hématologie', 'biochimie', 'sérologie', 'immunologie', 'parasitologie']):
        return 'Biologie'
    elif any(word in gamme_lower for word in ['chirurgie', 'anesthésie', 'dentaire', 'bloc opératoire', 'instrumentation', 'pédiatrie', 'réanimation', 'urgences']):
        return 'Chirurgie'
    elif any(word in gamme_lower for word in ['imagerie', 'radiologie', 'échographie', 'cardio', 'neurologie', 'diagnostic']):
        return 'Imagerie'
    else:
        return 'Autre'