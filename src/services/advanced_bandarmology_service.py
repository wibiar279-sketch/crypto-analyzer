"""
Advanced Bandarmology Analysis Service
Deteksi fake orders, whale activity, market maker patterns, dan manipulation score
"""

import numpy as np
from typing import Dict, List, Tuple
from collections import Counter

class AdvancedBandarmologyService:
    
    def __init__(self):
        self.fake_order_threshold = 70  # Score threshold untuk fake order
        self.whale_percentile = 95  # Top 5% = whale
        
    def analyze_order_book_advanced(self, order_book: Dict, current_price: float) -> Dict:
        """
        Analisa order book secara mendalam untuk deteksi manipulation
        """
        try:
            bids = order_book.get('buy', [])
            asks = order_book.get('sell', [])
            
            # Convert to standard format
            all_orders = []
            for bid in bids[:50]:  # Top 50 bids
                all_orders.append({
                    'price': float(bid[0]),
                    'amount': float(bid[1]),
                    'total': float(bid[0]) * float(bid[1]),
                    'side': 'buy'
                })
            
            for ask in asks[:50]:  # Top 50 asks
                all_orders.append({
                    'price': float(ask[0]),
                    'amount': float(ask[1]),
                    'total': float(ask[0]) * float(ask[1]),
                    'side': 'sell'
                })
            
            # Run all analysis
            fake_order_analysis = self.detect_fake_orders(all_orders, current_price)
            whale_analysis = self.detect_whale_activity(all_orders)
            market_maker_analysis = self.analyze_market_makers(all_orders, current_price)
            manipulation_score = self.calculate_manipulation_score(
                fake_order_analysis,
                whale_analysis,
                market_maker_analysis
            )
            order_authenticity = self.classify_order_authenticity(all_orders, current_price)
            real_order_direction = self.calculate_real_order_direction(all_orders, order_authenticity)
            
            return {
                'fake_order_detection': fake_order_analysis,
                'whale_activity': whale_analysis,
                'market_maker_analysis': market_maker_analysis,
                'manipulation_score': manipulation_score,
                'order_authenticity': order_authenticity,
                'real_order_direction': real_order_direction,
                'summary': self.generate_summary(
                    fake_order_analysis,
                    whale_analysis,
                    manipulation_score,
                    real_order_direction
                )
            }
        except Exception as e:
            return self._get_error_response(str(e))
    
    def detect_fake_orders(self, orders: List[Dict], current_price: float) -> Dict:
        """
        Deteksi fake orders berdasarkan multiple indicators
        """
        fake_orders = []
        suspicious_orders = []
        
        # Calculate average order size
        order_sizes = [o['amount'] for o in orders]
        avg_size = np.mean(order_sizes)
        std_size = np.std(order_sizes)
        
        for order in orders:
            score = self._calculate_fake_order_score(order, current_price, avg_size, std_size)
            
            if score >= 70:
                fake_orders.append({
                    **order,
                    'fake_score': score,
                    'reasons': self._get_fake_reasons(order, current_price, avg_size)
                })
            elif score >= 40:
                suspicious_orders.append({
                    **order,
                    'suspicious_score': score
                })
        
        total_orders = len(orders)
        fake_buy = [o for o in fake_orders if o['side'] == 'buy']
        fake_sell = [o for o in fake_orders if o['side'] == 'sell']
        
        return {
            'total_fake_orders': len(fake_orders),
            'fake_buy_orders': len(fake_buy),
            'fake_sell_orders': len(fake_sell),
            'fake_buy_volume': sum([o['amount'] for o in fake_buy]),
            'fake_sell_volume': sum([o['amount'] for o in fake_sell]),
            'fake_order_percentage': (len(fake_orders) / total_orders * 100) if total_orders > 0 else 0,
            'suspicious_orders': len(suspicious_orders),
            'top_fake_orders': sorted(fake_orders, key=lambda x: x['fake_score'], reverse=True)[:5]
        }
    
    def _calculate_fake_order_score(self, order: Dict, current_price: float, avg_size: float, std_size: float) -> float:
        """
        Calculate fake order score (0-100)
        Higher score = more likely fake
        """
        score = 0
        
        # Factor 1: Unusually large size (max 30 points)
        if order['amount'] > avg_size + 3 * std_size:
            score += 30
        elif order['amount'] > avg_size + 2 * std_size:
            score += 20
        elif order['amount'] > avg_size + std_size:
            score += 10
        
        # Factor 2: Distance from current price (max 25 points)
        distance_pct = abs(order['price'] - current_price) / current_price * 100
        if distance_pct > 5:  # More than 5% away
            score += 25
        elif distance_pct > 3:
            score += 15
        elif distance_pct > 2:
            score += 10
        
        # Factor 3: Round number psychology (max 15 points)
        # Fake orders often at round numbers
        if self._is_round_number(order['price']):
            score += 15
        
        # Factor 4: Uniform size pattern (max 20 points)
        # Check if multiple orders have same size (spoofing pattern)
        # This would require tracking all orders, simplified here
        if order['amount'] == round(order['amount']):  # Whole numbers suspicious
            score += 10
        
        # Factor 5: Extreme total value (max 10 points)
        # Very large total value in single order
        if order['total'] > avg_size * current_price * 5:
            score += 10
        
        return min(score, 100)
    
    def _is_round_number(self, price: float) -> bool:
        """Check if price is a round number"""
        # Check if price ends in 000, 500, etc.
        price_str = str(int(price))
        if len(price_str) >= 3:
            last_three = price_str[-3:]
            if last_three == '000' or last_three == '500':
                return True
        return False
    
    def _get_fake_reasons(self, order: Dict, current_price: float, avg_size: float) -> List[str]:
        """Get human-readable reasons why order is flagged as fake"""
        reasons = []
        
        if order['amount'] > avg_size * 3:
            reasons.append(f"Unusually large size ({order['amount']:.2f}x average)")
        
        distance_pct = abs(order['price'] - current_price) / current_price * 100
        if distance_pct > 3:
            reasons.append(f"Far from current price ({distance_pct:.1f}% away)")
        
        if self._is_round_number(order['price']):
            reasons.append("Placed at round number (psychological level)")
        
        return reasons
    
    def detect_whale_activity(self, orders: List[Dict]) -> Dict:
        """
        Detect whale orders (top 5% by size)
        """
        if not orders:
            return self._get_empty_whale_response()
        
        order_amounts = [o['amount'] for o in orders]
        whale_threshold = np.percentile(order_amounts, self.whale_percentile)
        
        whale_orders = [o for o in orders if o['amount'] >= whale_threshold]
        whale_buy = [o for o in whale_orders if o['side'] == 'buy']
        whale_sell = [o for o in whale_orders if o['side'] == 'sell']
        
        total_volume = sum(order_amounts)
        whale_volume = sum([o['amount'] for o in whale_orders])
        whale_dominance = (whale_volume / total_volume * 100) if total_volume > 0 else 0
        
        # Whale pressure analysis
        whale_buy_volume = sum([o['amount'] for o in whale_buy])
        whale_sell_volume = sum([o['amount'] for o in whale_sell])
        whale_pressure = "BULLISH" if whale_buy_volume > whale_sell_volume * 1.2 else \
                        "BEARISH" if whale_sell_volume > whale_buy_volume * 1.2 else "NEUTRAL"
        
        return {
            'whale_threshold': whale_threshold,
            'total_whale_orders': len(whale_orders),
            'whale_buy_orders': len(whale_buy),
            'whale_sell_orders': len(whale_sell),
            'whale_buy_volume': whale_buy_volume,
            'whale_sell_volume': whale_sell_volume,
            'whale_dominance': whale_dominance,
            'whale_pressure': whale_pressure,
            'whale_activity_level': self._get_whale_activity_level(whale_dominance),
            'top_whale_orders': sorted(whale_orders, key=lambda x: x['amount'], reverse=True)[:3]
        }
    
    def _get_whale_activity_level(self, dominance: float) -> str:
        """Classify whale activity level"""
        if dominance >= 50:
            return "VERY_HIGH"
        elif dominance >= 35:
            return "HIGH"
        elif dominance >= 20:
            return "MEDIUM"
        else:
            return "LOW"
    
    def analyze_market_makers(self, orders: List[Dict], current_price: float) -> Dict:
        """
        Analyze market maker behavior
        """
        buy_orders = [o for o in orders if o['side'] == 'buy']
        sell_orders = [o for o in orders if o['side'] == 'sell']
        
        if not buy_orders or not sell_orders:
            return self._get_empty_mm_response()
        
        # Calculate spread
        best_bid = max([o['price'] for o in buy_orders])
        best_ask = min([o['price'] for o in sell_orders])
        spread = best_ask - best_bid
        spread_pct = (spread / current_price * 100) if current_price > 0 else 0
        
        # Volume symmetry (legitimate MM have balanced volumes)
        buy_volume = sum([o['amount'] for o in buy_orders])
        sell_volume = sum([o['amount'] for o in sell_orders])
        symmetry_ratio = min(buy_volume, sell_volume) / max(buy_volume, sell_volume) if max(buy_volume, sell_volume) > 0 else 0
        
        # Spread consistency
        spread_status = "TIGHT" if spread_pct < 0.5 else \
                       "NORMAL" if spread_pct < 1.0 else \
                       "WIDE" if spread_pct < 2.0 else "VERY_WIDE"
        
        # Market maker classification
        if symmetry_ratio > 0.8 and spread_pct < 1.0:
            mm_behavior = "LEGITIMATE"
        elif symmetry_ratio < 0.5 or spread_pct > 2.0:
            mm_behavior = "SUSPICIOUS"
        else:
            mm_behavior = "NORMAL"
        
        return {
            'best_bid': best_bid,
            'best_ask': best_ask,
            'spread': spread,
            'spread_percentage': spread_pct,
            'spread_status': spread_status,
            'volume_symmetry': symmetry_ratio,
            'market_maker_behavior': mm_behavior,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume
        }
    
    def calculate_manipulation_score(self, fake_analysis: Dict, whale_analysis: Dict, mm_analysis: Dict) -> Dict:
        """
        Calculate overall manipulation score (0-100)
        Higher = more manipulation detected
        """
        score = 0
        factors = []
        
        # Factor 1: Fake order percentage (max 40 points)
        fake_pct = fake_analysis.get('fake_order_percentage', 0)
        fake_score = min(fake_pct * 2, 40)
        score += fake_score
        if fake_score > 0:
            factors.append(f"Fake orders: {fake_pct:.1f}%")
        
        # Factor 2: Whale dominance (max 30 points)
        whale_dom = whale_analysis.get('whale_dominance', 0)
        whale_score = min(whale_dom * 0.6, 30)
        score += whale_score
        if whale_score > 15:
            factors.append(f"High whale dominance: {whale_dom:.1f}%")
        
        # Factor 3: Market maker behavior (max 30 points)
        mm_behavior = mm_analysis.get('market_maker_behavior', 'NORMAL')
        if mm_behavior == 'SUSPICIOUS':
            mm_score = 30
            factors.append("Suspicious market maker activity")
        elif mm_behavior == 'NORMAL':
            mm_score = 10
        else:
            mm_score = 0
        score += mm_score
        
        # Determine level and confidence
        level = self._get_manipulation_level(score)
        confidence = self._calculate_confidence(fake_analysis, whale_analysis)
        
        return {
            'score': min(score, 100),
            'level': level,
            'confidence': confidence,
            'factors': factors,
            'interpretation': self._get_manipulation_interpretation(level)
        }
    
    def _get_manipulation_level(self, score: float) -> str:
        """Classify manipulation level"""
        if score >= 75:
            return "VERY_HIGH"
        elif score >= 50:
            return "HIGH"
        elif score >= 30:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_confidence(self, fake_analysis: Dict, whale_analysis: Dict) -> str:
        """Calculate confidence in manipulation detection"""
        # More data points = higher confidence
        total_orders = fake_analysis.get('total_fake_orders', 0) + fake_analysis.get('suspicious_orders', 0)
        
        if total_orders >= 10:
            return "HIGH"
        elif total_orders >= 5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_manipulation_interpretation(self, level: str) -> str:
        """Get human-readable interpretation"""
        interpretations = {
            "VERY_HIGH": "Sangat tinggi kemungkinan manipulasi. Hati-hati dengan order book, banyak fake orders terdeteksi.",
            "HIGH": "Tinggi kemungkinan manipulasi. Perhatikan pergerakan harga dengan seksama.",
            "MEDIUM": "Sedang kemungkinan manipulasi. Beberapa aktivitas mencurigakan terdeteksi.",
            "LOW": "Rendah kemungkinan manipulasi. Order book terlihat relatif natural."
        }
        return interpretations.get(level, "Unknown")
    
    def classify_order_authenticity(self, orders: List[Dict], current_price: float) -> Dict:
        """
        Classify each order as REAL, SUSPICIOUS, or FAKE
        """
        order_sizes = [o['amount'] for o in orders]
        avg_size = np.mean(order_sizes)
        std_size = np.std(order_sizes)
        
        real_orders = []
        suspicious_orders = []
        fake_orders = []
        
        for order in orders:
            score = self._calculate_fake_order_score(order, current_price, avg_size, std_size)
            
            if score >= 70:
                fake_orders.append(order)
            elif score >= 40:
                suspicious_orders.append(order)
            else:
                real_orders.append(order)
        
        total = len(orders)
        
        return {
            'real_orders': len(real_orders),
            'suspicious_orders': len(suspicious_orders),
            'fake_orders': len(fake_orders),
            'real_percentage': (len(real_orders) / total * 100) if total > 0 else 0,
            'suspicious_percentage': (len(suspicious_orders) / total * 100) if total > 0 else 0,
            'fake_percentage': (len(fake_orders) / total * 100) if total > 0 else 0,
            'real_buy_orders': len([o for o in real_orders if o['side'] == 'buy']),
            'real_sell_orders': len([o for o in real_orders if o['side'] == 'sell'])
        }
    
    def calculate_real_order_direction(self, orders: List[Dict], authenticity: Dict) -> Dict:
        """
        Calculate price direction based on REAL orders only (excluding fake orders)
        """
        order_sizes = [o['amount'] for o in orders]
        avg_size = np.mean(order_sizes)
        std_size = np.std(order_sizes)
        
        # Filter to get only real orders (score < 40)
        real_orders = []
        for order in orders:
            score = self._calculate_fake_order_score(order, 0, avg_size, std_size)  # price doesn't matter for filtering
            if score < 40:
                real_orders.append(order)
        
        if not real_orders:
            return self._get_empty_direction_response()
        
        # Calculate pressure from real orders only
        real_buy_volume = sum([o['amount'] for o in real_orders if o['side'] == 'buy'])
        real_sell_volume = sum([o['amount'] for o in real_orders if o['side'] == 'sell'])
        
        total_real_volume = real_buy_volume + real_sell_volume
        buy_pressure_pct = (real_buy_volume / total_real_volume * 100) if total_real_volume > 0 else 50
        sell_pressure_pct = (real_sell_volume / total_real_volume * 100) if total_real_volume > 0 else 50
        
        # Determine direction
        if buy_pressure_pct > 55:
            direction = "BULLISH"
            confidence = "HIGH" if buy_pressure_pct > 65 else "MEDIUM"
        elif sell_pressure_pct > 55:
            direction = "BEARISH"
            confidence = "HIGH" if sell_pressure_pct > 65 else "MEDIUM"
        else:
            direction = "NEUTRAL"
            confidence = "MEDIUM"
        
        return {
            'direction': direction,
            'confidence': confidence,
            'buy_pressure': buy_pressure_pct,
            'sell_pressure': sell_pressure_pct,
            'real_buy_volume': real_buy_volume,
            'real_sell_volume': real_sell_volume,
            'interpretation': self._get_direction_interpretation(direction, buy_pressure_pct, sell_pressure_pct)
        }
    
    def _get_direction_interpretation(self, direction: str, buy_pct: float, sell_pct: float) -> str:
        """Get human-readable direction interpretation"""
        if direction == "BULLISH":
            return f"Tekanan beli lebih kuat ({buy_pct:.1f}% vs {sell_pct:.1f}%). Kemungkinan harga naik."
        elif direction == "BEARISH":
            return f"Tekanan jual lebih kuat ({sell_pct:.1f}% vs {buy_pct:.1f}%). Kemungkinan harga turun."
        else:
            return f"Tekanan seimbang ({buy_pct:.1f}% vs {sell_pct:.1f}%). Arah belum jelas."
    
    def generate_summary(self, fake_analysis: Dict, whale_analysis: Dict, 
                        manipulation_score: Dict, direction: Dict) -> Dict:
        """
        Generate executive summary for dashboard
        """
        # Overall assessment
        manip_level = manipulation_score.get('level', 'UNKNOWN')
        whale_level = whale_analysis.get('whale_activity_level', 'UNKNOWN')
        direction_signal = direction.get('direction', 'NEUTRAL')
        
        # Risk level
        if manip_level in ['VERY_HIGH', 'HIGH']:
            risk = "HIGH"
        elif manip_level == 'MEDIUM' or whale_level in ['VERY_HIGH', 'HIGH']:
            risk = "MEDIUM"
        else:
            risk = "LOW"
        
        # Trading recommendation based on manipulation
        if manip_level == 'VERY_HIGH':
            recommendation = "AVOID"
            reason = "Manipulasi sangat tinggi, hindari trading"
        elif manip_level == 'HIGH':
            recommendation = "CAUTION"
            reason = "Manipulasi tinggi, trading dengan hati-hati"
        elif direction_signal == "BULLISH":
            recommendation = "CONSIDER_BUY"
            reason = "Tekanan beli kuat dari real orders"
        elif direction_signal == "BEARISH":
            recommendation = "CONSIDER_SELL"
            reason = "Tekanan jual kuat dari real orders"
        else:
            recommendation = "HOLD"
            reason = "Sinyal tidak jelas, tunggu konfirmasi"
        
        return {
            'manipulation_level': manip_level,
            'whale_activity': whale_level,
            'direction': direction_signal,
            'risk_level': risk,
            'recommendation': recommendation,
            'reason': reason,
            'fake_order_pct': fake_analysis.get('fake_order_percentage', 0),
            'whale_dominance': whale_analysis.get('whale_dominance', 0),
            'real_order_direction': direction_signal
        }
    
    # Helper methods for empty responses
    def _get_error_response(self, error: str) -> Dict:
        return {
            'error': error,
            'fake_order_detection': {},
            'whale_activity': {},
            'market_maker_analysis': {},
            'manipulation_score': {'score': 0, 'level': 'UNKNOWN'},
            'order_authenticity': {},
            'real_order_direction': {},
            'summary': {}
        }
    
    def _get_empty_whale_response(self) -> Dict:
        return {
            'whale_threshold': 0,
            'total_whale_orders': 0,
            'whale_buy_orders': 0,
            'whale_sell_orders': 0,
            'whale_buy_volume': 0,
            'whale_sell_volume': 0,
            'whale_dominance': 0,
            'whale_pressure': 'NEUTRAL',
            'whale_activity_level': 'LOW',
            'top_whale_orders': []
        }
    
    def _get_empty_mm_response(self) -> Dict:
        return {
            'best_bid': 0,
            'best_ask': 0,
            'spread': 0,
            'spread_percentage': 0,
            'spread_status': 'UNKNOWN',
            'volume_symmetry': 0,
            'market_maker_behavior': 'UNKNOWN',
            'buy_volume': 0,
            'sell_volume': 0
        }
    
    def _get_empty_direction_response(self) -> Dict:
        return {
            'direction': 'NEUTRAL',
            'confidence': 'LOW',
            'buy_pressure': 50,
            'sell_pressure': 50,
            'real_buy_volume': 0,
            'real_sell_volume': 0,
            'interpretation': 'Tidak ada data untuk analisa'
        }

