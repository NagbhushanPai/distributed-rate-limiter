"""Rate Limit Middleware (Future Feature - Week 4)"""

from functools import wraps
from flask import request
from app.services.rate_limiter import RateLimiterService


def rate_limit(key_func=None, limit=100, window=60):
    """
    Rate limit decorator for Flask routes
    
    Args:
        key_func: Function to extract rate limit key from request
        limit: Max requests per window
        window: Window size in seconds
    
    Example:
        @app.route('/api/data')
        @rate_limit(lambda: request.remote_addr, limit=100, window=60)
        def get_data():
            return {"data": "..."}
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key_func is None:
                key = request.remote_addr
            else:
                key = key_func()
            
            rate_limiter = RateLimiterService()
            result = rate_limiter.is_allowed(key)
            
            if not result["allowed"]:
                return {
                    "error": "Rate limit exceeded",
                    "retry_after": result["retry_after"]
                }, 429
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
