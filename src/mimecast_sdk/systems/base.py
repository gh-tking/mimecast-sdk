"""
Base class for Mimecast API systems
"""
from typing import Optional, Dict, Any
from ..client import MimecastClient

class BaseAPI:
    def __init__(
        self,
        client: Optional[MimecastClient] = None,
        **kwargs
    ):
        """
        Initialize base API class

        Args:
            client: Optional MimecastClient instance
            **kwargs: Additional arguments passed to MimecastClient if client not provided
        """
        self.client = client or MimecastClient(**kwargs)
        
    def _check_response_errors(self, json_response: Dict[str, Any]) -> None:
        """
        Check for errors in Mimecast API response
        
        Args:
            json_response: JSON response from API
            
        Raises:
            ValueError: If API returns any errors
        """
        # Check meta status
        meta = json_response.get('meta', {})
        if meta.get('status') == 'fail':
            errors = meta.get('errors', [])
            error_messages = '; '.join(f"{e.get('code')}: {e.get('message')}" for e in errors)
            raise ValueError(f"Mimecast API error: {error_messages}")
        
        # Check fail array
        fail = json_response.get('fail', [])
        if fail:
            errors = []
            for failure in fail:
                errors.extend(failure.get('errors', []))
            error_messages = '; '.join(f"{e.get('code')}: {e.get('message')}" for e in errors)
            raise ValueError(f"Mimecast API error: {error_messages}")

    def _get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make GET request and return JSON data"""
        response = self.client.get(endpoint, **kwargs)
        json_response = response.json()
        self._check_response_errors(json_response)
        return json_response.get('data', {})

    def _post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make POST request and return JSON data"""
        response = self.client.post(endpoint, **kwargs)
        json_response = response.json()
        self._check_response_errors(json_response)
        return json_response.get('data', {})

    def _put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make PUT request and return JSON data"""
        response = self.client.put(endpoint, **kwargs)
        json_response = response.json()
        self._check_response_errors(json_response)
        return json_response.get('data', {})

    def _delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request and return JSON data"""
        response = self.client.delete(endpoint, **kwargs)
        json_response = response.json()
        self._check_response_errors(json_response)
        return json_response.get('data', {})