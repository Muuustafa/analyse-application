import pandas as pd
import streamlit as st

def load_and_clean_data(uploaded_file):
    """
    Charge et nettoie les données du fichier Excel uploadé
    
    Args:
        uploaded_file: Fichier uploadé via Streamlit
        
    Returns:
        DataFrame: Données nettoyées et standardisées
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

def validate_data_structure(df):
    """
    Valide la structure des données
    
    Args:
        df: DataFrame à valider
        
    Returns:
        tuple: (bool, str) - (Est valide, Message d'erreur)
    """
    required_columns = ['paillasse', 'gamme', 'distributeur', 'montant soumission']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"Colonnes manquantes: {', '.join(missing_columns)}"
    
    if df.empty:
        return False, "Le fichier ne contient aucune donnée valide"
    
    return True, "Structure des données valide"
