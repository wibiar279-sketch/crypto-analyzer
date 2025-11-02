# 🚀 Crypto Analyzer v2.2

Professional-grade cryptocurrency analysis platform with real-time market sentiment, advanced bandarmology, and comprehensive trading signals.

## ✨ What's New in v2.2

### 🎯 Fear & Greed Index Integration
- **FREE** market-wide sentiment from alternative.me
- Real-time updates with 7-day trend analysis
- Contrarian buy/sell signals
- No API key required

### 📊 New Dashboard Layout
- **Recommended Section**: Top 50 cryptos with best signals
- **All Cryptos Section**: 478 cryptos with search & filter
- **No Pagination**: See all cryptos at once
- **Enhanced UX**: Quick insights without clicking

### 🔍 Search & Filter
- Search by symbol (real-time)
- Filter by action (BUY/SELL/HOLD)
- Filter by risk (LOW/MEDIUM/HIGH)
- Filter by trending status

## 🎯 Features

### Core Analysis
- ✅ **Actual Trades Analysis** - OFI, CVD, Kyle's Lambda
- ✅ **Microstructure Indicators** - CPS, SRI, OBI, LVI, micro-skew
- ✅ **Slippage & Break-even** - Lift/hit logic implementation
- ✅ **Fake Order Detection** - Multi-factor manipulation analysis
- ✅ **Whale Activity Tracking** - Large order detection
- ✅ **Market Maker Analysis** - Order book manipulation

### Sentiment Analysis
- ✅ **Fear & Greed Index** - Market-wide sentiment (FREE)
- ✅ **Simulated Sentiment** - Based on trading behavior
- ✅ **CoinGecko Integration** - Optional social sentiment

### Technical Analysis
- ✅ **RSI** - Overbought/oversold detection
- ✅ **MACD** - Trend and momentum
- ✅ **Moving Averages** - SMA & EMA
- ✅ **Bollinger Bands** - Volatility analysis

## 🚀 Quick Start

### Backend
```bash
cd crypto_analyzer
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python wsgi.py
```

### Frontend
```bash
cd crypto-analyzer-frontend
pnpm install
pnpm run build
cp -r dist/* ../crypto_analyzer/src/static/
```

### Access
```
http://localhost:5000
```

## 📡 API Endpoints (v2.2)

### Market Sentiment
```
GET /api/v2/market-sentiment
```
Returns Fear & Greed Index with trend analysis.

### Recommended Cryptos
```
GET /api/v2/recommended?limit=50&min_score=55
```
Returns top recommended cryptocurrencies.

### All Cryptos
```
GET /api/v2/all-cryptos?search=BTC&action=BUY&risk=LOW
```
Returns all cryptos with filters.

### Comprehensive Analysis
```
GET /api/v2/analysis/btc_idr
```
Returns complete analysis for a specific crypto.

## 💰 Cost

**Total: $0/month**

All features are completely FREE:
- Fear & Greed Index (no API key)
- Indodax API (public endpoints)
- Simulated sentiment (calculated)
- CoinGecko (optional, free tier)

## 📊 Architecture

### Backend (Python/Flask)
- `fear_greed_service.py` - Market sentiment
- `comprehensive_analysis_v21_updated.py` - Integrated analysis
- `api_v22.py` - New API endpoints
- All v2.1 services retained

### Frontend (React)
- Dashboard with 2 sections
- Market sentiment widget
- Search & filter UI
- Enhanced crypto cards

## 🎓 Documentation

- `README_V22.md` - This file
- `CRYPTO_ANALYZER_V22_COMPLETE.md` - Complete documentation
- `V22_SUMMARY.md` - Quick summary
- `sentiment_api_alternatives.md` - Sentiment API research
- `coingecko_api_research.md` - CoinGecko details
- `lift_hit_logic_verification.md` - Lift/hit logic
- `advanced_parameters_analysis.md` - Advanced parameters

## 🚀 Deploy to Railway

1. **Push to GitHub** (done)
2. **Railway Dashboard**: https://railway.app/dashboard
3. **New Project** → Deploy from GitHub
4. **Select**: wibiar279-sketch/crypto-analyzer
5. **Deploy** and wait 3-5 minutes
6. **Generate Domain** in Settings

## ⚠️ Disclaimer

This is an **ANALYSIS TOOL**, NOT financial advice.

- Cryptocurrency trading is HIGH RISK
- Always Do Your Own Research (DYOR)
- Never invest more than you can afford to lose
- Developer is NOT responsible for trading losses

## 📞 Support

**GitHub**: https://github.com/wibiar279-sketch/crypto-analyzer  
**Issues**: https://github.com/wibiar279-sketch/crypto-analyzer/issues

## 📝 Version History

### v2.2 (Current)
- Fear & Greed Index integration
- New dashboard layout (recommended + all)
- Search & filter functionality
- Enhanced UI/UX

### v2.1
- Actual trades analysis (OFI, CVD)
- Microstructure indicators (CPS, SRI, OBI, LVI)
- Slippage & break-even analysis
- Fake order detection

### v2.0
- Basic dashboard
- Technical analysis
- Bandarmology analysis
- Trading recommendations

## 🏆 Credits

**Developed by**: Manus AI Assistant  
**Commissioned by**: wibiar279  
**Version**: 2.2  
**Date**: November 2, 2025  

**Data Sources**:
- Indodax API (trading data)
- Alternative.me (Fear & Greed Index)
- CoinGecko API (optional sentiment)

---

**Ready to trade smarter! 🚀📈💰**

