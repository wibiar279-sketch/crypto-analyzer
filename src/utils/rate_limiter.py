"""
Rate Limiter - Prevent hitting Indodax API rate limits
"""
import time
from threading import Lock
from collections import deque

class RateLimiter:
    """
    Token bucket rate limiter
    """
    def __init__(self, max_requests=10, time_window=60):
        """
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = Lock()
    
    def can_proceed(self):
        """Check if request can proceed without hitting rate limit"""
        with self.lock:
            now = time.time()
            
            # Remove old requests outside time window
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()
            
            # Check if under limit
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
    
    def wait_if_needed(self, timeout=30):
        """
        Wait until request can proceed or timeout
        Returns True if can proceed, False if timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            if self.can_proceed():
                return True
            time.sleep(0.5)
        return False

# Global rate limiter - 10 requests per minute to be safe
indodax_limiter = RateLimiter(max_requests=10, time_window=60)
