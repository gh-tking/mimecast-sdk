"""
Unit tests for Mimecast authentication
"""
import pytest
from unittest.mock import patch, Mock
from mimecast_sdk.auth import MimecastAuth

def test_auth_initialization():
    auth = MimecastAuth(
        client_id="test_id",
        client_secret="test_secret"
    )
    assert auth.client_id == "test_id"
    assert auth.client_secret == "test_secret"
    assert auth.base_url == "https://us-api.mimecast.com"  # default URL

def test_auth_custom_base_url():
    auth = MimecastAuth(
        client_id="test_id",
        client_secret="test_secret",
        base_url="https://eu-api.mimecast.com"
    )
    assert auth.base_url == "https://eu-api.mimecast.com"

@patch('requests.post')
def test_get_access_token(mock_post):
    # Mock successful token response
    mock_response = Mock()
    mock_response.json.return_value = {
        "access_token": "test_token",
        "expires_in": 3600
    }
    mock_post.return_value = mock_response

    auth = MimecastAuth("test_id", "test_secret")
    token = auth._get_access_token()

    assert token == "test_token"
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://us-api.mimecast.com/oauth/token"
    assert kwargs["data"] == {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "grant_type": "client_credentials"
    }

@patch('requests.post')
def test_get_auth_headers(mock_post):
    # Mock successful token response
    mock_response = Mock()
    mock_response.json.return_value = {
        "access_token": "test_token",
        "expires_in": 3600
    }
    mock_post.return_value = mock_response

    auth = MimecastAuth("test_id", "test_secret")
    headers = auth.get_auth_headers()

    assert headers["Authorization"] == "Bearer test_token"
    assert headers["Content-Type"] == "application/json"
    assert headers["Accept"] == "application/json"

@patch('requests.post')
def test_token_refresh(mock_post):
    # Mock successful token responses
    mock_response1 = Mock()
    mock_response1.json.return_value = {
        "access_token": "token1",
        "expires_in": 0  # Immediate expiration
    }
    mock_response2 = Mock()
    mock_response2.json.return_value = {
        "access_token": "token2",
        "expires_in": 3600
    }
    mock_post.side_effect = [mock_response1, mock_response2]

    auth = MimecastAuth("test_id", "test_secret")
    
    # First call gets token1
    headers1 = auth.get_auth_headers()
    assert headers1["Authorization"] == "Bearer token1"
    
    # Second call should get new token due to expiration
    headers2 = auth.get_auth_headers()
    assert headers2["Authorization"] == "Bearer token2"
    
    assert mock_post.call_count == 2