"""Flask Application Entry Point"""

import logging
from app import create_app
from app.core.config import Config

# Configure logging
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create Flask app
app = create_app()


@app.before_request
def log_request():
    """Log incoming requests"""
    logger.debug(f"{request.method} {request.path}")


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )
