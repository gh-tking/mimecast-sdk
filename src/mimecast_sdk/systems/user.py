"""
User management API client for Mimecast
"""
from typing import Dict, Any, Optional
from .base import BaseAPI

class UserAPI(BaseAPI):
    """User management API client"""
    
    def add_delegate(
        self,
        delegate_address: str,
        primary_address: str
    ) -> Dict[str, Any]:
        """
        Add a delegate user to a primary user's account
        
        Args:
            delegate_address: Email address of the delegate user
            primary_address: Email address of the primary user
            
        Returns:
            Dict containing the response status
            
        Example response:
            {
                "meta": {
                    "status": 200
                },
                "data": [
                    {
                        "primaryAddress": "primary@example.com",
                        "delegateAddress": "delegate@example.com",
                        "status": "updated"
                    }
                ]
            }
            
        Note:
            The delegate user will be able to:
            - Send emails on behalf of the primary user
            - Access the primary user's archive
            - Perform actions on behalf of the primary user
        """
        data = {
            "data": [{
                "delegateAddress": delegate_address,
                "primaryAddress": primary_address
            }]
        }
        
        return self._post("/api/user/add-delegate-user", json=data)