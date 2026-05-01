"""Development Server Entry Point"""

import sys
from app import create_app
from app.core.config import Config

if __name__ == '__main__':
    app = create_app(Config)
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )
