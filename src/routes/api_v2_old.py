"""
API Routes v2.0 for Enhanced Crypto Analyzer
Includes: All cryptos, recommendations, order book, price trends, buy/sell volume trends
"""

from flask import Blueprint, jsonify, request
from ..services.indodax_service import IndodaxService
from ..services.enhanced_recommendation_service import EnhancedRecommendationService
import time
import statistics

api_v2 = Blueprint('api_v2', __name__)

indodax_service = IndodaxService()
enhanced_service = EnhancedRecommendationService()

# Cache for summaries (30 seconds TTL)
summaries_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': 30
}

@api_v2.route('/summaries/v2', methods=['GET'])
def get_summaries_v2():
    """
    Get comprehensive summaries for ALL cryptocurrencies (478 cryptos)
    Returns quick-decision data for each crypto with real analysis
    """
    try:
        # Check cache
        current_time = time.time()
        if summaries_cache['data'] and (current_time - summaries_cache['timestamp']) < summaries_cache['ttl']:
            return jsonify(summaries_cache['data'])
        
        # Get all pairs
        pairs = indodax_service.get_pairs()
        if not pairs or not isinstance(pairs, list):
            return jsonify({'error': 'Failed to fetch pairs or invalid format'}), 500
        
        # Get ticker all for prices
        ticker_all = indodax_service.get_ticker_all()
        if not ticker_all or not isinstance(ticker_all, dict):
            return jsonify({'error': 'Failed to fetch tickers or invalid format'}), 500
        
        tickers = ticker_all.get('tickers', {})
        if not isinstance(tickers, dict):
            return jsonify({'error': 'Invalid tickers format'}), 500
        
        cryptos = []
        
        # Process ALL pairs (no limit)
        for pair in pairs:
            if not isinstance(pair, dict):
                continue
            
            pair_id = pair.get('id')
            symbol = pair.get('symbol')
            
            if not pair_id or not symbol:
                continue
            
            try:
                # Convert pair_id format: 'btcidr' -> 'btc_idr'
                if 'idr' in pair_id:
                    ticker_key = pair_id.replace('idr', '_idr')
                else:
                    ticker_key = pair_id
                
                ticker = tickers.get(ticker_key, {})
                
                if not ticker:
                    continue
                
                current_price = float(ticker.get('last', 0))
                volume_24h_base = float(ticker.get('vol_' + symbol.lower(), 0))
                volume_24h_idr = volume_24h_base * current_price
                high_24h = float(ticker.get('high', current_price))
                low_24h = float(ticker.get('low', current_price))
                buy_volume = float(ticker.get('buy', 0))
                sell_volume = float(ticker.get('sell', 0))
                
                # Calculate price change percentage
                if low_24h > 0:
                    price_change_24h = ((current_price - low_24h) / low_24h) * 100
                else:
                    price_change_24h = 0
                
                # Get comprehensive analysis
                analysis = enhanced_service.get_comprehensive_analysis(pair_id)
                
                if 'error' not in analysis:
                    summary = analysis.get('summary', {})
                else:
                    # Fallback summary if analysis fails
                    summary = {
                        'action': 'HOLD',
                        'total_score': 50,
                        'risk_level': 'MEDIUM',
                        'sentiment': {'label': 'NEUTRAL', 'emoji': '😐', 'score': 50, 'trending': False},
                        'manipulation': {'level': 'UNKNOWN', 'score': 0, 'fake_orders_pct': 0},
                        'whale_activity': 'MEDIUM',
                        'real_order_direction': 'NEUTRAL',
                        'price_change_24h': price_change_24h,
                        'quick_insight': 'Analysis in progress...'
                    }
                
                crypto_data = {
                    'pair_id': pair_id,
                    'symbol': symbol,
                    'name': pair['description'],
                    'price': current_price,
                    'volume_24h': volume_24h_idr,
                    'volume_24h_base': volume_24h_base,
                    'price_change_24h': price_change_24h,
                    'high_24h': high_24h,
                    'low_24h': low_24h,
                    'buy_volume': buy_volume,
                    'sell_volume': sell_volume,
                    'summary': summary
                }
                
                cryptos.append(crypto_data)
                
            except Exception as e:
                print(f"Error processing {pair_id}: {str(e)}")
                continue
        
        result = {
            'cryptos': cryptos,
            'total': len(cryptos),
            'timestamp': current_time
        }
        
        # Update cache
        summaries_cache['data'] = result
        summaries_cache['timestamp'] = current_time
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v2.route('/recommended', methods=['GET'])
def get_recommended():
    """
    Get recommended cryptocurrencies for buying (profitable opportunities)
    Returns cryptos with BUY/STRONG_BUY signals, sorted by score
    """
    try:
        # Get all summaries - call the function and get the response
        summaries_response = get_summaries_v2()
        
        # Handle both Response object and tuple (Response, status_code)
        if isinstance(summaries_response, tuple):
            summaries_data = summaries_response[0].get_json()
        else:
            summaries_data = summaries_response.get_json()
        
        if 'error' in summaries_data:
            return jsonify(summaries_data), 500
        
        cryptos = summaries_data.get('cryptos', [])
        
        # Filter for buy recommendations
        recommended = []
        for crypto in cryptos:
            summary = crypto.get('summary', {})
            action = summary.get('action', 'HOLD')
            total_score = summary.get('total_score', 0)
            risk_level = summary.get('risk_level', 'VERY_HIGH')
            manipulation_score = summary.get('manipulation', {}).get('score', 100)
            
            # Criteria: BUY or STRONG_BUY, score > 55, not very high risk, low manipulation
            if action in ['BUY', 'STRONG_BUY'] and total_score > 55 and risk_level != 'VERY_HIGH' and manipulation_score < 60:
                recommended.append(crypto)
        
        # Sort by total score descending
        recommended.sort(key=lambda x: x.get('summary', {}).get('total_score', 0), reverse=True)
        
        return jsonify({
            'recommended': recommended[:50],  # Top 50
            'total': len(recommended)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v2.route('/order-book/<pair_id>', methods=['GET'])
def get_order_book(pair_id):
    """
    Get order book (buy and sell orders) for a specific crypto
    """
    try:
        depth = indodax_service.get_depth(pair_id)
        
        if not depth:
            return jsonify({'error': 'Failed to fetch order book'}), 500
        
        buy_orders = depth.get('buy', [])[:20]  # Top 20 buy orders
        sell_orders = depth.get('sell', [])[:20]  # Top 20 sell orders
        
        # Calculate total volumes
        total_buy_volume = sum([float(order[1]) for order in buy_orders])
        total_sell_volume = sum([float(order[1]) for order in sell_orders])
        
        # Calculate weighted average prices
        buy_vwap = sum([float(order[0]) * float(order[1]) for order in buy_orders]) / total_buy_volume if total_buy_volume > 0 else 0
        sell_vwap = sum([float(order[0]) * float(order[1]) for order in sell_orders]) / total_sell_volume if total_sell_volume > 0 else 0
        
        return jsonify({
            'pair_id': pair_id,
            'buy_orders': [[float(order[0]), float(order[1])] for order in buy_orders],
            'sell_orders': [[float(order[0]), float(order[1])] for order in sell_orders],
            'total_buy_volume': total_buy_volume,
            'total_sell_volume': total_sell_volume,
            'buy_vwap': buy_vwap,
            'sell_vwap': sell_vwap,
            'spread': sell_vwap - buy_vwap if sell_vwap > 0 and buy_vwap > 0 else 0,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v2.route('/price-trend/<pair_id>', methods=['GET'])
def get_price_trend(pair_id):
    """
    Get price trend data for a specific crypto (OHLC data)
    """
    try:
        # Get symbol from pair_id
        symbol = pair_id.replace('idr', '').replace('_', '').upper()
        
        # Get OHLC data (1 hour candles)
        ohlc = indodax_service.get_ohlc(symbol, period='1h')
        
        if not ohlc:
            return jsonify({'error': 'Failed to fetch price trend'}), 500
        
        return jsonify({
            'pair_id': pair_id,
            'symbol': symbol,
            'ohlc': ohlc,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v2.route('/buy-sell-trend/<pair_id>', methods=['GET'])
def get_buy_sell_trend(pair_id):
    """
    Get actual buy/sell volume trend for a specific crypto
    Returns real-time buy and sell pressure
    """
    try:
        # Get recent trades
        trades = indodax_service.get_trades(pair_id)
        
        if not trades:
            return jsonify({'error': 'Failed to fetch trades'}), 500
        
        # Analyze buy vs sell volume from recent trades
        buy_volume = 0
        sell_volume = 0
        buy_count = 0
        sell_count = 0
        
        for trade in trades[:100]:  # Last 100 trades
            amount = float(trade.get('amount', 0))
            trade_type = trade.get('type', 'buy')
            
            if trade_type == 'buy':
                buy_volume += amount
                buy_count += 1
            else:
                sell_volume += amount
                sell_count += 1
        
        total_volume = buy_volume + sell_volume
        buy_percentage = (buy_volume / total_volume * 100) if total_volume > 0 else 50
        sell_percentage = (sell_volume / total_volume * 100) if total_volume > 0 else 50
        
        # Determine pressure direction
        if buy_percentage > 60:
            pressure = 'STRONG_BUY'
            emoji = '🚀'
        elif buy_percentage > 52:
            pressure = 'BUY'
            emoji = '📈'
        elif sell_percentage > 60:
            pressure = 'STRONG_SELL'
            emoji = '📉'
        elif sell_percentage > 52:
            pressure = 'SELL'
            emoji = '⚠️'
        else:
            pressure = 'NEUTRAL'
            emoji = '➡️'
        
        return jsonify({
            'pair_id': pair_id,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'buy_percentage': round(buy_percentage, 2),
            'sell_percentage': round(sell_percentage, 2),
            'pressure': pressure,
            'emoji': emoji,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v2.route('/analysis/v2/<pair_id>', methods=['GET'])
def get_analysis_v2(pair_id):
    """
    Get comprehensive analysis for a specific cryptocurrency
    """
    try:
        analysis = enhanced_service.get_comprehensive_analysis(pair_id)
        
        if 'error' in analysis:
            return jsonify(analysis), 500
        
        return jsonify(analysis)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v2.route('/health', methods=['GET'])
def health_check_v2():
    """Health check endpoint for v2 API"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0',
        'features': [
            'all_478_cryptos',
            'recommendations',
            'order_book',
            'price_trends',
            'buy_sell_trends',
            'comprehensive_analysis',
            'manipulation_detection'
        ]
    })
