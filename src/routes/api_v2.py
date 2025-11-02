"""
API Routes v2.0 for Enhanced Crypto Analyzer
Includes: Summary dashboard, comprehensive analysis with sentiment and advanced bandarmology
"""

from flask import Blueprint, jsonify
from ..services.indodax_service import IndodaxService
from ..services.enhanced_recommendation_service import EnhancedRecommendationService
import time

api_v2 = Blueprint('api_v2', __name__)

indodax_service = IndodaxService()
enhanced_service = EnhancedRecommendationService()

# Cache for summaries (10 seconds TTL)
summaries_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': 10
}

@api_v2.route('/summaries/v2', methods=['GET'])
def get_summaries_v2():
    """
    Get comprehensive summaries for all cryptocurrencies
    This is the main endpoint for dashboard v2.0
    Returns quick-decision data for each crypto
    """
    try:
        # Check cache
        current_time = time.time()
        if summaries_cache['data'] and (current_time - summaries_cache['timestamp']) < summaries_cache['ttl']:
            return jsonify(summaries_cache['data'])
        
        # Get all pairs
        pairs = indodax_service.get_pairs()
        if not pairs:
            return jsonify({'error': 'Failed to fetch pairs'}), 500
        
        # Get ticker all for prices
        ticker_all = indodax_service.get_ticker_all()
        tickers = ticker_all.get('tickers', {}) if ticker_all else {}
        
        cryptos = []
        
        # Process each pair (limit to first 10 for testing)
        # In production, you might want to process all or use async
        for pair in pairs[:10]:  # Limit for testing
            pair_id = pair['id']
            symbol = pair['symbol']
            
            try:
                # Get ticker for this pair
                # Convert pair_id format: 'btcidr' -> 'btc_idr'
                # Extract symbol and add underscore before 'idr'
                if 'idr' in pair_id:
                    ticker_key = pair_id.replace('idr', '_idr')
                else:
                    ticker_key = pair_id
                
                ticker = tickers.get(ticker_key, {})
                
                if not ticker:
                    continue
                
                current_price = float(ticker.get('last', 0))
                volume_24h = float(ticker.get('vol_' + symbol.lower(), 0))
                high_24h = float(ticker.get('high', current_price))
                low_24h = float(ticker.get('low', current_price))
                
                # Calculate simple price change
                if high_24h > 0 and low_24h > 0:
                    price_change_24h = ((current_price - low_24h) / low_24h) * 100
                else:
                    price_change_24h = 0
                
                # Create simplified summary (skip comprehensive analysis for now)
                summary = {
                    'action': 'HOLD',
                    'total_score': 50,
                    'risk_level': 'MEDIUM',
                    'sentiment': {'label': 'NEUTRAL', 'emoji': '😐', 'score': 50, 'trending': False},
                    'manipulation': {'level': 'UNKNOWN', 'score': 0, 'fake_orders_pct': 0},
                    'whale_activity': 'MEDIUM',
                    'real_order_direction': 'NEUTRAL',
                    'price_change_24h': price_change_24h,
                    'quick_insight': '⏸️ Loading analysis...'
                }
                
                crypto_data = {
                    'pair_id': pair_id,
                    'symbol': symbol,
                    'name': pair['description'],
                    'price': current_price,
                    'volume_24h': volume_24h,
                    'price_change_24h': price_change_24h,
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


@api_v2.route('/analysis/v2/<pair_id>', methods=['GET'])
def get_analysis_v2(pair_id):
    """
    Get comprehensive analysis for a specific cryptocurrency
    This is the main endpoint for detail page v2.0
    """
    try:
        analysis = enhanced_service.get_comprehensive_analysis(pair_id)
        
        if 'error' in analysis:
            return jsonify(analysis), 500
        
        return jsonify(analysis)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v2.route('/quick-summary/<pair_id>', methods=['GET'])
def get_quick_summary(pair_id):
    """
    Get ultra-quick summary for a single crypto (for tooltips, etc.)
    """
    try:
        analysis = enhanced_service.get_comprehensive_analysis(pair_id)
        
        if 'error' in analysis:
            return jsonify(analysis), 500
        
        # Return only summary
        return jsonify({
            'pair_id': pair_id,
            'symbol': analysis.get('symbol'),
            'current_price': analysis.get('current_price'),
            'summary': analysis.get('summary')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v2.route('/top-opportunities', methods=['GET'])
def get_top_opportunities():
    """
    Get top trading opportunities (highest scores, low manipulation)
    """
    try:
        # Get all summaries
        summaries_response = get_summaries_v2()
        summaries_data = summaries_response.get_json()
        
        if 'error' in summaries_data:
            return jsonify(summaries_data), 500
        
        cryptos = summaries_data.get('cryptos', [])
        
        # Filter and sort
        opportunities = []
        for crypto in cryptos:
            summary = crypto.get('summary', {})
            
            # Criteria for opportunity:
            # 1. Action is BUY or STRONG_BUY
            # 2. Manipulation score < 50
            # 3. Risk level not VERY_HIGH
            # 4. Total score > 60
            
            action = summary.get('action', '')
            manip_score = summary.get('manipulation', {}).get('score', 100)
            risk_level = summary.get('risk_level', 'VERY_HIGH')
            total_score = summary.get('total_score', 0)
            
            if action in ['BUY', 'STRONG_BUY'] and manip_score < 50 and risk_level != 'VERY_HIGH' and total_score > 60:
                opportunities.append(crypto)
        
        # Sort by total score descending
        opportunities.sort(key=lambda x: x.get('summary', {}).get('total_score', 0), reverse=True)
        
        return jsonify({
            'opportunities': opportunities[:10],  # Top 10
            'total': len(opportunities)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v2.route('/high-risk-alerts', methods=['GET'])
def get_high_risk_alerts():
    """
    Get cryptocurrencies with high manipulation/risk alerts
    """
    try:
        # Get all summaries
        summaries_response = get_summaries_v2()
        summaries_data = summaries_response.get_json()
        
        if 'error' in summaries_data:
            return jsonify(summaries_data), 500
        
        cryptos = summaries_data.get('cryptos', [])
        
        # Filter high risk
        alerts = []
        for crypto in cryptos:
            summary = crypto.get('summary', {})
            
            # Criteria for alert:
            # 1. Manipulation score > 70 OR
            # 2. Risk level VERY_HIGH OR
            # 3. Fake orders > 20%
            
            manip_score = summary.get('manipulation', {}).get('score', 0)
            risk_level = summary.get('risk_level', 'LOW')
            fake_orders = summary.get('manipulation', {}).get('fake_orders_pct', 0)
            
            if manip_score > 70 or risk_level == 'VERY_HIGH' or fake_orders > 20:
                alerts.append(crypto)
        
        # Sort by manipulation score descending
        alerts.sort(key=lambda x: x.get('summary', {}).get('manipulation', {}).get('score', 0), reverse=True)
        
        return jsonify({
            'alerts': alerts,
            'total': len(alerts)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v2.route('/trending', methods=['GET'])
def get_trending():
    """
    Get trending cryptocurrencies (based on social media sentiment)
    """
    try:
        # Get all summaries
        summaries_response = get_summaries_v2()
        summaries_data = summaries_response.get_json()
        
        if 'error' in summaries_data:
            return jsonify(summaries_data), 500
        
        cryptos = summaries_data.get('cryptos', [])
        
        # Filter trending
        trending = []
        for crypto in cryptos:
            summary = crypto.get('summary', {})
            sentiment = summary.get('sentiment', {})
            
            if sentiment.get('trending', False):
                trending.append(crypto)
        
        # Sort by sentiment score descending
        trending.sort(key=lambda x: x.get('summary', {}).get('sentiment', {}).get('score', 0), reverse=True)
        
        return jsonify({
            'trending': trending,
            'total': len(trending)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v2.route('/health', methods=['GET'])
def health_check_v2():
    """Health check endpoint for v2 API"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0',
        'features': [
            'comprehensive_analysis',
            'social_sentiment',
            'advanced_bandarmology',
            'fake_order_detection',
            'whale_tracking',
            'manipulation_detection'
        ]
    })

