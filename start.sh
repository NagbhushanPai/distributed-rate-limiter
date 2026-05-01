#!/bin/bash
# Quick start script for Distributed Rate Limiter

set -e

echo "🚀 Distributed Rate Limiter - Quick Start"
echo ""

# Check if Redis is running
echo "📊 Checking Redis..."
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  Redis CLI not found. Using Docker..."
    if ! docker ps | grep -q redis; then
        echo "🐳 Starting Redis in Docker..."
        docker run -d -p 6379:6379 --name rate-limiter-redis redis:7-alpine
        sleep 2
    fi
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Create .env file if not exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
fi

# Start the application
echo ""
echo "🎉 Starting Flask application..."
echo "📍 API available at: http://localhost:5000"
echo "🧪 Health check: curl http://localhost:5000/health"
echo ""

python app.py
