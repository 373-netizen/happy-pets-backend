"""
Wikipedia API Service
Fetches breed description and main image from Wikipedia
"""

import logging
from typing import Dict, Optional

from info.services.base_service import BaseAPIService
from info.constants import WIKIPEDIA_BASE_URL, BREED_CACHE_TTL
from info.exceptions import WikipediaAPIException

logger = logging.getLogger(__name__)


class WikipediaService(BaseAPIService):
    """
    Service for fetching breed data from Wikipedia REST API
    
    API Docs: https://en.wikipedia.org/api/rest_v1/
    """
    
    @property
    def base_url(self) -> str:
        return WIKIPEDIA_BASE_URL
    
    @property
    def service_name(self) -> str:
        return "Wikipedia"
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': 'PetPlatform/1.0 (Breed Information System)',
            'Accept': 'application/json',
        }
    
    def search_page(self, breed_name: str) -> Optional[str]:
        """
        Search for Wikipedia page title
        
        Args:
            breed_name: Breed name to search
            
        Returns:
            Page title if found, None otherwise
        """
        try:
            endpoint = f"/page/title/{breed_name}"
            
            logger.info(f"Searching Wikipedia for: {breed_name}")
            
            # Try direct page access first
            try:
                response = self.get(endpoint)
                if response and 'title' in response:
                    logger.info(f"Found Wikipedia page: {response['title']}")
                    return response['title']
            except Exception:
                pass
            
            # Fallback: search endpoint
            search_endpoint = f"/page/search/{breed_name}"
            response = self.get(search_endpoint)
            
            if response and 'pages' in response and len(response['pages']) > 0:
                # Get first result
                first_result = response['pages'][0]
                page_title = first_result.get('title')
                logger.info(f"Found via search: {page_title}")
                return page_title
            
            logger.warning(f"No Wikipedia page found for: {breed_name}")
            return None
            
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return None
    
    def fetch_summary(self, page_title: str) -> Dict[str, any]:
        """
        Fetch page summary and extract data
        
        Args:
            page_title: Wikipedia page title
            
        Returns:
            Dict with description, image, and URL
        """
        try:
            endpoint = f"/page/summary/{page_title}"
            
            cache_key = f"wikipedia_{page_title.lower().replace(' ', '_')}"
            response = self.get(
                endpoint,
                cache_key=cache_key,
                cache_ttl=BREED_CACHE_TTL
            )
            
            if not response:
                raise WikipediaAPIException("Empty response from Wikipedia")
            
            # Extract data
            data = {
                'description': response.get('extract', ''),
                'main_image': None,
                'wikipedia_url': response.get('content_urls', {}).get('desktop', {}).get('page', ''),
                'origin': self._extract_origin(response),
            }
            
            # Get thumbnail/image
            thumbnail = response.get('thumbnail', {})
            if thumbnail and 'source' in thumbnail:
                data['main_image'] = thumbnail['source']
            elif 'originalimage' in response:
                data['main_image'] = response['originalimage'].get('source')
            
            logger.info(f"Successfully fetched Wikipedia data for: {page_title}")
            return data
            
        except WikipediaAPIException:
            raise
        except Exception as e:
            logger.error(f"Error fetching Wikipedia summary: {e}")
            raise WikipediaAPIException(f"Failed to fetch summary: {str(e)}")
    
    def _extract_origin(self, response: Dict) -> str:
        """
        Try to extract origin/country from Wikipedia response
        This is a best-effort extraction
        """
        try:
            # Check description for country mentions
            description = response.get('extract', '')
            
            # Common patterns
            if 'originated in' in description.lower():
                # Extract text after "originated in"
                parts = description.lower().split('originated in')
                if len(parts) > 1:
                    origin_text = parts[1].split('.')[0].strip()
                    return origin_text[:100]  # Limit length
            
            # Check for "from [Country]" pattern
            if ' from ' in description.lower():
                parts = description.lower().split(' from ')
                if len(parts) > 1:
                    origin_text = parts[1].split('.')[0].split(',')[0].strip()
                    return origin_text[:100]
            
            return ''
            
        except Exception as e:
            logger.debug(f"Could not extract origin: {e}")
            return ''
    
    def fetch_breed_info(self, breed_name: str) -> Dict[str, any]:
        """
        Main method: Search and fetch breed information
        
        Args:
            breed_name: Breed name
            
        Returns:
            Dict with breed data from Wikipedia
        """
        # Step 1: Search for page
        page_title = self.search_page(breed_name)
        
        if not page_title:
            logger.warning(f"Wikipedia: No page found for '{breed_name}'")
            return {
                'description': '',
                'main_image': None,
                'wikipedia_url': '',
                'origin': '',
            }
        
        # Step 2: Fetch summary
        return self.fetch_summary(page_title)