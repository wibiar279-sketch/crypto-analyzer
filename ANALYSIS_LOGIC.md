# 📊 Crypto Analyzer - Analysis Logic Documentation

## Overview

Crypto Analyzer menggunakan kombinasi analisis teknikal, bandarmology, sentiment, dan deteksi manipulasi untuk memberikan rekomendasi trading yang akurat.

---

## Core Analysis Services

### 1. **Fear & Greed Index** (`fear_greed_service.py`)
Mengintegrasikan Fear & Greed Index untuk mengukur sentimen pasar secara keseluruhan.

**Logic:**
- Mengambil data dari API Fear & Greed Index
- Range: 0-100
  - 0-25: Extreme Fear (waktu beli)
  - 26-45: Fear (hati-hati)
  - 46-55: Neutral
  - 56-75: Greed (hati-hati jual)
  - 76-100: Extreme Greed (waktu jual)

---

### 2. **Trades Analysis** (`trades_analysis_service.py`)
Menganalisis transaksi aktual untuk mendeteksi pola trading.

**Indicators:**
- **OFI (Order Flow Imbalance)**: Mengukur ketidakseimbangan antara buy dan sell orders
- **CVD (Cumulative Volume Delta)**: Akumulasi perbedaan volume buy-sell
- **Kyle's Lambda**: Mengukur dampak harga dari volume trading

**Logic:**
```python
OFI = (Buy Volume - Sell Volume) / Total Volume
CVD = Σ(Buy Volume - Sell Volume)
Kyle's Lambda = Price Impact / Volume
```

**Interpretation:**
- OFI > 0.3: Strong buying pressure (BULLISH)
- OFI < -0.3: Strong selling pressure (BEARISH)
- CVD trending up: Accumulation phase
- CVD trending down: Distribution phase

---

### 3. **Microstructure Indicators** (`microstructure_indicators_service.py`)
Analisis mendalam struktur mikro pasar.

**Indicators:**
- **CPS (Cumulative Price Swing)**: Mengukur pergerakan harga kumulatif
- **SRI (Spread Return Index)**: Mengukur efisiensi spread
- **OBI (Order Book Imbalance)**: Ketidakseimbangan order book
- **LVI (Liquidity Volatility Index)**: Volatilitas likuiditas
- **Micro-skew**: Asimetri distribusi harga

**Logic:**
```python
OBI = (Total Buy Orders - Total Sell Orders) / (Total Buy Orders + Total Sell Orders)
LVI = StdDev(Liquidity) / Mean(Liquidity)
```

**Interpretation:**
- OBI > 0.2: Buy pressure dominan
- OBI < -0.2: Sell pressure dominan
- LVI > 0.5: High volatility (risky)

---

### 4. **Slippage & Breakeven** (`slippage_breakeven_service.py`)
Menghitung slippage dan break-even point.

**Logic:**
- **Slippage**: Perbedaan harga eksekusi vs harga yang diharapkan
- **VWAP (Volume Weighted Average Price)**: Harga rata-rata tertimbang volume
- **Lift/Hit Logic**: Biaya untuk mengambil likuiditas dari order book
- **Break-even**: Harga minimal untuk profit setelah fee

**Formula:**
```python
VWAP = Σ(Price × Volume) / Σ(Volume)
Slippage = |Execution Price - Expected Price| / Expected Price
Break-even = Buy Price × (1 + Trading Fee × 2)
```

---

### 5. **Advanced Bandarmology** (`advanced_bandarmology_service.py`)
Deteksi aktivitas bandar, whale, dan market maker.

**Detection Methods:**

#### A. **Fake Order Detection**
Mendeteksi order palsu yang dipasang untuk manipulasi.

**Logic:**
```python
# Order dianggap fake jika:
1. Order size > 10x average order size
2. Order tidak dieksekusi dalam 5 menit
3. Order sering di-cancel dan dipasang ulang
4. Order dipasang di harga yang jauh dari market price

Fake Order Percentage = (Fake Orders / Total Orders) × 100
```

**Threshold:**
- < 10%: Low manipulation
- 10-30%: Medium manipulation
- > 30%: High manipulation (AVOID)

#### B. **Whale Activity Detection**
Mendeteksi transaksi besar dari whale/bandar.

