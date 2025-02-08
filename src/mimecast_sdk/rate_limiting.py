"""
Rate limiting implementation for Mimecast API
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from threading import Lock
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded and retry attempts exhausted"""
    pass

class RateLimitHandler:
    """
    Handles Mimecast API rate limiting
    
    Attributes:
        max_retries: Maximum number of retry attempts
        min_backoff: Minimum backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        jitter: Whether to add jitter to backoff times
    """
    
    # Rate limit header names
    LIMIT_HEADER = 'x-mc-rate-limit'
    REMAINING_HEADER = 'x-mc-rate-limit-remaining'
    RESET_HEADER = 'x-mc-rate-limit-reset'
    
    def __init__(
        self,
        max_retries: int = 3,
        min_backoff: float = 1.0,
        max_backoff: float = 60.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.min_backoff = min_backoff
        self.max_backoff = max_backoff
        self.jitter = jitter
        
        # Rate limit tracking
        self._rate_limits: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
    
    def _get_endpoint_key(self, url: str) -> str:
        """Extract endpoint key from URL for rate limit tracking"""
        # Remove query parameters and normalize
        base_url = url.split('?')[0].rstrip('/')
        # Extract endpoint path
        path = '/'.join(base_url.split('/')[-2:])
        return path
    
    def _update_rate_limits(self, endpoint: str, response: requests.Response) -> None:
        """Update rate limit information from response headers"""
        with self._lock:
            limit = response.headers.get(self.LIMIT_HEADER)
            remaining = response.headers.get(self.REMAINING_HEADER)
            reset = response.headers.get(self.RESET_HEADER)
            
            if all([limit, remaining, reset]):
                try:
                    self._rate_limits[endpoint] = {
                        'limit': int(limit),
                        'remaining': int(remaining),
                        'reset': datetime.fromtimestamp(int(reset)),
                        'last_updated': datetime.now()
                    }
                    logger.debug(
                        f"Rate limits for {endpoint}: "
                        f"{remaining}/{limit} remaining, "
                        f"resets at {self._rate_limits[endpoint]['reset']}"
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse rate limit headers: {e}")
    
    def _calculate_backoff(self, retry_count: int) -> float:
        """Calculate backoff time using exponential backoff with optional jitter"""
        backoff = min(
            self.max_backoff,
            self.min_backoff * (2 ** retry_count)
        )
        
        if self.jitter:
            import random
            backoff = backoff * (0.5 + random.random())
        
        return backoff
    
    def _should_retry(self, endpoint: str) -> tuple[bool, float]:
        """
        Check if request should be retried and calculate wait time
        
        Returns:
            Tuple of (should_retry, wait_time_seconds)
        """
        with self._lock:
            rate_info = self._rate_limits.get(endpoint)
            if not rate_info:
                return True, 0
            
            # If we have remaining requests, allow immediately
            if rate_info['remaining'] > 0:
                return True, 0
            
            # Calculate time until reset
            now = datetime.now()
            if rate_info['reset'] > now:
                wait_time = (rate_info['reset'] - now).total_seconds()
                return True, wait_time + 1  # Add 1 second buffer
            
            # Reset time has passed, allow retry
            return True, 0
    
    def create_retry_session(self) -> requests.Session:
        """Create a requests Session with retry configuration"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.min_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def handle_request(
        self,
        method: str,
        url: str,
        session: Optional[requests.Session] = None,
        **kwargs
    ) -> requests.Response:
        """
        Make a request with rate limit handling
        
        Args:
            method: HTTP method
            url: Request URL
            session: Optional requests Session to use
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded and retries exhausted
            requests.exceptions.RequestException: For other request errors
        """
        endpoint = self._get_endpoint_key(url)
        retry_count = 0
        session = session or self.create_retry_session()
        
        while retry_count <= self.max_retries:
            # Check rate limits before making request
            should_retry, wait_time = self._should_retry(endpoint)
            if should_retry and wait_time > 0:
                logger.warning(
                    f"Rate limit reached for {endpoint}, "
                    f"waiting {wait_time:.1f} seconds"
                )
                time.sleep(wait_time)
            
            try:
                response = session.request(method, url, **kwargs)
                
                # Update rate limits from response headers
                self._update_rate_limits(endpoint, response)
                
                # Handle rate limit response
                if response.status_code == 429:
                    retry_count += 1
                    if retry_count > self.max_retries:
                        raise RateLimitExceeded(
                            f"Rate limit exceeded for {endpoint} "
                            f"after {self.max_retries} retries"
                        )
                    
                    # Calculate backoff time
                    backoff = self._calculate_backoff(retry_count)
                    logger.warning(
                        f"Rate limit response for {endpoint}, "
                        f"attempt {retry_count}/{self.max_retries}, "
                        f"backing off for {backoff:.1f} seconds"
                    )
                    time.sleep(backoff)
                    continue
                
                # Return successful response
                return response
                
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count > self.max_retries:
                    raise
                
                backoff = self._calculate_backoff(retry_count)
                logger.warning(
                    f"Request failed for {endpoint}, "
                    f"attempt {retry_count}/{self.max_retries}, "
                    f"backing off for {backoff:.1f} seconds: {str(e)}"
                )
                time.sleep(backoff)
        
        raise RateLimitExceeded(
            f"Max retries ({self.max_retries}) exceeded for {endpoint}"
        )