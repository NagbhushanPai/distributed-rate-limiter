# Distributed Rate Limiter - Setup & Deployment Guide

## Local Development Setup

### 1. Prerequisites

- Python 3.11+
- Redis 7+ or Docker
- Git

### 2. Clone Repository

```bash
git clone https://github.com/yourusername/distributed-rate-limiter.git
cd distributed-rate-limiter
```

### 3. Create Virtual Environment

```bash
# On Linux/macOS
python -m venv venv
source venv/bin/activate

# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# On Windows (Command Prompt)
python -m venv venv
venv\Scripts\activate.bat
```

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Start Redis

**Option A: Using Docker Compose (Recommended)**

```bash
docker-compose up -d redis
```

**Option B: Using Docker directly**

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Option C: Local Redis installation**

```bash
# Install Redis: https://redis.io/download
redis-server
```

### 6. Run Application

```bash
python app.py
```

The API will be available at `http://localhost:5000`

### 7. Test the Application

```bash
# Basic test
curl -X POST "http://localhost:5000/allow?user_id=test_user&tokens=1"

# Check status
curl -X GET "http://localhost:5000/status?user_id=test_user"

# Health check
curl -X GET "http://localhost:5000/health"
```

## Running Tests

### Unit Tests

```bash
# Run all tests
pytest test_app.py -v

# Run with coverage
pytest test_app.py -v --cov=app --cov-report=html

# Run specific test
pytest test_app.py::test_allow_request_within_limit -v
```

### Load Testing

```bash
# Install Locust (included in requirements.txt)
locust -f load_test.py --host=http://localhost:5000

# Then open browser to http://localhost:8089
```

## Docker Deployment

### Build Image

```bash
docker build -f docker/Dockerfile -t distributed-rate-limiter:latest .
```

### Run Full Stack

```bash
# Start all services (Redis + Flask)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Environment Variables

Create or modify `.env`:

```env
# Flask Configuration
FLASK_ENV=production
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Rate Limiter Configuration
RATE_LIMIT_CAPACITY=100
RATE_LIMIT_REFILL_RATE=10.0
```

## Production Deployment

### Using Gunicorn

```bash
# Single worker
gunicorn --bind 0.0.0.0:5000 app:app

# Multiple workers (recommended)
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 60 app:app
```

### Using Nginx Reverse Proxy

```nginx
upstream rate_limiter {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://rate_limiter;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rate-limiter
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rate-limiter
  template:
    metadata:
      labels:
        app: rate-limiter
    spec:
      containers:
        - name: rate-limiter
          image: yourusername/distributed-rate-limiter:latest
          ports:
            - containerPort: 5000
          env:
            - name: REDIS_HOST
              value: redis-service
            - name: REDIS_PORT
              value: "6379"
```

## Monitoring & Logging

### View Application Logs

```bash
# Live logs
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail 100 app
```

### Health Check

```bash
curl http://localhost:5000/health
```

## Troubleshooting

### Redis Connection Error

**Problem:** `ConnectionError: Cannot connect to Redis`

**Solution:**

1. Verify Redis is running: `redis-cli ping`
2. Check REDIS_HOST and REDIS_PORT in `.env`
3. Restart Redis: `docker-compose restart redis`

### High Latency

**Problem:** Requests are slow

**Solution:**

1. Check Redis performance: `redis-cli --latency`
2. Increase Flask workers: `gunicorn --workers 8`
3. Monitor network connectivity

### Rate Limit Not Working

**Problem:** All requests are allowed

**Solution:**

1. Check RATE_LIMIT_CAPACITY in `.env`
2. Verify rate limit configuration: `GET /status?user_id=test`
3. Check Redis data: `redis-cli KEYS "rate_limit:*"`

## Performance Tuning

### Redis Optimization

```bash
# Increase timeout in docker-compose.yml
# Add to redis service:
command: redis-server --timeout 300
```

### Flask Optimization

```bash
# Increase workers for better throughput
gunicorn --bind 0.0.0.0:5000 --workers 8 --worker-class gevent --timeout 120 app:app
```

### Network Optimization

- Use connection pooling in Redis client
- Enable gzip compression for responses
- Use HTTP/2 protocol

## Additional Resources

- [Redis Documentation](https://redis.io/documentation)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Gunicorn Documentation](https://gunicorn.org/)
