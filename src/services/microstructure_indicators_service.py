"""
Microstructure Indicators Service

Implements professional-grade market microstructure indicators:
- Microprice & Micro-skew
- OBI (Order Book Imbalance) - multi-level
- Depth Ratio & z_log_dratio
- LVI (Liquidity Vacuum Index)
- CPS (Composite Pressure Score)
- SRI (Stop Risk Index)
"""

import numpy as np
import statistics
from typing import Dict, List, Optional
from datetime import datetime


class MicrostructureIndicatorsService:
    """Service for calculating market microstructure indicators"""
    
    def __init__(self):
        # History for z-score calculations
        self.log_dratio_history = {}  # pair_id -> list of log(dratio)
        self.spread_history = {}  # pair_id -> list of spreads
        self.depth_history = {}  # pair_id -> dict of depth metrics
        
    def calculate_all_indicators(self, order_book: Dict, trades_analysis: Dict, 
                                 ticker: Dict, pair_id: str) -> Dict:
        """
        Calculate all microstructure indicators
        
        Args:
            order_book: Order book data (bids, asks)
            trades_analysis: Trades analysis results (OFI, CVD, etc.)
            ticker: Ticker data
            pair_id: Trading pair ID
            
        Returns:
            Dict with all indicators
        """
        try:
            # Extract order book
            bids = order_book.get('buy', [])
            asks = order_book.get('sell', [])
            
            if not bids or not asks:
                return self._empty_result()
            
            # Parse order book
            bids_parsed = self._parse_order_book_side(bids)
            asks_parsed = self._parse_order_book_side(asks)
            
            if not bids_parsed or not asks_parsed:
                return self._empty_result()
            
            # Calculate indicators
            microprice_data = self._calculate_microprice(bids_parsed, asks_parsed)
            obi_data = self._calculate_obi_multilevel(bids_parsed, asks_parsed)
            depth_ratio_data = self._calculate_depth_ratio(bids_parsed, asks_parsed, 
                                                          microprice_data['mid'], pair_id)
            lvi_data = self._calculate_lvi(bids_parsed, asks_parsed, microprice_data['mid'])
            spread_data = self._calculate_spread_metrics(bids_parsed, asks_parsed, pair_id)
            
            # Calculate CPS (Composite Pressure Score)
            cps_data = self._calculate_cps(
                microprice_data['micro_skew'],
                obi_data['obi_5'],
                trades_analysis.get('ofi', {}).get('z_score', 0),
                depth_ratio_data['z_log_dratio']
            )
            
            # Calculate SRI (Stop Risk Index) - placeholder for now
            sri_data = self._calculate_sri_placeholder(bids_parsed, asks_parsed, 
                                                       microprice_data['mid'])
            
            return {
                'microprice': microprice_data,
                'obi': obi_data,
                'depth_ratio': depth_ratio_data,
                'lvi': lvi_data,
                'spread': spread_data,
                'cps': cps_data,
                'sri': sri_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error calculating microstructure indicators: {e}")
            return self._empty_result()
    
    def _parse_order_book_side(self, side_data: List) -> List[Dict]:
        """Parse order book side data"""
        parsed = []
        
        for level in side_data:
            try:
                if isinstance(level, list) and len(level) >= 2:
                    parsed.append({
                        'price': float(level[0]),
                        'qty': float(level[1])
                    })
                elif isinstance(level, dict):
                    parsed.append({
                        'price': float(level.get('price', 0)),
                        'qty': float(level.get('qty', 0))
                    })
            except (ValueError, TypeError):
                continue
        
        return parsed
    
    def _calculate_microprice(self, bids: List[Dict], asks: List[Dict]) -> Dict:
        """
        Calculate Microprice and Micro-skew
        
        Microprice (μ) = (ask1 × qty_bid1 + bid1 × qty_ask1) / (qty_bid1 + qty_ask1)
        Micro-skew = (μ - mid) / (spread/2) ∈ [−1, +1]
        """
        bid1_price = bids[0]['price']
        bid1_qty = bids[0]['qty']
        ask1_price = asks[0]['price']
        ask1_qty = asks[0]['qty']
        
        # Mid price
        mid = (bid1_price + ask1_price) / 2
        
        # Spread
        spread = ask1_price - bid1_price
        
        # Microprice
        total_qty = bid1_qty + ask1_qty
        if total_qty > 0:
            microprice = (ask1_price * bid1_qty + bid1_price * ask1_qty) / total_qty
        else:
            microprice = mid
        
        # Micro-skew
        if spread > 0:
            micro_skew = (microprice - mid) / (spread / 2)
            # Clamp to [-1, +1]
            micro_skew = max(-1, min(1, micro_skew))
        else:
            micro_skew = 0
        
        # Interpretation
        if micro_skew >= 0.8:
            signal = 'VERY_BULLISH'
            interpretation = f"🔥 Very strong short-term buy pressure (skew={micro_skew:.3f})"
        elif micro_skew >= 0.5:
            signal = 'BULLISH'
            interpretation = f"📈 Strong short-term buy pressure (skew={micro_skew:.3f})"
        elif micro_skew <= -0.8:
            signal = 'VERY_BEARISH'
            interpretation = f"❄️ Very strong short-term sell pressure (skew={micro_skew:.3f})"
        elif micro_skew <= -0.5:
            signal = 'BEARISH'
            interpretation = f"📉 Strong short-term sell pressure (skew={micro_skew:.3f})"
        else:
            signal = 'NEUTRAL'
            interpretation = f"⚖️ Balanced pressure (skew={micro_skew:.3f})"
        
        return {
            'microprice': round(microprice, 2),
            'mid': round(mid, 2),
            'spread': round(spread, 2),
            'micro_skew': round(micro_skew, 4),
            'signal': signal,
            'interpretation': interpretation
        }
    
    def _calculate_obi_multilevel(self, bids: List[Dict], asks: List[Dict]) -> Dict:
        """
        Calculate Order Book Imbalance for multiple levels
        
        OBI_k = (Σ qty_bid_k - Σ qty_ask_k) / (Σ qty_bid_k + Σ qty_ask_k)
        """
        results = {}
        
        for k in [5, 10, 20]:
            # Get top k levels
            bids_k = bids[:min(k, len(bids))]
            asks_k = asks[:min(k, len(asks))]
            
            # Sum quantities
            total_bid_qty = sum(level['qty'] for level in bids_k)
            total_ask_qty = sum(level['qty'] for level in asks_k)
            
            # Calculate OBI
            total_qty = total_bid_qty + total_ask_qty
            if total_qty > 0:
                obi = (total_bid_qty - total_ask_qty) / total_qty
            else:
                obi = 0
            
            results[f'obi_{k}'] = round(obi, 4)
        
        # Interpretation based on OBI_5
        obi_5 = results['obi_5']
        
        if obi_5 >= 0.3:
            signal = 'STRONG_BID_SIDE'
            interpretation = f"💪 Bid side much thicker (OBI5={obi_5:.3f}) - Bullish"
        elif obi_5 >= 0.2:
            signal = 'BID_SIDE'
            interpretation = f"📊 Bid side thicker (OBI5={obi_5:.3f}) - Slightly bullish"
        elif obi_5 <= -0.3:
            signal = 'STRONG_ASK_SIDE'
            interpretation = f"💪 Ask side much thicker (OBI5={obi_5:.3f}) - Bearish"
        elif obi_5 <= -0.2:
            signal = 'ASK_SIDE'
            interpretation = f"📊 Ask side thicker (OBI5={obi_5:.3f}) - Slightly bearish"
        else:
            signal = 'BALANCED'
            interpretation = f"⚖️ Balanced order book (OBI5={obi_5:.3f})"
        
        results['signal'] = signal
        results['interpretation'] = interpretation
        
        return results
    
    def _calculate_depth_ratio(self, bids: List[Dict], asks: List[Dict], 
                               mid: float, pair_id: str) -> Dict:
        """
        Calculate Depth Ratio and z_log_dratio
        
        dratio = depth_bid_±1% / depth_ask_±1%
        z_log_dratio = z-score of log(dratio)
        """
        # Calculate depth within ±1% of mid
        lower_bound = mid * 0.99
        upper_bound = mid * 1.01
        
        depth_bid_1pct = sum(level['qty'] for level in bids if level['price'] >= lower_bound)
        depth_ask_1pct = sum(level['qty'] for level in asks if level['price'] <= upper_bound)
        
        # Depth ratio
        if depth_ask_1pct > 0:
            dratio = depth_bid_1pct / depth_ask_1pct
        else:
            dratio = float('inf') if depth_bid_1pct > 0 else 1.0
        
        # Log transform
        log_dratio = np.log(dratio) if dratio > 0 and dratio != float('inf') else 0
        
        # Z-score
        if pair_id not in self.log_dratio_history:
            self.log_dratio_history[pair_id] = []
        
        self.log_dratio_history[pair_id].append(log_dratio)
        
        # Keep only last 1000 values
        if len(self.log_dratio_history[pair_id]) > 1000:
            self.log_dratio_history[pair_id] = self.log_dratio_history[pair_id][-1000:]
        
        # Calculate z-score
        if len(self.log_dratio_history[pair_id]) > 10:
            mean_log_dratio = statistics.mean(self.log_dratio_history[pair_id])
            std_log_dratio = statistics.stdev(self.log_dratio_history[pair_id])
            
            if std_log_dratio > 0:
                z_log_dratio = (log_dratio - mean_log_dratio) / std_log_dratio
            else:
                z_log_dratio = 0
        else:
            z_log_dratio = 0
        
        # Interpretation
        if z_log_dratio > 1.5:
            interpretation = f"💪 Significantly more bid depth (z={z_log_dratio:.2f})"
        elif z_log_dratio > 0.5:
            interpretation = f"📊 More bid depth (z={z_log_dratio:.2f})"
        elif z_log_dratio < -1.5:
            interpretation = f"💪 Significantly more ask depth (z={z_log_dratio:.2f})"
        elif z_log_dratio < -0.5:
            interpretation = f"📊 More ask depth (z={z_log_dratio:.2f})"
        else:
            interpretation = f"⚖️ Balanced depth (z={z_log_dratio:.2f})"
        
        return {
            'depth_bid_1pct': round(depth_bid_1pct, 4),
            'depth_ask_1pct': round(depth_ask_1pct, 4),
            'dratio': round(dratio, 4),
            'log_dratio': round(log_dratio, 4),
            'z_log_dratio': round(z_log_dratio, 4),
            'interpretation': interpretation
        }
    
    def _calculate_lvi(self, bids: List[Dict], asks: List[Dict], mid: float) -> Dict:
        """
        Calculate Liquidity Vacuum Index (LVI)
        
        LVI = 1 - (depth_top2 / depth_within_0.5%)
        
        High LVI = liquidity is spread thin (vacuum)
        Low LVI = liquidity concentrated at top
        """
        # Bid side
        depth_top2_bid = sum(bids[i]['qty'] for i in range(min(2, len(bids))))
        depth_within_0.5pct_bid = sum(level['qty'] for level in bids 
                                      if level['price'] >= mid * 0.995)
        
        if depth_within_0.5pct_bid > 0:
            lvi_bid = 1 - (depth_top2_bid / depth_within_0.5pct_bid)
        else:
            lvi_bid = 1.0
        
        # Ask side
        depth_top2_ask = sum(asks[i]['qty'] for i in range(min(2, len(asks))))
        depth_within_0.5pct_ask = sum(level['qty'] for level in asks 
                                      if level['price'] <= mid * 1.005)
        
        if depth_within_0.5pct_ask > 0:
            lvi_ask = 1 - (depth_top2_ask / depth_within_0.5pct_ask)
        else:
            lvi_ask = 1.0
        
        # Clamp to [0, 1]
        lvi_bid = max(0, min(1, lvi_bid))
        lvi_ask = max(0, min(1, lvi_ask))
        
        # Interpretation
        if lvi_ask >= 0.7:
            ask_interpretation = "⚠️ Ask liquidity vacuum - Easy to lift ask"
        elif lvi_ask >= 0.5:
            ask_interpretation = "📊 Ask liquidity spread thin"
        else:
            ask_interpretation = "✅ Ask liquidity concentrated"
        
        if lvi_bid >= 0.7:
            bid_interpretation = "⚠️ Bid liquidity vacuum - Easy to hit bid"
        elif lvi_bid >= 0.5:
            bid_interpretation = "📊 Bid liquidity spread thin"
        else:
            bid_interpretation = "✅ Bid liquidity concentrated"
        
        return {
            'lvi_bid': round(lvi_bid, 4),
            'lvi_ask': round(lvi_ask, 4),
            'bid_interpretation': bid_interpretation,
            'ask_interpretation': ask_interpretation
        }
    
    def _calculate_spread_metrics(self, bids: List[Dict], asks: List[Dict], 
                                  pair_id: str) -> Dict:
        """Calculate spread metrics with z-score"""
        bid1_price = bids[0]['price']
        ask1_price = asks[0]['price']
        
        spread = ask1_price - bid1_price
        mid = (bid1_price + ask1_price) / 2
        
        spread_pct = (spread / mid * 100) if mid > 0 else 0
        
        # Z-score
        if pair_id not in self.spread_history:
            self.spread_history[pair_id] = []
        
        self.spread_history[pair_id].append(spread_pct)
        
        # Keep only last 1000 values
        if len(self.spread_history[pair_id]) > 1000:
            self.spread_history[pair_id] = self.spread_history[pair_id][-1000:]
        
        # Calculate z-score
        if len(self.spread_history[pair_id]) > 10:
            mean_spread = statistics.mean(self.spread_history[pair_id])
            std_spread = statistics.stdev(self.spread_history[pair_id])
            
            if std_spread > 0:
                z_spread = (spread_pct - mean_spread) / std_spread
            else:
                z_spread = 0
        else:
            z_spread = 0
        
        # Interpretation
        if z_spread >= 1.5:
            interpretation = "⚠️ Spread widening abnormally - Liquidity deteriorating"
        elif z_spread >= 1.0:
            interpretation = "📊 Spread wider than normal"
        elif z_spread <= -1.0:
            interpretation = "✅ Spread tighter than normal - Good liquidity"
        else:
            interpretation = "⚖️ Normal spread"
        
        return {
            'spread': round(spread, 2),
            'spread_pct': round(spread_pct, 4),
            'z_spread': round(z_spread, 4),
            'interpretation': interpretation
        }
    
    def _calculate_cps(self, micro_skew: float, obi_5: float, 
                      z_ofi: float, z_log_dratio: float) -> Dict:
        """
        Calculate Composite Pressure Score (CPS)
        
        CPS = 35% × micro_skew + 25% × OBI5 + 20% × z_OFI + 20% × z_log_dratio
        
        Scaled to [-100, +100]
        """
        # Normalize components to [-1, +1] range
        micro_skew_norm = micro_skew  # Already in [-1, +1]
        obi_5_norm = obi_5  # Already in [-1, +1]
        z_ofi_norm = np.tanh(z_ofi / 2)  # Squash z-score to [-1, +1]
        z_log_dratio_norm = np.tanh(z_log_dratio / 2)  # Squash z-score to [-1, +1]
        
        # Weighted sum
        cps_raw = (0.35 * micro_skew_norm + 
                   0.25 * obi_5_norm + 
                   0.20 * z_ofi_norm + 
                   0.20 * z_log_dratio_norm)
        
        # Scale to [-100, +100]
        cps = cps_raw * 100
        
        # Determine signal
        if cps >= 40:
            signal = 'STRONG_BULLISH'
            interpretation = f"🔥 Strong bullish pressure (CPS={cps:.1f}) - Bias naik kuat"
        elif cps >= 30:
            signal = 'BULLISH'
            interpretation = f"📈 Bullish pressure (CPS={cps:.1f}) - Bias naik"
        elif cps <= -40:
            signal = 'STRONG_BEARISH'
            interpretation = f"❄️ Strong bearish pressure (CPS={cps:.1f}) - Bias turun kuat"
        elif cps <= -30:
            signal = 'BEARISH'
            interpretation = f"📉 Bearish pressure (CPS={cps:.1f}) - Bias turun"
        else:
            signal = 'NEUTRAL'
            interpretation = f"⚖️ Neutral pressure (CPS={cps:.1f})"
        
        return {
            'value': round(cps, 2),
            'signal': signal,
            'interpretation': interpretation,
            'components': {
                'micro_skew_contribution': round(0.35 * micro_skew_norm * 100, 2),
                'obi_5_contribution': round(0.25 * obi_5_norm * 100, 2),
                'z_ofi_contribution': round(0.20 * z_ofi_norm * 100, 2),
                'z_log_dratio_contribution': round(0.20 * z_log_dratio_norm * 100, 2)
            }
        }
    
    def _calculate_sri_placeholder(self, bids: List[Dict], asks: List[Dict], 
                                   mid: float) -> Dict:
        """
        Calculate Stop Risk Index (SRI) - Simplified version
        
        Full implementation would require:
        - Historical stop cluster detection
        - Distance to known stop levels
        
        This is a simplified version based on depth thinness
        """
        # Calculate depth within ±2% of mid (stop zone)
        lower_2pct = mid * 0.98
        upper_2pct = mid * 1.02
        
        depth_bid_2pct = sum(level['qty'] for level in bids if level['price'] >= lower_2pct)
        depth_ask_2pct = sum(level['qty'] for level in asks if level['price'] <= upper_2pct)
        
        # Calculate average depth
        avg_depth_bid = depth_bid_2pct / min(len(bids), 10) if len(bids) > 0 else 0
        avg_depth_ask = depth_ask_2pct / min(len(asks), 10) if len(asks) > 0 else 0
        
        # SRI based on thinness (inverse of depth)
        # Higher SRI = thinner depth = higher cascade risk
        if avg_depth_bid > 0:
            sri_sell = max(0, min(100, 100 - (avg_depth_bid / (avg_depth_bid + 1)) * 100))
        else:
            sri_sell = 100
        
        if avg_depth_ask > 0:
            sri_buy = max(0, min(100, 100 - (avg_depth_ask / (avg_depth_ask + 1)) * 100))
        else:
            sri_buy = 100
        
        # Interpretation
        if sri_sell >= 70:
            sell_interpretation = "⚠️ HIGH RISK - Stop-sell cascade risk"
        elif sri_sell >= 50:
            sell_interpretation = "📊 Medium risk - Watch for stop-sell"
        else:
            sell_interpretation = "✅ Low risk"
        
        if sri_buy >= 70:
            buy_interpretation = "⚠️ HIGH RISK - Stop-buy cascade risk"
        elif sri_buy >= 50:
            buy_interpretation = "📊 Medium risk - Watch for stop-buy"
        else:
            buy_interpretation = "✅ Low risk"
        
        return {
            'sri_buy': round(sri_buy, 2),
            'sri_sell': round(sri_sell, 2),
            'buy_interpretation': buy_interpretation,
            'sell_interpretation': sell_interpretation,
            'note': 'Simplified SRI based on depth thinness'
        }
    
    def _empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            'microprice': {
                'microprice': 0,
                'mid': 0,
                'spread': 0,
                'micro_skew': 0,
                'signal': 'UNKNOWN',
                'interpretation': 'No data'
            },
            'obi': {
                'obi_5': 0,
                'obi_10': 0,
                'obi_20': 0,
                'signal': 'UNKNOWN',
                'interpretation': 'No data'
            },
            'depth_ratio': {
                'depth_bid_1pct': 0,
                'depth_ask_1pct': 0,
                'dratio': 1.0,
                'log_dratio': 0,
                'z_log_dratio': 0,
                'interpretation': 'No data'
            },
            'lvi': {
                'lvi_bid': 0,
                'lvi_ask': 0,
                'bid_interpretation': 'No data',
                'ask_interpretation': 'No data'
            },
            'spread': {
                'spread': 0,
                'spread_pct': 0,
                'z_spread': 0,
                'interpretation': 'No data'
            },
            'cps': {
                'value': 0,
                'signal': 'UNKNOWN',
                'interpretation': 'No data',
                'components': {}
            },
            'sri': {
                'sri_buy': 0,
                'sri_sell': 0,
                'buy_interpretation': 'No data',
                'sell_interpretation': 'No data',
                'note': 'No data'
            },
            'timestamp': datetime.now().isoformat()
        }

