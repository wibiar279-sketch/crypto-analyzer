"""
Cache Manager - Aggressive caching to avoid Indodax rate limits
"""
import time
from threading import Lock
from collections import OrderedDict

class CacheManager:
    """
    Simple in-memory cache with TTL and LRU eviction
    """
    def __init__(self, max_size=1000):
        self.cache = OrderedDict()
        self.lock = Lock()
        self.max_size = max_size
    
    def get(self, key):
        """Get value from cache if not expired"""
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if time.time() < expiry:
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    return value
                else:
                    # Expired, remove
                    del self.cache[key]
            return None
    
    def set(self, key, value, ttl_seconds):
        """Set value in cache with TTL"""
        with self.lock:
            expiry = time.time() + ttl_seconds
            self.cache[key] = (value, expiry)
            self.cache.move_to_end(key)
            
            # Evict oldest if over max size
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()
    
    def size(self):
        """Get current cache size"""
        with self.lock:
            return len(self.cache)

# Global cache instances
summary_cache = CacheManager(max_size=10)  # Only need 1 entry for summary
detail_cache = CacheManager(max_size=500)  # Cache up to 500 cryptos
