"""
Domain management API client for Mimecast
"""
from typing import Dict, Any, Optional, List, Literal
from .base import BaseAPI

class DomainAPI(BaseAPI):
    """Domain management API client"""
    
    def create_domain(
        self,
        domain: str,
        segment: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        verify_by_txt: bool = False,
        verify_by_mx: bool = False,
        verify_by_dmarc: bool = False,
        verify_by_dkim: bool = False,
        verify_by_spf: bool = False,
        verify_by_link: bool = False,
        verify_by_email: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new domain in Mimecast
        
        Args:
            domain: Domain name to create
            segment: Optional segment ID
            aliases: Optional list of domain aliases
            verify_by_txt: Verify domain ownership using TXT record
            verify_by_mx: Verify domain using MX record
            verify_by_dmarc: Verify domain using DMARC record
            verify_by_dkim: Verify domain using DKIM record
            verify_by_spf: Verify domain using SPF record
            verify_by_link: Verify domain using link tracking
            verify_by_email: Verify domain using email
            
        Returns:
            Dict containing the response status and domain information
            
        Example:
            >>> api.create_domain(
            ...     domain="example.com",
            ...     aliases=["alias1.com", "alias2.com"],
            ...     verify_by_txt=True,
            ...     verify_by_mx=True
            ... )
            
        Note:
            At least one verification method must be selected.
            The domain must not already exist in Mimecast.
        """
        # Ensure at least one verification method is selected
        verification_methods = [
            verify_by_txt,
            verify_by_mx,
            verify_by_dmarc,
            verify_by_dkim,
            verify_by_spf,
            verify_by_link,
            verify_by_email
        ]
        if not any(verification_methods):
            raise ValueError("At least one verification method must be selected")
            
        data = {
            "data": [{
                "domain": domain,
                "verifyByTxt": verify_by_txt,
                "verifyByMx": verify_by_mx,
                "verifyByDmarc": verify_by_dmarc,
                "verifyByDkim": verify_by_dkim,
                "verifyBySpf": verify_by_spf,
                "verifyByLink": verify_by_link,
                "verifyByEmail": verify_by_email
            }]
        }
        
        # Add optional parameters
        if segment:
            data["data"][0]["segment"] = segment
        if aliases:
            data["data"][0]["aliases"] = aliases
            
        return self._post("/api/domain/create-domain", json=data)
        
    def get_pending_domains(
        self,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get pending domain verification status
        
        Args:
            domain: Optional domain name to filter results
            
        Returns:
            Dict containing pending domain information
            
        Example:
            >>> # Get all pending domains
            >>> api.get_pending_domains()
            
            >>> # Get specific domain status
            >>> api.get_pending_domains(domain="example.com")
            
        Example response:
            {
                "meta": {
                    "status": 200
                },
                "data": [
                    {
                        "domain": "example.com",
                        "verificationStatus": "pending",
                        "verificationMethods": [
                            {
                                "type": "txt",
                                "status": "pending",
                                "record": "txt-record-value",
                                "value": "txt-record-value"
                            }
                        ]
                    }
                ]
            }
        """
        data = {"data": [{}]}  # Empty filter by default
        
        if domain:
            data["data"][0]["domain"] = domain
            
        return self._post("/api/domain/get-pending-domain", json=data)