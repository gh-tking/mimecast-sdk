"""
Integration tests for Mimecast API
"""
import os
import pytest
from mimecast_sdk import MimecastClient

# Skip these tests if credentials are not set
requires_credentials = pytest.mark.skipif(
    not (os.getenv("MIMECAST_CLIENT_ID") and os.getenv("MIMECAST_CLIENT_SECRET")),
    reason="Mimecast credentials not set in environment"
)

@pytest.fixture
def client():
    return MimecastClient(
        client_id=os.getenv("MIMECAST_CLIENT_ID"),
        client_secret=os.getenv("MIMECAST_CLIENT_SECRET")
    )

@requires_credentials
def test_discovery_endpoint(client):
    """Test the discovery endpoint to verify authentication"""
    response = client.get("/api/v2/discovery")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data

@requires_credentials
def test_account_info(client):
    """Test retrieving account information"""
    response = client.get("/api/v2/account/get-account")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "account" in data["data"]