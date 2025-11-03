"""
API Routes v2.0 OPTIMIZED for Enhanced Crypto Analyzer
Strategy: Show all cryptos with basic data, deep analysis only on-demand
"""

from flask import Blueprint, jsonify, request
from ..services.indodax_service import IndodaxService
from ..services.enhanced_recommendation_service import EnhancedRecommendationService
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.cache_manager import summary_cache
from src.utils.rate_limiter import indodax_limiter

api_v2 = Blueprint('api_v2', __name__)

indodax_service = IndodaxService()
enhanced_service = EnhancedRecommendationService()

# Using global cache manager now (5 minutes TTL)

@api_v2.route('/summaries/v2', methods=['GET'])
def get_summaries_v2():
    """
    Get BASIC summaries for ALL cryptocurrencies (467+ cryptos)
    Returns lightweight data without deep analysis
    Deep analysis is done on-demand when user clicks on a crypto
    """
    try:
        # Check cache (5 minutes TTL)
        current_time = time.time()
        cache_key = 'summaries_v2'
        cached_data = summary_cache.get(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # Get all pairs
        pairs = indodax_service.get_pairs()
        if not pairs or not isinstance(pairs, list):
            return jsonify({'error': 'Failed to fetch pairs or invalid format'}), 500
        
        # Get ticker all for prices - THIS IS THE ONLY API CALL WE NEED
        ticker_all = indodax_service.get_ticker_all()
        if not ticker_all or not isinstance(ticker_all, dict):
            return jsonify({'error': 'Failed to fetch tickers or invalid format'}), 500
        
        tickers = ticker_all.get('tickers', {})
        if not isinstance(tickers, dict):
            return jsonify({'error': 'Invalid tickers format'}), 500
        
        cryptos = []
        
        # Process ALL pairs with BASIC data only
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
                
                if not ticker or not isinstance(ticker, dict):
                    continue
                
                # Extract basic data from ticker
                current_price = float(ticker.get('last', 0))
                if current_price == 0:
                    continue
                    
                volume_24h_base = float(ticker.get('vol_' + symbol.lower(), 0))
                volume_24h_idr = volume_24h_base * current_price
                high_24h = float(ticker.get('high', current_price))
                low_24h = float(ticker.get('low', current_price))
                buy_price = float(ticker.get('buy', 0))
                sell_price = float(ticker.get('sell', 0))
                
                # Calculate price change percentage
                if low_24h > 0:
                    price_change_24h = ((current_price - low_24h) / low_24h) * 100
                else:
                    price_change_24h = 0
                
                # Simple scoring based on price action and volume
                score = 50  # Neutral base
                
                # Price momentum (±20 points)
                if price_change_24h > 10:
                    score += 20
                elif price_change_24h > 5:
                    score += 10
                elif price_change_24h < -10:
                    score -= 20
                elif price_change_24h < -5:
                    score -= 10
                
                # Volume (±15 points)
                if volume_24h_idr > 1_000_000_000:  # > 1B IDR
                    score += 15
                elif volume_24h_idr > 100_000_000:  # > 100M IDR
                    score += 10
                elif volume_24h_idr < 10_000_000:  # < 10M IDR
                    score -= 10
                
                # Buy/Sell pressure (±15 points)
                if buy_price > 0 and sell_price > 0:
                    spread_pct = ((sell_price - buy_price) / buy_price) * 100
                    if spread_pct < 0.5:  # Tight spread = good liquidity
                        score += 15
                    elif spread_pct > 2:  # Wide spread = poor liquidity
                        score -= 15
                
                # Determine action based on score
                if score >= 75:
                    action = 'STRONG_BUY'
                    risk_level = 'LOW'
                elif score >= 60:
                    action = 'BUY'
                    risk_level = 'MEDIUM'
                elif score >= 45:
                    action = 'HOLD'
                    risk_level = 'MEDIUM'
                elif score >= 30:
                    action = 'SELL'
                    risk_level = 'HIGH'
                else:
                    action = 'STRONG_SELL'
                    risk_level = 'VERY_HIGH'
                
                # Calculate component scores for display
                # Technical score based on price action
                technical_score = 50
                if price_change_24h > 10:
                    technical_score = 75
                elif price_change_24h > 5:
                    technical_score = 65
                elif price_change_24h < -10:
                    technical_score = 25
                elif price_change_24h < -5:
                    technical_score = 35
                
                # Order book score based on spread
                orderbook_score = 50
                if buy_price > 0 and sell_price > 0:
                    spread_pct = ((sell_price - buy_price) / buy_price) * 100
                    if spread_pct < 0.5:
                        orderbook_score = 80
                    elif spread_pct < 1:
                        orderbook_score = 65
                    elif spread_pct > 2:
                        orderbook_score = 30
                
                # Liquidity score based on volume
                liquidity_score = 50
                if volume_24h_idr > 1_000_000_000:
                    liquidity_score = 85
                elif volume_24h_idr > 100_000_000:
                    liquidity_score = 70
                elif volume_24h_idr > 10_000_000:
                    liquidity_score = 55
                else:
                    liquidity_score = 30
                
                # Create basic summary (no deep analysis)
                summary = {
                    'action': action,
                    'total_score': max(0, min(100, score)),
                    'technical_score': technical_score,
                    'orderbook_score': orderbook_score,
                    'liquidity_score': liquidity_score,
                    'risk_level': risk_level,
                    'sentiment': {
                        'label': 'NEUTRAL',
                        'emoji': '😐',
                        'score': 50,
                        'trending': False
                    },
                    'manipulation': {
                        'level': 'UNKNOWN',
                        'score': 0,
                        'fake_orders_pct': 0
                    },
                    'whale_activity': 'UNKNOWN',
                    'real_order_direction': 'NEUTRAL',
                    'price_change_24h': price_change_24h,
                    'quick_insight': f"Price {'+' if price_change_24h > 0 else ''}{price_change_24h:.1f}% | Vol {volume_24h_idr/1_000_000:.0f}M IDR"
                }
                
                crypto_data = {
                    'pair_id': pair_id,
                    'symbol': symbol,
                    'name': pair.get('description', symbol),
                    'price': current_price,
                    'volume_24h': volume_24h_idr,
                    'volume_24h_base': volume_24h_base,
                    'price_change_24h': price_change_24h,
                    'high_24h': high_24h,
                    'low_24h': low_24h,
                    'buy_volume': buy_price,
                    'sell_volume': sell_price,
                    'summary': summary
                }
                
                cryptos.append(crypto_data)
                
            except Exception as e:
                print(f"Error processing {pair_id}: {str(e)}")
                continue
        
        result = {
            'cryptos': cryptos,
            'total': len(cryptos),
            'timestamp': current_time,
            'note': 'Basic analysis. Click on crypto for detailed analysis.'
        }
        
        # Update cache (5 minutes = 300 seconds)
        summary_cache.set(cache_key, result, ttl_seconds=300)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in get_summaries_v2: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_v2.route('/recommended', methods=['GET'])
def get_recommended():
    """
    Get recommended cryptocurrencies for buying
    """
    try:
        # Get all summaries
        summaries_response = get_summaries_v2()
        
        # Handle both Response object and tuple
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
            
            # Criteria: BUY or STRONG_BUY, score > 55, not very high risk
            if action in ['BUY', 'STRONG_BUY'] and total_score > 55 and risk_level != 'VERY_HIGH':
                recommended.append(crypto)
        
        # Sort by total score descending
        recommended.sort(key=lambda x: x.get('summary', {}).get('total_score', 0), reverse=True)
        
        # Limit to top 20
        recommended = recommended[:20]
        
        return jsonify({
            'recommended': recommended,
            'total': len(recommended),
            'timestamp': time.time()
        })
        
    except Exception as e:
        print(f"Error in get_recommended: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_v2.route('/analysis/v2/<pair_id>', methods=['GET'])
def get_detailed_analysis(pair_id):
    """
    Get DEEP analysis for a specific cryptocurrency
    This is called when user clicks on a crypto card
    """
    try:
        # Get comprehensive analysis with all the bells and whistles
        analysis = enhanced_service.get_comprehensive_analysis(pair_id)
        
        if 'error' in analysis:
            return jsonify(analysis), 500
        
        return jsonify(analysis)
        
    except Exception as e:
        print(f"Error in get_detailed_analysis for {pair_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_v2.route('/order-book/<pair_id>', methods=['GET'])
def get_order_book(pair_id):
    """Get order book for a specific pair"""
    try:
        depth = indodax_service.get_depth(pair_id)
        if not depth:
            return jsonify({'error': 'Failed to fetch order book'}), 500
        
        return jsonify({
            'pair_id': pair_id,
            'buy_orders': depth.get('buy', [])[:20],  # Top 20 buy orders
            'sell_orders': depth.get('sell', [])[:20],  # Top 20 sell orders
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v2.route('/price-trend/<pair_id>', methods=['GET'])
def get_price_trend(pair_id):
    """Get price trend data for a specific pair"""
    try:
        trades = indodax_service.get_trades(pair_id)
        if not trades:
            return jsonify({'error': 'Failed to fetch trades'}), 500
        
        # Get last 50 trades for trend
        recent_trades = trades[:50] if len(trades) > 50 else trades
        
        trend_data = []
        for trade in recent_trades:
            trend_data.append({
                'price': float(trade.get('price', 0)),
                'amount': float(trade.get('amount', 0)),
                'type': trade.get('type', 'buy'),
                'timestamp': trade.get('date', 0)
            })
        
        return jsonify({
            'pair_id': pair_id,
            'trend': trend_data,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v2.route('/buy-sell-trend/<pair_id>', methods=['GET'])
def get_buy_sell_trend(pair_id):
    """Get buy vs sell volume trend"""
    try:
        trades = indodax_service.get_trades(pair_id)
        if not trades:
            return jsonify({'error': 'Failed to fetch trades'}), 500
        
        # Analyze last 100 trades
        recent_trades = trades[:100] if len(trades) > 100 else trades
        
        buy_volume = 0
        sell_volume = 0
        
        for trade in recent_trades:
            amount = float(trade.get('amount', 0))
            trade_type = trade.get('type', 'buy')
            
            if trade_type == 'buy':
                buy_volume += amount
            else:
                sell_volume += amount
        
        total_volume = buy_volume + sell_volume
        buy_percentage = (buy_volume / total_volume * 100) if total_volume > 0 else 50
        sell_percentage = (sell_volume / total_volume * 100) if total_volume > 0 else 50
        
        # Determine trend
        if buy_percentage > 60:
            trend = 'BULLISH'
        elif sell_percentage > 60:
            trend = 'BEARISH'
        else:
            trend = 'NEUTRAL'
        
        return jsonify({
            'pair_id': pair_id,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'buy_percentage': buy_percentage,
            'sell_percentage': sell_percentage,
            'trend': trend,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v2.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Crypto Analyzer API v2.0',
        'timestamp': time.time()
    })
