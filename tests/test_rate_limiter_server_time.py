"""Regression tests for Redis-time token bucket behavior"""

from app.redis.client import redis_client
from app.services.rate_limiter import RateLimiterService


def test_rate_limiter_uses_server_side_time(monkeypatch):
    """Service should not pass local timestamps into the Redis script call."""
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


def test_rate_limiter_fails_open_by_default(monkeypatch):
    """Redis errors should allow traffic by default."""
    def raise_error(**kwargs):
        raise RuntimeError('redis unavailable')

    monkeypatch.setattr(redis_client, 'execute_token_bucket', raise_error)

    service = RateLimiterService()
    result = service.is_allowed('user9', 1)

    assert result['allowed'] is True
    assert result['remaining_tokens'] == service.capacity
    assert result['retry_after'] == 0


def test_rate_limiter_can_fail_closed(monkeypatch):
    """Redis errors should reject traffic when fail-open is disabled."""
    def raise_error(**kwargs):
        raise RuntimeError('redis unavailable')

    monkeypatch.setattr(redis_client, 'execute_token_bucket', raise_error)

    service = RateLimiterService(fail_open=False)
    result = service.is_allowed('user10', 1)

    assert result['allowed'] is False
    assert result['remaining_tokens'] == 0
    assert result['retry_after'] == 1