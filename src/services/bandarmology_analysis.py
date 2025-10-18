"""
Bandarmology Analysis Service
Analyzes order book data to detect whale activities and market manipulation
"""
import numpy as np
from typing import Dict, List, Tuple

class BandarmologyAnalysis:
    
    def __init__(self, depth_data: Dict):
        """
        Initialize with order book depth data
        
        Args:
            depth_data: Dictionary with 'buy' and 'sell' arrays
        """
        self.depth_data = depth_data
        self.buy_orders = depth_data.get('buy', [])
        self.sell_orders = depth_data.get('sell', [])
    
    def calculate_order_book_imbalance(self) -> Dict:
        """
        Calculate buy/sell order imbalance ratio
        Higher ratio = more buying pressure
        """
        if not self.buy_orders or not self.sell_orders:
            return {"error": "No order book data"}
        
        # Calculate total volume for top 20 orders on each side
        top_n = min(20, len(self.buy_orders), len(self.sell_orders))
        
        buy_volume = sum([float(order[1]) for order in self.buy_orders[:top_n]])
        sell_volume = sum([float(order[1]) for order in self.sell_orders[:top_n]])
        
        total_volume = buy_volume + sell_volume
        
        if total_volume == 0:
            return {"error": "No volume data"}
        
        # Calculate imbalance ratio
        buy_ratio = (buy_volume / total_volume) * 100
        sell_ratio = (sell_volume / total_volume) * 100
        
        # Determine pressure
        pressure = "NEUTRAL"
        if buy_ratio > 60:
            pressure = "STRONG_BUY"
        elif buy_ratio > 55:
            pressure = "BUY"
        elif sell_ratio > 60:
            pressure = "STRONG_SELL"
        elif sell_ratio > 55:
            pressure = "SELL"
        
        return {
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'buy_ratio': buy_ratio,
            'sell_ratio': sell_ratio,
            'pressure': pressure
        }
    
    def detect_walls(self, threshold_multiplier: float = 3.0) -> Dict:
        """
        Detect buy and sell walls (large orders)
        
        Args:
            threshold_multiplier: How many times larger than average to be considered a wall
        """
        if not self.buy_orders or not self.sell_orders:
            return {"error": "No order book data"}
        
        # Calculate average order size
        buy_volumes = [float(order[1]) for order in self.buy_orders[:50]]
        sell_volumes = [float(order[1]) for order in self.sell_orders[:50]]
        
        avg_buy_volume = np.mean(buy_volumes) if buy_volumes else 0
        avg_sell_volume = np.mean(sell_volumes) if sell_volumes else 0
        
        # Detect walls
        buy_walls = []
        sell_walls = []
        
        for order in self.buy_orders[:20]:
            price, volume = float(order[0]), float(order[1])
            if volume > avg_buy_volume * threshold_multiplier:
                buy_walls.append({
                    'price': price,
                    'volume': volume,
                    'strength': volume / avg_buy_volume
                })
        
        for order in self.sell_orders[:20]:
            price, volume = float(order[0]), float(order[1])
            if volume > avg_sell_volume * threshold_multiplier:
                sell_walls.append({
                    'price': price,
                    'volume': volume,
                    'strength': volume / avg_sell_volume
                })
        
        return {
            'buy_walls': buy_walls,
            'sell_walls': sell_walls,
            'buy_wall_count': len(buy_walls),
            'sell_wall_count': len(sell_walls)
        }
    
    def detect_whale_orders(self, percentile: int = 95) -> Dict:
        """
        Detect whale orders (very large orders in top percentile)
        """
        if not self.buy_orders or not self.sell_orders:
            return {"error": "No order book data"}
        
        # Get all volumes
        all_buy_volumes = [float(order[1]) for order in self.buy_orders]
        all_sell_volumes = [float(order[1]) for order in self.sell_orders]
        
        # Calculate threshold (95th percentile)
        buy_threshold = np.percentile(all_buy_volumes, percentile) if all_buy_volumes else 0
        sell_threshold = np.percentile(all_sell_volumes, percentile) if all_sell_volumes else 0
        
        # Find whale orders
        whale_buy_orders = []
        whale_sell_orders = []
        
        for order in self.buy_orders:
            price, volume = float(order[0]), float(order[1])
            if volume >= buy_threshold:
                whale_buy_orders.append({
                    'price': price,
                    'volume': volume
                })
        
        for order in self.sell_orders:
            price, volume = float(order[0]), float(order[1])
            if volume >= sell_threshold:
                whale_sell_orders.append({
                    'price': price,
                    'volume': volume
                })
        
        return {
            'whale_buy_orders': whale_buy_orders[:10],  # Top 10
            'whale_sell_orders': whale_sell_orders[:10],
            'whale_buy_count': len(whale_buy_orders),
            'whale_sell_count': len(whale_sell_orders),
            'buy_threshold': buy_threshold,
            'sell_threshold': sell_threshold
        }
    
    def calculate_spread(self) -> Dict:
        """Calculate bid-ask spread"""
        if not self.buy_orders or not self.sell_orders:
            return {"error": "No order book data"}
        
        best_bid = float(self.buy_orders[0][0])
        best_ask = float(self.sell_orders[0][0])
        
        spread = best_ask - best_bid
        spread_percentage = (spread / best_bid) * 100
        
        # Determine liquidity
        liquidity = "GOOD"
        if spread_percentage > 1.0:
            liquidity = "POOR"
        elif spread_percentage > 0.5:
            liquidity = "MODERATE"
        
        return {
            'best_bid': best_bid,
            'best_ask': best_ask,
            'spread': spread,
            'spread_percentage': spread_percentage,
            'liquidity': liquidity
        }
    
    def analyze_order_depth(self) -> Dict:
        """Analyze order book depth at different price levels"""
        if not self.buy_orders or not self.sell_orders:
            return {"error": "No order book data"}
        
        # Calculate cumulative volume at different depths
        depths = [5, 10, 20]
        depth_analysis = {}
        
        for depth in depths:
            buy_depth = min(depth, len(self.buy_orders))
            sell_depth = min(depth, len(self.sell_orders))
            
            buy_vol = sum([float(order[1]) for order in self.buy_orders[:buy_depth]])
            sell_vol = sum([float(order[1]) for order in self.sell_orders[:sell_depth]])
            
            depth_analysis[f'depth_{depth}'] = {
                'buy_volume': buy_vol,
                'sell_volume': sell_vol,
                'ratio': (buy_vol / (buy_vol + sell_vol)) * 100 if (buy_vol + sell_vol) > 0 else 50
            }
        
        return depth_analysis
    
    def get_all_analysis(self) -> Dict:
        """Get complete bandarmology analysis"""
        if not self.buy_orders or not self.sell_orders:
            return {"error": "No order book data"}
        
        analysis = {}
        
        # Order book imbalance
        analysis['imbalance'] = self.calculate_order_book_imbalance()
        
        # Walls detection
        analysis['walls'] = self.detect_walls()
        
        # Whale orders
        analysis['whales'] = self.detect_whale_orders()
        
        # Spread
        analysis['spread'] = self.calculate_spread()
        
        # Depth analysis
        analysis['depth'] = self.analyze_order_depth()
        
        return analysis
    
    def get_bandarmology_score(self) -> int:
        """
        Calculate bandarmology score (0-40)
        """
        if not self.buy_orders or not self.sell_orders:
            return 20  # Neutral score
        
        score = 0
        
        # Order book imbalance score (0-15)
        imbalance = self.calculate_order_book_imbalance()
        if not imbalance.get('error'):
            buy_ratio = imbalance.get('buy_ratio', 50)
            if buy_ratio > 65:
                score += 15
            elif buy_ratio > 60:
                score += 12
            elif buy_ratio > 55:
                score += 10
            elif buy_ratio < 35:
                score += 0
            elif buy_ratio < 40:
                score += 3
            elif buy_ratio < 45:
                score += 5
            else:
                score += 7
        
        # Wall strength score (0-15)
        walls = self.detect_walls()
        if not walls.get('error'):
            buy_wall_count = walls.get('buy_wall_count', 0)
            sell_wall_count = walls.get('sell_wall_count', 0)
            
            if buy_wall_count > sell_wall_count:
                score += min(15, buy_wall_count * 3)
            elif sell_wall_count > buy_wall_count:
                score += max(0, 15 - sell_wall_count * 3)
            else:
                score += 7
        
        # Whale activity score (0-10)
        whales = self.detect_whale_orders()
        if not whales.get('error'):
            whale_buy = whales.get('whale_buy_count', 0)
            whale_sell = whales.get('whale_sell_count', 0)
            
            if whale_buy > whale_sell:
                score += 10
            elif whale_sell > whale_buy:
                score += 0
            else:
                score += 5
        
        return min(score, 40)

