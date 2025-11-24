import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

class BidAnalyzer:
    def __init__(self, data):
        self.data = data
        self.ts_data = data[data['distributeur'] == 'TECHNOLOGIES SERVICES']
        self.no_bidder_data = self._identify_no_bidder_gammes()
    
    def _identify_no_bidder_gammes(self):
        """Identifie les gammes sans soumissionnaire"""
        return self.data[
            self.data['distributeur'].str.contains(
                'pas de soumissionnaire|aucun|non', 
                case=False, 
                na=False
            )
        ]
    
    # ==================== ANALYSE MARCHÉ ====================
    
    def get_market_overview(self):
        """Vue d'ensemble du marché"""
        total_bids = len(self.data)
        total_amount = self.data['montant soumission'].sum()
        ts_participation = len(self.ts_data)
        ts_market_share = (ts_participation / total_bids * 100) if total_bids > 0 else 0
        
        return {
            'total_soumissions': total_bids,
            'montant_total_marche': total_amount,
            'participation_ts': ts_participation,
            'part_marche_ts': ts_market_share,
            'gammes_sans_soumissionnaires': len(self.no_bidder_data)
        }
    
    def get_category_analysis(self):
        """Analyse détaillée par catégorie"""
        category_stats = self.data.groupby('catégorie').agg({
            'montant soumission': ['count', 'sum', 'mean', 'median', 'std'],
            'distributeur': 'nunique'
        }).round(2)
        
        category_stats.columns = [
            'nombre_soumissions', 'montant_total', 'prix_moyen', 
            'prix_median', 'ecart_type', 'nombre_distributeurs'
        ]
        
        # Calculer l'attractivité du marché
        category_stats['densite_concurrentielle'] = (
            category_stats['nombre_distributeurs'] / category_stats['nombre_soumissions']
        ).round(3)
        
        category_stats['potentiel_marche'] = category_stats['montant_total']
        
        return category_stats.reset_index()
    
    # ==================== ANALYSE TS ====================
    
    def get_ts_performance(self):
        """Performance détaillée de Technologies Services"""
        if self.ts_data.empty:
            return pd.DataFrame()
        
        ts_perf = self.ts_data.groupby('catégorie').agg({
            'montant soumission': ['count', 'sum', 'mean', 'median'],
            'gamme': 'nunique'
        }).round(2)
        
        ts_perf.columns = [
            'soumissions_ts', 'montant_ts', 'prix_moyen_ts', 
            'prix_median_ts', 'gammes_couvertes'
        ]
        
        # Comparaison avec le marché
        market_stats = self.get_category_analysis()
        ts_perf = ts_perf.merge(
            market_stats[['catégorie', 'montant_total', 'nombre_soumissions']], 
            on='catégorie', 
            how='left'
        )
        
        ts_perf['part_marche_volume'] = (
            ts_perf['soumissions_ts'] / ts_perf['nombre_soumissions'] * 100
        ).round(2)
        
        ts_perf['part_marche_montant'] = (
            ts_perf['montant_ts'] / ts_perf['montant_total'] * 100
        ).round(2)
        
        return ts_perf.reset_index()
    
    def get_ts_competitive_position(self):
        """Position concurrentielle de TS"""
        ts_perf = self.get_ts_performance()
        if ts_perf.empty:
            return pd.DataFrame()
        
        # Classer les positions
        def classify_position(row):
            part_marche = row['part_marche_montant']
            if part_marche >= 30:
                return 'Leader'
            elif part_marche >= 15:
                return 'Compétiteur fort'
            elif part_marche >= 5:
                return 'Compétiteur moyen'
            else:
                return 'Marginal'
        
        ts_perf['position_concurrentielle'] = ts_perf.apply(classify_position, axis=1)
        
        return ts_perf
    
    # ==================== OPPORTUNITÉS STRATÉGIQUES ====================
    
    def estimate_missing_bids_value(self):
        """Estime la valeur des gammes sans soumissionnaire"""
        if self.no_bidder_data.empty:
            return pd.DataFrame()
        
        estimated_values = []
        
        for _, gamme in self.no_bidder_data.iterrows():
            estimation = self._estimate_gamme_price(gamme)
            estimated_values.append({
                'catégorie': gamme['catégorie'],
                'gamme': gamme['gamme'],
                'modele': gamme['modele'],
                'marque': gamme['marque'],
                'montant_estime': estimation['price'],
                'niveau_confiance': estimation['confidence'],
                'methode_estimation': estimation['method'],
                'opportunite_id': f"{gamme['catégorie']}_{gamme['gamme']}"
            })
        
        return pd.DataFrame(estimated_values)
    
    def _estimate_gamme_price(self, gamme):
        """Estime le prix d'une gamme spécifique"""
        # Méthode 1: Produits similaires dans la même catégorie
        similar_gammes = self.data[
            (self.data['catégorie'] == gamme['catégorie']) &
            (self.data['gamme'].str.contains(gamme['gamme'].split('-')[0], na=False))
        ]
        
        if len(similar_gammes) >= 2:
            return {
                'price': similar_gammes['montant soumission'].median(),
                'confidence': 'Élevé',
                'method': 'Médiane produits similaires'
            }
        
        # Méthode 2: Prix médian de la catégorie
        category_median = self.data[
            self.data['catégorie'] == gamme['catégorie']
        ]['montant soumission'].median()
        
        if not pd.isna(category_median):
            return {
                'price': category_median,
                'confidence': 'Moyen',
                'method': 'Médiane catégorielle'
            }
        
        # Méthode 3: Estimation conservative
        market_median = self.data['montant soumission'].median()
        return {
            'price': market_median * 0.7,  # Réduction de 30% pour estimation prudente
            'confidence': 'Faible',
            'method': 'Estimation marché global'
        }
    
    def get_strategic_opportunities(self):
        """Identifie les opportunités stratégiques pour TS"""
        opportunities = self.estimate_missing_bids_value()
        
        if opportunities.empty:
            return pd.DataFrame()
        
        # Calcul du score d'opportunité
        confidence_weights = {'Élevé': 1.0, 'Moyen': 0.7, 'Faible': 0.4}
        opportunities['score_confiance'] = opportunities['niveau_confiance'].map(confidence_weights)
        
        opportunities['score_opportunite'] = (
            opportunities['montant_estime'] * opportunities['score_confiance'] / 1000000
        ).round(2)
        
        # Priorisation
        opportunities['priorite'] = pd.cut(
            opportunities['score_opportunite'],
            bins=[0, 1, 5, float('inf')],
            labels=['Basse', 'Moyenne', 'Haute']
        )
        
        return opportunities.sort_values('score_opportunite', ascending=False)
    
    def get_ts_growth_potential(self):
        """Calcule le potentiel de croissance pour TS"""
        opportunities = self.get_strategic_opportunities()
        ts_position = self.get_ts_competitive_position()
        
        growth_potential = {
            'opportunites_identifiees': len(opportunities),
            'montant_total_opportunites': opportunities['montant_estime'].sum() if not opportunities.empty else 0,
            'opportunites_haute_priorite': len(opportunities[opportunities['priorite'] == 'Haute']) if not opportunities.empty else 0,
            'categories_sous_exploitees': [],
            'recommandations': []
        }
        
        # Analyser les catégories sous-exploitées
        if not ts_position.empty:
            weak_categories = ts_position[ts_position['part_marche_montant'] < 10]
            growth_potential['categories_sous_exploitees'] = weak_categories['catégorie'].tolist()
        
        # Générer des recommandations
        if not opportunities.empty:
            top_opportunity = opportunities.iloc[0]
            growth_potential['recommandations'].append(
                f"Prioriser '{top_opportunity['gamme']}' - Potentiel: {top_opportunity['montant_estime']:,.0f} FCFA"
            )
        
        return growth_potential
    
    # ==================== ANALYSE CONCURRENTIELLE ====================
    
    def get_competitive_landscape(self):
        """Analyse du paysage concurrentiel"""
        competitor_analysis = self.data.groupby('distributeur').agg({
            'montant soumission': ['count', 'sum', 'mean'],
            'catégorie': 'nunique',
            'gamme': 'nunique'
        }).round(2)
        
        competitor_analysis.columns = [
            'nombre_soumissions', 'montant_total', 'prix_moyen',
            'categories_couvertes', 'gammes_couvertes'
        ]
        
        competitor_analysis['part_marche_volume'] = (
            competitor_analysis['nombre_soumissions'] / len(self.data) * 100
        ).round(2)
        
        competitor_analysis['part_marche_montant'] = (
            competitor_analysis['montant_total'] / self.data['montant soumission'].sum() * 100
        ).round(2)
        
        return competitor_analysis.reset_index()
    
    def get_ts_vs_competitors(self):
        """Comparaison TS vs principaux concurrents"""
        competitors = self.get_competitive_landscape()
        ts_data = competitors[competitors['distributeur'] == 'TECHNOLOGIES SERVICES']
        
        if ts_data.empty:
            return pd.DataFrame()
        
        main_competitors = competitors[
            (competitors['distributeur'] != 'TECHNOLOGIES SERVICES') &
            (competitors['nombre_soumissions'] >= 5)
        ].nlargest(5, 'nombre_soumissions')
        
        comparison = pd.concat([ts_data, main_competitors])
        return comparison
    
    # ==================== VISUALISATIONS ====================
    
    def create_strategic_dashboard(self):
        """Crée un tableau de bord stratégique complet"""
        # Récupérer les données
        market_overview = self.get_market_overview()
        opportunities = self.get_strategic_opportunities()
        ts_position = self.get_ts_competitive_position()
        
        # Créer les visualisations
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Potentiel des Opportunités par Catégorie',
                'Position Concurrentielle de TS',
                'Top 10 Opportunités à Haut Potentiel',
                'Répartition par Niveau de Confiance'
            ),
            specs=[[{"type": "bar"}, {"type": "pie"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Graphique 1: Potentiel des opportunités
        if not opportunities.empty:
            opp_by_category = opportunities.groupby('catégorie')['montant_estime'].sum().reset_index()
            fig.add_trace(
                go.Bar(x=opp_by_category['catégorie'], y=opp_by_category['montant_estime'],
                      name="Potentiel par catégorie"),
                row=1, col=1
            )
        
        # Graphique 2: Position de TS
        if not ts_position.empty:
            fig.add_trace(
                go.Pie(labels=ts_position['position_concurrentielle'], 
                      values=ts_position['soumissions_ts'],
                      name="Position TS"),
                row=1, col=2
            )
        
        # Graphique 3: Top 10 opportunités
        if not opportunities.empty:
            top_10 = opportunities.head(10)
            fig.add_trace(
                go.Bar(x=top_10['gamme'], y=top_10['score_opportunite'],
                      name="Top 10 opportunités"),
                row=2, col=1
            )
        
        # Graphique 4: Niveau de confiance
        if not opportunities.empty:
            confidence_dist = opportunities['niveau_confiance'].value_counts()
            fig.add_trace(
                go.Bar(x=confidence_dist.index, y=confidence_dist.values,
                      name="Niveau confiance"),
                row=2, col=2
            )
        
        fig.update_layout(height=800, title_text="Tableau de Bord Stratégique - Technologies Services")
        return fig