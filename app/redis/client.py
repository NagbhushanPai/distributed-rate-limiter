"""Redis Client with Connection Pooling"""

import redis
from flask import current_app


class RedisClient:
    """Redis client with connection pooling and script management"""
    
    def __init__(self):
        self.client = None
        self.token_bucket_script = None
    
    def init_app(self, app):
        """Initialize Redis connection"""
        redis_url = app.config.get('REDIS_URL')
        
        # Create connection pool
        self.client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30
        )
        
        # Load Lua scripts
        self._load_scripts()
    
    def _load_scripts(self):
        """Load Lua scripts"""
        import os
        script_path = os.path.join(
            os.path.dirname(__file__),
            'lua',
            'token_bucket.lua'
        )
        
        with open(script_path, 'r') as f:
            script = f.read()
        
        self.token_bucket_script = self.client.register_script(script)
    
    def execute_token_bucket(self, key, capacity, refill_rate, current_time, tokens_requested=1):
        """Execute token bucket Lua script"""
        return self.token_bucket_script(
            keys=[key],
            args=[capacity, refill_rate, current_time, tokens_requested],
            client=self.client
        )
    
    def get(self, key):
        """Get value from Redis"""
        return self.client.get(key)
    
    def set(self, key, value):
        """Set value in Redis"""
        return self.client.set(key, value)
    
    def delete(self, key):
        """Delete key from Redis"""
        return self.client.delete(key)
    
    def ping(self):
        """Check Redis connectivity"""
        return self.client.ping()


# Global Redis client instance
redis_client = RedisClient()
