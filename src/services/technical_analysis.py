"""
Technical Analysis Service
Calculates technical indicators from OHLC data
"""
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice
from typing import Dict, List

class TechnicalAnalysis:
    
    def __init__(self, ohlc_data: List[Dict]):
        """
        Initialize with OHLC data
        
        Args:
            ohlc_data: List of OHLC dictionaries with keys: Time, Open, High, Low, Close, Volume
        """
        if not ohlc_data or 'error' in str(ohlc_data):
            self.df = pd.DataFrame()
            return
        
        # Convert to DataFrame
        self.df = pd.DataFrame(ohlc_data)
        
        # Ensure numeric types
        for col in ['Open', 'High', 'Low', 'Close']:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Convert Volume to numeric, handling string format
        self.df['Volume'] = pd.to_numeric(self.df['Volume'], errors='coerce')
        
        # Sort by time
        self.df = self.df.sort_values('Time')
        self.df.reset_index(drop=True, inplace=True)
    
    def calculate_sma(self, periods: List[int] = [7, 25, 99]) -> Dict:
        """Calculate Simple Moving Averages"""
        if self.df.empty:
            return {}
        
        sma_data = {}
        for period in periods:
            if len(self.df) >= period:
                sma = SMAIndicator(close=self.df['Close'], window=period)
                sma_data[f'SMA_{period}'] = sma.sma_indicator().iloc[-1]
        
        return sma_data
    
    def calculate_ema(self, periods: List[int] = [12, 26]) -> Dict:
        """Calculate Exponential Moving Averages"""
        if self.df.empty:
            return {}
        
        ema_data = {}
        for period in periods:
            if len(self.df) >= period:
                ema = EMAIndicator(close=self.df['Close'], window=period)
                ema_data[f'EMA_{period}'] = ema.ema_indicator().iloc[-1]
        
        return ema_data
    
    def calculate_rsi(self, period: int = 14) -> Dict:
        """Calculate Relative Strength Index"""
        if self.df.empty or len(self.df) < period:
            return {}
        
        rsi = RSIIndicator(close=self.df['Close'], window=period)
        rsi_value = rsi.rsi().iloc[-1]
        
        # Determine signal
        signal = "NEUTRAL"
        if rsi_value > 70:
            signal = "OVERBOUGHT"
        elif rsi_value < 30:
            signal = "OVERSOLD"
        
        return {
            'RSI': rsi_value,
            'RSI_signal': signal
        }
    
    def calculate_macd(self) -> Dict:
        """Calculate MACD"""
        if self.df.empty or len(self.df) < 26:
            return {}
        
        macd = MACD(close=self.df['Close'])
        macd_line = macd.macd().iloc[-1]
        signal_line = macd.macd_signal().iloc[-1]
        histogram = macd.macd_diff().iloc[-1]
        
        # Determine signal
        signal = "NEUTRAL"
        if macd_line > signal_line and histogram > 0:
            signal = "BULLISH"
        elif macd_line < signal_line and histogram < 0:
            signal = "BEARISH"
        
        return {
            'MACD': macd_line,
            'MACD_signal': signal_line,
            'MACD_histogram': histogram,
            'MACD_trend': signal
        }
    
    def calculate_bollinger_bands(self, period: int = 20, std_dev: int = 2) -> Dict:
        """Calculate Bollinger Bands"""
        if self.df.empty or len(self.df) < period:
            return {}
        
        bb = BollingerBands(close=self.df['Close'], window=period, window_dev=std_dev)
        
        current_price = self.df['Close'].iloc[-1]
        upper_band = bb.bollinger_hband().iloc[-1]
        middle_band = bb.bollinger_mavg().iloc[-1]
        lower_band = bb.bollinger_lband().iloc[-1]
        
        # Determine position
        position = "MIDDLE"
        if current_price >= upper_band:
            position = "UPPER"
        elif current_price <= lower_band:
            position = "LOWER"
        
        return {
            'BB_upper': upper_band,
            'BB_middle': middle_band,
            'BB_lower': lower_band,
            'BB_position': position
        }
    
    def calculate_volume_analysis(self) -> Dict:
        """Calculate volume-based indicators"""
        if self.df.empty or len(self.df) < 20:
            return {}
        
        # Volume MA
        volume_ma = self.df['Volume'].rolling(window=20).mean().iloc[-1]
        current_volume = self.df['Volume'].iloc[-1]
        
        # Volume trend
        volume_trend = "NORMAL"
        if current_volume > volume_ma * 1.5:
            volume_trend = "HIGH"
        elif current_volume < volume_ma * 0.5:
            volume_trend = "LOW"
        
        return {
            'Volume_MA': volume_ma,
            'Current_Volume': current_volume,
            'Volume_trend': volume_trend
        }
    
    def get_all_indicators(self) -> Dict:
        """Get all technical indicators"""
        if self.df.empty:
            return {"error": "No data available"}
        
        indicators = {}
        
        # Moving Averages
        indicators.update(self.calculate_sma())
        indicators.update(self.calculate_ema())
        
        # Momentum
        indicators.update(self.calculate_rsi())
        indicators.update(self.calculate_macd())
        
        # Volatility
        indicators.update(self.calculate_bollinger_bands())
        
        # Volume
        indicators.update(self.calculate_volume_analysis())
        
        # Current price
        indicators['Current_Price'] = self.df['Close'].iloc[-1]
        
        return indicators
    
    def get_technical_score(self) -> int:
        """
        Calculate technical analysis score (0-40)
        """
        if self.df.empty:
            return 0
        
        score = 0
        
        # RSI Score (0-10)
        rsi_data = self.calculate_rsi()
        if rsi_data:
            rsi = rsi_data.get('RSI', 50)
            if rsi < 30:
                score += 10  # Oversold - bullish
            elif rsi < 40:
                score += 7
            elif rsi > 70:
                score += 0  # Overbought - bearish
            elif rsi > 60:
                score += 3
            else:
                score += 5  # Neutral
        
        # MACD Score (0-10)
        macd_data = self.calculate_macd()
        if macd_data:
            if macd_data.get('MACD_trend') == 'BULLISH':
                score += 10
            elif macd_data.get('MACD_trend') == 'BEARISH':
                score += 0
            else:
                score += 5
        
        # MA Crossover Score (0-10)
        sma_data = self.calculate_sma([7, 25])
        if 'SMA_7' in sma_data and 'SMA_25' in sma_data:
            if sma_data['SMA_7'] > sma_data['SMA_25']:
                score += 10  # Golden cross
            else:
                score += 0  # Death cross
        
        # Bollinger Bands Score (0-10)
        bb_data = self.calculate_bollinger_bands()
        if bb_data:
            if bb_data.get('BB_position') == 'LOWER':
                score += 10  # Near lower band - bullish
            elif bb_data.get('BB_position') == 'UPPER':
                score += 0  # Near upper band - bearish
            else:
                score += 5
        
        return min(score, 40)

