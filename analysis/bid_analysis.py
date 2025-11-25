import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

class BidAnalyzer:
    def __init__(self, data):
        self.data = data
        self.ts_name = "TECHNOLOGIES SERVICES"
    
    def calculate_market_share(self):
        """Calcule la part de marché globale"""
        total_market = self.data['montant soumission'].sum()
        ts_data = self.data[self.data['distributeur'] == self.ts_name]
        ts_total = ts_data['montant soumission'].sum()
        
        ts_market_share = (ts_total / total_market * 100) if total_market > 0 else 0
        
        return {
            'total_marche': total_market,
            'total_ts': ts_total,
            'part_marche_ts': ts_market_share,
            'nombre_soumissions_ts': len(ts_data),
            'nombre_soumissions_total': len(self.data)
        }
    
    def get_market_distribution(self):
        """Répartition du marché par distributeur"""
        market_distribution = self.data.groupby('distributeur')['montant soumission'].sum().reset_index()
        market_distribution = market_distribution.sort_values('montant soumission', ascending=False)
        
        # Grouper les petits distributeurs
        top_distributors = market_distribution.head(8)
        others = market_distribution[8:]['montant soumission'].sum()
        
        if others > 0:
            top_distributors = pd.concat([
                top_distributors,
                pd.DataFrame([{'distributeur': 'AUTRES', 'montant soumission': others}])
            ])
        
        return top_distributors
    
    def analyze_by_paillasse(self):
        """Analyse détaillée par paillasse"""
        analysis = self.data.groupby('paillasse').agg({
            'montant soumission': ['sum', 'count', 'mean'],
            'distributeur': 'nunique'
        }).round(2)
        
        analysis.columns = ['montant_total', 'nombre_soumissions', 'montant_moyen', 'nombre_distributeurs']
        
        # Calcul de la part de TS par paillasse
        ts_by_paillasse = self.data[self.data['distributeur'] == self.ts_name].groupby('paillasse').agg({
            'montant soumission': 'sum',
            'gamme': 'count'
        })
        
        ts_by_paillasse.columns = ['montant_ts', 'soumissions_ts']
        
        analysis = analysis.merge(ts_by_paillasse, on='paillasse', how='left').fillna(0)
        analysis['part_marche_ts'] = (analysis['montant_ts'] / analysis['montant_total'] * 100).round(2)
        
        return analysis.reset_index()
    
    def get_top_paillasses(self):
        """Top paillasses par montant total"""
        paillasse_analysis = self.analyze_by_paillasse()
        return paillasse_analysis.nlargest(10, 'montant_total')
    
    def get_ts_paillasse_performance(self):
        """Performance TS par paillasse"""
        paillasse_analysis = self.analyze_by_paillasse()
        return paillasse_analysis[paillasse_analysis['montant_ts'] > 0]
    
    def get_paillasse_distributors(self, paillasse):
        """Répartition par distributeur pour une paillasse spécifique"""
        paillasse_data = self.data[self.data['paillasse'] == paillasse]
        distributor_share = paillasse_data.groupby('distributeur')['montant soumission'].sum().reset_index()
        return distributor_share.sort_values('montant soumission', ascending=False)
    
    def get_paillasse_gammes(self, paillasse):
        """Analyse des gammes pour une paillasse spécifique"""
        paillasse_data = self.data[self.data['paillasse'] == paillasse]
        
        gammes_analysis = paillasse_data.groupby('gamme').agg({
            'montant soumission': ['sum', 'count'],
            'distributeur': 'nunique'
        }).round(2)
        
        gammes_analysis.columns = ['montant_total', 'nombre_soumissions', 'nombre_distributeurs']
        return gammes_analysis.reset_index().sort_values('montant_total', ascending=False)
    
    def get_competitors_analysis(self):
        """Analyse des concurrents principaux"""
        competitors = self.data[self.data['distributeur'] != self.ts_name]
        competitor_stats = competitors.groupby('distributeur').agg({
            'montant soumission': ['sum', 'count'],
            'paillasse': 'nunique',
            'gamme': 'nunique'
        }).round(2)
        
        competitor_stats.columns = ['montant_total', 'nombre_soumissions', 'paillasses_couvertes', 'gammes_couvertes']
        competitor_stats['part_marche'] = (competitor_stats['montant_total'] / self.data['montant soumission'].sum() * 100).round(2)
        
        return competitor_stats.reset_index().sort_values('montant_total', ascending=False)
    
    def get_ts_vs_competitors_comparison(self):
        """Comparaison TS vs principaux concurrents"""
        competitors = self.get_competitors_analysis()
        market_share = self.calculate_market_share()
        
        top_competitors = competitors.head(5)
        comparison_data = []
        
        # Ajouter TS
        comparison_data.append({
            'distributeur': self.ts_name,
            'montant_total': market_share['total_ts'],
            'nombre_soumissions': market_share['nombre_soumissions_ts'],
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
        
        return pd.DataFrame(comparison_data)
    
    def get_ts_performance_details(self):
        """Détails de performance de TS - CORRIGÉ"""
        ts_data = self.data[self.data['distributeur'] == self.ts_name]
        
        if ts_data.empty:
            return pd.DataFrame()
        
        # Performance de TS par paillasse
        performance = ts_data.groupby('paillasse').agg({
            'montant soumission': ['sum', 'count', 'mean'],
            'gamme': 'nunique'
        }).round(2)
        
        performance.columns = ['montant_total_ts', 'nombre_soumissions', 'montant_moyen', 'gammes_couvertes']
        performance = performance.reset_index()
        
        # Montant total du marché par paillasse
        market_by_paillasse = self.data.groupby('paillasse')['montant soumission'].sum().reset_index()
        market_by_paillasse.columns = ['paillasse', 'montant_total_marche']
        
        # Fusionner les données
        performance = performance.merge(market_by_paillasse, on='paillasse', how='left')
        
        # Calculer la part de marché
        performance['part_marche'] = (performance['montant_total_ts'] / performance['montant_total_marche'] * 100).round(2)
        
        return performance
    
    def get_ts_strong_points(self):
        """Points forts de TS (part de marché >= 20%)"""
        ts_performance = self.get_ts_performance_details()
        if ts_performance.empty:
            return pd.DataFrame()
        return ts_performance[ts_performance['part_marche'] >= 20]
    
    def get_ts_improvement_areas(self):
        """Axes d'amélioration de TS (part de marché < 10%)"""
        ts_performance = self.get_ts_performance_details()
        if ts_performance.empty:
            return pd.DataFrame()
        return ts_performance[ts_performance['part_marche'] < 10]
