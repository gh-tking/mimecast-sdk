"""
Unit tests for Mimecast client
"""
import pytest
from unittest.mock import patch, Mock
from mimecast_sdk import MimecastClient

@pytest.fixture
def mock_config(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("""
        base_url: https://us-api.mimecast.com
        credentials:
            client_id: test_id
            client_secret: test_secret
    """)
    return config

def test_client_direct_init():
    client = MimecastClient(
        client_id="test_id",
        client_secret="test_secret"
    )
    assert client.auth.client_id == "test_id"
    assert client.auth.client_secret == "test_secret"
    assert client.base_url == "https://us-api.mimecast.com"

def test_client_custom_base_url():
    client = MimecastClient(
        client_id="test_id",
        client_secret="test_secret",
        base_url="https://eu-api.mimecast.com"
    )
    assert client.base_url == "https://eu-api.mimecast.com"

@patch('requests.request')
def test_client_get_request(mock_request):
    # Mock successful response
    mock_response = Mock()
    mock_response.json.return_value = {"data": "test"}
    mock_request.return_value = mock_response

    client = MimecastClient(
        client_id="test_id",
        client_secret="test_secret"
    )
    
    response = client.get("/api/v2/test")
    assert response.json() == {"data": "test"}
    
    args, kwargs = mock_request.call_args
    assert kwargs["method"] == "GET"
    assert kwargs["url"] == "https://us-api.mimecast.com/api/v2/test"

@patch('requests.request')
def test_client_post_request(mock_request):
    # Mock successful response
    mock_response = Mock()
    mock_response.json.return_value = {"status": "success"}
    mock_request.return_value = mock_response

    client = MimecastClient(
        client_id="test_id",
        client_secret="test_secret"
    )
    
    data = {"test": "data"}
    response = client.post("/api/v2/test", json=data)
    assert response.json() == {"status": "success"}
    
    args, kwargs = mock_request.call_args
    assert kwargs["method"] == "POST"
    assert kwargs["url"] == "https://us-api.mimecast.com/api/v2/test"
    assert kwargs["json"] == data