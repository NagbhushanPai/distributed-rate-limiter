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