# Caching and Rate Limiting Strategy

## Problem
Indodax API has rate limits (~10-20 requests per minute). When we try to fetch detailed data (order book + trades) for 467 cryptos, we hit the rate limit and get "too_many_requests" errors.

## Solution: Aggressive Caching + Rate Limiting

### 1. Cache Manager (`src/utils/cache_manager.py`)
- **In-memory cache** with TTL (Time To Live)
- **LRU eviction** (Least Recently Used) when cache is full
- Thread-safe with locks

**Cache Instances:**
- `summary_cache`: Cache for `/api/summaries/v2` endpoint
  - Max size: 10 entries (only need 1)
  - TTL: **5 minutes (300 seconds)**
  
- `detail_cache`: Cache for individual crypto details
  - Max size: 500 entries (can cache 500 different cryptos)
  - TTL: **10 minutes (600 seconds)**

### 2. Rate Limiter (`src/utils/rate_limiter.py`)
- **Token bucket algorithm**
- Limits: **10 requests per 60 seconds**
- `wait_if_needed()`: Blocks until request can proceed (with timeout)

### 3. Implementation

#### Summary Endpoint (`/api/summaries/v2`)
```python
# Check cache first
cached_data = summary_cache.get('summaries_v2')
if cached_data:
    return jsonify(cached_data)  # Return cached data

# Fetch from Indodax (only 1 API call for all 467 cryptos)
# ... fetch and process ...

# Cache for 5 minutes
summary_cache.set('summaries_v2', result, ttl_seconds=300)
```

**Result:** Summary loads in 2-3 seconds, cached for 5 minutes. No rate limit issues.

#### Detail Endpoint (`/api/detail/<pair_id>`)
```python
def get_order_book(pair_id):
    # Check cache first (10 minutes)
    cache_key = f"orderbook_{pair_id}"
    cached = detail_cache.get(cache_key)
    if cached:
        return cached  # Return cached data
    
    # Wait for rate limiter (max 10 seconds)
    if not indodax_limiter.wait_if_needed(timeout=10):
        return None  # Rate limit exceeded, return None
    
    # Fetch from Indodax
    response = requests.get(f"{INDODAX_BASE}/{pair_id}/depth")
    data = response.json()
    
    # Cache for 10 minutes
    detail_cache.set(cache_key, data, ttl_seconds=600)
    return data
```

**Result:** First user to click a crypto waits ~2-3 seconds. Subsequent users (within 10 minutes) get instant response from cache.

### 4. Benefits

✅ **Reduced API Calls:**
- Summary: 1 call per 5 minutes (instead of every 30 seconds)
- Detail: 1 call per crypto per 10 minutes (instead of every click)

✅ **No Rate Limit Errors:**
- Rate limiter ensures we never exceed 10 requests/minute
- Requests are queued and processed safely

✅ **Better Performance:**
- Cached responses are instant (no network latency)
- Users get faster load times

✅ **Manipulation/Fake Orders/Whale Activity Data:**
- Now available! (when not rate-limited)
- Cached for 10 minutes so multiple users can see the same analysis

### 5. Trade-offs

⚠️ **Data Freshness:**
- Summary data can be up to 5 minutes old
- Detail data can be up to 10 minutes old
- Acceptable for crypto analysis (not high-frequency trading)

⚠️ **Memory Usage:**
- In-memory cache uses RAM
- Max ~500 cryptos × ~50KB each = ~25MB
- Negligible for modern servers

### 6. Future Improvements

🔮 **Redis Cache:**
- Replace in-memory cache with Redis
- Shared cache across multiple server instances
- Persistent cache (survives server restarts)

🔮 **Background Fetching:**
- Pre-fetch popular cryptos in background
- Always have fresh data ready
- Users never wait

🔮 **Websocket Updates:**
- Real-time updates without polling
- Push new data to connected clients
- No need for 30-second refresh
