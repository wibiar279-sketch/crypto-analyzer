"""
Comprehensive Analysis Service v2.1 - UPDATED with Fear & Greed Index

Integrates all analysis services:
1. Trading data (Indodax)
2. Technical analysis
3. Bandarmology analysis (basic + advanced)
4. Trades analysis (OFI, CVD, Kyle's Lambda)
5. Microstructure indicators (CPS, SRI, OBI, LVI, micro-skew)
6. Slippage & break-even analysis
7. Sentiment analysis (simulated + Fear & Greed Index)
8. Social sentiment (optional CoinGecko)
"""

from typing import Dict, List, Optional
from datetime import datetime
import numpy as np

from .indodax_service import IndodaxService
from .technical_analysis import TechnicalAnalysis
from .bandarmology_analysis import BandarmologyAnalysis
from .advanced_bandarmology_service import AdvancedBandarmologyService
from .trades_analysis_service import TradesAnalysisService
from .microstructure_indicators_service import MicrostructureIndicatorsService
from .slippage_breakeven_service import SlippageBreakevenService
from .fear_greed_service import FearGreedService
from .social_sentiment_service import SocialSentimentService


class ComprehensiveAnalysisV21:
    """Comprehensive analysis service integrating all components"""
    
    def __init__(self):
        """Initialize all services"""
        self.indodax = IndodaxService()
        self.fear_greed = FearGreedService()
        self.social_sentiment = SocialSentimentService()
        self.advanced_bandar = AdvancedBandarmologyService()
        self.trades_analysis = TradesAnalysisService()
        self.microstructure = MicrostructureIndicatorsService()
        self.slippage_service = SlippageBreakevenService()
    
    def analyze_crypto(self, pair_id: str) -> Dict:
        """
        Perform comprehensive analysis on a cryptocurrency pair
        
        Args:
            pair_id: Trading pair ID (e.g., 'btc_idr')
            
        Returns:
            Dict with complete analysis
        """
        try:
            # 1. Fetch all data
            ticker = self.indodax.get_ticker(pair_id)
            depth = self.indodax.get_depth(pair_id)
            trades = self.indodax.get_trades(pair_id)
            
            if not ticker or not depth or not trades:
                return self._empty_analysis(pair_id)
            
            # 2. Basic info
            symbol = pair_id.replace('_idr', '').upper()
            price = float(ticker.get('last', 0))
            volume_24h = float(ticker.get('vol_idr', 0))
            
            # 3. Technical Analysis (simplified for trades data)
            tech_analysis = self._analyze_technical_simple(trades, ticker)
            
            # 4. Bandarmology Analysis
            bandar_analysis = self._analyze_bandarmology(depth, ticker)
            
            # 5. Advanced Bandarmology
            advanced_bandar = self.advanced_bandar.analyze_order_book(depth, ticker)
            
            # 6. Trades Analysis (OFI, CVD, Kyle's Lambda)
            trades_metrics = self.trades_analysis.analyze_trades(trades, depth)
            
            # 7. Microstructure Indicators (CPS, SRI, OBI, LVI, micro-skew)
            microstructure_metrics = self.microstructure.calculate_all_indicators(
                depth, trades, ticker
            )
            
            # 8. Slippage & Break-even
            slippage_analysis = self.slippage_service.analyze_order_execution(depth, ticker)
            
            # 9. Market-wide Sentiment (Fear & Greed Index)
            market_sentiment = self.fear_greed.get_market_sentiment()
            
            # 10. Per-coin Sentiment (simulated + optional CoinGecko)
            coin_sentiment = self.social_sentiment.get_sentiment(symbol.lower())
            
            # 11. Generate comprehensive recommendation
            recommendation = self._generate_recommendation(
                tech_analysis=tech_analysis,
                bandar_analysis=bandar_analysis,
                advanced_bandar=advanced_bandar,
                trades_metrics=trades_metrics,
                microstructure=microstructure_metrics,
                market_sentiment=market_sentiment,
                coin_sentiment=coin_sentiment,
                price=price
            )
            
            # 12. Generate alerts
            alerts = self._generate_alerts(
                microstructure=microstructure_metrics,
                advanced_bandar=advanced_bandar,
                trades_metrics=trades_metrics
            )
            
            # 13. Compile complete analysis
            return {
                'symbol': symbol,
                'pair_id': pair_id,
                'price': price,
                'volume_24h': volume_24h,
                'volume_24h_idr': volume_24h,
                
                # Core metrics
                'technical': tech_analysis,
                'bandarmology': bandar_analysis,
                'advanced_bandarmology': advanced_bandar,
                'trades_analysis': trades_metrics,
                'microstructure': microstructure_metrics,
                'slippage': slippage_analysis,
                
                # Sentiment
                'market_sentiment': market_sentiment,
                'coin_sentiment': coin_sentiment,
                
                # Recommendation
                'recommendation': recommendation,
                'alerts': alerts,
                
                # Summary for dashboard
                'summary': {
                    'action': recommendation['action'],
                    'score': recommendation['overall_score'],
                    'confidence': recommendation['confidence'],
                    'risk_level': recommendation['risk_level'],
                    'sentiment': coin_sentiment['sentiment'],
                    'trending': coin_sentiment['trending'],
                    'market_mood': market_sentiment['mood'],
                    'quick_insight': recommendation['quick_insight']
                },
                
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error analyzing {pair_id}: {e}")
            return self._empty_analysis(pair_id)
    
    def _analyze_technical_simple(self, trades: List, ticker: Dict) -> Dict:
        """Simplified technical analysis from trades data"""
        try:
            if not trades or len(trades) < 20:
                return {}
            
            # Extract prices from trades
            prices = [float(t['price']) for t in trades[:100]]
            
            # Calculate simple indicators
            current_price = prices[0]
            avg_price = np.mean(prices)
            
            # RSI approximation
            price_changes = np.diff(prices)
            gains = price_changes[price_changes > 0]
            losses = abs(price_changes[price_changes < 0])
            
            avg_gain = np.mean(gains) if len(gains) > 0 else 0
            avg_loss = np.mean(losses) if len(losses) > 0 else 0
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            # Trend
            if current_price > avg_price * 1.02:
                trend = "UPTREND"
            elif current_price < avg_price * 0.98:
                trend = "DOWNTREND"
            else:
                trend = "SIDEWAYS"
            
            return {
                'rsi': round(rsi, 2),
                'trend': trend,
                'current_price': current_price,
                'avg_price': round(avg_price, 2),
                'signal': 'OVERSOLD' if rsi < 30 else 'OVERBOUGHT' if rsi > 70 else 'NEUTRAL'
            }
            
        except Exception as e:
            print(f"Error in technical analysis: {e}")
            return {}
    
    def _analyze_bandarmology(self, depth: Dict, ticker: Dict) -> Dict:
        """Basic bandarmology analysis"""
        try:
            analyzer = BandarmologyAnalysis(depth)
            
            return {
                'order_book_imbalance': analyzer.calculate_order_book_imbalance(),
                'spread_analysis': analyzer.analyze_spread(ticker),
                'buy_sell_walls': analyzer.detect_buy_sell_walls(),
                'whale_activity': analyzer.analyze_whale_activity()
            }
        except Exception as e:
            print(f"Error in bandarmology: {e}")
            return {}
    
    def _generate_recommendation(self, **kwargs) -> Dict:
        """
        Generate comprehensive trading recommendation
        
        Considers:
        - Technical score (20%)
        - Bandarmology score (20%)
        - Trades metrics score (20%)
        - Microstructure score (20%)
        - Sentiment score (20%)
        """
        try:
            # Extract data
            tech = kwargs.get('tech_analysis', {})
            bandar = kwargs.get('bandar_analysis', {})
            advanced_bandar = kwargs.get('advanced_bandar', {})
            trades = kwargs.get('trades_metrics', {})
            micro = kwargs.get('microstructure', {})
            market_sent = kwargs.get('market_sentiment', {})
            coin_sent = kwargs.get('coin_sentiment', {})
            
            # Calculate component scores (0-100)
            tech_score = self._calculate_technical_score(tech)
            bandar_score = self._calculate_bandarmology_score(bandar, advanced_bandar)
            trades_score = self._calculate_trades_score(trades)
            micro_score = self._calculate_microstructure_score(micro)
            sentiment_score = self._calculate_sentiment_score(market_sent, coin_sent)
            
            # Weighted overall score
            overall_score = (
                tech_score * 0.20 +
                bandar_score * 0.20 +
                trades_score * 0.20 +
                micro_score * 0.20 +
                sentiment_score * 0.20
            )
            
            # Determine action
            if overall_score >= 70:
                action = "BUY"
                confidence = "HIGH"
            elif overall_score >= 55:
                action = "BUY"
                confidence = "MEDIUM"
            elif overall_score >= 45:
                action = "HOLD"
                confidence = "MEDIUM"
            elif overall_score >= 30:
                action = "SELL"
                confidence = "MEDIUM"
            else:
                action = "SELL"
                confidence = "HIGH"
            
            # Determine risk level
            risk_factors = []
            
            if micro.get('sri', {}).get('buy', 0) > 70 or micro.get('sri', {}).get('sell', 0) > 70:
                risk_factors.append("High stop-loss cascade risk")
            
            if advanced_bandar.get('manipulation_score', 0) > 70:
                risk_factors.append("High manipulation detected")
            
            if market_sent.get('value', 50) > 75 or market_sent.get('value', 50) < 25:
                risk_factors.append("Extreme market sentiment")
            
            if len(risk_factors) >= 2:
                risk_level = "VERY_HIGH"
            elif len(risk_factors) == 1:
                risk_level = "HIGH"
            elif overall_score < 40 or overall_score > 60:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            # Generate quick insight
            quick_insight = self._generate_quick_insight(
                action, overall_score, risk_level, coin_sent, market_sent
            )
            
            return {
                'action': action,
                'confidence': confidence,
                'overall_score': round(overall_score, 2),
                'component_scores': {
                    'technical': round(tech_score, 2),
                    'bandarmology': round(bandar_score, 2),
                    'trades': round(trades_score, 2),
                    'microstructure': round(micro_score, 2),
                    'sentiment': round(sentiment_score, 2)
                },
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'quick_insight': quick_insight,
                'explanation': self._generate_explanation(
                    action, overall_score, tech, bandar, trades, micro, market_sent, coin_sent
                )
            }
            
        except Exception as e:
            print(f"Error generating recommendation: {e}")
            return self._default_recommendation()
    
    def _calculate_technical_score(self, tech: Dict) -> float:
        """Calculate technical analysis score (0-100)"""
        if not tech:
            return 50
        
        score = 50  # Start neutral
        
        rsi = tech.get('rsi', 50)
        trend = tech.get('trend', 'SIDEWAYS')
        
        # RSI contribution
        if rsi < 30:
            score += 20  # Oversold = bullish
        elif rsi > 70:
            score -= 20  # Overbought = bearish
        
        # Trend contribution
        if trend == 'UPTREND':
            score += 15
        elif trend == 'DOWNTREND':
            score -= 15
        
        return max(0, min(100, score))
    
    def _calculate_bandarmology_score(self, bandar: Dict, advanced: Dict) -> float:
        """Calculate bandarmology score (0-100)"""
        score = 50
        
        # Order book imbalance
        imbalance = bandar.get('order_book_imbalance', {}).get('ratio', 1.0)
        if imbalance > 1.2:
            score += 15
        elif imbalance < 0.8:
            score -= 15
        
        # Manipulation detection
        manipulation = advanced.get('manipulation_score', 0)
        if manipulation > 70:
            score -= 20  # High manipulation = bearish
        elif manipulation < 30:
            score += 10  # Low manipulation = bullish
        
        # Real order direction
        real_direction = advanced.get('real_order_direction', {})
        if real_direction.get('direction') == 'BULLISH':
            score += 10
        elif real_direction.get('direction') == 'BEARISH':
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_trades_score(self, trades: Dict) -> float:
        """Calculate trades analysis score (0-100)"""
        score = 50
        
        # OFI (Order Flow Imbalance)
        ofi = trades.get('ofi', {})
        if ofi.get('direction') == 'BULLISH':
            score += 15
        elif ofi.get('direction') == 'BEARISH':
            score -= 15
        
        # CVD (Cumulative Volume Delta)
        cvd = trades.get('cvd', {})
        if cvd.get('direction') == 'BULLISH':
            score += 10
        elif cvd.get('direction') == 'BEARISH':
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_microstructure_score(self, micro: Dict) -> float:
        """Calculate microstructure indicators score (0-100)"""
        score = 50
        
        # CPS (Composite Pressure Score)
        cps = micro.get('cps', {}).get('value', 0)
        if cps > 40:
            score += 20
        elif cps < -40:
            score -= 20
        elif cps > 20:
            score += 10
        elif cps < -20:
            score -= 10
        
        # OBI (Order Book Imbalance at multiple levels)
        obi = micro.get('obi', {})
        obi_5 = obi.get('obi_5', 0)
        if obi_5 > 0.3:
            score += 10
        elif obi_5 < -0.3:
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_sentiment_score(self, market: Dict, coin: Dict) -> float:
        """Calculate sentiment score (0-100)"""
        score = 50
        
        # Market sentiment (Fear & Greed)
        market_value = market.get('value', 50)
        # Contrarian approach: extreme fear = buy, extreme greed = sell
        if market_value < 25:
            score += 15  # Extreme fear = opportunity
        elif market_value > 75:
            score -= 15  # Extreme greed = risk
        
        # Coin sentiment
        coin_sent = coin.get('sentiment', 'NEUTRAL')
        if coin_sent == 'POSITIVE':
            score += 15
        elif coin_sent == 'NEGATIVE':
            score -= 15
        
        # Trending bonus
        if coin.get('trending', False):
            score += 10
        
        return max(0, min(100, score))
    
    def _generate_quick_insight(self, action: str, score: float, risk: str, 
                                coin_sent: Dict, market_sent: Dict) -> str:
        """Generate one-liner insight for dashboard"""
        sentiment_emoji = coin_sent.get('emoji', '😐')
        market_emoji = market_sent.get('emoji', '😐')
        trending = "🔥 TRENDING" if coin_sent.get('trending') else ""
        
        if action == "BUY" and score >= 70:
            return f"Strong buy signal {sentiment_emoji} {trending}"
        elif action == "BUY":
            return f"Moderate buy opportunity {sentiment_emoji}"
        elif action == "SELL" and score <= 30:
            return f"Strong sell signal {sentiment_emoji}"
        elif action == "SELL":
            return f"Consider taking profits {sentiment_emoji}"
        else:
            return f"Hold position, wait for clarity {sentiment_emoji}"
    
    def _generate_explanation(self, action: str, score: float, tech: Dict, 
                             bandar: Dict, trades: Dict, micro: Dict,
                             market_sent: Dict, coin_sent: Dict) -> str:
        """Generate detailed explanation"""
        parts = []
        
        parts.append(f"Overall score: {score:.1f}/100 suggests {action}.")
        
        # Technical
        if tech:
            rsi = tech.get('rsi', 50)
            parts.append(f"Technical: RSI at {rsi:.1f} ({tech.get('signal', 'NEUTRAL')}).")
        
        # Sentiment
        market_mood = market_sent.get('mood', 'NEUTRAL')
        coin_mood = coin_sent.get('sentiment', 'NEUTRAL')
        parts.append(f"Sentiment: Market is {market_mood}, coin is {coin_mood}.")
        
        # Microstructure
        if micro:
            cps = micro.get('cps', {}).get('value', 0)
            parts.append(f"Pressure: CPS at {cps:.1f} ({'bullish' if cps > 0 else 'bearish' if cps < 0 else 'neutral'}).")
        
        return " ".join(parts)
    
    def _generate_alerts(self, microstructure: Dict, advanced_bandar: Dict, 
                        trades_metrics: Dict) -> List[Dict]:
        """Generate trading alerts based on thresholds"""
        alerts = []
        
        # CPS alerts
        cps = microstructure.get('cps', {}).get('value', 0)
        if cps >= 40:
            alerts.append({
                'type': 'CPS_HIGH',
                'severity': 'HIGH',
                'message': f'Strong bullish pressure detected (CPS: {cps:.1f})',
                'action': 'Consider buying'
            })
        elif cps <= -40:
            alerts.append({
                'type': 'CPS_LOW',
                'severity': 'HIGH',
                'message': f'Strong bearish pressure detected (CPS: {cps:.1f})',
                'action': 'Consider selling'
            })
        
        # SRI alerts
        sri_buy = microstructure.get('sri', {}).get('buy', 0)
        sri_sell = microstructure.get('sri', {}).get('sell', 0)
        
        if sri_buy >= 70:
            alerts.append({
                'type': 'SRI_HIGH',
                'severity': 'WARNING',
                'message': f'High stop-loss cascade risk on buy side (SRI: {sri_buy:.1f})',
                'action': 'Avoid buying near support'
            })
        
        if sri_sell >= 70:
            alerts.append({
                'type': 'SRI_HIGH',
                'severity': 'WARNING',
                'message': f'High stop-loss cascade risk on sell side (SRI: {sri_sell:.1f})',
                'action': 'Avoid selling near resistance'
            })
        
        # OFI alerts
        ofi_z = trades_metrics.get('ofi', {}).get('z_score', 0)
        if ofi_z >= 1.5:
            alerts.append({
                'type': 'OFI_EXTREME',
                'severity': 'INFO',
                'message': f'Extreme aggressive buying detected (z-OFI: {ofi_z:.2f})',
                'action': 'Strong buy pressure'
            })
        elif ofi_z <= -1.5:
            alerts.append({
                'type': 'OFI_EXTREME',
                'severity': 'INFO',
                'message': f'Extreme aggressive selling detected (z-OFI: {ofi_z:.2f})',
                'action': 'Strong sell pressure'
            })
        
        # Manipulation alerts
        manipulation = advanced_bandar.get('manipulation_score', 0)
        if manipulation > 70:
            alerts.append({
                'type': 'MANIPULATION',
                'severity': 'WARNING',
                'message': f'High manipulation detected ({manipulation:.1f}/100)',
                'action': 'Trade with caution'
            })
        
        return alerts
    
    def _default_recommendation(self) -> Dict:
        """Return default recommendation when analysis fails"""
        return {
            'action': 'HOLD',
            'confidence': 'LOW',
            'overall_score': 50,
            'component_scores': {
                'technical': 50,
                'bandarmology': 50,
                'trades': 50,
                'microstructure': 50,
                'sentiment': 50
            },
            'risk_level': 'MEDIUM',
            'risk_factors': ['Insufficient data'],
            'quick_insight': 'Insufficient data for analysis',
            'explanation': 'Unable to perform complete analysis due to data issues.'
        }
    
    def _empty_analysis(self, pair_id: str) -> Dict:
        """Return empty analysis structure"""
        symbol = pair_id.replace('_idr', '').upper()
        return {
            'symbol': symbol,
            'pair_id': pair_id,
            'error': 'Unable to fetch data',
            'recommendation': self._default_recommendation(),
            'timestamp': datetime.now().isoformat()
        }


# Example usage
if __name__ == "__main__":
    analyzer = ComprehensiveAnalysisV21()
    
    # Analyze BTC
    result = analyzer.analyze_crypto('btc_idr')
    
    print(f"Symbol: {result['symbol']}")
    print(f"Action: {result['recommendation']['action']}")
    print(f"Score: {result['recommendation']['overall_score']}/100")
    print(f"Risk: {result['recommendation']['risk_level']}")
    print(f"Quick Insight: {result['summary']['quick_insight']}")
    print(f"\nAlerts: {len(result['alerts'])}")
    for alert in result['alerts']:
        print(f"  - {alert['message']}")

