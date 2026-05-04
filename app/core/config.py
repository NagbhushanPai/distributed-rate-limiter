"""Application Configuration"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    
    # Flask
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/0")
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    
    # Rate Limiter
    RATE_LIMIT_CAPACITY = int(os.getenv('RATE_LIMIT_CAPACITY', 100))
    RATE_LIMIT_REFILL_RATE = float(os.getenv('RATE_LIMIT_REFILL_RATE', 10.0))
    RATE_LIMIT_FAIL_OPEN = os.getenv('RATE_LIMIT_FAIL_OPEN', 'true').strip().lower() in {'1', 'true', 'yes', 'on'}
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
