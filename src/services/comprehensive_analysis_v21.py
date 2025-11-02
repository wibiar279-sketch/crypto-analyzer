"""
Comprehensive Analysis Service v2.1

Integrates all analysis components:
- Actual Trades Analysis (OFI, CVD, Kyle's Lambda)
- Microstructure Indicators (CPS, OBI, LVI, Micro-skew, SRI)
- Slippage & Break-even Analysis
- Advanced Bandarmology (Fake orders, Whale, Market maker)
- Social Sentiment
- Technical Analysis
- Final Recommendation with Alerts
"""

from typing import Dict, List
from datetime import datetime
from .indodax_service import IndodaxService
from .trades_analysis_service import TradesAnalysisService
from .microstructure_indicators_service import MicrostructureIndicatorsService
from .slippage_breakeven_service import SlippageBreakevenService
from .advanced_bandarmology_service import AdvancedBandarmologyService
from .social_sentiment_service import SocialSentimentService
from .technical_analysis import TechnicalAnalysis


class ComprehensiveAnalysisV21:
    """Comprehensive analysis service combining all components"""
    
    def __init__(self):
        self.indodax = IndodaxService()
        self.trades_analysis = TradesAnalysisService()
        self.microstructure = MicrostructureIndicatorsService()
        self.slippage_breakeven = SlippageBreakevenService()
        self.advanced_bandar = AdvancedBandarmologyService()
        self.sentiment = SocialSentimentService()
        self.technical = TechnicalAnalysis()
    
    def analyze_crypto(self, pair_id: str) -> Dict:
        """
        Perform comprehensive analysis on a cryptocurrency
        
        Args:
            pair_id: Trading pair ID (e.g., 'btc_idr')
            
        Returns:
            Dict with complete analysis and recommendation
        """
        try:
            print(f"[v2.1] Analyzing {pair_id}...")
            
            # Fetch data from Indodax
            ticker = self.indodax.get_ticker(pair_id)
            order_book = self.indodax.get_depth(pair_id)
            trades = self.indodax.get_trades(pair_id)
            
            # Check for errors
            if 'error' in ticker or 'error' in order_book:
                return self._error_result(pair_id, "Failed to fetch data from Indodax")
            
            # Extract ticker data
            ticker_data = ticker.get('ticker', {})
            
            # 1. Actual Trades Analysis
            print(f"[v2.1] Analyzing trades...")
            trades_result = self.trades_analysis.analyze_trades(trades, pair_id)
            
            # 2. Microstructure Indicators
            print(f"[v2.1] Calculating microstructure indicators...")
            microstructure_result = self.microstructure.calculate_all_indicators(
                order_book, trades_result, ticker_data, pair_id
            )
            
            # 3. Slippage & Break-even Analysis
            print(f"[v2.1] Analyzing slippage and break-even...")
            slippage_result = self.slippage_breakeven.analyze_order_execution(
                order_book, ticker_data
            )
            
            # 4. Advanced Bandarmology
            print(f"[v2.1] Performing advanced bandarmology analysis...")
            bandar_result = self.advanced_bandar.analyze_comprehensive(
                order_book, ticker_data
            )
            
            # 5. Social Sentiment
            print(f"[v2.1] Analyzing social sentiment...")
            sentiment_result = self.sentiment.get_sentiment(pair_id.split('_')[0].upper())
            
            # 6. Technical Analysis (simplified)
            print(f"[v2.1] Performing technical analysis...")
            try:
                technical_result = self._simplified_technical_analysis(
                    ticker_data, trades
                )
            except Exception as e:
                print(f"[v2.1] Technical analysis error: {e}")
                technical_result = {'score': 50, 'signal': 'NEUTRAL'}
            
            # 7. Generate Final Recommendation
            print(f"[v2.1] Generating recommendation...")
            recommendation = self._generate_recommendation_v21(
                ticker_data,
                trades_result,
                microstructure_result,
                slippage_result,
                bandar_result,
                sentiment_result,
                technical_result,
                pair_id
            )
            
            # 8. Generate Alerts
            alerts = self._generate_alerts(
                microstructure_result,
                trades_result,
                bandar_result,
                recommendation
            )
            
            return {
                'pair_id': pair_id,
                'symbol': pair_id.split('_')[0].upper(),
                'price': float(ticker_data.get('last', 0)),
                'volume_24h': float(ticker_data.get('vol_idr', 0)),
                'change_24h': self._calculate_change_24h(ticker_data),
                
                # Core analyses
                'trades_analysis': trades_result,
                'microstructure': microstructure_result,
                'slippage_breakeven': slippage_result,
                'advanced_bandarmology': bandar_result,
                'sentiment': sentiment_result,
                'technical': technical_result,
                
                # Final output
                'recommendation': recommendation,
                'alerts': alerts,
                
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[v2.1] Error analyzing {pair_id}: {e}")
            import traceback
            traceback.print_exc()
            return self._error_result(pair_id, str(e))
    
    def _simplified_technical_analysis(self, ticker_data: Dict, trades: List) -> Dict:
        """Simplified technical analysis from ticker and trades"""
        try:
            last_price = float(ticker_data.get('last', 0))
            high_24h = float(ticker_data.get('high', last_price))
            low_24h = float(ticker_data.get('low', last_price))
            
            # Simple momentum indicator
            if high_24h > low_24h:
                position = (last_price - low_24h) / (high_24h - low_24h)
            else:
                position = 0.5
            
            # Score based on position in 24h range
            score = position * 100
            
            if score >= 70:
                signal = 'STRONG_BUY'
            elif score >= 55:
                signal = 'BUY'
            elif score >= 45:
                signal = 'NEUTRAL'
            elif score >= 30:
                signal = 'SELL'
            else:
                signal = 'STRONG_SELL'
            
            return {
                'score': round(score, 2),
                'signal': signal,
                'position_in_range': round(position * 100, 2),
                'interpretation': f"Price at {position*100:.1f}% of 24h range"
            }
            
        except Exception as e:
            return {'score': 50, 'signal': 'NEUTRAL', 'interpretation': 'Error'}
    
    def _generate_recommendation_v21(self, ticker_data: Dict, trades_result: Dict,
                                    microstructure_result: Dict, slippage_result: Dict,
                                    bandar_result: Dict, sentiment_result: Dict,
                                    technical_result: Dict, pair_id: str) -> Dict:
        """
        Generate final recommendation based on all analyses
        
        Scoring:
        - CPS (Composite Pressure Score): 30%
        - Trades Analysis (OFI, CVD): 20%
        - Advanced Bandarmology: 20%
        - Sentiment: 15%
        - Technical: 15%
        """
        
        # Extract scores
        cps_value = microstructure_result.get('cps', {}).get('value', 0)
        ofi_z = trades_result.get('ofi', {}).get('z_score', 0)
        cvd_trend = trades_result.get('cvd', {}).get('trend', 'NEUTRAL')
        manipulation_score = bandar_result.get('manipulation', {}).get('score', 50)
        real_order_direction = bandar_result.get('real_order_direction', {}).get('direction', 'NEUTRAL')
        sentiment_score = sentiment_result.get('score', 50)
        technical_score = technical_result.get('score', 50)
        
        # 1. CPS Score (30%) - Scale from [-100, +100] to [0, 100]
        cps_normalized = (cps_value + 100) / 2  # Convert to 0-100
        cps_contribution = cps_normalized * 0.30
        
        # 2. Trades Score (20%)
        # OFI z-score: normalize to 0-100
        ofi_normalized = 50 + (ofi_z * 10)  # z=0 -> 50, z=+5 -> 100, z=-5 -> 0
        ofi_normalized = max(0, min(100, ofi_normalized))
        
        # CVD trend: BULLISH=70, NEUTRAL=50, BEARISH=30
        cvd_score = {'BULLISH': 70, 'NEUTRAL': 50, 'BEARISH': 30}.get(cvd_trend, 50)
        
        trades_score = (ofi_normalized * 0.6 + cvd_score * 0.4)
        trades_contribution = trades_score * 0.20
        
        # 3. Bandarmology Score (20%)
        # Lower manipulation = better
        # Real order direction: BULLISH=70, NEUTRAL=50, BEARISH=30
        real_order_score = {'BULLISH': 70, 'NEUTRAL': 50, 'BEARISH': 30}.get(real_order_direction, 50)
        manipulation_penalty = manipulation_score / 2  # High manipulation = penalty
        
        bandar_score = real_order_score - manipulation_penalty
        bandar_score = max(0, min(100, bandar_score))
        bandar_contribution = bandar_score * 0.20
        
        # 4. Sentiment Score (15%)
        sentiment_contribution = sentiment_score * 0.15
        
        # 5. Technical Score (15%)
        technical_contribution = technical_score * 0.15
        
        # Total Score
        total_score = (cps_contribution + trades_contribution + bandar_contribution +
                      sentiment_contribution + technical_contribution)
        
        # Determine Action
        if manipulation_score >= 70:
            action = 'AVOID'
            confidence = 'HIGH'
            interpretation = f"⚠️ HINDARI - Manipulasi tinggi ({manipulation_score:.0f}/100)"
        elif total_score >= 75:
            action = 'STRONG_BUY'
            confidence = 'HIGH' if total_score >= 85 else 'MEDIUM'
            interpretation = f"🔥 Strong Buy Signal - Score {total_score:.1f}/100"
        elif total_score >= 60:
            action = 'BUY'
            confidence = 'MEDIUM'
            interpretation = f"📈 Buy Signal - Score {total_score:.1f}/100"
        elif total_score >= 40:
            action = 'HOLD'
            confidence = 'MEDIUM'
            interpretation = f"⏸️ Hold - Score {total_score:.1f}/100"
        elif total_score >= 25:
            action = 'SELL'
            confidence = 'MEDIUM'
            interpretation = f"📉 Sell Signal - Score {total_score:.1f}/100"
        else:
            action = 'STRONG_SELL'
            confidence = 'HIGH' if total_score <= 15 else 'MEDIUM'
            interpretation = f"❄️ Strong Sell Signal - Score {total_score:.1f}/100"
        
        # Risk Assessment
        risk_factors = []
        risk_score = 0
        
        if manipulation_score >= 50:
            risk_factors.append(f"Manipulation: {manipulation_score:.0f}/100")
            risk_score += manipulation_score * 0.4
        
        if abs(microstructure_result.get('spread', {}).get('z_spread', 0)) >= 1.5:
            risk_factors.append("Wide spread")
            risk_score += 15
        
        if microstructure_result.get('sri', {}).get('sri_buy', 0) >= 70 or \
           microstructure_result.get('sri', {}).get('sri_sell', 0) >= 70:
            risk_factors.append("Stop cascade risk")
            risk_score += 20
        
        if abs(ofi_z) >= 2.0:
            risk_factors.append("Extreme order flow")
            risk_score += 10
        
        # Risk level
        if risk_score >= 70:
            risk_level = 'VERY_HIGH'
        elif risk_score >= 50:
            risk_level = 'HIGH'
        elif risk_score >= 30:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        # Quick Insight
        quick_insight = self._generate_quick_insight(
            action, cps_value, real_order_direction, sentiment_result,
            manipulation_score, risk_level
        )
        
        return {
            'action': action,
            'confidence': confidence,
            'overall_score': round(total_score, 2),
            'score_breakdown': {
                'cps_score': round(cps_normalized, 2),
                'cps_contribution': round(cps_contribution, 2),
                'trades_score': round(trades_score, 2),
                'trades_contribution': round(trades_contribution, 2),
                'bandarmology_score': round(bandar_score, 2),
                'bandarmology_contribution': round(bandar_contribution, 2),
                'sentiment_score': round(sentiment_score, 2),
                'sentiment_contribution': round(sentiment_contribution, 2),
                'technical_score': round(technical_score, 2),
                'technical_contribution': round(technical_contribution, 2)
            },
            'risk_assessment': {
                'level': risk_level,
                'score': round(risk_score, 2),
                'factors': risk_factors
            },
            'interpretation': interpretation,
            'quick_insight': quick_insight
        }
    
    def _generate_quick_insight(self, action: str, cps: float, real_direction: str,
                               sentiment: Dict, manipulation: float, risk: str) -> str:
        """Generate one-liner quick insight"""
        
        if action == 'AVOID':
            return f"⚠️ HINDARI - Manipulasi {manipulation:.0f}/100, terlalu berbahaya"
        
        if action == 'STRONG_BUY':
            factors = []
            if cps >= 40:
                factors.append("CPS bullish")
            if real_direction == 'BULLISH':
                factors.append("real orders bullish")
            if sentiment.get('label') == 'POSITIVE':
                factors.append("sentiment positive")
            
            return f"🔥 {' + '.join(factors)} - Strong buy opportunity"
        
        if action == 'BUY':
            return f"📈 Peluang beli - {real_direction.lower()} pressure, risk {risk.lower()}"
        
        if action == 'HOLD':
            return f"⏸️ Tunggu signal lebih jelas - Neutral market"
        
        if action == 'SELL':
            return f"📉 Consider exit - Bearish signals, risk {risk.lower()}"
        
        if action == 'STRONG_SELL':
            return f"❄️ Exit recommended - Strong bearish pressure"
        
        return "⚖️ Neutral - Monitor closely"
    
    def _generate_alerts(self, microstructure: Dict, trades: Dict,
                        bandar: Dict, recommendation: Dict) -> List[Dict]:
        """Generate alerts based on thresholds"""
        alerts = []
        
        # 1. CPS Alerts
        cps_value = microstructure.get('cps', {}).get('value', 0)
        if cps_value >= 40:
            alerts.append({
                'type': 'CPS_BULLISH',
                'severity': 'HIGH',
                'message': f"🔥 Strong bullish pressure (CPS={cps_value:.1f})"
            })
        elif cps_value <= -40:
            alerts.append({
                'type': 'CPS_BEARISH',
                'severity': 'HIGH',
                'message': f"❄️ Strong bearish pressure (CPS={cps_value:.1f})"
            })
        
        # 2. OFI Alerts
        ofi_z = trades.get('ofi', {}).get('z_score', 0)
        if ofi_z >= 1.5:
            alerts.append({
                'type': 'OFI_EXTREME_BUY',
                'severity': 'HIGH',
                'message': f"🔥 Extreme aggressive buying (z_OFI={ofi_z:.2f})"
            })
        elif ofi_z <= -1.5:
            alerts.append({
                'type': 'OFI_EXTREME_SELL',
                'severity': 'HIGH',
                'message': f"❄️ Extreme aggressive selling (z_OFI={ofi_z:.2f})"
            })
        
        # 3. SRI Alerts
        sri_buy = microstructure.get('sri', {}).get('sri_buy', 0)
        sri_sell = microstructure.get('sri', {}).get('sri_sell', 0)
        
        if sri_buy >= 70:
            alerts.append({
                'type': 'SRI_BUY_CASCADE',
                'severity': 'CRITICAL',
                'message': f"⚠️ Stop-buy cascade risk (SRI={sri_buy:.0f})"
            })
        
        if sri_sell >= 70:
            alerts.append({
                'type': 'SRI_SELL_CASCADE',
                'severity': 'CRITICAL',
                'message': f"⚠️ Stop-sell cascade risk (SRI={sri_sell:.0f})"
            })
        
        # 4. Micro-skew Alerts
        micro_skew = microstructure.get('microprice', {}).get('micro_skew', 0)
        if micro_skew >= 0.8:
            alerts.append({
                'type': 'MICROSKEW_BULLISH',
                'severity': 'MEDIUM',
                'message': f"📈 Very strong short-term buy pressure (skew={micro_skew:.3f})"
            })
        elif micro_skew <= -0.8:
            alerts.append({
                'type': 'MICROSKEW_BEARISH',
                'severity': 'MEDIUM',
                'message': f"📉 Very strong short-term sell pressure (skew={micro_skew:.3f})"
            })
        
        # 5. Spread Alerts
        z_spread = microstructure.get('spread', {}).get('z_spread', 0)
        if z_spread >= 1.5:
            alerts.append({
                'type': 'SPREAD_WIDE',
                'severity': 'MEDIUM',
                'message': f"⚠️ Spread widening abnormally (z={z_spread:.2f})"
            })
        
        # 6. Manipulation Alerts
        manipulation_score = bandar.get('manipulation', {}).get('score', 0)
        if manipulation_score >= 70:
            alerts.append({
                'type': 'MANIPULATION_HIGH',
                'severity': 'CRITICAL',
                'message': f"🚨 High manipulation detected ({manipulation_score:.0f}/100) - AVOID!"
            })
        elif manipulation_score >= 50:
            alerts.append({
                'type': 'MANIPULATION_MEDIUM',
                'severity': 'HIGH',
                'message': f"⚠️ Medium manipulation detected ({manipulation_score:.0f}/100)"
            })
        
        # 7. Action Alerts
        if recommendation.get('action') == 'AVOID':
            alerts.append({
                'type': 'ACTION_AVOID',
                'severity': 'CRITICAL',
                'message': "🚨 AVOID TRADING - High risk detected"
            })
        
        return alerts
    
    def _calculate_change_24h(self, ticker_data: Dict) -> float:
        """Calculate 24h price change percentage"""
        try:
            last = float(ticker_data.get('last', 0))
            high = float(ticker_data.get('high', last))
            low = float(ticker_data.get('low', last))
            
            # Estimate opening price (mid of high-low)
            open_estimate = (high + low) / 2
            
            if open_estimate > 0:
                change = (last - open_estimate) / open_estimate * 100
                return round(change, 2)
            else:
                return 0.0
        except:
            return 0.0
    
    def _error_result(self, pair_id: str, error_msg: str) -> Dict:
        """Return error result"""
        return {
            'pair_id': pair_id,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }

