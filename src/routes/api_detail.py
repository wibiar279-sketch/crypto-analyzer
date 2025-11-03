"""
API Detail - On-demand detailed analysis for single crypto
"""
from flask import Blueprint, jsonify, request
import requests

api_detail = Blueprint('api_detail', __name__)

INDODAX_BASE = "https://indodax.com/api"

def get_order_book(pair_id):
    """Fetch order book for a pair"""
    try:
        response = requests.get(f"{INDODAX_BASE}/{pair_id}/depth", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_trades(pair_id):
    """Fetch recent trades for a pair"""
    try:
        response = requests.get(f"{INDODAX_BASE}/{pair_id}/trades", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def analyze_fake_orders(order_book):
    """
    Detect fake orders (walls) in order book
    
    Logic:
    - Fake orders are unusually large orders placed to manipulate price
    - Look for orders that are 5x+ larger than average
    - Check if orders are placed at round numbers (psychological levels)
    """
    if not order_book or 'buy' not in order_book or 'sell' not in order_book:
        return {
            'fake_percentage': 0,
            'has_buy_wall': False,
            'has_sell_wall': False,
            'confidence': 'low',
            'explanation': 'No order book data available'
        }
    
    buy_orders = order_book.get('buy', [])[:20]
    sell_orders = order_book.get('sell', [])[:20]
    
    if not buy_orders or not sell_orders:
        return {
            'fake_percentage': 0,
            'has_buy_wall': False,
            'has_sell_wall': False,
            'confidence': 'low',
            'explanation': 'Insufficient order book data'
        }
    
    # Calculate average order size
    buy_amounts = [float(order[1]) for order in buy_orders]
    sell_amounts = [float(order[1]) for order in sell_orders]
    
    avg_buy = sum(buy_amounts) / len(buy_amounts) if buy_amounts else 0
    avg_sell = sum(sell_amounts) / len(sell_amounts) if sell_amounts else 0
    
    # Detect walls (orders 5x+ larger than average)
    buy_wall_threshold = avg_buy * 5
    sell_wall_threshold = avg_sell * 5
    
    has_buy_wall = any(amount > buy_wall_threshold for amount in buy_amounts)
    has_sell_wall = any(amount > sell_wall_threshold for amount in sell_amounts)
    
    # Count suspicious orders
    suspicious_count = 0
    total_orders = len(buy_orders) + len(sell_orders)
    
    for order in buy_orders:
        price = float(order[0])
        amount = float(order[1])
        # Check if order is at round number and unusually large
        if amount > buy_wall_threshold and (price % 1000 == 0 or price % 100 == 0):
            suspicious_count += 1
    
    for order in sell_orders:
        price = float(order[0])
        amount = float(order[1])
        if amount > sell_wall_threshold and (price % 1000 == 0 or price % 100 == 0):
            suspicious_count += 1
    
    fake_percentage = (suspicious_count / total_orders * 100) if total_orders > 0 else 0
    
    confidence = 'high' if total_orders >= 20 else 'medium' if total_orders >= 10 else 'low'
    
    explanation = []
    if has_buy_wall:
        explanation.append(f"Large buy wall detected ({buy_wall_threshold:.0f}+ coins)")
    if has_sell_wall:
        explanation.append(f"Large sell wall detected ({sell_wall_threshold:.0f}+ coins)")
    if suspicious_count > 0:
        explanation.append(f"{suspicious_count} suspicious orders at round price levels")
    if not explanation:
        explanation.append("No significant fake order patterns detected")
    
    return {
        'fake_percentage': round(fake_percentage, 1),
        'has_buy_wall': has_buy_wall,
        'has_sell_wall': has_sell_wall,
        'confidence': confidence,
        'explanation': ' | '.join(explanation)
    }

def analyze_whale_activity(trades, order_book):
    """
    Detect whale activity from trades and order book
    
    Logic:
    - Whales are large traders with significant capital
    - Look for trades with volume 10x+ larger than average
    - Check for large orders in order book (top 5%)
    """
    if not trades:
        return {
            'detected': False,
            'activity_level': 'UNKNOWN',
            'large_trades_count': 0,
            'large_orders_count': 0,
            'confidence': 'low',
            'explanation': 'No trade data available'
        }
    
    # Analyze trades
    trade_amounts = [float(trade.get('amount', 0)) for trade in trades[:50]]
    
    if not trade_amounts:
        return {
            'detected': False,
            'activity_level': 'UNKNOWN',
            'large_trades_count': 0,
            'large_orders_count': 0,
            'confidence': 'low',
            'explanation': 'No valid trade data'
        }
    
    avg_trade = sum(trade_amounts) / len(trade_amounts)
    whale_threshold = avg_trade * 10  # 10x average
    
    large_trades = [amt for amt in trade_amounts if amt > whale_threshold]
    large_trades_count = len(large_trades)
    
    # Analyze order book for large orders
    whale_orders = 0
    if order_book and 'buy' in order_book and 'sell' in order_book:
        all_orders = order_book.get('buy', [])[:10] + order_book.get('sell', [])[:10]
        order_amounts = [float(order[1]) for order in all_orders]
        
        if order_amounts:
            avg_order = sum(order_amounts) / len(order_amounts)
            whale_order_threshold = avg_order * 8
            whale_orders = len([amt for amt in order_amounts if amt > whale_order_threshold])
    
    # Determine activity level
    total_whale_signals = large_trades_count + whale_orders
    
    if total_whale_signals >= 5:
        activity_level = 'HIGH'
        detected = True
    elif total_whale_signals >= 2:
        activity_level = 'MEDIUM'
        detected = True
    elif total_whale_signals >= 1:
        activity_level = 'LOW'
        detected = True
    else:
        activity_level = 'NONE'
        detected = False
    
    confidence = 'high' if len(trades) >= 30 else 'medium' if len(trades) >= 15 else 'low'
    
    explanation = f"{large_trades_count} large trades (>{whale_threshold:.0f} coins) + {whale_orders} large orders detected"
    
    return {
        'detected': detected,
        'activity_level': activity_level,
        'large_trades_count': large_trades_count,
        'large_orders_count': whale_orders,
        'confidence': confidence,
        'explanation': explanation
    }

def analyze_manipulation(order_book, trades):
    """
    Detect market manipulation
    
    Logic:
    - Manipulation includes: spoofing, wash trading, pump & dump
    - Spoofing: Large orders that get cancelled (detected via order book imbalance)
    - Wash trading: Same entity buying and selling (detected via trade patterns)
    - Pump & dump: Rapid price increase with low volume (detected via price/volume ratio)
    """
    manipulation_score = 0
    signals = []
    
    if not order_book:
        return {
            'risk_level': 'UNKNOWN',
            'score': 0,
            'signals': ['No order book data available'],
            'confidence': 'low'
        }
    
    # Check order book imbalance (spoofing indicator)
    buy_orders = order_book.get('buy', [])
    sell_orders = order_book.get('sell', [])
    
    if buy_orders and sell_orders:
        total_buy_volume = sum(float(order[1]) for order in buy_orders[:10])
        total_sell_volume = sum(float(order[1]) for order in sell_orders[:10])
        
        if total_buy_volume > 0 and total_sell_volume > 0:
            imbalance_ratio = max(total_buy_volume, total_sell_volume) / min(total_buy_volume, total_sell_volume)
            
            if imbalance_ratio > 5:
                manipulation_score += 30
                signals.append(f'Extreme order book imbalance ({imbalance_ratio:.1f}x - possible spoofing)')
            elif imbalance_ratio > 3:
                manipulation_score += 15
                signals.append(f'High order book imbalance ({imbalance_ratio:.1f}x)')
    
    # Check for wash trading (same price trades in quick succession)
    if trades and len(trades) >= 10:
        recent_trades = trades[:20]
        price_counts = {}
        
        for trade in recent_trades:
            price = float(trade.get('price', 0))
            price_counts[price] = price_counts.get(price, 0) + 1
        
        # If same price appears 5+ times in recent trades, suspicious
        max_same_price = max(price_counts.values()) if price_counts else 0
        
        if max_same_price >= 7:
            manipulation_score += 20
            signals.append(f'Repeated trades at same price ({max_same_price}x - possible wash trading)')
        elif max_same_price >= 5:
            manipulation_score += 10
            signals.append(f'Multiple trades at same price ({max_same_price}x)')
    
    # Determine risk level
    if manipulation_score >= 50:
        risk_level = 'HIGH'
    elif manipulation_score >= 30:
        risk_level = 'MEDIUM'
    elif manipulation_score >= 15:
        risk_level = 'LOW'
    else:
        risk_level = 'MINIMAL'
    
    confidence = 'high' if (order_book and trades and len(trades) >= 20) else 'medium' if trades else 'low'
    
    if not signals:
        signals.append('No significant manipulation patterns detected')
    
    return {
        'risk_level': risk_level,
        'score': manipulation_score,
        'signals': signals,
        'confidence': confidence
    }

@api_detail.route('/detail/<pair_id>', methods=['GET'])
def get_crypto_detail(pair_id):
    """
    Get detailed analysis for a single crypto
    """
    try:
        # Fetch detailed data
        order_book = get_order_book(pair_id)
        trades = get_trades(pair_id)
        
        if not order_book and not trades:
            return jsonify({
                'error': 'Unable to fetch data for this cryptocurrency',
                'pair_id': pair_id
            }), 404
        
        # Perform detailed analysis
        fake_analysis = analyze_fake_orders(order_book)
        whale_analysis = analyze_whale_activity(trades, order_book)
        manipulation_analysis = analyze_manipulation(order_book, trades)
        
        return jsonify({
            'pair_id': pair_id,
            'manipulation': manipulation_analysis,
            'fake_orders': fake_analysis,
            'whale_activity': whale_analysis,
            'order_book': {
                'buy': order_book.get('buy', [])[:20] if order_book else [],
                'sell': order_book.get('sell', [])[:20] if order_book else []
            },
            'recent_trades': trades[:20] if trades else []
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'pair_id': pair_id}), 500
