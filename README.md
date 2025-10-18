# Crypto Analyzer - Professional Cryptocurrency Analysis

Website profesional untuk analisa cryptocurrency yang terintegrasi dengan API Indodax, menampilkan analisa **Bandarmology**, **Technical Analysis**, dan **Fundamental Analysis** dengan rekomendasi buy/sell otomatis.

## 🚀 Fitur Utama

### 1. **Dashboard Cryptocurrency**
- Menampilkan daftar lengkap 470+ cryptocurrency yang tersedia di Indodax
- Real-time price updates setiap 30 detik
- Informasi harga, volume, dan perubahan 24 jam
- Search functionality untuk mencari cryptocurrency tertentu
- Responsive design yang bekerja di desktop dan mobile

### 2. **Analisa Bandarmology**
Analisa khusus untuk mendeteksi aktivitas "bandar" atau whale traders:

- **Order Book Imbalance**: Rasio tekanan buy vs sell
- **Buy/Sell Walls Detection**: Deteksi order besar yang membentuk "dinding"
- **Whale Activity**: Identifikasi order dari whale traders (top 5% volume)
- **Spread Analysis**: Analisa likuiditas pasar
- **Order Depth Visualization**: Visualisasi order book dengan grafik

### 3. **Analisa Technical**
Indikator technical analysis lengkap:

- **RSI (Relative Strength Index)**: Deteksi overbought/oversold
- **MACD**: Trend momentum analysis
- **Moving Averages**: SMA 7, 25, 99 dan EMA 12, 26
- **Bollinger Bands**: Volatility analysis
- **Volume Analysis**: Trend volume trading

### 4. **Analisa Fundamental**
- Market cap analysis
- 24h dan 7d price comparison
- Volume trends
- Liquidity metrics

### 5. **Rekomendasi Buy/Sell**
Sistem scoring otomatis (0-100) berdasarkan:
- **Technical Score** (40%): Dari indikator technical
- **Bandarmology Score** (40%): Dari analisa order book
- **Momentum Score** (20%): Dari price dan volume momentum

Rekomendasi:
- **STRONG BUY** (Score > 75)
- **BUY** (Score 60-75)
- **HOLD** (Score 40-60)
- **SELL** (Score 25-40)
- **STRONG SELL** (Score < 25)

## 🛠️ Teknologi

### Backend
- **Flask**: Web framework Python
- **Pandas & NumPy**: Data processing
- **TA-Lib**: Technical analysis indicators
- **Requests**: API integration

### Frontend
- **React**: UI framework
- **Tailwind CSS**: Styling
- **shadcn/ui**: Component library
- **Lucide Icons**: Icon set
- **React Router**: Navigation

### API Integration
- **Indodax Public API**: Real-time cryptocurrency data
  - Ticker data
  - Order book (depth)
  - OHLC historical data
  - Trading pairs information

## 📊 Cara Menggunakan

### 1. Dashboard
1. Buka website
2. Lihat daftar cryptocurrency dengan informasi real-time
3. Gunakan search bar untuk mencari cryptocurrency tertentu
4. Klik "Refresh" untuk update data manual

### 2. Detail Analysis
1. Klik pada card cryptocurrency yang ingin dianalisa
2. Tunggu loading analysis (5-10 detik)
3. Lihat rekomendasi buy/sell di bagian atas
4. Scroll untuk melihat:
   - Technical indicators
   - Bandarmology analysis
   - Order book visualization

### 3. Interpretasi Rekomendasi

**Contoh: BTC/IDR**
```
Action: HOLD
Confidence: MEDIUM
Total Score: 40/100

Breakdown:
  Technical Score: 15/40
  Bandarmology Score: 20/40
  Momentum Score: 5/20
```

Interpretasi:
- Score rendah (40/100) menunjukkan kondisi netral
- Technical score rendah (15/40) menunjukkan indikator technical tidak bullish
- Bandarmology score sedang (20/40) menunjukkan order book cukup seimbang
- Momentum score rendah (5/20) menunjukkan momentum lemah

## 🔧 Instalasi & Development

### Prerequisites
- Python 3.11+
- Node.js 22+
- pnpm

### Backend Setup
```bash
cd crypto_analyzer
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

### Frontend Setup
```bash
cd crypto-analyzer-frontend
pnpm install
pnpm run dev
```

### Build Production
```bash
# Build frontend
cd crypto-analyzer-frontend
pnpm run build

# Copy to Flask static
cp -r dist/* ../crypto_analyzer/src/static/

# Run Flask
cd ../crypto_analyzer
source venv/bin/activate
python wsgi.py
```

## 📁 Struktur Project

```
crypto_analyzer/
├── src/
│   ├── services/
│   │   ├── indodax_service.py          # API integration
│   │   ├── technical_analysis.py       # Technical indicators
│   │   ├── bandarmology_analysis.py    # Order book analysis
│   │   └── recommendation_service.py   # Recommendation engine
│   ├── routes/
│   │   └── api.py                      # API endpoints
│   ├── static/                         # Frontend build
│   └── main.py                         # Flask app
├── requirements.txt
└── wsgi.py

crypto-analyzer-frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx               # Main dashboard
│   │   ├── CryptoDetail.jsx            # Detail analysis page
│   │   ├── TechnicalIndicators.jsx     # Technical display
│   │   └── OrderBookChart.jsx          # Order book visualization
│   └── App.jsx
└── package.json
```

## 🌐 API Endpoints

### Public Endpoints
- `GET /api/health` - Health check
- `GET /api/pairs` - Get all trading pairs
- `GET /api/summaries` - Get market summaries
- `GET /api/ticker_all` - Get all tickers
- `GET /api/ticker/:pair_id` - Get specific ticker
- `GET /api/depth/:pair_id` - Get order book
- `GET /api/trades/:pair_id` - Get recent trades
- `GET /api/ohlc/:symbol` - Get OHLC data

### Analysis Endpoints
- `GET /api/analysis/:pair_id` - Complete analysis
- `GET /api/technical/:pair_id` - Technical analysis only
- `GET /api/bandarmology/:pair_id` - Bandarmology analysis only
- `GET /api/recommendation/:pair_id` - Recommendation only

## ⚠️ Disclaimer

**PENTING**: Website ini adalah tools analisa dan **BUKAN** saran investasi. 

- Cryptocurrency trading memiliki risiko tinggi
- Selalu lakukan riset sendiri (DYOR)
- Jangan investasi lebih dari yang mampu Anda rugikan
- Rekomendasi sistem adalah berdasarkan algoritma dan bisa salah
- Gunakan sebagai referensi tambahan, bukan keputusan utama

## 📝 License

MIT License - Free to use and modify

## 👨‍💻 Developer

Developed with ❤️ for crypto traders and analysts

---

**Note**: Website ini menggunakan data dari Indodax API. Pastikan koneksi internet stabil untuk mendapatkan data real-time.

