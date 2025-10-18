"""
Indodax API Service
Handles all API calls to Indodax exchange
"""
import requests
from typing import Dict, List, Optional
import time

class IndodaxService:
    BASE_URL = "https://indodax.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; CryptoAnalyzer/1.0)'
        })
        self._cache = {}
        self._cache_timeout = 10  # seconds
    
    def _get_cached(self, key: str) -> Optional[Dict]:
        """Get cached data if still valid"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_timeout:
                return data
        return None
    
    def _set_cache(self, key: str, data: Dict):
        """Set cache with timestamp"""
        self._cache[key] = (data, time.time())
    
    def get_server_time(self) -> Dict:
        """Get server time"""
        try:
            response = self.session.get(f"{self.BASE_URL}/api/server_time")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_pairs(self) -> List[Dict]:
        """Get all available trading pairs"""
        cache_key = "pairs"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            response = self.session.get(f"{self.BASE_URL}/api/pairs")
            response.raise_for_status()
            data = response.json()
            self._set_cache(cache_key, data)
            return data
        except Exception as e:
            return {"error": str(e)}
    
    def get_summaries(self) -> Dict:
        """Get summaries for all pairs"""
        cache_key = "summaries"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            response = self.session.get(f"{self.BASE_URL}/api/summaries")
            response.raise_for_status()
            data = response.json()
            self._set_cache(cache_key, data)
            return data
        except Exception as e:
            return {"error": str(e)}
    
    def get_ticker(self, pair_id: str = "btc_idr") -> Dict:
        """Get ticker for specific pair"""
        cache_key = f"ticker_{pair_id}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # Convert pair_id format: btc_idr -> btcidr  
            pair_format = pair_id.replace('_', '')
            response = self.session.get(f"{self.BASE_URL}/api/ticker/{pair_format}")
            response.raise_for_status()
            data = response.json()
            self._set_cache(cache_key, data)
            return data
        except Exception as e:
            return {"error": str(e)}
    
    def get_ticker_all(self) -> Dict:
        """Get ticker for all pairs"""
        cache_key = "ticker_all"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            response = self.session.get(f"{self.BASE_URL}/api/ticker_all")
            response.raise_for_status()
            data = response.json()
            self._set_cache(cache_key, data)
            return data
        except Exception as e:
            return {"error": str(e)}
    
    def get_trades(self, pair_id: str = "btc_idr") -> List[Dict]:
        """Get recent trades for specific pair"""
        cache_key = f"trades_{pair_id}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # Convert pair_id format: btc_idr -> btcidr
            pair_format = pair_id.replace('_', '')
            response = self.session.get(f"{self.BASE_URL}/api/trades/{pair_format}")
            response.raise_for_status()
            data = response.json()
            self._set_cache(cache_key, data)
            return data
        except Exception as e:
            return {"error": str(e)}
    
    def get_depth(self, pair_id: str = "btc_idr") -> Dict:
        """Get order book depth for specific pair"""
        cache_key = f"depth_{pair_id}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # Convert pair_id format: btc_idr -> btcidr
            pair_format = pair_id.replace('_', '')
            response = self.session.get(f"{self.BASE_URL}/api/depth/{pair_format}")
            response.raise_for_status()
            data = response.json()
            
            # Check for API error
            if 'error' in data:
                return data
            
            self._set_cache(cache_key, data)
            return data
        except Exception as e:
            return {"error": str(e)}
    
    def get_ohlc(self, symbol: str, timeframe: str = "15", 
                 from_time: int = None, to_time: int = None) -> List[Dict]:
        """
        Get OHLC data for charting
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCIDR')
            timeframe: Time frame (1, 15, 30, 60, 240, 1D, 3D, 1W)
            from_time: Start timestamp (unix)
            to_time: End timestamp (unix)
        """
        if not from_time:
            from_time = int(time.time()) - 86400 * 7  # 7 days ago
        if not to_time:
            to_time = int(time.time())
        
        cache_key = f"ohlc_{symbol}_{timeframe}_{from_time}_{to_time}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.BASE_URL}/tradingview/history_v2"
            params = {
                'symbol': symbol,
                'tf': timeframe,
                'from': from_time,
                'to': to_time
            }
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            self._set_cache(cache_key, data)
            return data
        except Exception as e:
            return {"error": str(e)}

