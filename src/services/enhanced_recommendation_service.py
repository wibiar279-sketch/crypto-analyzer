"""
Enhanced Recommendation Service v2.0
Integrates: Technical + Bandarmology + Sentiment + Advanced Manipulation Detection
"""

from .technical_analysis import TechnicalAnalysis
from .bandarmology_analysis import BandarmologyAnalysis
from .advanced_bandarmology_service import AdvancedBandarmologyService
from .social_sentiment_service import SocialSentimentService
from .indodax_service import IndodaxService
import numpy as np

class EnhancedRecommendationService:
    
    def __init__(self):
        self.advanced_bandarmology_service = AdvancedBandarmologyService()
        self.sentiment_service = SocialSentimentService()
        self.indodax_service = IndodaxService()
    
    def get_comprehensive_analysis(self, pair_id: str) -> dict:
        """
        Get comprehensive analysis with all metrics
        This is the main method for v2.0
        """
        try:
            # Extract symbol from pair_id (e.g., 'btc_idr' -> 'BTC')
            symbol = pair_id.split('_')[0].upper()
            
            # Get all data
            ticker_data = self.indodax_service.get_ticker(pair_id)
            trades = self.indodax_service.get_trades(pair_id)
            depth = self.indodax_service.get_depth(pair_id)
            
            if not ticker_data or not trades or not depth:
                return {'error': 'Failed to fetch market data'}
            
            # Extract ticker from response
            ticker = ticker_data.get('ticker', {})
            if not ticker:
                return {'error': 'Invalid ticker data'}
            
            current_price = float(ticker.get('last', 0))
            
            # Run all analyses
            # Technical analysis - use simplified version since trades != OHLC
            technical = self._get_simplified_technical_analysis(trades, ticker)
            
            # Basic bandarmology
            basic_bandarmology_analyzer = BandarmologyAnalysis(depth)
            basic_bandarmology = {
                'order_book_imbalance': basic_bandarmology_analyzer.calculate_order_book_imbalance(),
                'whale_activity': basic_bandarmology_analyzer.detect_whale_orders()
            }
            advanced_bandarmology = self.advanced_bandarmology_service.analyze_order_book_advanced(
                depth, 
                current_price
            )
            sentiment = self.sentiment_service.get_sentiment_analysis(symbol, pair_id)
            
            # Calculate enhanced recommendation
            recommendation = self._calculate_enhanced_recommendation(
                technical,
                basic_bandarmology,
                advanced_bandarmology,
                sentiment,
                ticker
            )
            
            # Generate executive summary
            summary = self._generate_executive_summary(
                recommendation,
                advanced_bandarmology,
                sentiment,
                ticker
            )
            
            return {
                'pair_id': pair_id,
                'symbol': symbol,
                'current_price': current_price,
                'ticker': ticker,
                'summary': summary,
                'recommendation': recommendation,
                'technical_analysis': technical,
                'basic_bandarmology': basic_bandarmology,
                'advanced_bandarmology': advanced_bandarmology,
                'sentiment_analysis': sentiment,
                'last_updated': sentiment['last_updated']
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_enhanced_recommendation(self, technical: dict, basic_bandar: dict,
                                          advanced_bandar: dict, sentiment: dict,
                                          ticker: dict) -> dict:
        """
        Calculate recommendation with new scoring system:
        - Technical: 30% (was 40%)
        - Basic Bandarmology: 20% (was 40%)
        - Advanced Bandarmology: 30% (new)
        - Sentiment: 20% (new)
        Total: 100%
        """
        
        # Technical Score (0-30)
        technical_score = self._calculate_technical_score(technical) * 0.3
        
        # Basic Bandarmology Score (0-20)
        basic_bandar_score = self._calculate_basic_bandarmology_score(basic_bandar) * 0.2
        
        # Advanced Bandarmology Score (0-30)
        advanced_bandar_score = self._calculate_advanced_bandarmology_score(advanced_bandar) * 0.3
        
        # Sentiment Score (0-20)
        sentiment_score = self._calculate_sentiment_score(sentiment) * 0.2
        
        # Total Score (0-100)
        total_score = technical_score + basic_bandar_score + advanced_bandar_score + sentiment_score
        
        # Determine action
        action, confidence = self._determine_action(
            total_score,
            advanced_bandar['manipulation_score'],
            sentiment
        )
        
        # Calculate target prices
        current_price = float(ticker['last'])
        targets = self._calculate_target_prices(current_price, action, total_score)
        
        return {
            'action': action,
            'confidence': confidence,
            'total_score': round(total_score, 1),
            'scores': {
                'technical': round(technical_score, 1),
                'basic_bandarmology': round(basic_bandar_score, 1),
                'advanced_bandarmology': round(advanced_bandar_score, 1),
                'sentiment': round(sentiment_score, 1)
            },
            'targets': targets,
            'reasoning': self._generate_reasoning(
                action,
                technical_score,
                basic_bandar_score,
                advanced_bandar_score,
                sentiment_score,
                advanced_bandar,
                sentiment
            )
        }
    
    def _calculate_technical_score(self, technical: dict) -> float:
        """Calculate technical score (0-100)"""
        score = 0
        signals = technical.get('signals', {})
        
        # RSI (0-25 points)
        rsi_signal = signals.get('rsi', 'NEUTRAL')
        if rsi_signal == 'OVERSOLD':
            score += 25
        elif rsi_signal == 'OVERBOUGHT':
            score += 0
        else:
            score += 12.5
        
        # MACD (0-25 points)
        macd_signal = signals.get('macd', 'NEUTRAL')
        if macd_signal == 'BULLISH':
            score += 25
        elif macd_signal == 'BEARISH':
            score += 0
        else:
            score += 12.5
        
        # Moving Averages (0-25 points)
        ma_signal = signals.get('ma_cross', 'NEUTRAL')
        if ma_signal == 'GOLDEN_CROSS':
            score += 25
        elif ma_signal == 'DEATH_CROSS':
            score += 0
        else:
            score += 12.5
        
        # Bollinger Bands (0-25 points)
        bb_signal = signals.get('bollinger', 'NEUTRAL')
        if bb_signal == 'OVERSOLD':
            score += 25
        elif bb_signal == 'OVERBOUGHT':
            score += 0
        else:
            score += 12.5
        
        return score
    
    def _calculate_basic_bandarmology_score(self, bandar: dict) -> float:
        """Calculate basic bandarmology score (0-100)"""
        score = 50  # Start neutral
        
        # Order book imbalance (±30 points)
        imbalance = bandar.get('order_book_imbalance', {})
        buy_pressure = imbalance.get('buy_pressure', 50)
        score += (buy_pressure - 50) * 0.6
        
        # Whale activity (±20 points)
        whale = bandar.get('whale_activity', {})
        whale_signal = whale.get('signal', 'NEUTRAL')
        if whale_signal == 'BULLISH':
            score += 20
        elif whale_signal == 'BEARISH':
            score -= 20
        
        return max(0, min(100, score))
    
    def _calculate_advanced_bandarmology_score(self, advanced: dict) -> float:
        """Calculate advanced bandarmology score (0-100)"""
        score = 50  # Start neutral
        
        # Manipulation penalty (-40 points max)
        manipulation = advanced.get('manipulation_score', {})
        manip_score = manipulation.get('score', 0)
        manip_penalty = -manip_score * 0.4
        score += manip_penalty
        
        # Real order direction (+40 points max)
        direction = advanced.get('real_order_direction', {})
        buy_pressure = direction.get('buy_pressure', 50)
        direction_bonus = (buy_pressure - 50) * 0.8
        score += direction_bonus
        
        # Whale activity adjustment (±10 points)
        whale = advanced.get('whale_activity', {})
        whale_pressure = whale.get('whale_pressure', 'NEUTRAL')
        if whale_pressure == 'BULLISH':
            score += 10
        elif whale_pressure == 'BEARISH':
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_sentiment_score(self, sentiment: dict) -> float:
        """Calculate sentiment score (0-100)"""
        base_score = sentiment.get('sentiment_score', 50)
        
        # Trending bonus (+20 points)
        if sentiment.get('trending', False):
            base_score += 20
        
        # Volume change adjustment (±10 points)
        volume_change = sentiment.get('volume_change_24h', 0)
        if volume_change > 50:
            base_score += 10
        elif volume_change < -30:
            base_score -= 10
        
        return max(0, min(100, base_score))
    
    def _determine_action(self, total_score: float, manipulation: dict, sentiment: dict) -> tuple:
        """Determine trading action and confidence"""
        
        # Check for high manipulation (override)
        manip_level = manipulation.get('level', 'LOW')
        if manip_level == 'VERY_HIGH':
            return 'AVOID', 'HIGH'
        elif manip_level == 'HIGH' and total_score < 60:
            return 'AVOID', 'MEDIUM'
        
        # Normal recommendation based on score
        if total_score >= 75:
            action = 'STRONG_BUY'
            confidence = 'HIGH'
        elif total_score >= 60:
            action = 'BUY'
            confidence = 'MEDIUM' if manip_level in ['MEDIUM', 'HIGH'] else 'HIGH'
        elif total_score >= 45:
            action = 'HOLD'
            confidence = 'MEDIUM'
        elif total_score >= 30:
            action = 'SELL'
            confidence = 'MEDIUM' if manip_level in ['MEDIUM', 'HIGH'] else 'HIGH'
        else:
            action = 'STRONG_SELL'
            confidence = 'HIGH'
        
        # Adjust confidence based on sentiment confidence
        if sentiment.get('confidence', 'MEDIUM') == 'LOW':
            if confidence == 'HIGH':
                confidence = 'MEDIUM'
            elif confidence == 'MEDIUM':
                confidence = 'LOW'
        
        return action, confidence
    
    def _calculate_target_prices(self, current_price: float, action: str, score: float) -> dict:
        """Calculate target prices based on action and score"""
        
        if action in ['STRONG_BUY', 'BUY']:
            # Bullish targets
            target_1 = current_price * 1.05  # +5%
            target_2 = current_price * 1.10  # +10%
            stop_loss = current_price * 0.97  # -3%
        elif action in ['STRONG_SELL', 'SELL']:
            # Bearish targets
            target_1 = current_price * 0.95  # -5%
            target_2 = current_price * 0.90  # -10%
            stop_loss = current_price * 1.03  # +3%
        else:
            # Hold - no specific targets
            target_1 = current_price * 1.02  # +2%
            target_2 = current_price * 0.98  # -2%
            stop_loss = current_price * 0.95  # -5%
        
        return {
            'target_1': round(target_1, 0),
            'target_2': round(target_2, 0),
            'stop_loss': round(stop_loss, 0),
            'current': round(current_price, 0)
        }
    
    def _generate_reasoning(self, action: str, tech_score: float, basic_score: float,
                           adv_score: float, sent_score: float, advanced_bandar: dict,
                           sentiment: dict) -> list:
        """Generate human-readable reasoning"""
        reasons = []
        
        # Technical reasoning
        if tech_score > 20:
            reasons.append(f"✅ Indikator teknikal positif (score: {tech_score:.0f}/30)")
        elif tech_score < 10:
            reasons.append(f"❌ Indikator teknikal negatif (score: {tech_score:.0f}/30)")
        
        # Advanced bandarmology reasoning
        manip = advanced_bandar.get('manipulation_score', {})
        if manip.get('level') in ['HIGH', 'VERY_HIGH']:
            reasons.append(f"⚠️ Manipulasi terdeteksi tinggi ({manip.get('score', 0):.0f}/100)")
        
        real_direction = advanced_bandar.get('real_order_direction', {})
        if real_direction.get('direction') == 'BULLISH':
            reasons.append(f"✅ Real orders menunjukkan tekanan beli ({real_direction.get('buy_pressure', 0):.0f}%)")
        elif real_direction.get('direction') == 'BEARISH':
            reasons.append(f"❌ Real orders menunjukkan tekanan jual ({real_direction.get('sell_pressure', 0):.0f}%)")
        
        fake_orders = advanced_bandar.get('fake_order_detection', {})
        fake_pct = fake_orders.get('fake_order_percentage', 0)
        if fake_pct > 15:
            reasons.append(f"⚠️ Banyak fake orders terdeteksi ({fake_pct:.0f}%)")
        
        # Sentiment reasoning
        if sent_score > 15:
            reasons.append(f"✅ Sentiment social media positif ({sentiment.get('sentiment_score', 0):.0f}/100)")
        elif sent_score < 10:
            reasons.append(f"❌ Sentiment social media negatif ({sentiment.get('sentiment_score', 0):.0f}/100)")
        
        if sentiment.get('trending'):
            reasons.append("🔥 Sedang trending di social media")
        
        return reasons
    
    def _generate_executive_summary(self, recommendation: dict, advanced_bandar: dict,
                                   sentiment: dict, ticker: dict) -> dict:
        """
        Generate executive summary for dashboard card
        This is the key feature for v2.0 - quick decision making
        """
        
        action = recommendation['action']
        confidence = recommendation['confidence']
        total_score = recommendation['total_score']
        
        # Get key metrics
        manip_score = advanced_bandar.get('manipulation_score', {})
        manip_level = manip_score.get('level', 'UNKNOWN')
        manip_value = manip_score.get('score', 0)
        
        fake_detection = advanced_bandar.get('fake_order_detection', {})
        fake_pct = fake_detection.get('fake_order_percentage', 0)
        
        whale = advanced_bandar.get('whale_activity', {})
        whale_level = whale.get('whale_activity_level', 'UNKNOWN')
        
        sentiment_label = sentiment.get('sentiment_label', 'NEUTRAL')
        sentiment_score = sentiment.get('sentiment_score', 50)
        sentiment_emoji = sentiment.get('sentiment_emoji', '😐')
        
        real_direction = advanced_bandar.get('real_order_direction', {})
        direction = real_direction.get('direction', 'NEUTRAL')
        
        # Price change
        price_change = float(ticker.get('change_24h', 0))
        
        # Generate action color
        action_color = self._get_action_color(action)
        
        # Generate risk level
        risk_level = self._calculate_risk_level(manip_level, whale_level, fake_pct)
        
        return {
            'action': action,
            'action_color': action_color,
            'confidence': confidence,
            'total_score': total_score,
            'risk_level': risk_level,
            'manipulation': {
                'level': manip_level,
                'score': manip_value,
                'fake_orders_pct': fake_pct
            },
            'whale_activity': whale_level,
            'sentiment': {
                'label': sentiment_label,
                'score': sentiment_score,
                'emoji': sentiment_emoji,
                'trending': sentiment.get('trending', False)
            },
            'real_order_direction': direction,
            'price_change_24h': price_change,
            'quick_insight': self._generate_quick_insight(
                action, manip_level, sentiment_label, direction, fake_pct
            )
        }
    
    def _get_action_color(self, action: str) -> str:
        """Get color for action badge"""
        colors = {
            'STRONG_BUY': 'green',
            'BUY': 'lightgreen',
            'HOLD': 'yellow',
            'SELL': 'orange',
            'STRONG_SELL': 'red',
            'AVOID': 'darkred'
        }
        return colors.get(action, 'gray')
    
    def _calculate_risk_level(self, manip_level: str, whale_level: str, fake_pct: float) -> str:
        """Calculate overall risk level"""
        risk_score = 0
        
        # Manipulation risk
        if manip_level == 'VERY_HIGH':
            risk_score += 40
        elif manip_level == 'HIGH':
            risk_score += 30
        elif manip_level == 'MEDIUM':
            risk_score += 15
        
        # Whale risk
        if whale_level == 'VERY_HIGH':
            risk_score += 30
        elif whale_level == 'HIGH':
            risk_score += 20
        elif whale_level == 'MEDIUM':
            risk_score += 10
        
        # Fake orders risk
        if fake_pct > 20:
            risk_score += 30
        elif fake_pct > 10:
            risk_score += 15
        
        # Classify
        if risk_score >= 70:
            return 'VERY_HIGH'
        elif risk_score >= 50:
            return 'HIGH'
        elif risk_score >= 30:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_quick_insight(self, action: str, manip: str, sentiment: str,
                               direction: str, fake_pct: float) -> str:
        """Generate one-line quick insight for dashboard"""
        
        if action == 'AVOID':
            return f"⚠️ HINDARI - Manipulasi {manip.lower()}, {fake_pct:.0f}% fake orders"
        
        if manip in ['HIGH', 'VERY_HIGH']:
            return f"⚠️ Hati-hati - Manipulasi tinggi terdeteksi"
        
        if action in ['STRONG_BUY', 'BUY']:
            if sentiment == 'POSITIVE' and direction == 'BULLISH':
                return f"✅ Signal kuat - Sentiment & real orders bullish"
            else:
                return f"📈 Peluang beli - Perhatikan entry point"
        
        if action in ['STRONG_SELL', 'SELL']:
            if sentiment == 'NEGATIVE' and direction == 'BEARISH':
                return f"❌ Signal kuat - Sentiment & real orders bearish"
            else:
                return f"📉 Pertimbangkan jual - Momentum melemah"
        
        return f"⏸️ Tunggu signal lebih jelas"
    
    def _get_simplified_technical_analysis(self, trades: list, ticker: dict) -> dict:
        """Simplified technical analysis without OHLC data"""
        try:
            # Extract basic price info from ticker
            current_price = float(ticker.get('last', 0))
            high_24h = float(ticker.get('high', current_price))
            low_24h = float(ticker.get('low', current_price))
            
            # Calculate simple RSI-like indicator from price position
            price_range = high_24h - low_24h
            if price_range > 0:
                price_position = ((current_price - low_24h) / price_range) * 100
            else:
                price_position = 50
            
            # Determine signals based on price position
            if price_position > 70:
                rsi_signal = 'OVERBOUGHT'
            elif price_position < 30:
                rsi_signal = 'OVERSOLD'
            else:
                rsi_signal = 'NEUTRAL'
            
            # Simple momentum from recent trades
            if len(trades) > 10:
                recent_prices = [float(t.get('price', 0)) for t in trades[:10]]
                older_prices = [float(t.get('price', 0)) for t in trades[-10:]]
                
                avg_recent = sum(recent_prices) / len(recent_prices) if recent_prices else current_price
                avg_older = sum(older_prices) / len(older_prices) if older_prices else current_price
                
                if avg_recent > avg_older * 1.01:
                    macd_signal = 'BULLISH'
                elif avg_recent < avg_older * 0.99:
                    macd_signal = 'BEARISH'
                else:
                    macd_signal = 'NEUTRAL'
            else:
                macd_signal = 'NEUTRAL'
            
            return {
                'indicators': {
                    'rsi': price_position,
                    'price_position': price_position
                },
                'signals': {
                    'rsi': rsi_signal,
                    'macd': macd_signal,
                    'ma_cross': 'NEUTRAL',
                    'bollinger': 'NEUTRAL'
                }
            }
        except Exception as e:
            # Return neutral if error
            return {
                'indicators': {'rsi': 50},
                'signals': {
                    'rsi': 'NEUTRAL',
                    'macd': 'NEUTRAL',
                    'ma_cross': 'NEUTRAL',
                    'bollinger': 'NEUTRAL'
                }
            }

