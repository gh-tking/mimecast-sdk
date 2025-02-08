"""
Authentication module for Mimecast API 2.0
"""
from datetime import datetime, timedelta
import requests
from typing import Optional, Dict

class MimecastAuth:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: Optional[str] = None
    ):
        """
        Initialize Mimecast API 2.0 authentication
        
        Args:
            client_id: The client ID obtained from Mimecast
            client_secret: The client secret obtained from Mimecast
            base_url: Optional base URL for the API (defaults to US)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url or "https://api.services.mimecast.com"
        self._token = None
        self._token_expiry = None

    def _get_access_token(self) -> str:
        """
        Get an access token using client credentials flow
        
        Returns:
            The access token string
        
        Raises:
            requests.exceptions.RequestException: If the authentication request fails
        """
        url = f"{self.base_url}/oauth/token"
        
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        
        token_data = response.json()
        self._token = token_data['access_token']
        # Set token expiry with a small buffer (e.g., 5 minutes)
        self._token_expiry = datetime.now() + timedelta(seconds=token_data['expires_in'] - 300)
        
        return self._token

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for Mimecast API 2.0 request
        
        Returns:
            Dict containing the required headers for authentication
        """
        # Check if we need to get a new token
        if not self._token or datetime.now() >= self._token_expiry:
            self._get_access_token()
        
        return {
            'Authorization': f'Bearer {self._token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }