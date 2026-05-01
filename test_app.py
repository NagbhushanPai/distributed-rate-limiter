import pytest
import json
import time
from app import app, rate_limiter, redis_client


@pytest.fixture
def client():
    """Test client fixture"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up Redis before and after each test"""
    redis_client.flushdb()
    yield
    redis_client.flushdb()


def test_allow_request_within_limit(client):
    """Test that requests within limit are allowed"""
    response = client.post('/allow?user_id=user1&tokens=1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['allowed'] is True
    assert data['remaining_tokens'] == 99  # 100 - 1


def test_deny_request_exceeding_limit(client):
    """Test that requests exceeding limit are denied"""
    # Consume all tokens
    for i in range(100):
        response = client.post('/allow?user_id=user2&tokens=1')

    # Next request should be denied
    response = client.post('/allow?user_id=user2&tokens=1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['allowed'] is False
    assert data['remaining_tokens'] == 0


def test_burst_traffic(client):
    """Test burst traffic handling"""
    response = client.post('/allow?user_id=user3&tokens=50')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['allowed'] is True
    assert data['remaining_tokens'] == 50


def test_independent_user_limits(client):
    """Test that rate limits are independent per user"""
    response1 = client.post('/allow?user_id=user4')
    response2 = client.post('/allow?user_id=user5')

    data1 = json.loads(response1.data)
    data2 = json.loads(response2.data)

    assert data1['allowed'] is True
    assert data2['allowed'] is True


def test_reset_functionality(client):
    """Test reset functionality"""
    # Consume tokens
    client.post('/allow?user_id=user6&tokens=100')

    # Reset
    response = client.post('/reset?user_id=user6')
    assert response.status_code == 200

    # Should be able to use tokens again
    response = client.post('/allow?user_id=user6&tokens=1')
    data = json.loads(response.data)
    assert data['allowed'] is True


def test_status_endpoint(client):
    """Test status endpoint"""
    client.post('/allow?user_id=user7&tokens=10')

    response = client.get('/status?user_id=user7')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'tokens' in data
    assert 'capacity' in data
    assert 'refill_rate' in data


def test_missing_user_id(client):
    """Test error handling for missing user_id"""
    response = client.post('/allow')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'


def test_retry_after_calculation(client):
    """Test retry_after calculation"""
    # Consume all tokens
    for i in range(100):
        client.post('/allow?user_id=user8&tokens=1')

    response = client.post('/allow?user_id=user8&tokens=1')
    data = json.loads(response.data)
    assert data['allowed'] is False
    assert data['retry_after'] > 0


def test_concurrent_requests(client):
    """Test handling of concurrent-like requests"""
    user_id = 'user9'

    # Simulate rapid requests
    responses = []
    for i in range(5):
        response = client.post(f'/allow?user_id={user_id}&tokens=1')
        responses.append(json.loads(response.data))

    # All should be allowed
    for resp in responses:
        assert resp['allowed'] is True

    assert responses[0]['remaining_tokens'] == 99
    assert responses[4]['remaining_tokens'] == 95
