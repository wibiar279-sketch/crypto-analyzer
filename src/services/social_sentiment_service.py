"""
Social Media Sentiment Analysis Service
Analisa sentiment dari social media (Twitter, Reddit, etc.)

Note: Menggunakan simulated data karena API berbayar.
Untuk production, integrate dengan LunarCrush API atau build custom NLP.
"""

import random
import hashlib
from typing import Dict, List
from datetime import datetime, timedelta

class SocialSentimentService:
    
    def __init__(self):
        # Simulated data - in production, replace with real API calls
        self.use_simulation = True
        
        # Keywords yang sering muncul untuk crypto
        self.positive_keywords = [
            'bullish', 'moon', 'breakout', 'pump', 'rally', 'surge',
            'adoption', 'partnership', 'upgrade', 'innovation', 'growth'
        ]
        
        self.negative_keywords = [
            'bearish', 'dump', 'crash', 'scam', 'rug', 'hack',
            'regulation', 'ban', 'lawsuit', 'decline', 'selloff'
        ]
        
        self.neutral_keywords = [
            'trading', 'analysis', 'chart', 'price', 'volume',
            'market', 'crypto', 'blockchain', 'update', 'news'
        ]
    
    def get_sentiment_analysis(self, symbol: str, pair_id: str) -> Dict:
        """
        Get comprehensive sentiment analysis for a cryptocurrency
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            pair_id: Trading pair ID (e.g., 'btc_idr')
        
        Returns:
            Dict with sentiment metrics
        """
        if self.use_simulation:
            return self._get_simulated_sentiment(symbol, pair_id)
        else:
            # In production, call real API here
            # return self._get_lunarcrush_sentiment(symbol)
            pass
    
    def _get_simulated_sentiment(self, symbol: str, pair_id: str) -> Dict:
        """
        Generate simulated but realistic sentiment data
        Uses symbol hash for consistency (same symbol = same sentiment in short time)
        """
        # Use symbol hash for pseudo-random but consistent data
        seed = int(hashlib.md5(f"{symbol}{datetime.now().strftime('%Y%m%d%H')}".encode()).hexdigest(), 16) % 10000
        random.seed(seed)
        
        # Generate sentiment score (0-100)
        # Major coins tend to have more positive sentiment
        major_coins = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']
        base_sentiment = 55 if symbol.upper() in major_coins else 50
        sentiment_score = max(0, min(100, base_sentiment + random.randint(-20, 30)))
        
        # Classify sentiment
        if sentiment_score >= 65:
            sentiment_label = 'POSITIVE'
            emoji = '😊'
        elif sentiment_score >= 45:
            sentiment_label = 'NEUTRAL'
            emoji = '😐'
        else:
            sentiment_label = 'NEGATIVE'
            emoji = '😞'
        
        # Social volume (mentions count)
        # Major coins have higher volume
        base_volume = 50000 if symbol.upper() in major_coins else 5000
        social_volume = base_volume + random.randint(-base_volume//2, base_volume)
        
        # Social dominance (% of total crypto discussions)
        if symbol.upper() == 'BTC':
            social_dominance = 25 + random.uniform(-5, 5)
        elif symbol.upper() in ['ETH', 'BNB']:
            social_dominance = 10 + random.uniform(-3, 3)
        elif symbol.upper() in major_coins:
            social_dominance = 3 + random.uniform(-1, 2)
        else:
            social_dominance = 0.5 + random.uniform(-0.3, 1)
        
        # Trending status
        trending = sentiment_score > 60 and social_volume > 10000
        
        # Influencer activity
        influencer_count = random.randint(5, 50) if trending else random.randint(1, 15)
        
        # Engagement rate (likes, shares, comments per mention)
        engagement_rate = 2.5 + random.uniform(-1, 3)
        
        # Volume change 24h
        volume_change_24h = random.uniform(-30, 80)
        
        # Top keywords
        if sentiment_label == 'POSITIVE':
            top_keywords = random.sample(self.positive_keywords, min(5, len(self.positive_keywords)))
        elif sentiment_label == 'NEGATIVE':
            top_keywords = random.sample(self.negative_keywords, min(5, len(self.negative_keywords)))
        else:
            top_keywords = random.sample(self.neutral_keywords, min(5, len(self.neutral_keywords)))
        
        # Confidence level
        if social_volume > 20000:
            confidence = 'HIGH'
        elif social_volume > 5000:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        # Sentiment trend (last 7 days)
        sentiment_trend = self._generate_sentiment_trend(sentiment_score)
        
        # Platform breakdown
        platform_breakdown = self._generate_platform_breakdown(social_volume)
        
        return {
            'sentiment_score': round(sentiment_score, 1),
            'sentiment_label': sentiment_label,
            'sentiment_emoji': emoji,
            'social_volume': social_volume,
            'social_dominance': round(social_dominance, 2),
            'trending': trending,
            'influencer_count': influencer_count,
            'engagement_rate': round(engagement_rate, 2),
            'volume_change_24h': round(volume_change_24h, 1),
            'top_keywords': top_keywords,
            'confidence': confidence,
            'sentiment_trend': sentiment_trend,
            'platform_breakdown': platform_breakdown,
            'last_updated': datetime.now().isoformat(),
            'interpretation': self._get_sentiment_interpretation(
                sentiment_label, 
                sentiment_score, 
                trending,
                volume_change_24h
            )
        }
    
    def _generate_sentiment_trend(self, current_score: float) -> List[Dict]:
        """Generate 7-day sentiment trend"""
        trend = []
        score = current_score
        
        for i in range(7, 0, -1):
            # Random walk with mean reversion
            change = random.uniform(-5, 5)
            score = max(0, min(100, score + change))
            
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            trend.append({
                'date': date,
                'score': round(score, 1)
            })
        
        return trend
    
    def _generate_platform_breakdown(self, total_volume: int) -> Dict:
        """Generate platform-specific volume breakdown"""
        # Typical distribution
        twitter_pct = random.uniform(0.4, 0.6)
        reddit_pct = random.uniform(0.2, 0.3)
        youtube_pct = random.uniform(0.1, 0.2)
        other_pct = 1 - twitter_pct - reddit_pct - youtube_pct
        
        return {
            'twitter': {
                'volume': int(total_volume * twitter_pct),
                'percentage': round(twitter_pct * 100, 1)
            },
            'reddit': {
                'volume': int(total_volume * reddit_pct),
                'percentage': round(reddit_pct * 100, 1)
            },
            'youtube': {
                'volume': int(total_volume * youtube_pct),
                'percentage': round(youtube_pct * 100, 1)
            },
            'others': {
                'volume': int(total_volume * other_pct),
                'percentage': round(other_pct * 100, 1)
            }
        }
    
    def _get_sentiment_interpretation(self, label: str, score: float, 
                                     trending: bool, volume_change: float) -> str:
        """Generate human-readable interpretation"""
        base_text = {
            'POSITIVE': f"Sentiment positif ({score:.0f}/100). Komunitas optimis.",
            'NEUTRAL': f"Sentiment netral ({score:.0f}/100). Komunitas wait-and-see.",
            'NEGATIVE': f"Sentiment negatif ({score:.0f}/100). Komunitas pesimis."
        }
        
        interpretation = base_text.get(label, "Unknown sentiment")
        
        if trending:
            interpretation += " 🔥 Sedang trending di social media!"
        
        if volume_change > 50:
            interpretation += f" Volume diskusi meningkat {volume_change:.0f}% (viral)."
        elif volume_change < -30:
            interpretation += f" Volume diskusi menurun {abs(volume_change):.0f}% (kehilangan momentum)."
        
        return interpretation
    
    def get_sentiment_summary(self, symbol: str) -> str:
        """Get one-line sentiment summary for dashboard"""
        sentiment = self.get_sentiment_analysis(symbol, f"{symbol.lower()}_idr")
        
        emoji = sentiment['sentiment_emoji']
        label = sentiment['sentiment_label']
        score = sentiment['sentiment_score']
        
        if sentiment['trending']:
            return f"{emoji} {label} ({score:.0f}/100) 🔥 TRENDING"
        else:
            return f"{emoji} {label} ({score:.0f}/100)"
    
    def compare_sentiment_with_price(self, sentiment_data: Dict, price_change_24h: float) -> Dict:
        """
        Compare sentiment with actual price movement
        Detect divergence (sentiment vs price)
        """
        sentiment_score = sentiment_data['sentiment_score']
        
        # Normalize to -50 to +50 scale
        sentiment_direction = sentiment_score - 50
        
        # Detect divergence
        if sentiment_direction > 10 and price_change_24h < -2:
            divergence = "BULLISH_DIVERGENCE"
            interpretation = "Sentiment positif tapi harga turun. Kemungkinan reversal naik."
        elif sentiment_direction < -10 and price_change_24h > 2:
            divergence = "BEARISH_DIVERGENCE"
            interpretation = "Sentiment negatif tapi harga naik. Kemungkinan reversal turun."
        elif abs(sentiment_direction) < 10 and abs(price_change_24h) > 5:
            divergence = "SENTIMENT_LAG"
            interpretation = "Sentiment belum mengikuti pergerakan harga. Tunggu konfirmasi."
        else:
            divergence = "ALIGNED"
            interpretation = "Sentiment sejalan dengan pergerakan harga."
        
        return {
            'divergence_type': divergence,
            'interpretation': interpretation,
            'sentiment_direction': 'BULLISH' if sentiment_direction > 0 else 'BEARISH',
            'price_direction': 'UP' if price_change_24h > 0 else 'DOWN',
            'alignment_score': 100 - abs(sentiment_direction - price_change_24h * 5)  # 0-100
        }
    
    def get_sentiment_alerts(self, sentiment_data: Dict) -> List[Dict]:
        """
        Generate alerts based on sentiment data
        """
        alerts = []
        
        # Trending alert
        if sentiment_data['trending']:
            alerts.append({
                'type': 'TRENDING',
                'severity': 'INFO',
                'message': f"🔥 {sentiment_data.get('symbol', 'Crypto')} sedang trending di social media!"
            })
        
        # Volume spike alert
        if sentiment_data['volume_change_24h'] > 100:
            alerts.append({
                'type': 'VOLUME_SPIKE',
                'severity': 'WARNING',
                'message': f"⚠️ Volume diskusi meningkat {sentiment_data['volume_change_24h']:.0f}% dalam 24 jam!"
            })
        
        # Extreme sentiment alert
        if sentiment_data['sentiment_score'] > 80:
            alerts.append({
                'type': 'EXTREME_POSITIVE',
                'severity': 'WARNING',
                'message': "⚠️ Sentiment sangat positif (possible FOMO). Hati-hati dengan euphoria."
            })
        elif sentiment_data['sentiment_score'] < 20:
            alerts.append({
                'type': 'EXTREME_NEGATIVE',
                'severity': 'WARNING',
                'message': "⚠️ Sentiment sangat negatif (possible panic). Bisa jadi buying opportunity."
            })
        
        return alerts
    
    def calculate_sentiment_score_for_recommendation(self, symbol: str) -> float:
        """
        Calculate sentiment score (0-20) for recommendation engine
        To be integrated with technical and bandarmology scores
        """
        sentiment = self.get_sentiment_analysis(symbol, f"{symbol.lower()}_idr")
        
        # Base score from sentiment (0-15 points)
        base_score = (sentiment['sentiment_score'] / 100) * 15
        
        # Bonus for trending (+3 points)
        trending_bonus = 3 if sentiment['trending'] else 0
        
        # Bonus for high volume change (+2 points)
        volume_bonus = 2 if sentiment['volume_change_24h'] > 50 else 0
        
        total_score = base_score + trending_bonus + volume_bonus
        
        return min(total_score, 20)  # Cap at 20

