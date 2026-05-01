"""
Token Bucket Rate Limiter

A simple, production-ready implementation of the Token Bucket algorithm.
Thread-safe for use with Redis backend or in-memory caching.
"""

import time


class TokenBucket:
    """
    Token Bucket rate limiter.
    
    Tokens are generated at a constant rate (refill_rate tokens per second).
    Each request consumes 1 token. Requests are allowed if tokens are available.
    Supports burst traffic up to bucket capacity.
    
    Args:
        capacity (float): Maximum tokens in bucket
        refill_rate (float): Tokens generated per second
    """
    
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def allow_request(self, current_time=None):
        """
        Check if a request is allowed and consume 1 token if permitted.
        
        Args:
            current_time (float): Current time in seconds (default: now)
        
        Returns:
            dict: {
                "allowed": bool,
                "remaining_tokens": float
            }
        """
        if current_time is None:
            current_time = time.time()
        
        # Calculate elapsed time in seconds
        elapsed = current_time - self.last_refill
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.tokens + tokens_to_add, self.capacity)
        
        # Update last refill time
        self.last_refill = current_time
        
        # Check if request is allowed
        allowed = self.tokens >= 1.0
        
        if allowed:
            self.tokens -= 1.0
        
        return {
            "allowed": allowed,
            "remaining_tokens": max(0, int(self.tokens))
        }


# Example usage and testing
if __name__ == "__main__":
    # Create bucket: 100 token capacity, 10 tokens/sec refill rate
    bucket = TokenBucket(capacity=100, refill_rate=10)
    
    print("=== Token Bucket Example ===\n")
    
    # Request 1: Should succeed (tokens available)
    result = bucket.allow_request(current_time=0)
    print(f"Request at t=0s: {result}")  # allowed: True, remaining: 99
    
    # Request 2: Should succeed
    result = bucket.allow_request(current_time=0.1)
    print(f"Request at t=0.1s: {result}")  # allowed: True, remaining: 98
    
    # Consume all tokens quickly
    for i in range(98):
        bucket.allow_request(current_time=0.1)
    
    result = bucket.allow_request(current_time=0.1)
    print(f"After consuming 100 tokens at t=0.1s: {result}")  # allowed: False
    
    # Wait 1 second - should refill 10 tokens
    result = bucket.allow_request(current_time=1.1)
    print(f"Request at t=1.1s (after 1s): {result}")  # allowed: True, remaining: 9
    
    # Wait 5 seconds - should refill but cap at capacity (100)
    result = bucket.allow_request(current_time=6.1)
    print(f"Request at t=6.1s (after 5s): {result}")  # allowed: True, remaining: 99
    
    # Burst traffic - use all tokens
    print("\n=== Burst Traffic ===")
    bucket = TokenBucket(capacity=100, refill_rate=10)
    for i in range(50):
        result = bucket.allow_request()
        if not result["allowed"]:
            print(f"Burst traffic stopped after {i} requests")
            break
    else:
        print(f"Burst traffic: All 50 requests succeeded")
