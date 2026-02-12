"""
Abstract base class for all external API services
Provides common functionality: HTTP calls, error handling, retries, logging
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

import requests
from django.core.cache import cache

from info.constants import (
    API_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
)
from info.exceptions import APIServiceException, RateLimitException

logger = logging.getLogger(__name__)


class BaseAPIService(ABC):
    """
    Abstract base class for external API services.
    
    Subclasses must implement:
        - base_url (property)
        - service_name (property)
        - _get_headers() (method)
    """
    
    def __init__(self):
        self.timeout = API_TIMEOUT
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
        self.session = requests.Session()
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Return the base URL for the API"""
        pass
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """Return the service name for logging"""
        pass
    
    @abstractmethod
    def _get_headers(self) -> Dict[str, str]:
        """Return headers for API requests"""
        pass
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from base URL and endpoint"""
        base = self.base_url.rstrip('/')
        endpoint = endpoint.lstrip('/')
        return f"{base}/{endpoint}"
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """
        Make HTTP request with retry logic and error handling
        """
        url = self._build_url(endpoint)
        request_headers = self._get_headers()
        
        if headers:
            request_headers.update(headers)
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"[{self.service_name}] {method} {url} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers,
                    timeout=self.timeout,
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', 60)
                    raise RateLimitException(
                        self.service_name,
                        retry_after=int(retry_after)
                    )
                
                # Raise for 4xx/5xx errors
                response.raise_for_status()
                
                logger.info(
                    f"[{self.service_name}] Success: {method} {url} "
                    f"(status: {response.status_code})"
                )
                
                return response
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(
                    f"[{self.service_name}] Timeout on attempt {attempt + 1}: {e}"
                )
                
            except requests.exceptions.HTTPError as e:
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    logger.error(f"[{self.service_name}] Client error: {e}")
                    raise APIServiceException(
                        self.service_name,
                        f"HTTP {e.response.status_code}: {e.response.text}",
                        e.response.status_code
                    )
                last_exception = e
                logger.warning(
                    f"[{self.service_name}] HTTP error on attempt {attempt + 1}: {e}"
                )
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(
                    f"[{self.service_name}] Request error on attempt {attempt + 1}: {e}"
                )
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        error_msg = f"Failed after {self.max_retries} attempts: {last_exception}"
        logger.error(f"[{self.service_name}] {error_msg}")
        raise APIServiceException(self.service_name, error_msg)
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None,
        cache_ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Make GET request with optional caching
        """
        # Sanitize cache key
        if cache_key:
            cache_key = cache_key.replace(' ', '_').replace(':', '_').replace('/', '_')
        
        # Check cache first
        if cache_key:
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.info(f"[{self.service_name}] Cache hit: {cache_key}")
                return cached_data
        
        # Make request
        response = self._make_request('GET', endpoint, params=params)
        
        # Parse JSON
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"[{self.service_name}] JSON parse error: {e}")
            raise APIServiceException(self.service_name, f"Invalid JSON: {e}")
        
        # Cache result
        if cache_key and cache_ttl:
            cache.set(cache_key, data, cache_ttl)
            logger.info(f"[{self.service_name}] Cached: {cache_key}")
        
        return data
    
    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make POST request"""
        response = self._make_request('POST', endpoint, params=params, data=data)
        return response.json()
    
    def __del__(self):
        """Close session on cleanup"""
        if hasattr(self, 'session'):
            self.session.close()