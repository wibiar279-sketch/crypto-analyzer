"""
Slippage and Break-even Analysis Service

Calculates:
- Slippage curves for different order sizes
- VWAP (Volume-Weighted Average Price)
- Break-even price considering fees
- Optimal order size recommendations
"""

from typing import Dict, List, Tuple
from datetime import datetime


class SlippageBreakevenService:
    """Service for slippage and break-even analysis"""
    
    # Indodax fees (example - adjust based on actual fees)
    DEFAULT_TAKER_FEE_PCT = 0.30  # 0.30%
    DEFAULT_MAKER_FEE_PCT = 0.00  # 0.00% for maker
    
    def __init__(self, taker_fee_pct: float = None, maker_fee_pct: float = None):
        """
        Initialize with fee percentages
        
        Args:
            taker_fee_pct: Taker fee percentage (e.g., 0.30 for 0.30%)
            maker_fee_pct: Maker fee percentage (e.g., 0.00 for 0.00%)
        """
        self.taker_fee_pct = taker_fee_pct or self.DEFAULT_TAKER_FEE_PCT
        self.maker_fee_pct = maker_fee_pct or self.DEFAULT_MAKER_FEE_PCT
    
    def analyze_order_execution(self, order_book: Dict, ticker: Dict) -> Dict:
        """
        Analyze order execution for various sizes
        
        Args:
            order_book: Order book data (bids, asks)
            ticker: Ticker data for reference price
            
        Returns:
            Dict with slippage curves and recommendations
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
            
            # Get reference price
            best_bid = bids_parsed[0]['price']
            best_ask = asks_parsed[0]['price']
            mid_price = (best_bid + best_ask) / 2
            
            # Calculate total available liquidity
            total_bid_liquidity = sum(level['qty'] for level in bids_parsed)
            total_ask_liquidity = sum(level['qty'] for level in asks_parsed)
            
            # Generate slippage curves
            buy_curves = self._generate_slippage_curve(asks_parsed, 'buy', best_ask, 
                                                       total_ask_liquidity)
            sell_curves = self._generate_slippage_curve(bids_parsed, 'sell', best_bid, 
                                                        total_bid_liquidity)
            
            # Find optimal order sizes
            optimal_buy_size = self._find_optimal_size(buy_curves, threshold_slippage=0.5)
            optimal_sell_size = self._find_optimal_size(sell_curves, threshold_slippage=0.5)
            
            # Calculate break-even prices
            buy_breakeven = self._calculate_breakeven_scenarios(buy_curves, 'buy')
            sell_breakeven = self._calculate_breakeven_scenarios(sell_curves, 'sell')
            
            return {
                'buy_slippage_curve': buy_curves,
                'sell_slippage_curve': sell_curves,
                'optimal_sizes': {
                    'buy': optimal_buy_size,
                    'sell': optimal_sell_size
                },
                'breakeven_analysis': {
                    'buy': buy_breakeven,
                    'sell': sell_breakeven
                },
                'liquidity_summary': {
                    'total_bid_liquidity': round(total_bid_liquidity, 4),
                    'total_ask_liquidity': round(total_ask_liquidity, 4),
                    'best_bid': round(best_bid, 2),
                    'best_ask': round(best_ask, 2),
                    'mid_price': round(mid_price, 2),
                    'spread': round(best_ask - best_bid, 2),
                    'spread_pct': round((best_ask - best_bid) / mid_price * 100, 4)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error analyzing order execution: {e}")
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
    
    def _generate_slippage_curve(self, levels: List[Dict], side: str, 
                                 best_price: float, total_liquidity: float) -> List[Dict]:
        """
        Generate slippage curve for different order sizes
        
        Args:
            levels: Order book levels (sorted)
            side: 'buy' or 'sell'
            best_price: Best available price
            total_liquidity: Total available liquidity
            
        Returns:
            List of dicts with order size, VWAP, slippage, etc.
        """
        curves = []
        
        # Define order sizes to test (as percentage of total liquidity)
        size_percentages = [0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
        
        for pct in size_percentages:
            order_size = total_liquidity * pct
            
            if order_size <= 0:
                continue
            
            # Calculate VWAP and slippage
            result = self._calculate_vwap_slippage(levels, order_size, best_price, side)
            
            if result:
                # Calculate break-even
                if side == 'buy':
                    breakeven_price = self._calculate_breakeven(
                        result['vwap'], 
                        self.taker_fee_pct, 
                        self.taker_fee_pct
                    )
                else:  # sell
                    # For sell, we need to calculate what buy price would break even
                    # if we sell at this VWAP
                    breakeven_price = self._calculate_breakeven_reverse(
                        result['vwap'],
                        self.taker_fee_pct,
                        self.taker_fee_pct
                    )
                
                curves.append({
                    'order_size': round(order_size, 4),
                    'order_size_pct': round(pct * 100, 2),
                    'vwap': round(result['vwap'], 2),
                    'slippage_pct': round(result['slippage_pct'], 4),
                    'total_cost': round(result['total_cost'], 2),
                    'levels_consumed': result['levels_consumed'],
                    'breakeven_price': round(breakeven_price, 2),
                    'profit_needed_pct': round((breakeven_price / result['vwap'] - 1) * 100, 4) if side == 'buy' else round((result['vwap'] / breakeven_price - 1) * 100, 4)
                })
        
        return curves
    
    def _calculate_vwap_slippage(self, levels: List[Dict], order_size: float, 
                                 best_price: float, side: str) -> Dict:
        """
        Calculate VWAP and slippage for given order size
        
        Args:
            levels: Order book levels
            order_size: Size of order to execute
            best_price: Best available price
            side: 'buy' or 'sell'
            
        Returns:
            Dict with VWAP, slippage, etc. or None if insufficient liquidity
        """
        remaining = order_size
        total_cost = 0
        levels_consumed = 0
        
        for level in levels:
            if remaining <= 0:
                break
            
            executed = min(remaining, level['qty'])
            total_cost += executed * level['price']
            remaining -= executed
            levels_consumed += 1
        
        # Check if order can be fully executed
        if remaining > 0:
            # Insufficient liquidity
            return None
        
        # Calculate VWAP
        vwap = total_cost / order_size
        
        # Calculate slippage
        slippage_pct = (vwap / best_price - 1) * 100
        
        return {
            'vwap': vwap,
            'slippage_pct': slippage_pct,
            'total_cost': total_cost,
            'levels_consumed': levels_consumed
        }
    
    def _calculate_breakeven(self, buy_vwap: float, fee_buy_pct: float, 
                            fee_sell_pct: float) -> float:
        """
        Calculate break-even sell price
        
        Args:
            buy_vwap: Average buy price (VWAP)
            fee_buy_pct: Buy fee percentage (e.g., 0.30 for 0.30%)
            fee_sell_pct: Sell fee percentage (e.g., 0.30 for 0.30%)
            
        Returns:
            Break-even sell price
        """
        alpha = fee_buy_pct / 100  # Convert to decimal
        beta = fee_sell_pct / 100
        
        # Total cost including buy fee
        cost_per_unit = buy_vwap * (1 + alpha)
        
        # Break-even sell price (after sell fee)
        breakeven_price = cost_per_unit / (1 - beta)
        
        return breakeven_price
    
    def _calculate_breakeven_reverse(self, sell_vwap: float, fee_buy_pct: float,
                                    fee_sell_pct: float) -> float:
        """
        Calculate what buy price would break even if selling at sell_vwap
        
        Args:
            sell_vwap: Average sell price (VWAP)
            fee_buy_pct: Buy fee percentage
            fee_sell_pct: Sell fee percentage
            
        Returns:
            Maximum buy price to break even
        """
        alpha = fee_buy_pct / 100
        beta = fee_sell_pct / 100
        
        # Revenue after sell fee
        revenue_per_unit = sell_vwap * (1 - beta)
        
        # Maximum buy price (before buy fee)
        max_buy_price = revenue_per_unit / (1 + alpha)
        
        return max_buy_price
    
    def _find_optimal_size(self, curves: List[Dict], threshold_slippage: float = 0.5) -> Dict:
        """
        Find optimal order size based on slippage threshold
        
        Args:
            curves: Slippage curve data
            threshold_slippage: Maximum acceptable slippage percentage
            
        Returns:
            Dict with optimal size recommendation
        """
        if not curves:
            return {
                'recommended_size': 0,
                'slippage_pct': 0,
                'interpretation': 'No data available'
            }
        
        # Find largest size with slippage below threshold
        optimal = None
        
        for curve in curves:
            if abs(curve['slippage_pct']) <= threshold_slippage:
                optimal = curve
            else:
                break  # Slippage exceeded threshold
        
        if optimal:
            return {
                'recommended_size': optimal['order_size'],
                'recommended_size_pct': optimal['order_size_pct'],
                'slippage_pct': optimal['slippage_pct'],
                'vwap': optimal['vwap'],
                'interpretation': f"✅ Optimal size: {optimal['order_size']:.4f} ({optimal['order_size_pct']:.1f}% of liquidity) with {optimal['slippage_pct']:.2f}% slippage"
            }
        else:
            # Even smallest size exceeds threshold
            smallest = curves[0]
            return {
                'recommended_size': smallest['order_size'],
                'recommended_size_pct': smallest['order_size_pct'],
                'slippage_pct': smallest['slippage_pct'],
                'vwap': smallest['vwap'],
                'interpretation': f"⚠️ High slippage warning: Even smallest size ({smallest['order_size_pct']:.1f}%) has {smallest['slippage_pct']:.2f}% slippage"
            }
    
    def _calculate_breakeven_scenarios(self, curves: List[Dict], side: str) -> List[Dict]:
        """
        Calculate break-even scenarios for different order sizes
        
        Args:
            curves: Slippage curve data
            side: 'buy' or 'sell'
            
        Returns:
            List of break-even scenarios
        """
        scenarios = []
        
        for curve in curves:
            if side == 'buy':
                interpretation = f"Need {curve['profit_needed_pct']:.2f}% profit to break even"
            else:  # sell
                interpretation = f"Can buy up to {curve['breakeven_price']:.2f} to break even"
            
            scenarios.append({
                'order_size': curve['order_size'],
                'order_size_pct': curve['order_size_pct'],
                'vwap': curve['vwap'],
                'breakeven_price': curve['breakeven_price'],
                'profit_needed_pct': curve['profit_needed_pct'],
                'interpretation': interpretation
            })
        
        return scenarios
    
    def _empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            'buy_slippage_curve': [],
            'sell_slippage_curve': [],
            'optimal_sizes': {
                'buy': {
                    'recommended_size': 0,
                    'slippage_pct': 0,
                    'interpretation': 'No data'
                },
                'sell': {
                    'recommended_size': 0,
                    'slippage_pct': 0,
                    'interpretation': 'No data'
                }
            },
            'breakeven_analysis': {
                'buy': [],
                'sell': []
            },
            'liquidity_summary': {
                'total_bid_liquidity': 0,
                'total_ask_liquidity': 0,
                'best_bid': 0,
                'best_ask': 0,
                'mid_price': 0,
                'spread': 0,
                'spread_pct': 0
            },
            'timestamp': datetime.now().isoformat()
        }

