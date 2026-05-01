#!/bin/bash
# Local development startup script

set -e

echo "🚀 Starting Rate Limiter (Local Development)"
echo ""

# Check if Redis is running
if ! command -v redis-cli &> /dev/null; then
    echo "📊 Redis CLI not found. Using Docker..."
    if ! docker ps | grep -q redis; then
        echo "🐳 Starting Redis in Docker..."
        docker run -d -p 6379:6379 --name rate-limiter-redis redis:7-alpine
        sleep 2
    fi
fi

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python -m venv venv
fi

# Activate environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Create .env if needed
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env..."
    cp .env.example .env
fi

# Start app
echo ""
echo "✅ Starting Flask app..."
echo "📍 API: http://localhost:5000"
echo "🧪 Health: curl http://localhost:5000/health"
echo ""

python -m app.main
