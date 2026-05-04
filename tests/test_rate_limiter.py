"""Tests for Rate Limiter Service"""

import pytest
import json
import time
from app import create_app
from app.redis.client import redis_client


@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Test client"""
    with app.app_context():
        yield app.test_client()


@pytest.fixture(autouse=True)
def cleanup(app):
    """Clean Redis before/after tests"""
    with app.app_context():
        redis_client.client.flushdb()
    yield
    with app.app_context():
        redis_client.client.flushdb()


def test_allow_request_within_limit(client):
    """Test request within limit"""
    response = client.post('/allow?user_id=user1&tokens=1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['allowed'] is True
    assert data['remaining_tokens'] == 99


def test_deny_request_exceeding_limit(client, app):
    """Test request exceeding limit"""
    # Use a service with refill_rate=0 to avoid tokens being added back during test
    with app.app_context():
        from app.services.rate_limiter import RateLimiterService
        service = RateLimiterService(capacity=100, refill_rate=0)
        
        # Exhaust the bucket (capacity=100, no refill)
        for i in range(100):
            service.is_allowed('user2_no_refill', 1)
        
        # Request when bucket is empty should be denied
        result = service.is_allowed('user2_no_refill', 1)
        assert result['allowed'] is False, f"Expected denied but got: {result}"
        assert result['remaining_tokens'] == 0


def test_burst_traffic(client):
    """Test burst traffic"""
    response = client.post('/allow?user_id=user3&tokens=50')
    data = json.loads(response.data)
    assert data['allowed'] is True
    assert data['remaining_tokens'] == 50


def test_independent_limits(client):
    """Test independent user limits"""
    r1 = client.post('/allow?user_id=user4')
    r2 = client.post('/allow?user_id=user5')
    
    d1 = json.loads(r1.data)
    d2 = json.loads(r2.data)
    
    assert d1['allowed'] is True
    assert d2['allowed'] is True


def test_reset(client):
    """Test reset"""
    client.post('/allow?user_id=user6&tokens=100')
    client.post('/reset?user_id=user6')
    
    response = client.post('/allow?user_id=user6&tokens=1')
    data = json.loads(response.data)
    assert data['allowed'] is True


def test_status_endpoint(client):
    """Test status endpoint"""
    client.post('/allow?user_id=user7&tokens=10')
    
    response = client.get('/status?user_id=user7')
    data = json.loads(response.data)
    assert 'tokens' in data
    assert 'capacity' in data


def test_missing_user_id(client):
    """Test missing user_id"""
    response = client.post('/allow')
    assert response.status_code == 400


def test_health_check(client):
    """Test health check"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
