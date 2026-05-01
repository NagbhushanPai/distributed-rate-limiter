"""Tests for Token Bucket Algorithm"""

import pytest
from app.algorithms.token_bucket import TokenBucket


def test_allow_request_within_limit():
    """Test request within limit"""
    bucket = TokenBucket(100, 10)
    result = bucket.allow_request(0)
    assert result['allowed'] is True
    assert result['remaining_tokens'] == 99


def test_deny_request_exceeding_limit():
    """Test request exceeding limit"""
    bucket = TokenBucket(100, 10)
    for i in range(100):
        bucket.allow_request(0)
    
    result = bucket.allow_request(0)
    assert result['allowed'] is False


def test_token_refill():
    """Test token refill over time"""
    bucket = TokenBucket(100, 10)
    bucket.allow_request(0)
    
    # After 1 second, 10 tokens refilled
    result = bucket.allow_request(1.0)
    assert result['remaining_tokens'] == 99


def test_capacity_capping():
    """Test capacity doesn't exceed max"""
    bucket = TokenBucket(100, 10)
    
    # After 1000 seconds, should cap at capacity
    result = bucket.allow_request(1000)
    assert result['remaining_tokens'] == 99


def test_burst_traffic():
    """Test burst traffic support"""
    bucket = TokenBucket(100, 10)
    
    for i in range(50):
        result = bucket.allow_request(0)
        assert result['allowed'] is True
    
    assert result['remaining_tokens'] == 50


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
