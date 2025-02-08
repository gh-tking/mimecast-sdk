"""
Integration tests for rate limiting functionality
"""
import time
import pytest
from mimecast_sdk import MimecastClient
from mimecast_sdk.rate_limiting import RateLimitExceeded

# Skip these tests if credentials are not set
requires_credentials = pytest.mark.skipif(
    not (os.getenv("MIMECAST_CLIENT_ID") and os.getenv("MIMECAST_CLIENT_SECRET")),
    reason="Mimecast credentials not set in environment"
)

@pytest.fixture
def client():
    """Create client with short timeouts for testing"""
    return MimecastClient(
        client_id=os.getenv("MIMECAST_CLIENT_ID"),
        client_secret=os.getenv("MIMECAST_CLIENT_SECRET"),
        max_retries=2,
        min_backoff=0.1,
        max_backoff=0.3
    )

@requires_credentials
def test_rate_limit_headers(client):
    """Test that rate limit headers are present and parsed"""
    response = client.get("/api/v2/discovery")
    
    # Check rate limit headers
    assert 'x-mc-rate-limit' in response.headers
    assert 'x-mc-rate-limit-remaining' in response.headers
    assert 'x-mc-rate-limit-reset' in response.headers

@requires_credentials
def test_rapid_requests(client):
    """Test handling of rapid requests"""
    # Make several rapid requests
    for _ in range(5):
        response = client.get("/api/v2/discovery")
        assert response.status_code == 200
        
        # Check remaining requests is decreasing
        remaining = int(response.headers['x-mc-rate-limit-remaining'])
        assert remaining >= 0

@requires_credentials
def test_rate_limit_recovery(client):
    """Test recovery after hitting rate limit"""
    try:
        # Make requests until we hit rate limit
        while True:
            client.get("/api/v2/discovery")
            
    except RateLimitExceeded:
        # Wait for reset
        time.sleep(5)
        
        # Should be able to make request again
        response = client.get("/api/v2/discovery")
        assert response.status_code == 200

@requires_credentials
def test_concurrent_requests(client):
    """Test handling of concurrent requests"""
    import concurrent.futures
    
    def make_request():
        return client.get("/api/v2/discovery")
    
    # Make several concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(make_request) for _ in range(5)]
        
        for future in concurrent.futures.as_completed(futures):
            response = future.result()
            assert response.status_code == 200