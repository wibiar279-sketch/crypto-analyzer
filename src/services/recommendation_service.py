"""
Recommendation Service
Combines all analyses to provide buy/sell recommendations
"""
from typing import Dict
import numpy as np
from src.services.technical_analysis import TechnicalAnalysis
from src.services.bandarmology_analysis import BandarmologyAnalysis

class RecommendationService:
    
    def __init__(self, ticker_data: Dict, summaries_data: Dict, 
                 technical_analysis: TechnicalAnalysis, 
                 bandarmology_analysis: BandarmologyAnalysis):
        """
        Initialize with all analysis data
        """
        self.ticker_data = ticker_data
        self.summaries_data = summaries_data
        self.technical_analysis = technical_analysis
        self.bandarmology_analysis = bandarmology_analysis
    
    def calculate_fundamental_score(self) -> Dict:
        """
        Calculate fundamental analysis score based on market data
        Returns score (0-100) and details
        """
        ticker = self.ticker_data.get('ticker', {})
        
        if not ticker:
            return {"score": 50, "details": {}}
        
        # Get price data
        current_price = float(ticker.get('last', 0))
        high_24h = float(ticker.get('high', current_price))
        low_24h = float(ticker.get('low', current_price))
        
        # Calculate price position in 24h range
        if high_24h > low_24h:
            price_position = ((current_price - low_24h) / (high_24h - low_24h)) * 100
        else:
            price_position = 50
        
        # Get volume data
        volume_key = [k for k in ticker.keys() if k.startswith('vol_') and k != 'vol_idr'][0] if any(k.startswith('vol_') and k != 'vol_idr' for k in ticker.keys()) else None
        current_volume = float(ticker.get(volume_key, 0)) if volume_key else 0
        
        details = {
            'current_price': current_price,
            'high_24h': high_24h,
            'low_24h': low_24h,
            'price_position': price_position,
            'volume': current_volume
        }
        
        return {
            'score': price_position,
            'details': details
        }
    
    def calculate_momentum_score(self) -> int:
        """
        Calculate momentum score (0-20)
        Based on price change and volume trend
        """
        ticker = self.ticker_data.get('ticker', {})
        
        if not ticker:
            return 10  # Neutral
        
        score = 0
        
        # Price change score (0-10)
        current_price = float(ticker.get('last', 0))
        high_24h = float(ticker.get('high', current_price))
        low_24h = float(ticker.get('low', current_price))
        
        if high_24h > low_24h:
            price_position = ((current_price - low_24h) / (high_24h - low_24h)) * 100
            
            if price_position > 80:
                score += 10  # Strong upward momentum
            elif price_position > 60:
                score += 7
            elif price_position < 20:
                score += 0  # Strong downward momentum
            elif price_position < 40:
                score += 3
            else:
                score += 5
        else:
            score += 5
        
        # Volume trend score (0-10)
        # This would require historical data, for now use simple heuristic
        volume_key = [k for k in ticker.keys() if k.startswith('vol_') and k != 'vol_idr'][0] if any(k.startswith('vol_') and k != 'vol_idr' for k in ticker.keys()) else None
        
        if volume_key:
            current_volume = float(ticker.get(volume_key, 0))
            # If volume is high, it's a good sign
            if current_volume > 0:
                score += 5  # Moderate volume activity
        
        return min(score, 20)
    
    def get_overall_score(self) -> Dict:
        """
        Calculate overall recommendation score (0-100)
        
        Breakdown:
        - Technical Analysis: 40%
        - Bandarmology Analysis: 40%
        - Momentum: 20%
        """
        # Get individual scores
        technical_score = self.technical_analysis.get_technical_score()  # 0-40
        bandarmology_score = self.bandarmology_analysis.get_bandarmology_score()  # 0-40
        momentum_score = self.calculate_momentum_score()  # 0-20
        
        # Calculate total score
        total_score = technical_score + bandarmology_score + momentum_score
        
        # Determine recommendation
        recommendation = self._get_recommendation_text(total_score)
        
        return {
            'total_score': total_score,
            'technical_score': technical_score,
            'bandarmology_score': bandarmology_score,
            'momentum_score': momentum_score,
            'recommendation': recommendation['action'],
            'recommendation_text': recommendation['text'],
            'confidence': recommendation['confidence']
        }
    
    def _get_recommendation_text(self, score: int) -> Dict:
        """
        Convert score to recommendation text
        """
        if score >= 75:
            return {
                'action': 'STRONG_BUY',
                'text': 'Strong buy signal detected. Multiple indicators show bullish momentum.',
                'confidence': 'HIGH'
            }
        elif score >= 60:
            return {
                'action': 'BUY',
                'text': 'Buy signal detected. Indicators show positive momentum.',
                'confidence': 'MEDIUM'
            }
        elif score >= 40:
            return {
                'action': 'HOLD',
                'text': 'Hold position. Market is neutral, wait for clearer signals.',
                'confidence': 'MEDIUM'
            }
        elif score >= 25:
            return {
                'action': 'SELL',
                'text': 'Sell signal detected. Indicators show negative momentum.',
                'confidence': 'MEDIUM'
            }
        else:
            return {
                'action': 'STRONG_SELL',
                'text': 'Strong sell signal detected. Multiple indicators show bearish momentum.',
                'confidence': 'HIGH'
            }
    
    def get_detailed_recommendation(self) -> Dict:
        """
        Get detailed recommendation with all analysis
        """
        # Get all indicators
        technical_indicators = self.technical_analysis.get_all_indicators()
        bandarmology_data = self.bandarmology_analysis.get_all_analysis()
        fundamental_data = self.calculate_fundamental_score()
        overall_score = self.get_overall_score()
        
        # Convert numpy types to Python types for JSON serialization
        def convert_to_json_serializable(obj):
            if isinstance(obj, dict):
                return {k: convert_to_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_json_serializable(item) for item in obj]
            elif isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        result = {
            'recommendation': overall_score,
            'technical_analysis': technical_indicators,
            'bandarmology_analysis': bandarmology_data,
            'fundamental_analysis': fundamental_data,
            'ticker_data': self.ticker_data.get('ticker', {})
        }
        
        return convert_to_json_serializable(result)

