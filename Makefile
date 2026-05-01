# Makefile for Distributed Rate Limiter

.PHONY: help install dev test test-cov test-watch lint format clean docker-build docker-up docker-down load-test

help:
	@echo "Distributed Rate Limiter - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies"
	@echo "  make venv             Create virtual environment"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Run app in development mode"
	@echo "  make test             Run unit tests"
	@echo "  make test-cov         Run tests with coverage report"
	@echo "  make test-watch       Run tests in watch mode"
	@echo "  make lint             Lint Python code"
	@echo "  make format           Auto-format Python code"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-up        Start Docker Compose services"
	@echo "  make docker-down      Stop Docker Compose services"
	@echo "  make docker-logs      View Docker logs"
	@echo ""
	@echo "Testing:"
	@echo "  make load-test        Run Locust load tests"
	@echo "  make health-check     Check API health"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            Remove build artifacts and cache"
	@echo "  make requirements      Update requirements.txt"

# Setup targets
venv:
	python -m venv venv
	@echo "Virtual environment created. Activate with:"
	@echo "  - Linux/macOS: source venv/bin/activate"
	@echo "  - Windows: venv\\Scripts\\activate"

install:
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt
	@echo "Dependencies installed successfully"

# Development targets
dev:
	python app.py

test:
	pytest test_app.py -v

test-cov:
	pytest test_app.py -v --cov=app --cov-report=html --cov-report=term-missing
	@echo "Coverage report: htmlcov/index.html"

test-watch:
	pytest test_app.py -v --tb=short -s 2>/dev/null
	@while true; do \
		inotifywait -e modify app.py test_app.py; \
		clear; \
		pytest test_app.py -v --tb=short -s 2>/dev/null; \
	done

lint:
	python -m flake8 app.py load_test.py --max-line-length=100
	python -m pylint app.py load_test.py --disable=missing-docstring

format:
	python -m black app.py load_test.py test_app.py
	python -m isort app.py load_test.py test_app.py

# Docker targets
docker-build:
	docker build -f docker/Dockerfile -t distributed-rate-limiter:latest .

docker-up:
	docker-compose up -d
	@echo "Services started. Redis on localhost:6379, Flask on localhost:5000"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

docker-clean:
	docker-compose down -v

# Testing targets
load-test:
	@echo "Starting Locust load test..."
	@echo "Open browser to http://localhost:8089"
	locust -f load_test.py --host=http://localhost:5000

health-check:
	@curl -s http://localhost:5000/health | python -m json.tool || echo "API is not running"

test-api:
	@echo "Testing rate limiter API..."
	@echo ""
	@echo "1. Check rate limit:"
	@curl -s -X POST "http://localhost:5000/allow?user_id=test&tokens=1" | python -m json.tool
	@echo ""
	@echo "2. Get status:"
	@curl -s -X GET "http://localhost:5000/status?user_id=test" | python -m json.tool
	@echo ""
	@echo "3. Reset limiter:"
	@curl -s -X POST "http://localhost:5000/reset?user_id=test" | python -m json.tool

redis-cli:
	docker-compose exec redis redis-cli

# Maintenance targets
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov .eggs *.egg-info
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "__pycache__" -delete
	@echo "Cleaned up build artifacts"

requirements:
	pip freeze > requirements.txt
	@echo "requirements.txt updated"

git-init:
	git init
	git add .
	git commit -m "Initial commit: Distributed Rate Limiter"

.DEFAULT_GOAL := help
