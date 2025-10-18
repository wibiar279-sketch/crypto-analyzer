"""
API Routes for Crypto Analyzer
"""
from flask import Blueprint, jsonify, request
from src.services.indodax_service import IndodaxService
from src.services.technical_analysis import TechnicalAnalysis
from src.services.bandarmology_analysis import BandarmologyAnalysis
from src.services.recommendation_service import RecommendationService

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize Indodax service
indodax = IndodaxService()

@api_bp.route('/pairs', methods=['GET'])
def get_pairs():
    """Get all available trading pairs"""
    pairs = indodax.get_pairs()
    return jsonify(pairs)

@api_bp.route('/summaries', methods=['GET'])
def get_summaries():
    """Get summaries for all pairs"""
    summaries = indodax.get_summaries()
    return jsonify(summaries)

@api_bp.route('/ticker/<pair_id>', methods=['GET'])
def get_ticker(pair_id):
    """Get ticker for specific pair"""
    ticker = indodax.get_ticker(pair_id)
    return jsonify(ticker)

@api_bp.route('/ticker_all', methods=['GET'])
def get_ticker_all():
    """Get ticker for all pairs"""
    ticker_all = indodax.get_ticker_all()
    return jsonify(ticker_all)

@api_bp.route('/trades/<pair_id>', methods=['GET'])
def get_trades(pair_id):
    """Get recent trades for specific pair"""
    trades = indodax.get_trades(pair_id)
    return jsonify(trades)

@api_bp.route('/depth/<pair_id>', methods=['GET'])
def get_depth(pair_id):
    """Get order book depth for specific pair"""
    depth = indodax.get_depth(pair_id)
    return jsonify(depth)

@api_bp.route('/ohlc/<symbol>', methods=['GET'])
def get_ohlc(symbol):
    """
    Get OHLC data for charting
    Query params: timeframe, from, to
    """
    timeframe = request.args.get('timeframe', '15')
    from_time = request.args.get('from', type=int)
    to_time = request.args.get('to', type=int)
    
    ohlc = indodax.get_ohlc(symbol, timeframe, from_time, to_time)
    return jsonify(ohlc)

@api_bp.route('/analysis/<pair_id>', methods=['GET'])
def get_analysis(pair_id):
    """
    Get complete analysis for a specific pair
    Includes: technical, bandarmology, fundamental, and recommendation
    """
    try:
        # Get symbol for OHLC (convert pair_id to symbol format)
        # e.g., btc_idr -> BTCIDR
        symbol = pair_id.replace('_', '').upper()
        
        # Fetch all required data
        ticker_data = indodax.get_ticker(pair_id)
        depth_data = indodax.get_depth(pair_id)
        ohlc_data = indodax.get_ohlc(symbol, timeframe='60')  # 1 hour timeframe
        summaries = indodax.get_summaries()
        
        # Check for errors
        if 'error' in ticker_data:
            return jsonify({'error': 'Failed to fetch ticker data'}), 500
        
        if 'error' in depth_data:
            return jsonify({'error': 'Failed to fetch depth data'}), 500
        
        # Initialize analysis services
        technical = TechnicalAnalysis(ohlc_data)
        bandarmology = BandarmologyAnalysis(depth_data)
        recommendation = RecommendationService(
            ticker_data, 
            summaries, 
            technical, 
            bandarmology
        )
        
        # Get detailed recommendation
        analysis = recommendation.get_detailed_recommendation()
        
        return jsonify(analysis)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/technical/<pair_id>', methods=['GET'])
def get_technical_analysis(pair_id):
    """Get technical analysis for specific pair"""
    try:
        symbol = pair_id.replace('_', '').upper()
        timeframe = request.args.get('timeframe', '60')
        
        ohlc_data = indodax.get_ohlc(symbol, timeframe=timeframe)
        
        if 'error' in ohlc_data:
            return jsonify({'error': 'Failed to fetch OHLC data'}), 500
        
        technical = TechnicalAnalysis(ohlc_data)
        indicators = technical.get_all_indicators()
        
        return jsonify(indicators)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/bandarmology/<pair_id>', methods=['GET'])
def get_bandarmology_analysis(pair_id):
    """Get bandarmology analysis for specific pair"""
    try:
        depth_data = indodax.get_depth(pair_id)
        
        if 'error' in depth_data:
            return jsonify({'error': 'Failed to fetch depth data'}), 500
        
        bandarmology = BandarmologyAnalysis(depth_data)
        analysis = bandarmology.get_all_analysis()
        
        return jsonify(analysis)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/recommendation/<pair_id>', methods=['GET'])
def get_recommendation(pair_id):
    """Get buy/sell recommendation for specific pair"""
    try:
        symbol = pair_id.replace('_', '').upper()
        
        # Fetch required data
        ticker_data = indodax.get_ticker(pair_id)
        depth_data = indodax.get_depth(pair_id)
        ohlc_data = indodax.get_ohlc(symbol, timeframe='60')
        summaries = indodax.get_summaries()
        
        # Initialize analysis
        technical = TechnicalAnalysis(ohlc_data)
        bandarmology = BandarmologyAnalysis(depth_data)
        recommendation = RecommendationService(
            ticker_data, 
            summaries, 
            technical, 
            bandarmology
        )
        
        # Get recommendation
        result = recommendation.get_overall_score()
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'Crypto Analyzer API'})

