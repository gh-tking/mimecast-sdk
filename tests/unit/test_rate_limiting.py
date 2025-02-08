"""
Unit tests for rate limiting functionality
"""
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pytest
import requests
from mimecast_sdk.rate_limiting import RateLimitHandler, RateLimitExceeded

@pytest.fixture
def rate_limiter():
    return RateLimitHandler(
        max_retries=2,
        min_backoff=0.1,  # Small values for testing
        max_backoff=0.3,
        jitter=False  # Disable jitter for predictable tests
    )

@pytest.fixture
def mock_response():
    response = Mock(spec=requests.Response)
    response.status_code = 200
    response.headers = {
        'x-mc-rate-limit': '100',
        'x-mc-rate-limit-remaining': '99',
        'x-mc-rate-limit-reset': str(int(time.time() + 3600))
    }
    return response

def test_rate_limit_tracking(rate_limiter, mock_response):
    """Test that rate limits are correctly tracked"""
    endpoint = "email/send"
    rate_limiter._update_rate_limits(endpoint, mock_response)
    
    with rate_limiter._lock:
        assert endpoint in rate_limiter._rate_limits
        assert rate_limiter._rate_limits[endpoint]['limit'] == 100
        assert rate_limiter._rate_limits[endpoint]['remaining'] == 99

def test_backoff_calculation(rate_limiter):
    """Test exponential backoff calculation"""
    # Without jitter, should be predictable
    assert rate_limiter._calculate_backoff(0) == 0.1  # min_backoff
    assert rate_limiter._calculate_backoff(1) == 0.2  # min_backoff * 2
    assert rate_limiter._calculate_backoff(2) == 0.3  # max_backoff

@pytest.mark.parametrize("status_code,remaining,should_retry", [
    (200, 10, True),   # Normal response with remaining quota
    (429, 0, True),    # Rate limit exceeded, should retry
    (500, 10, True),   # Server error, should retry
    (400, 10, False),  # Bad request, should not retry
])
def test_retry_conditions(rate_limiter, mock_response, status_code, remaining, should_retry):
    """Test various conditions that should or should not trigger retries"""
    mock_response.status_code = status_code
    mock_response.headers['x-mc-rate-limit-remaining'] = str(remaining)
    
    session = Mock()
    session.request.return_value = mock_response
    
    if not should_retry:
        with pytest.raises(requests.exceptions.HTTPError):
            rate_limiter.handle_request('GET', 'https://api.mimecast.com/api/v2/test', session=session)
    else:
        response = rate_limiter.handle_request('GET', 'https://api.mimecast.com/api/v2/test', session=session)
        assert response == mock_response

def test_rate_limit_exceeded_max_retries(rate_limiter):
    """Test that RateLimitExceeded is raised after max retries"""
    session = Mock()
    response = Mock(spec=requests.Response)
    response.status_code = 429
    response.headers = {
        'x-mc-rate-limit': '100',
        'x-mc-rate-limit-remaining': '0',
        'x-mc-rate-limit-reset': str(int(time.time() + 60))
    }
    session.request.return_value = response
    
    with pytest.raises(RateLimitExceeded):
        rate_limiter.handle_request('GET', 'https://api.mimecast.com/api/v2/test', session=session)
    
    # Should have tried max_retries + 1 times
    assert session.request.call_count == rate_limiter.max_retries + 1

def test_rate_limit_reset_waiting(rate_limiter, mock_response):
    """Test waiting for rate limit reset"""
    endpoint = "email/send"
    reset_time = datetime.now() + timedelta(seconds=2)
    
    mock_response.headers['x-mc-rate-limit-remaining'] = '0'
    mock_response.headers['x-mc-rate-limit-reset'] = str(int(reset_time.timestamp()))
    
    rate_limiter._update_rate_limits(endpoint, mock_response)
    
    should_retry, wait_time = rate_limiter._should_retry(endpoint)
    assert should_retry
    assert 1 < wait_time < 3  # Should be about 2 seconds plus buffer

@patch('time.sleep')  # Mock sleep to speed up tests
def test_retry_with_backoff(mock_sleep, rate_limiter):
    """Test retry behavior with backoff"""
    session = Mock()
    response = Mock(spec=requests.Response)
    response.status_code = 429
    response.headers = {
        'x-mc-rate-limit': '100',
        'x-mc-rate-limit-remaining': '0',
        'x-mc-rate-limit-reset': str(int(time.time() + 60))
    }
    
    # First two calls return 429, third succeeds
    session.request.side_effect = [response, response, Mock(status_code=200)]
    
    rate_limiter.handle_request('GET', 'https://api.mimecast.com/api/v2/test', session=session)
    
    # Check that backoff was called with increasing delays
    assert mock_sleep.call_count == 2
    assert mock_sleep.call_args_list[0][0][0] == 0.1  # First backoff
    assert mock_sleep.call_args_list[1][0][0] == 0.2  # Second backoff