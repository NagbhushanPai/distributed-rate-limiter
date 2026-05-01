"""Token Bucket Algorithm (In-Memory Version for Testing)"""

import time


class TokenBucket:
    """
    Token Bucket rate limiter (in-memory, for testing).
    
    Production deployments should use the Redis-backed version in services.rate_limiter.
    """
    
    def __init__(self, capacity, refill_rate):
        """
        Args:
            capacity (float): Maximum tokens in bucket
            refill_rate (float): Tokens generated per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def allow_request(self, current_time=None):
        """
        Check if request is allowed
        
        Args:
            current_time (float): Current time (default: now)
        
        Returns:
            dict: {allowed: bool, remaining_tokens: int}
        """
        if current_time is None:
            current_time = time.time()
        
        # Calculate elapsed time
        elapsed = current_time - self.last_refill
        
        # Refill tokens
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.tokens + tokens_to_add, self.capacity)
        
        # Update last refill
        self.last_refill = current_time
        
        # Check if allowed
        allowed = self.tokens >= 1.0
        
        if allowed:
            self.tokens -= 1.0
        
        return {
            "allowed": allowed,
            "remaining_tokens": max(0, int(self.tokens))
        }
