"""
Targeted Threat Protection (TTP) API client for Mimecast
"""
from typing import Dict, Any, Optional, List, Literal
from .base import BaseAPI

class TtpAPI(BaseAPI):
    """TTP API client"""
    
    def create_managed_url(
        self,
        urls: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create managed URLs for URL protection
        
        Args:
            urls: List of URL configurations, each containing:
                - action: "block" or "permit"
                - url: URL to manage
                - comment: Optional comment
                - disableLogClick: Whether to disable click logging
                - disableRewrite: Whether to disable URL rewriting
                - disableUserAwareness: Whether to disable user awareness
                - matchType: "domain" or "explicit"
            
        Returns:
            Dict containing the response status and created URLs
            
        Example:
            >>> api.create_managed_url([
            ...     {
            ...         "action": "block",
            ...         "url": "malicious.com",
            ...         "comment": "Known malware site",
            ...         "matchType": "domain"
            ...     },
            ...     {
            ...         "action": "permit",
            ...         "url": "trusted.com",
            ...         "matchType": "explicit"
            ...     }
            ... ])
        """
        data = {"data": urls}
        return self._post("/api/ttp/url/create-managed-url", json=data)
        
    def block_url(
        self,
        url: str,
        match_type: Literal["domain", "explicit"] = "domain",
        comment: Optional[str] = None,
        disable_log_click: bool = False,
        disable_rewrite: bool = False,
        disable_user_awareness: bool = False
    ) -> Dict[str, Any]:
        """
        Block a URL using URL protection
        
        Args:
            url: URL to block
            match_type: How to match the URL ("domain" or "explicit")
            comment: Optional comment about the block
            disable_log_click: Whether to disable click logging
            disable_rewrite: Whether to disable URL rewriting
            disable_user_awareness: Whether to disable user awareness
            
        Returns:
            Dict containing the response status
        """
        url_config = {
            "action": "block",
            "url": url,
            "matchType": match_type,
            "disableLogClick": disable_log_click,
            "disableRewrite": disable_rewrite,
            "disableUserAwareness": disable_user_awareness
        }
        
        if comment:
            url_config["comment"] = comment
            
        return self.create_managed_url([url_config])
        
    def permit_url(
        self,
        url: str,
        match_type: Literal["domain", "explicit"] = "explicit",
        comment: Optional[str] = None,
        disable_log_click: bool = False,
        disable_rewrite: bool = False,
        disable_user_awareness: bool = False
    ) -> Dict[str, Any]:
        """
        Permit a URL using URL protection
        
        Args:
            url: URL to permit
            match_type: How to match the URL ("domain" or "explicit")
            comment: Optional comment about the permission
            disable_log_click: Whether to disable click logging
            disable_rewrite: Whether to disable URL rewriting
            disable_user_awareness: Whether to disable user awareness
            
        Returns:
            Dict containing the response status
        """
        url_config = {
            "action": "permit",
            "url": url,
            "matchType": match_type,
            "disableLogClick": disable_log_click,
            "disableRewrite": disable_rewrite,
            "disableUserAwareness": disable_user_awareness
        }
        
        if comment:
            url_config["comment"] = comment
            
        return self.create_managed_url([url_config])