**Logic:**
```python
# Transaksi dianggap whale jika:
Volume > Mean + (2 × StdDev)

# Whale impact:
Whale Buy Ratio = Whale Buy Volume / Total Volume
Whale Sell Ratio = Whale Sell Volume / Total Volume
```

**Interpretation:**
- Whale Buy Ratio > 0.3: Whale accumulating (BULLISH)
- Whale Sell Ratio > 0.3: Whale distributing (BEARISH)

#### C. **Market Maker Detection**
Mendeteksi aktivitas market maker.

**Logic:**
```python
# Market maker terdeteksi jika:
1. Spread sangat kecil (< 0.1%)
2. Order book balanced
3. Frequent order updates
4. Large orders at both sides

Market Maker Score = f(Spread, Order Balance, Update Frequency)
```

---

### 6. **Social Sentiment** (`social_sentiment_service.py`)
Simulasi analisis sentimen berdasarkan perilaku trading.

**Logic:**
```python
# Sentimen dihitung dari:
1. Price momentum (24h change)
2. Volume trend
3. Order book imbalance
4. Whale activity

Sentiment Score = (
    Price Momentum × 0.3 +
    Volume Trend × 0.2 +
    OBI × 0.3 +
    Whale Impact × 0.2
) × 100

# Normalisasi ke 0-100
```

**Categories:**
- 0-20: Very Bearish 😢
- 21-40: Bearish 😟
- 41-60: Neutral 😐
- 61-80: Bullish 😊
- 81-100: Very Bullish 🚀

---

### 7. **Technical Analysis** (`technical_analysis.py`)
Indikator teknikal klasik.

**Indicators:**
- **RSI (Relative Strength Index)**: Momentum oscillator
- **MACD (Moving Average Convergence Divergence)**: Trend following
- **Moving Averages**: Trend identification
- **Bollinger Bands**: Volatility bands

**Logic:**
```python
RSI = 100 - (100 / (1 + RS))
where RS = Average Gain / Average Loss

MACD = EMA(12) - EMA(26)
Signal = EMA(MACD, 9)

# Signals:
RSI < 30: Oversold (BUY signal)
RSI > 70: Overbought (SELL signal)
MACD crosses above Signal: BUY
MACD crosses below Signal: SELL
```

---

### 8. **Bandarmology Analysis** (`bandarmology_analysis.py`)
Analisis order book untuk deteksi manipulasi.

**Logic:**
```python
# Order book imbalance:
Buy Pressure = Σ(Buy Orders within 2% of mid price)
Sell Pressure = Σ(Sell Orders within 2% of mid price)

Imbalance = (Buy Pressure - Sell Pressure) / (Buy Pressure + Sell Pressure)

# Wall detection:
Wall = Order size > 5x average order size

# Spoofing detection:
Spoofing = Large order placed then cancelled within 1 minute
```

**Interpretation:**
- Imbalance > 0.3: Strong buy pressure
- Imbalance < -0.3: Strong sell pressure
- Buy Wall: Support level (bullish)
- Sell Wall: Resistance level (bearish)

---

### 9. **Enhanced Recommendation** (`enhanced_recommendation_service.py`)
Sistem rekomendasi cerdas yang mengintegrasikan semua analisis.

**Scoring System:**

```python
Total Score = (
    Technical Score × 0.25 +      # RSI, MACD, MA
    Bandarmology Score × 0.25 +   # Order book, manipulation
    Sentiment Score × 0.20 +       # Social sentiment
    Whale Score × 0.15 +           # Whale activity
    Liquidity Score × 0.15         # Volume, spread
) × 100
```

**Action Determination:**

```python
if Total Score >= 75 and Manipulation < 20%:
    Action = "STRONG_BUY"
elif Total Score >= 60 and Manipulation < 30%:
    Action = "BUY"
elif Total Score >= 40 and Total Score < 60:
    Action = "HOLD"
elif Total Score >= 25 and Total Score < 40:
    Action = "SELL"
else:
    Action = "STRONG_SELL" or "AVOID"
```

**Risk Level:**

```python
Risk Factors:
- High manipulation (> 30%)
- Low liquidity (volume < average)
- High volatility (price swing > 10%)
- Whale dumping (whale sell ratio > 0.3)

Risk Level:
- 0-1 factors: LOW
- 2 factors: MEDIUM
- 3 factors: HIGH
- 4+ factors: VERY_HIGH
```

---

