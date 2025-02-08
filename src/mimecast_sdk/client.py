"""
Mimecast API 2.0 Client
"""
import logging
from typing import Optional, Dict, Any
import requests

from .auth import MimecastAuth
from .rate_limiting import RateLimitHandler, RateLimitExceeded

logger = logging.getLogger(__name__)

class MimecastClient:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        min_backoff: float = 1.0,
        max_backoff: float = 60.0,
        jitter: bool = True
    ):
        """
        Initialize Mimecast API 2.0 client
        
        If credentials are not provided, they will be loaded from the configuration
        file or vault based on the configuration.
        
        Args:
            client_id: Optional client ID (if not provided, loaded from config/vault)
            client_secret: Optional client secret (if not provided, loaded from config/vault)
            base_url: Optional base URL (if not provided, loaded from config or defaults to US)
            max_retries: Maximum number of retry attempts (default: 3)
            min_backoff: Minimum backoff time in seconds (default: 1.0)
            max_backoff: Maximum backoff time in seconds (default: 60.0)
            jitter: Whether to add jitter to backoff times (default: True)
        """
        self.base_url = base_url or 'https://api.services.mimecast.com'
        
        if not (client_id and client_secret):
            raise ValueError(
                "client_id and client_secret are required"
            )
            
        self.auth = MimecastAuth(
            client_id=client_id,
            client_secret=client_secret,
            base_url=self.base_url
        )
        
        # Initialize rate limiting
        self.rate_limiter = RateLimitHandler(
            max_retries=max_retries,
            min_backoff=min_backoff,
            max_backoff=max_backoff,
            jitter=jitter
        )
        
        # Create session with retry configuration
        self.session = self.rate_limiter.create_retry_session()

    @classmethod
    def from_vault(
        cls,
        vault_type: str,
        vault_config: Dict[str, Any],
        base_url: Optional[str] = None,
        **kwargs
    ) -> 'MimecastClient':
        """
        Create client instance using credentials from a vault
        
        Args:
            vault_type: Type of vault ('aws', 'azure', 'kubernetes')
            vault_config: Vault configuration
            base_url: Optional base URL
            **kwargs: Additional arguments for MimecastClient
            
        Returns:
            MimecastClient instance
        """
        if vault_type == 'aws':
            vault = AWSSecretsManager(region_name=vault_config['region'])
        elif vault_type == 'azure':
            vault = AzureKeyVault(vault_url=vault_config['vault_url'])
        elif vault_type == 'kubernetes':
            vault = KubernetesSecrets(namespace=vault_config['namespace'])
        else:
            raise ValueError(f"Unsupported vault provider: {vault_type}")
        
        client_id = vault.get_secret('mimecast/client_id')
        client_secret = vault.get_secret('mimecast/client_secret')
        
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            **kwargs
        )

    def request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> requests.Response:
        """
        Make a request to the Mimecast API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/api/v2/email/send")
            json: Optional JSON payload
            **kwargs: Additional arguments passed to requests
            
        Returns:
            requests.Response object
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded and retries exhausted
            requests.exceptions.RequestException: For other request errors
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = self.auth.get_auth_headers()
        
        # Update headers with any provided in kwargs
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        try:
            response = self.rate_limiter.handle_request(
                method=method,
                url=url,
                session=self.session,
                json=json,
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            # Log the full response for debugging
            logger.debug(f"Full API Response: {response.text}")
            return response
            
        except RateLimitExceeded as e:
            logger.error(f"Rate limit exceeded: {str(e)}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Convenience method for GET requests"""
        return self.request('GET', endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Convenience method for POST requests"""
        return self.request('POST', endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """Convenience method for PUT requests"""
        return self.request('PUT', endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Convenience method for DELETE requests"""
        return self.request('DELETE', endpoint, **kwargs)