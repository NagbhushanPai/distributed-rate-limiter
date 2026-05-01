import redis
import time
import logging
from typing import Dict, Tuple
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Redis connection
redis_client = redis.StrictRedis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

# Lua script for atomic token bucket operation
TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local current_time = tonumber(ARGV[3])
local tokens_requested = tonumber(ARGV[4])

-- Get current state
local state = redis.call('GET', key)
local tokens, last_refill

if state == false then
    tokens = capacity
    last_refill = current_time
else
    local parts = {}
    for part in string.gmatch(state, "[^:]+") do
        table.insert(parts, part)
    end
    tokens = tonumber(parts[1])
    last_refill = tonumber(parts[2])
end

-- Calculate tokens to add
local time_passed = (current_time - last_refill) / 1000
local tokens_to_add = time_passed * refill_rate
tokens = math.min(tokens + tokens_to_add, capacity)

-- Check if allowed
local allowed = tokens >= tokens_requested
local remaining = tokens

if allowed then
    tokens = tokens - tokens_requested
    remaining = tokens
end

-- Update state
redis.call('SET', key, tokens .. ':' .. current_time)

-- Return result
return {allowed and 1 or 0, remaining, last_refill}
"""

# Register Lua script
token_bucket_eval = redis_client.register_script(TOKEN_BUCKET_SCRIPT)


class RateLimiter:
    """
    Distributed rate limiter using Redis and Token Bucket algorithm
    """

    def __init__(
        self,
        capacity: int = 100,
        refill_rate: float = 10.0,  # tokens per second
        key_prefix: str = "rate_limit:"
    ):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.key_prefix = key_prefix

    def _get_key(self, identifier: str) -> str:
        """Generate Redis key for identifier"""
        return f"{self.key_prefix}{identifier}"

    def is_allowed(self, identifier: str, tokens: int = 1) -> Dict[str, any]:
        """
        Check if request is allowed under rate limit

        Args:
            identifier: User ID, API key, or IP address
            tokens: Number of tokens to consume (default: 1)

        Returns:
            Dict with allowed (bool), remaining_tokens (int), retry_after (int)
        """
        key = self._get_key(identifier)
        current_time = int(time.time() * 1000)  # milliseconds

        try:
            allowed, remaining, last_refill = token_bucket_eval(
                keys=[key],
                args=[self.capacity, self.refill_rate, current_time, tokens],
                client=redis_client
            )

            allowed = bool(allowed)
            remaining = max(0, int(remaining))

            # Calculate retry_after in seconds
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
            # Fail open - allow request if Redis is down
            return {
                "allowed": True,
                "remaining_tokens": self.capacity,
                "retry_after": 0
            }

    def reset(self, identifier: str) -> bool:
        """Reset rate limiter for identifier"""
        key = self._get_key(identifier)
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error resetting rate limiter for {identifier}: {str(e)}")
            return False

    def get_status(self, identifier: str) -> Dict[str, any]:
        """Get current status of rate limiter"""
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


# Initialize rate limiter with defaults
rate_limiter = RateLimiter(
    capacity=int(os.getenv('RATE_LIMIT_CAPACITY', 100)),
    refill_rate=float(os.getenv('RATE_LIMIT_REFILL_RATE', 10.0))
)


@app.route('/allow', methods=['POST'])
def allow():
    """
    Check if request is allowed under rate limit

    Query parameters:
        - user_id: User identifier (required)
        - tokens: Tokens to consume (optional, default: 1)

    Returns:
        {
            "allowed": bool,
            "remaining_tokens": int,
            "retry_after": int (seconds)
        }
    """
    try:
        user_id = request.args.get('user_id') or request.json.get('user_id') if request.json else None
        tokens = int(request.args.get('tokens', 1) or request.json.get('tokens', 1) if request.json else 1)

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        result = rate_limiter.is_allowed(user_id, tokens)
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error in /allow endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/reset', methods=['POST'])
def reset():
    """Reset rate limiter for a user"""
    try:
        user_id = request.args.get('user_id') or request.json.get('user_id') if request.json else None

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        success = rate_limiter.reset(user_id)
        return jsonify({"success": success}), 200

    except Exception as e:
        logger.error(f"Error in /reset endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/status', methods=['GET'])
def status():
    """Get rate limiter status for a user"""
    try:
        user_id = request.args.get('user_id')

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        status_info = rate_limiter.get_status(user_id)
        return jsonify(status_info), 200

    except Exception as e:
        logger.error(f"Error in /status endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return jsonify({"status": "healthy"}), 200
    except:
        return jsonify({"status": "unhealthy"}), 503


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_ENV', 'production') == 'development'
    )