### 10. **Comprehensive Analysis v2.1** (`comprehensive_analysis_v21.py`)
Analisis terintegrasi dengan Fear & Greed Index.

**Integration Logic:**

```python
# Adjust recommendation based on market sentiment:
if Fear_Greed < 25:  # Extreme Fear
    # Good time to buy, boost buy signals
    if Action == "HOLD":
        Action = "BUY"
    elif Action == "BUY":
        Action = "STRONG_BUY"
        
elif Fear_Greed > 75:  # Extreme Greed
    # Good time to sell, boost sell signals
    if Action == "HOLD":
        Action = "SELL"
    elif Action == "SELL":
        Action = "STRONG_SELL"
```

---

## Complete Analysis Flow

```
1. Fetch Market Data
   ↓
2. Technical Analysis (RSI, MACD, MA)
   ↓
3. Order Book Analysis (Imbalance, Walls)
   ↓
4. Trades Analysis (OFI, CVD, Kyle's Lambda)
   ↓
5. Microstructure Analysis (CPS, SRI, OBI, LVI)
   ↓
6. Bandarmology Analysis (Fake orders, Whale, MM)
   ↓
7. Sentiment Analysis (Social + Trading behavior)
   ↓
8. Risk Assessment (Manipulation, Liquidity, Volatility)
   ↓
9. Score Calculation (Weighted average)
   ↓
10. Action Determination (BUY/SELL/HOLD)
   ↓
11. Fear & Greed Adjustment
   ↓
12. Final Recommendation
```

---

## Example Analysis Result

**Crypto: ASTERIDR**

### Input Data:
- Price: Rp 19,603
- 24h Change: +29.29%
- Volume 24h: Rp 0 (low liquidity)
- Buy Orders: 6,629,199
- Sell Orders: 1,556,23

### Analysis Steps:

1. **Technical Analysis:**
   - RSI: 65 (approaching overbought)
   - MACD: Bullish crossover
   - MA: Price above MA(20)
   - **Score: 70/100**

2. **Order Book Analysis:**
   - Buy/Sell Ratio: 81% / 19%
   - Imbalance: +0.62 (strong buy pressure)
   - No significant walls
   - **Score: 80/100**

3. **Bandarmology:**
   - Fake Orders: 0%
   - Whale Activity: UNKNOWN (insufficient data)
   - Market Maker: Not detected
   - **Score: 50/100** (neutral due to unknown)

4. **Sentiment:**
   - Price momentum: +29.29% (very bullish)
   - Volume trend: Low (concern)
   - **Score: 60/100**

5. **Risk Assessment:**
   - Manipulation: UNKNOWN (0%)
   - Liquidity: LOW (volume 0)
   - Volatility: HIGH (+29% swing)
   - **Risk Level: MEDIUM**

6. **Final Calculation:**
   ```
   Total Score = (70×0.25 + 80×0.25 + 50×0.25 + 60×0.25) × 100 / 100
               = 65/100
   ```

7. **Action:**
   - Score 65 + Low manipulation → **BUY**
   - But adjusted to **STRONG_BUY** due to strong order book imbalance

8. **Recommendation:**
   - **Action: STRONG_BUY**
   - **Score: 75/100**
   - **Risk: LOW** (despite volatility, no manipulation detected)
   - **Confidence: MEDIUM** (due to low volume data)

---

## Key Insights

### When to BUY:
1. ✅ Total Score > 60
2. ✅ Manipulation < 30%
3. ✅ Buy pressure > Sell pressure
4. ✅ RSI < 70 (not overbought)
5. ✅ Whale accumulating
6. ✅ Fear & Greed < 40 (market fear)

### When to SELL:
1. ❌ Total Score < 40
2. ❌ Manipulation > 30%
3. ❌ Sell pressure > Buy pressure
4. ❌ RSI > 70 (overbought)
5. ❌ Whale distributing
6. ❌ Fear & Greed > 70 (market greed)

### When to AVOID:
1. 🚫 Fake orders > 30%
2. 🚫 Very low liquidity
3. 🚫 High manipulation detected
4. 🚫 Whale dumping
5. 🚫 Extreme volatility without volume

---

## Disclaimer

Semua analisis ini adalah **tools bantu**, bukan jaminan profit. Selalu:
- DYOR (Do Your Own Research)
- Gunakan risk management
- Jangan invest lebih dari yang bisa Anda rugikan
- Crypto sangat volatile dan berisiko tinggi
