"""
Fear & Greed Index Service

Fetches market-wide sentiment from alternative.me Crypto Fear & Greed Index
- Completely FREE
- No API key required
- Updated daily
- Market-wide sentiment (0-100 scale)
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Optional


class FearGreedService:
    """Service for Crypto Fear & Greed Index from alternative.me"""
    
    API_URL = "https://api.alternative.me/fng/"
    CACHE_DURATION = 3600  # 1 hour cache
    
    def __init__(self):
        """Initialize with empty cache"""
        self._cache = None
        self._cache_time = None
    
    def get_market_sentiment(self) -> Dict:
        """
        Get current market sentiment from Fear & Greed Index
        
        Returns:
            Dict with:
                - value: 0-100 (0=extreme fear, 100=extreme greed)
                - classification: Text classification from API
                - mood: Enhanced mood classification
                - emoji: Emoji representation
                - color: Color for UI
                - timestamp: Unix timestamp
                - source: Data source
        """
        # Check cache
        if self._cache and self._cache_time:
            if datetime.now() - self._cache_time < timedelta(seconds=self.CACHE_DURATION):
                return self._cache
        
        try:
            # Fetch from API (no API key needed!)
            response = requests.get(self.API_URL, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data and 'data' in data and len(data['data']) > 0:
                fng_data = data['data'][0]
                
                value = int(fng_data['value'])
                classification = fng_data['value_classification']
                
                # Enhanced classification with more granular levels
                if value < 25:
                    mood = "EXTREME_FEAR"
                    emoji = "😱"
                    color = "#dc2626"  # red-600
                    signal = "STRONG_BUY"  # Contrarian indicator
                elif value < 45:
                    mood = "FEAR"
                    emoji = "😰"
                    color = "#f97316"  # orange-500
                    signal = "BUY"
                elif value < 55:
                    mood = "NEUTRAL"
                    emoji = "😐"
                    color = "#eab308"  # yellow-500
                    signal = "HOLD"
                elif value < 75:
                    mood = "GREED"
                    emoji = "😊"
                    color = "#84cc16"  # lime-500
                    signal = "SELL"
                else:
                    mood = "EXTREME_GREED"
                    emoji = "🤑"
                    color = "#22c55e"  # green-500
                    signal = "STRONG_SELL"  # Contrarian indicator
                
                result = {
                    'value': value,
                    'classification': classification,
                    'mood': mood,
                    'emoji': emoji,
                    'color': color,
                    'signal': signal,
                    'timestamp': int(fng_data['timestamp']),
                    'time_until_update': fng_data.get('time_until_update'),
                    'source': 'alternative.me',
                    'description': self._get_description(value)
                }
                
                # Update cache
                self._cache = result
                self._cache_time = datetime.now()
                
                return result
            
        except Exception as e:
            print(f"Error fetching Fear & Greed Index: {e}")
        
        # Return neutral if error
        return self._get_fallback_sentiment()
    
    def get_historical_sentiment(self, limit: int = 30) -> Dict:
        """
        Get historical Fear & Greed Index data
        
        Args:
            limit: Number of days to fetch (default 30)
            
        Returns:
            Dict with historical data
        """
        try:
            response = requests.get(
                self.API_URL,
                params={'limit': limit},
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data and 'data' in data:
                return {
                    'data': data['data'],
                    'count': len(data['data']),
                    'source': 'alternative.me'
                }
            
        except Exception as e:
            print(f"Error fetching historical Fear & Greed Index: {e}")
        
        return {'data': [], 'count': 0, 'source': 'error'}
    
    def _get_description(self, value: int) -> str:
        """Get description based on Fear & Greed value"""
        if value < 25:
            return "Extreme fear in the market. Investors are very worried. This could be a buying opportunity (contrarian indicator)."
        elif value < 45:
            return "Fear in the market. Investors are concerned about price movements. Consider accumulating positions."
        elif value < 55:
            return "Neutral market sentiment. No strong emotions driving the market. Wait for clearer signals."
        elif value < 75:
            return "Greed in the market. Investors are getting confident. Consider taking profits or reducing exposure."
        else:
            return "Extreme greed in the market. Investors are very bullish. High risk of correction (contrarian indicator)."
    
    def _get_fallback_sentiment(self) -> Dict:
        """Return neutral sentiment as fallback"""
        return {
            'value': 50,
            'classification': 'Neutral',
            'mood': 'NEUTRAL',
            'emoji': '😐',
            'color': '#eab308',
            'signal': 'HOLD',
            'timestamp': int(datetime.now().timestamp()),
            'time_until_update': None,
            'source': 'fallback',
            'description': 'Unable to fetch market sentiment. Assuming neutral.'
        }
    
    def get_sentiment_trend(self, days: int = 7) -> Dict:
        """
        Analyze sentiment trend over past N days
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with trend analysis
        """
        historical = self.get_historical_sentiment(limit=days)
        
        if not historical['data']:
            return {'trend': 'UNKNOWN', 'change': 0, 'direction': 'NEUTRAL'}
        
        data = historical['data']
        
        # Get current and past values
        current_value = int(data[0]['value'])
        past_value = int(data[-1]['value']) if len(data) > 1 else current_value
        
        # Calculate change
        change = current_value - past_value
        change_pct = (change / past_value * 100) if past_value > 0 else 0
        
        # Determine trend
        if change > 10:
            trend = "INCREASING"
            direction = "BULLISH"
        elif change < -10:
            trend = "DECREASING"
            direction = "BEARISH"
        else:
            trend = "STABLE"
            direction = "NEUTRAL"
        
        # Calculate average
        avg_value = sum(int(d['value']) for d in data) / len(data)
        
        return {
            'trend': trend,
            'direction': direction,
            'change': change,
            'change_pct': round(change_pct, 2),
            'current_value': current_value,
            'past_value': past_value,
            'avg_value': round(avg_value, 2),
            'days_analyzed': len(data)
        }


# Example usage
if __name__ == "__main__":
    service = FearGreedService()
    
    # Get current sentiment
    sentiment = service.get_market_sentiment()
    print(f"Market Sentiment: {sentiment['mood']} {sentiment['emoji']}")
    print(f"Fear & Greed Index: {sentiment['value']}/100")
    print(f"Signal: {sentiment['signal']}")
    print(f"Description: {sentiment['description']}")
    
    # Get trend
    trend = service.get_sentiment_trend(days=7)
    print(f"\n7-Day Trend: {trend['trend']} ({trend['direction']})")
    print(f"Change: {trend['change']} points ({trend['change_pct']}%)")

