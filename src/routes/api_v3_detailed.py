"""
API v3 - Detailed Analysis with Real Manipulation, Fake Orders, and Whale Detection
"""
from flask import Blueprint, jsonify
import requests
from datetime import datetime
import time
from functools import lru_cache

api_v3 = Blueprint('api_v3', __name__)

INDODAX_BASE = "https://indodax.com/api"

# Cache for 30 seconds to avoid hammering API
@lru_cache(maxsize=1)
def get_cached_pairs(timestamp):
    """Cache pairs data for 30 seconds"""
    response = requests.get(f"{INDODAX_BASE}/pairs")
    return response.json() if response.status_code == 200 else []

@lru_cache(maxsize=1)
def get_cached_ticker_all(timestamp):
    """Cache ticker_all data for 30 seconds"""
    response = requests.get(f"{INDODAX_BASE}/ticker_all")
    return response.json() if response.status_code == 200 else {}

def get_order_book(pair_id):
    """Fetch order book for a pair"""
    try:
        response = requests.get(f"{INDODAX_BASE}/{pair_id}/depth", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_trades(pair_id):
    """Fetch recent trades for a pair"""
    try:
        response = requests.get(f"{INDODAX_BASE}/{pair_id}/trades", timeout=5)
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
            'confidence': 'low'
        }
    
    buy_orders = order_book.get('buy', [])[:20]  # Top 20 buy orders
    sell_orders = order_book.get('sell', [])[:20]  # Top 20 sell orders
    
    if not buy_orders or not sell_orders:
        return {
            'fake_percentage': 0,
            'has_buy_wall': False,
            'has_sell_wall': False,
            'confidence': 'low'
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
        if amount > buy_wall_threshold and price % 1000 == 0:
            suspicious_count += 1
    
    for order in sell_orders:
        price = float(order[0])
        amount = float(order[1])
        if amount > sell_wall_threshold and price % 1000 == 0:
            suspicious_count += 1
    
    fake_percentage = (suspicious_count / total_orders * 100) if total_orders > 0 else 0
    
    confidence = 'high' if total_orders >= 20 else 'medium' if total_orders >= 10 else 'low'
    
    return {
        'fake_percentage': round(fake_percentage, 1),
        'has_buy_wall': has_buy_wall,
        'has_sell_wall': has_sell_wall,
        'confidence': confidence
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
            'confidence': 'low'
        }
    
    # Analyze trades
    trade_amounts = [float(trade.get('amount', 0)) for trade in trades[:50]]
    
    if not trade_amounts:
        return {
            'detected': False,
            'activity_level': 'UNKNOWN',
            'large_trades_count': 0,
            'confidence': 'low'
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
    
    return {
        'detected': detected,
        'activity_level': activity_level,
        'large_trades_count': large_trades_count,
        'large_orders_count': whale_orders,
        'confidence': confidence
    }

def analyze_manipulation(order_book, trades, ticker):
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
    
    if not order_book or not ticker:
        return {
            'risk_level': 'UNKNOWN',
            'score': 0,
            'signals': [],
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
                signals.append('Extreme order book imbalance (possible spoofing)')
            elif imbalance_ratio > 3:
                manipulation_score += 15
                signals.append('High order book imbalance')
    
    # Check price volatility vs volume (pump & dump indicator)
    price_change = abs(float(ticker.get('last', 0)) - float(ticker.get('high', 0)))
    volume = float(ticker.get('vol_idr', 0))
    
    if volume > 0 and price_change > 0:
        volatility_volume_ratio = price_change / (volume / 1_000_000)  # per million IDR
        
        if volatility_volume_ratio > 100:
            manipulation_score += 25
            signals.append('High price volatility with low volume (possible pump)')
        elif volatility_volume_ratio > 50:
            manipulation_score += 10
            signals.append('Moderate price volatility')
    
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
            signals.append('Repeated trades at same price (possible wash trading)')
        elif max_same_price >= 5:
            manipulation_score += 10
            signals.append('Multiple trades at same price')
    
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
    
    return {
        'risk_level': risk_level,
        'score': manipulation_score,
        'signals': signals,
        'confidence': confidence
    }

@api_v3.route('/summaries/v3', methods=['GET'])
def get_summaries_v3():
    """
    Get comprehensive analysis for all cryptos with detailed manipulation, fake orders, and whale detection
    """
    try:
        # Get current timestamp for cache (30 second buckets)
        cache_key = int(time.time() / 30)
        
        # Fetch basic data (cached)
        pairs = get_cached_pairs(cache_key)
        ticker_all = get_cached_ticker_all(cache_key)
        
        if not pairs or 'tickers' not in ticker_all:
            return jsonify({'error': 'Failed to fetch data from Indodax'}), 500
        
        cryptos = []
        processed_count = 0
        max_to_process = 100  # Process first 100 to avoid timeout, can be increased
        
        for pair in pairs[:max_to_process]:
            pair_id = pair.get('id')
            ticker_key = pair.get('ticker_id')
            
            if not ticker_key or ticker_key not in ticker_all['tickers']:
                continue
            
            ticker = ticker_all['tickers'][ticker_key]
            
            # Fetch detailed data for this pair
            order_book = get_order_book(pair_id)
            trades = get_trades(pair_id)
            
            # Perform detailed analysis
            fake_analysis = analyze_fake_orders(order_book)
            whale_analysis = analyze_whale_activity(trades, order_book)
            manipulation_analysis = analyze_manipulation(order_book, trades, ticker)
            
            # Calculate scores
            last_price = float(ticker.get('last', 0))
            high_24h = float(ticker.get('high', 0))
            low_24h = float(ticker.get('low', 0))
            volume_idr = float(ticker.get('vol_idr', 0))
            
            price_change_24h = ((last_price - low_24h) / low_24h * 100) if low_24h > 0 else 0
            
            # Technical score
            technical_score = 50
            if price_change_24h > 10:
                technical_score = 75
            elif price_change_24h > 5:
                technical_score = 65
            elif price_change_24h < -10:
                technical_score = 25
            elif price_change_24h < -5:
                technical_score = 35
            
            # Order book score (affected by fake orders)
            orderbook_score = 50
            if order_book:
                spread = ((high_24h - low_24h) / low_24h * 100) if low_24h > 0 else 0
                if spread < 0.5:
                    orderbook_score = 80
                elif spread < 1:
                    orderbook_score = 65
                elif spread > 5:
                    orderbook_score = 30
                
                # Penalize for fake orders
                if fake_analysis['fake_percentage'] > 20:
                    orderbook_score -= 20
                elif fake_analysis['fake_percentage'] > 10:
                    orderbook_score -= 10
            
            # Liquidity score
            liquidity_score = 50
            if volume_idr > 1_000_000_000:
                liquidity_score = 85
            elif volume_idr > 100_000_000:
                liquidity_score = 70
            elif volume_idr > 10_000_000:
                liquidity_score = 55
            else:
                liquidity_score = 30
            
            # Total score (penalized by manipulation)
            total_score = (technical_score * 0.35 + orderbook_score * 0.35 + liquidity_score * 0.30)
            
            # Penalize for manipulation
            if manipulation_analysis['risk_level'] == 'HIGH':
                total_score -= 20
            elif manipulation_analysis['risk_level'] == 'MEDIUM':
                total_score -= 10
            
            total_score = max(0, min(100, total_score))
            
            # Determine action
            if total_score >= 70 and price_change_24h > 5 and manipulation_analysis['risk_level'] in ['MINIMAL', 'LOW']:
                action = 'STRONG_BUY'
            elif total_score >= 60 and price_change_24h > 0:
                action = 'BUY'
            elif total_score >= 40:
                action = 'HOLD'
            elif total_score >= 20:
                action = 'SELL'
            else:
                action = 'STRONG_SELL'
            
            crypto_data = {
                'pair_id': pair_id,
                'name': pair.get('description', ''),
                'price': last_price,
                'price_change_24h': round(price_change_24h, 2),
                'volume_24h_idr': volume_idr,
                'high_24h': high_24h,
                'low_24h': low_24h,
                'total_score': round(total_score),
                'technical_score': technical_score,
                'orderbook_score': orderbook_score,
                'liquidity_score': liquidity_score,
                'action': action,
                'manipulation': manipulation_analysis,
                'fake_orders': fake_analysis,
                'whale_activity': whale_analysis,
                'summary': {
                    'quick_insight': f"Price {'+' if price_change_24h > 0 else ''}{price_change_24h:.1f}% | Vol {volume_idr/1_000_000:.0f}M IDR"
                }
            }
            
            cryptos.append(crypto_data)
            processed_count += 1
        
        # Calculate summary stats
        strong_buy_count = len([c for c in cryptos if c['action'] == 'STRONG_BUY'])
        high_risk_count = len([c for c in cryptos if c['manipulation']['risk_level'] == 'HIGH'])
        
        return jsonify({
            'cryptos': cryptos,
            'total_count': len(cryptos),
            'processed_count': processed_count,
            'summary': {
                'strong_buy_signals': strong_buy_count,
                'high_risk_cryptos': high_risk_count,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
