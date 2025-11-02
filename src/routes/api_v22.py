"""
API Routes v2.2 - Updated for new dashboard layout

Endpoints:
- /api/v2/market-sentiment - Fear & Greed Index
- /api/v2/recommended - Top recommended cryptos (max 50)
- /api/v2/all-cryptos - All cryptos with search/filter
- /api/v2/analysis/<pair_id> - Comprehensive analysis
"""

from flask import Blueprint, jsonify, request
from ..services.comprehensive_analysis_v21_updated import ComprehensiveAnalysisV21
from ..services.fear_greed_service import FearGreedService
from ..services.indodax_service import IndodaxService
from datetime import datetime
import time

# Create blueprint
api_v22 = Blueprint('api_v22', __name__)

# Initialize services
analyzer = ComprehensiveAnalysisV21()
fear_greed = FearGreedService()
indodax = IndodaxService()

# Cache for expensive operations
_cache = {
    'recommended': {'data': None, 'timestamp': 0},
    'all_cryptos': {'data': None, 'timestamp': 0}
}
CACHE_DURATION = 30  # 30 seconds


@api_v22.route('/market-sentiment', methods=['GET'])
def get_market_sentiment():
    """
    Get market-wide sentiment (Fear & Greed Index)
    
    Returns:
        JSON with Fear & Greed Index data
    """
    try:
        sentiment = fear_greed.get_market_sentiment()
        trend = fear_greed.get_sentiment_trend(days=7)
        
        return jsonify({
            'success': True,
            'data': {
                **sentiment,
                'trend': trend
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_v22.route('/recommended', methods=['GET'])
def get_recommended_cryptos():
    """
    Get top recommended cryptocurrencies (max 50)
    
    Query params:
        - limit: Max number of results (default 50, max 50)
        - min_score: Minimum score threshold (default 55)
    
    Returns:
        JSON with recommended cryptos sorted by score
    """
    try:
        # Check cache
        now = time.time()
        if _cache['recommended']['data'] and (now - _cache['recommended']['timestamp']) < CACHE_DURATION:
            cached_data = _cache['recommended']['data']
            
            # Apply filters from query params
            limit = min(int(request.args.get('limit', 50)), 50)
            min_score = float(request.args.get('min_score', 55))
            
            filtered = [c for c in cached_data if c['score'] >= min_score][:limit]
            
            return jsonify({
                'success': True,
                'data': filtered,
                'count': len(filtered),
                'cached': True
            })
        
        # Get all pairs
        pairs_data = indodax.get_pairs()
        if not pairs_data:
            return jsonify({'success': False, 'error': 'Failed to fetch pairs'}), 500
        
        # Get ticker for all pairs
        tickers = indodax.get_ticker_all()
        if not tickers:
            return jsonify({'success': False, 'error': 'Failed to fetch tickers'}), 500
        
        # Analyze top cryptos by volume (to limit API calls)
        cryptos = []
        
        for pair_id, ticker in list(tickers.items())[:100]:  # Top 100 by volume
            try:
                if not pair_id.endswith('_idr'):
                    continue
                
                symbol = pair_id.replace('_idr', '').upper()
                
                # Quick analysis (without full comprehensive analysis to save time)
                price = float(ticker.get('last', 0))
                volume_24h = float(ticker.get('vol_idr', 0))
                change_24h = float(ticker.get('change_24h', 0))
                
                if price == 0 or volume_24h == 0:
                    continue
                
                # Calculate quick score
                score = 50  # Start neutral
                
                # Volume factor
                if volume_24h > 10_000_000_000:  # > 10B IDR
                    score += 10
                elif volume_24h > 1_000_000_000:  # > 1B IDR
                    score += 5
                
                # Price change factor
                if change_24h > 5:
                    score += 15
                elif change_24h > 2:
                    score += 10
                elif change_24h > 0:
                    score += 5
                elif change_24h < -5:
                    score -= 15
                elif change_24h < -2:
                    score -= 10
                elif change_24h < 0:
                    score -= 5
                
                # Determine action
                if score >= 70:
                    action = "BUY"
                    confidence = "HIGH"
                elif score >= 55:
                    action = "BUY"
                    confidence = "MEDIUM"
                elif score >= 45:
                    action = "HOLD"
                    confidence = "MEDIUM"
                elif score >= 30:
                    action = "SELL"
                    confidence = "MEDIUM"
                else:
                    action = "SELL"
                    confidence = "HIGH"
                
                # Risk level
                if abs(change_24h) > 10:
                    risk_level = "HIGH"
                elif abs(change_24h) > 5:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "LOW"
                
                # Sentiment (simplified)
                if change_24h > 3:
                    sentiment = "POSITIVE"
                    emoji = "😊"
                elif change_24h < -3:
                    sentiment = "NEGATIVE"
                    emoji = "😞"
                else:
                    sentiment = "NEUTRAL"
                    emoji = "😐"
                
                # Trending
                trending = volume_24h > 5_000_000_000 and abs(change_24h) > 3
                
                # Quick insight
                if action == "BUY" and score >= 70:
                    quick_insight = f"Strong buy signal {emoji} {'🔥' if trending else ''}"
                elif action == "BUY":
                    quick_insight = f"Moderate buy opportunity {emoji}"
                elif action == "SELL" and score <= 30:
                    quick_insight = f"Strong sell signal {emoji}"
                elif action == "SELL":
                    quick_insight = f"Consider taking profits {emoji}"
                else:
                    quick_insight = f"Hold position {emoji}"
                
                cryptos.append({
                    'symbol': symbol,
                    'pair_id': pair_id,
                    'price': price,
                    'volume_24h_idr': volume_24h,
                    'change_24h': change_24h,
                    'score': round(score, 2),
                    'action': action,
                    'confidence': confidence,
                    'risk_level': risk_level,
                    'sentiment': sentiment,
                    'emoji': emoji,
                    'trending': trending,
                    'quick_insight': quick_insight
                })
                
            except Exception as e:
                print(f"Error processing {pair_id}: {e}")
                continue
        
        # Sort by score (descending)
        cryptos.sort(key=lambda x: x['score'], reverse=True)
        
        # Cache result
        _cache['recommended']['data'] = cryptos
        _cache['recommended']['timestamp'] = now
        
        # Apply filters
        limit = min(int(request.args.get('limit', 50)), 50)
        min_score = float(request.args.get('min_score', 55))
        
        filtered = [c for c in cryptos if c['score'] >= min_score][:limit]
        
        return jsonify({
            'success': True,
            'data': filtered,
            'count': len(filtered),
            'cached': False
        })
        
    except Exception as e:
        print(f"Error in get_recommended_cryptos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_v22.route('/all-cryptos', methods=['GET'])
def get_all_cryptos():
    """
    Get all cryptocurrencies with basic info
    
    Query params:
        - search: Search term for symbol/name
        - action: Filter by action (BUY/SELL/HOLD)
        - risk: Filter by risk level (LOW/MEDIUM/HIGH)
        - trending: Filter trending only (true/false)
    
    Returns:
        JSON with all cryptos
    """
    try:
        # Check cache
        now = time.time()
        if _cache['all_cryptos']['data'] and (now - _cache['all_cryptos']['timestamp']) < CACHE_DURATION:
            cached_data = _cache['all_cryptos']['data']
            
            # Apply filters
            filtered = apply_filters(cached_data, request.args)
            
            return jsonify({
                'success': True,
                'data': filtered,
                'count': len(filtered),
                'total': len(cached_data),
                'cached': True
            })
        
        # Get all tickers
        tickers = indodax.get_ticker_all()
        if not tickers:
            return jsonify({'success': False, 'error': 'Failed to fetch tickers'}), 500
        
        cryptos = []
        
        for pair_id, ticker in tickers.items():
            try:
                if not pair_id.endswith('_idr'):
                    continue
                
                symbol = pair_id.replace('_idr', '').upper()
                
                price = float(ticker.get('last', 0))
                volume_24h = float(ticker.get('vol_idr', 0))
                change_24h = float(ticker.get('change_24h', 0))
                
                if price == 0:
                    continue
                
                # Quick score calculation (same as recommended)
                score = 50
                
                if volume_24h > 10_000_000_000:
                    score += 10
                elif volume_24h > 1_000_000_000:
                    score += 5
                
                if change_24h > 5:
                    score += 15
                elif change_24h > 2:
                    score += 10
                elif change_24h > 0:
                    score += 5
                elif change_24h < -5:
                    score -= 15
                elif change_24h < -2:
                    score -= 10
                elif change_24h < 0:
                    score -= 5
                
                # Determine action
                if score >= 55:
                    action = "BUY"
                elif score >= 45:
                    action = "HOLD"
                else:
                    action = "SELL"
                
                # Risk level
                if abs(change_24h) > 10:
                    risk_level = "HIGH"
                elif abs(change_24h) > 5:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "LOW"
                
                # Sentiment
                if change_24h > 3:
                    sentiment = "POSITIVE"
                    emoji = "😊"
                elif change_24h < -3:
                    sentiment = "NEGATIVE"
                    emoji = "😞"
                else:
                    sentiment = "NEUTRAL"
                    emoji = "😐"
                
                # Trending
                trending = volume_24h > 5_000_000_000 and abs(change_24h) > 3
                
                cryptos.append({
                    'symbol': symbol,
                    'pair_id': pair_id,
                    'price': price,
                    'volume_24h_idr': volume_24h,
                    'change_24h': change_24h,
                    'score': round(score, 2),
                    'action': action,
                    'risk_level': risk_level,
                    'sentiment': sentiment,
                    'emoji': emoji,
                    'trending': trending
                })
                
            except Exception as e:
                print(f"Error processing {pair_id}: {e}")
                continue
        
        # Sort by volume (descending)
        cryptos.sort(key=lambda x: x['volume_24h_idr'], reverse=True)
        
        # Cache result
        _cache['all_cryptos']['data'] = cryptos
        _cache['all_cryptos']['timestamp'] = now
        
        # Apply filters
        filtered = apply_filters(cryptos, request.args)
        
        return jsonify({
            'success': True,
            'data': filtered,
            'count': len(filtered),
            'total': len(cryptos),
            'cached': False
        })
        
    except Exception as e:
        print(f"Error in get_all_cryptos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_v22.route('/analysis/<pair_id>', methods=['GET'])
def get_comprehensive_analysis(pair_id):
    """
    Get comprehensive analysis for a specific crypto
    
    Args:
        pair_id: Trading pair ID (e.g., 'btc_idr')
    
    Returns:
        JSON with complete analysis
    """
    try:
        analysis = analyzer.analyze_crypto(pair_id)
        
        return jsonify({
            'success': True,
            'data': analysis
        })
        
    except Exception as e:
        print(f"Error in get_comprehensive_analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def apply_filters(data: list, args: dict) -> list:
    """Apply filters to crypto data"""
    filtered = data
    
    # Search filter
    search = args.get('search', '').lower()
    if search:
        filtered = [c for c in filtered if search in c['symbol'].lower()]
    
    # Action filter
    action = args.get('action', '').upper()
    if action in ['BUY', 'SELL', 'HOLD']:
        filtered = [c for c in filtered if c['action'] == action]
    
    # Risk filter
    risk = args.get('risk', '').upper()
    if risk in ['LOW', 'MEDIUM', 'HIGH']:
        filtered = [c for c in filtered if c['risk_level'] == risk]
    
    # Trending filter
    trending = args.get('trending', '').lower()
    if trending == 'true':
        filtered = [c for c in filtered if c['trending']]
    
    return filtered


@api_v22.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'version': '2.2',
        'timestamp': datetime.now().isoformat()
    })

