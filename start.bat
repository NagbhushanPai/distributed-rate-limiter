@echo off
REM Quick start script for Distributed Rate Limiter (Windows)

echo.
echo 🚀 Distributed Rate Limiter - Quick Start
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo 🔧 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo ✅ Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
pip install -q -r requirements.txt

REM Create .env file if not exists
if not exist ".env" (
    echo ⚙️  Creating .env file from template...
    copy .env.example .env
)

REM Start the application
echo.
echo 🎉 Starting Flask application...
echo 📍 API available at: http://localhost:5000
echo 🧪 Health check: curl http://localhost:5000/health
echo.

python app.py
