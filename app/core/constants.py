"""Application Constants"""

# Redis keys
REDIS_KEY_PREFIX = "rate_limit:"

# Error messages
ERROR_INVALID_USER_ID = "user_id is required"
ERROR_INVALID_TOKENS = "tokens must be a positive integer"
ERROR_REDIS_UNAVAILABLE = "Redis is unavailable"

# Response status codes
STATUS_OK = 200
STATUS_BAD_REQUEST = 400
STATUS_SERVER_ERROR = 500
