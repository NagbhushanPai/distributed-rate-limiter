"""Rate Limiter Service - Business Logic"""

import time
import logging
from flask import current_app, has_app_context
from app.core.config import Config
from app.redis.client import redis_client
from app.core.constants import REDIS_KEY_PREFIX

logger = logging.getLogger(__name__)


class RateLimiterService:
    """Rate limiter service using Redis backend"""
    
    def __init__(self, capacity=None, refill_rate=None):
        # Allow instantiation outside of a Flask application context by
        # falling back to Config defaults when current_app is not available.
        if capacity is not None:
            self.capacity = capacity
        else:
            self.capacity = (
                current_app.config['RATE_LIMIT_CAPACITY']
                if has_app_context()
                else Config.RATE_LIMIT_CAPACITY
            )

        if refill_rate is not None:
            self.refill_rate = refill_rate
        else:
            self.refill_rate = (
                current_app.config['RATE_LIMIT_REFILL_RATE']
                if has_app_context()
                else Config.RATE_LIMIT_REFILL_RATE
            )
    
    def _get_key(self, identifier):
        """Generate Redis key"""
        return f"{REDIS_KEY_PREFIX}{identifier}"
    
    def is_allowed(self, identifier, tokens=1):
        """
        Check if request is allowed
        
        Args:
            identifier (str): User ID, API key, or IP
            tokens (int): Tokens to consume
        
        Returns:
            dict: {allowed: bool, remaining_tokens: int, retry_after: int}
        """
        key = self._get_key(identifier)
        try:
            allowed, remaining, server_time = redis_client.execute_token_bucket(
                key=key,
                capacity=self.capacity,
                refill_rate=self.refill_rate,
                tokens_requested=tokens
            )
            
            allowed = bool(allowed)
            remaining = max(0, int(remaining))
            
            # Calculate retry_after
            retry_after = 0
            if not allowed and self.refill_rate > 0:
                tokens_needed = tokens - remaining
                retry_after = int((tokens_needed / self.refill_rate) * 1000) // 1000 + 1
            
            return {
                "allowed": allowed,
                "remaining_tokens": remaining,
                "retry_after": retry_after
            }
        
        except Exception as e:
            logger.error(f"Rate limiter error for {identifier}: {str(e)}")
            # Fail-open: allow request if Redis is down
            return {
                "allowed": True,
                "remaining_tokens": self.capacity,
                "retry_after": 0
            }
    
    def reset(self, identifier):
        """Reset rate limiter for identifier"""
        key = self._get_key(identifier)
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error resetting rate limiter for {identifier}: {str(e)}")
            return False
    
    def get_status(self, identifier):
        """Get rate limiter status"""
        key = self._get_key(identifier)
        try:
            state = redis_client.get(key)
            
            if not state:
                return {
                    "tokens": self.capacity,
                    "last_refill": int(time.time() * 1000),
                    "capacity": self.capacity,
                    "refill_rate": self.refill_rate
                }
            
            parts = state.split(':')
            tokens = float(parts[0])
            last_refill = int(parts[1])
            
            # Recalculate tokens with refill
            current_time = int(time.time() * 1000)
            time_passed = (current_time - last_refill) / 1000
            tokens_to_add = time_passed * self.refill_rate
            tokens = min(tokens + tokens_to_add, self.capacity)
            
            return {
                "tokens": tokens,
                "last_refill": last_refill,
                "capacity": self.capacity,
                "refill_rate": self.refill_rate
            }
        
        except Exception as e:
            logger.error(f"Error getting status for {identifier}: {str(e)}")
            return None
