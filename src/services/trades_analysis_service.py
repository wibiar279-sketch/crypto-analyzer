"""
Trades Analysis Service - Analyze actual transactions (not just order book)

This service fetches and analyzes actual trades from Indodax API to calculate:
- OFI (Order Flow Imbalance)
- CVD (Cumulative Volume Delta)
- Aggressive buy/sell ratio
- Kyle's Lambda (price impact)
"""

import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import statistics


class TradesAnalysisService:
    """Service for analyzing actual trades data"""
    
    def __init__(self):
        self.cvd_history = {}  # pair_id -> CVD value
        self.ofi_history = {}  # pair_id -> list of OFI values
        
    def analyze_trades(self, trades: List[Dict], pair_id: str) -> Dict:
        """
        Analyze trades data to extract microstructure signals
        
        Args:
            trades: List of trade dicts from Indodax API
                    [{'date': timestamp, 'price': str, 'amount': str, 'type': 'buy'/'sell'}, ...]
            pair_id: Trading pair ID
            
        Returns:
            Dict with analysis results
        """
        if not trades or len(trades) == 0:
            return self._empty_result()
        
        try:
            # Parse trades
            parsed_trades = self._parse_trades(trades)
            
            if len(parsed_trades) == 0:
                return self._empty_result()
            
            # Calculate metrics
            cvd = self._calculate_cvd(parsed_trades, pair_id)
            ofi_metrics = self._calculate_ofi(parsed_trades, pair_id)
            buy_sell_ratio = self._calculate_buy_sell_ratio(parsed_trades)
            aggressive_metrics = self._calculate_aggressive_metrics(parsed_trades)
            kyle_lambda = self._calculate_kyle_lambda(parsed_trades)
            
            # Recent trades summary
            recent_summary = self._summarize_recent_trades(parsed_trades, window=20)
            
            return {
                'cvd': cvd,
                'ofi': ofi_metrics,
                'buy_sell_ratio': buy_sell_ratio,
                'aggressive_metrics': aggressive_metrics,
                'kyle_lambda': kyle_lambda,
                'recent_summary': recent_summary,
                'total_trades': len(parsed_trades),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error analyzing trades: {e}")
            return self._empty_result()
    
    def _parse_trades(self, trades: List[Dict]) -> List[Dict]:
        """Parse and clean trades data"""
        parsed = []
        
        for trade in trades:
            try:
                parsed.append({
                    'timestamp': int(trade.get('date', 0)),
                    'price': float(trade.get('price', 0)),
                    'amount': float(trade.get('amount', 0)),
                    'type': trade.get('type', 'buy').lower(),
                    'tid': trade.get('tid', '')
                })
            except (ValueError, TypeError):
                continue
        
        # Sort by timestamp (oldest first)
        parsed.sort(key=lambda x: x['timestamp'])
        
        return parsed
    
    def _calculate_cvd(self, trades: List[Dict], pair_id: str) -> Dict:
        """
        Calculate Cumulative Volume Delta (CVD)
        CVD = Σ(buy_volume - sell_volume)
        """
        # Get previous CVD or start from 0
        cvd = self.cvd_history.get(pair_id, 0)
        
        buy_volume = 0
        sell_volume = 0
        
        for trade in trades:
            if trade['type'] == 'buy':
                buy_volume += trade['amount']
                cvd += trade['amount']
            else:
                sell_volume += trade['amount']
                cvd -= trade['amount']
        
        # Update history
        self.cvd_history[pair_id] = cvd
        
        # Calculate trend
        if buy_volume > sell_volume * 1.2:
            trend = 'BULLISH'
        elif sell_volume > buy_volume * 1.2:
            trend = 'BEARISH'
        else:
            trend = 'NEUTRAL'
        
        return {
            'value': round(cvd, 4),
            'buy_volume': round(buy_volume, 4),
            'sell_volume': round(sell_volume, 4),
            'net_volume': round(buy_volume - sell_volume, 4),
            'trend': trend,
            'interpretation': self._interpret_cvd(cvd, buy_volume, sell_volume)
        }
    
    def _calculate_ofi(self, trades: List[Dict], pair_id: str, window: int = 10) -> Dict:
        """
        Calculate Order Flow Imbalance (OFI)
        Rolling sum of (buy_amount - sell_amount) over window
        """
        # Calculate OFI for each trade (rolling window)
        ofi_values = []
        
        for i in range(len(trades)):
            start_idx = max(0, i - window + 1)
            window_trades = trades[start_idx:i+1]
            
            ofi = 0
            for trade in window_trades:
                if trade['type'] == 'buy':
                    ofi += trade['amount']
                else:
                    ofi -= trade['amount']
            
            ofi_values.append(ofi)
        
        # Store history for z-score calculation
        if pair_id not in self.ofi_history:
            self.ofi_history[pair_id] = []
        
        self.ofi_history[pair_id].extend(ofi_values)
        
        # Keep only last 1000 values
        if len(self.ofi_history[pair_id]) > 1000:
            self.ofi_history[pair_id] = self.ofi_history[pair_id][-1000:]
        
        # Calculate current OFI and z-score
        current_ofi = ofi_values[-1] if ofi_values else 0
        
        if len(self.ofi_history[pair_id]) > 10:
            mean_ofi = statistics.mean(self.ofi_history[pair_id])
            std_ofi = statistics.stdev(self.ofi_history[pair_id])
            
            if std_ofi > 0:
                z_ofi = (current_ofi - mean_ofi) / std_ofi
            else:
                z_ofi = 0
        else:
            z_ofi = 0
        
        # Interpretation
        if z_ofi >= 1.5:
            signal = 'EXTREME_BUY'
            interpretation = f"🔥 Extreme aggressive buying (z={z_ofi:.2f})"
        elif z_ofi >= 1.0:
            signal = 'STRONG_BUY'
            interpretation = f"📈 Strong aggressive buying (z={z_ofi:.2f})"
        elif z_ofi <= -1.5:
            signal = 'EXTREME_SELL'
            interpretation = f"❄️ Extreme aggressive selling (z={z_ofi:.2f})"
        elif z_ofi <= -1.0:
            signal = 'STRONG_SELL'
            interpretation = f"📉 Strong aggressive selling (z={z_ofi:.2f})"
        else:
            signal = 'NEUTRAL'
            interpretation = f"⚖️ Balanced flow (z={z_ofi:.2f})"
        
        return {
            'value': round(current_ofi, 4),
            'z_score': round(z_ofi, 4),
            'signal': signal,
            'interpretation': interpretation,
            'window': window
        }
    
    def _calculate_buy_sell_ratio(self, trades: List[Dict]) -> Dict:
        """Calculate buy/sell ratio from trades"""
        buy_count = sum(1 for t in trades if t['type'] == 'buy')
        sell_count = len(trades) - buy_count
        
        buy_volume = sum(t['amount'] for t in trades if t['type'] == 'buy')
        sell_volume = sum(t['amount'] for t in trades if t['type'] == 'sell')
        
        # Ratios
        if sell_count > 0:
            count_ratio = buy_count / sell_count
        else:
            count_ratio = float('inf') if buy_count > 0 else 1.0
        
        if sell_volume > 0:
            volume_ratio = buy_volume / sell_volume
        else:
            volume_ratio = float('inf') if buy_volume > 0 else 1.0
        
        # Percentages
        total_count = buy_count + sell_count
        buy_pct = (buy_count / total_count * 100) if total_count > 0 else 50
        sell_pct = 100 - buy_pct
        
        total_volume = buy_volume + sell_volume
        buy_vol_pct = (buy_volume / total_volume * 100) if total_volume > 0 else 50
        sell_vol_pct = 100 - buy_vol_pct
        
        return {
            'buy_count': buy_count,
            'sell_count': sell_count,
            'buy_percentage': round(buy_pct, 2),
            'sell_percentage': round(sell_pct, 2),
            'buy_volume': round(buy_volume, 4),
            'sell_volume': round(sell_volume, 4),
            'buy_volume_percentage': round(buy_vol_pct, 2),
            'sell_volume_percentage': round(sell_vol_pct, 2),
            'count_ratio': round(count_ratio, 4),
            'volume_ratio': round(volume_ratio, 4)
        }
    
    def _calculate_aggressive_metrics(self, trades: List[Dict]) -> Dict:
        """
        Calculate aggressive buying/selling metrics
        All trades from API are aggressive (market orders)
        """
        recent_trades = trades[-20:] if len(trades) >= 20 else trades
        
        aggressive_buy = sum(t['amount'] for t in recent_trades if t['type'] == 'buy')
        aggressive_sell = sum(t['amount'] for t in recent_trades if t['type'] == 'sell')
        
        total_aggressive = aggressive_buy + aggressive_sell
        
        if total_aggressive > 0:
            buy_pressure = aggressive_buy / total_aggressive * 100
            sell_pressure = aggressive_sell / total_aggressive * 100
        else:
            buy_pressure = 50
            sell_pressure = 50
        
        # Determine pressure
        if buy_pressure >= 65:
            pressure = 'STRONG_BUY_PRESSURE'
        elif buy_pressure >= 55:
            pressure = 'BUY_PRESSURE'
        elif sell_pressure >= 65:
            pressure = 'STRONG_SELL_PRESSURE'
        elif sell_pressure >= 55:
            pressure = 'SELL_PRESSURE'
        else:
            pressure = 'BALANCED'
        
        return {
            'aggressive_buy_volume': round(aggressive_buy, 4),
            'aggressive_sell_volume': round(aggressive_sell, 4),
            'buy_pressure_pct': round(buy_pressure, 2),
            'sell_pressure_pct': round(sell_pressure, 2),
            'pressure': pressure,
            'recent_trades_count': len(recent_trades)
        }
    
    def _calculate_kyle_lambda(self, trades: List[Dict]) -> Dict:
        """
        Calculate Kyle's Lambda (price impact coefficient)
        Δp ≈ λ × q
        where q = net aggressive order size
        """
        if len(trades) < 10:
            return {
                'value': 0,
                'interpretation': 'Insufficient data',
                'confidence': 'LOW'
            }
        
        try:
            # Calculate price changes and net order sizes
            delta_prices = []
            net_sizes = []
            
            window = 5
            for i in range(window, len(trades)):
                # Price change
                p_start = trades[i-window]['price']
                p_end = trades[i]['price']
                delta_p = p_end - p_start
                
                # Net order size in window
                window_trades = trades[i-window:i]
                net_q = sum(t['amount'] if t['type'] == 'buy' else -t['amount'] 
                           for t in window_trades)
                
                delta_prices.append(delta_p)
                net_sizes.append(net_q)
            
            # Calculate covariance and variance
            if len(delta_prices) > 0 and len(net_sizes) > 0:
                cov = np.cov(delta_prices, net_sizes)[0, 1]
                var = np.var(net_sizes)
                
                if var > 0:
                    lambda_kyle = cov / var
                else:
                    lambda_kyle = 0
            else:
                lambda_kyle = 0
            
            # Interpretation
            abs_lambda = abs(lambda_kyle)
            
            if abs_lambda > 0.1:
                impact = 'HIGH'
                interpretation = f"High price impact (λ={lambda_kyle:.6f}) - Illiquid market"
            elif abs_lambda > 0.01:
                impact = 'MEDIUM'
                interpretation = f"Medium price impact (λ={lambda_kyle:.6f}) - Normal liquidity"
            else:
                impact = 'LOW'
                interpretation = f"Low price impact (λ={lambda_kyle:.6f}) - Liquid market"
            
            return {
                'value': round(lambda_kyle, 8),
                'impact_level': impact,
                'interpretation': interpretation,
                'confidence': 'MEDIUM' if len(trades) >= 50 else 'LOW'
            }
            
        except Exception as e:
            print(f"Error calculating Kyle's lambda: {e}")
            return {
                'value': 0,
                'interpretation': 'Calculation error',
                'confidence': 'LOW'
            }
    
    def _summarize_recent_trades(self, trades: List[Dict], window: int = 20) -> Dict:
        """Summarize recent trades"""
        recent = trades[-window:] if len(trades) >= window else trades
        
        if not recent:
            return {}
        
        prices = [t['price'] for t in recent]
        
        return {
            'count': len(recent),
            'avg_price': round(statistics.mean(prices), 2),
            'min_price': round(min(prices), 2),
            'max_price': round(max(prices), 2),
            'price_volatility': round(statistics.stdev(prices), 2) if len(prices) > 1 else 0,
            'first_price': round(recent[0]['price'], 2),
            'last_price': round(recent[-1]['price'], 2),
            'price_change': round(recent[-1]['price'] - recent[0]['price'], 2),
            'price_change_pct': round((recent[-1]['price'] / recent[0]['price'] - 1) * 100, 2) if recent[0]['price'] > 0 else 0
        }
    
    def _interpret_cvd(self, cvd: float, buy_volume: float, sell_volume: float) -> str:
        """Interpret CVD value"""
        if cvd > 0 and buy_volume > sell_volume * 1.5:
            return "📈 Strong net buying pressure - CVD trending up"
        elif cvd > 0:
            return "📊 Positive CVD - More buying than selling"
        elif cvd < 0 and sell_volume > buy_volume * 1.5:
            return "📉 Strong net selling pressure - CVD trending down"
        elif cvd < 0:
            return "📊 Negative CVD - More selling than buying"
        else:
            return "⚖️ Balanced CVD - Equal buying and selling"
    
    def _empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            'cvd': {
                'value': 0,
                'buy_volume': 0,
                'sell_volume': 0,
                'net_volume': 0,
                'trend': 'UNKNOWN',
                'interpretation': 'No trades data available'
            },
            'ofi': {
                'value': 0,
                'z_score': 0,
                'signal': 'UNKNOWN',
                'interpretation': 'No trades data available',
                'window': 10
            },
            'buy_sell_ratio': {
                'buy_count': 0,
                'sell_count': 0,
                'buy_percentage': 50,
                'sell_percentage': 50,
                'buy_volume': 0,
                'sell_volume': 0,
                'buy_volume_percentage': 50,
                'sell_volume_percentage': 50,
                'count_ratio': 1.0,
                'volume_ratio': 1.0
            },
            'aggressive_metrics': {
                'aggressive_buy_volume': 0,
                'aggressive_sell_volume': 0,
                'buy_pressure_pct': 50,
                'sell_pressure_pct': 50,
                'pressure': 'UNKNOWN',
                'recent_trades_count': 0
            },
            'kyle_lambda': {
                'value': 0,
                'interpretation': 'No data',
                'confidence': 'NONE'
            },
            'recent_summary': {},
            'total_trades': 0,
            'timestamp': datetime.now().isoformat()
        }

