"""Rate Limiter Application Package"""

from flask import Flask
from app.core.config import Config
from app.redis.client import redis_client


def create_app(config=None):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    if config:
        app.config.from_object(config)
    else:
        app.config.from_object(Config)
    
    # Initialize Redis
    redis_client.init_app(app)
    
    # Register blueprints
    from app.api.routes import api_bp
    app.register_blueprint(api_bp)
    
    return app
