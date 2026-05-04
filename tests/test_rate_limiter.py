"""Tests for Rate Limiter Service"""

import pytest
import json
import time
from app import create_app
from app.redis.client import redis_client
from app.services.rate_limiter import RateLimiterService


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


def test_deny_request_exceeding_limit(client):
    """Test request exceeding limit"""
    for i in range(100):
        client.post('/allow?user_id=user2&tokens=1')
    
    response = client.post('/allow?user_id=user2&tokens=1')
    data = json.loads(response.data)
    assert data['allowed'] is False


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


def test_rate_limiter_uses_server_side_time(monkeypatch):
    """Test service no longer passes local timestamps to Redis script"""
    captured = {}

    def fake_execute_token_bucket(**kwargs):
        captured.update(kwargs)
        return [1, 99, 1700000000000]

    monkeypatch.setattr(redis_client, 'execute_token_bucket', fake_execute_token_bucket)

    service = RateLimiterService()
    result = service.is_allowed('user8', 1)

    assert result['allowed'] is True
    assert result['remaining_tokens'] == 99
    assert set(captured.keys()) == {'key', 'capacity', 'refill_rate', 'tokens_requested'}
