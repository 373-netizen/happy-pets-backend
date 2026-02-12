"""
Dog API Service - Fetches breed data from TheDogAPI.com
"""

import requests
from django.conf import settings
from django.core.cache import cache

class DogAPIService:
    BASE_URL = "https://api.thedogapi.com/v1"
    CACHE_TIMEOUT = 86400  # 24 hours
    
    def __init__(self):
        self.api_key = getattr(settings, 'DOG_API_KEY', None)
        
        # CRITICAL: Set up headers with API key
        self.headers = {
            'x-api-key': self.api_key
        } if self.api_key else {}
        
        if not self.api_key:
            print("⚠️  WARNING: DOG_API_KEY not found in settings")
    
"""
The Dog API Service
Fetches dog breed images and characteristics
"""

import logging
from typing import Dict, List, Optional
from django.conf import settings
from django.core.cache import cache

from info.services.base_service import BaseAPIService
from info.constants import (
    DOG_API_BASE_URL,
    GALLERY_IMAGE_LIMIT,
    MIN_IMAGE_WIDTH,
    MIN_IMAGE_HEIGHT,
)
from info.exceptions import DogAPIException

logger = logging.getLogger(__name__)


class DogAPIService(BaseAPIService):
    """
    Service for The Dog API
    
    API Docs: https://docs.thedogapi.com/
    Get API key from: https://thedogapi.com/signup
    """
    
    @property
    def base_url(self) -> str:
        return DOG_API_BASE_URL
    
    @property
    def service_name(self) -> str:
        return "TheDogAPI"
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            'Accept': 'application/json',
        }
        
        # Add API key if configured
        api_key = getattr(settings, 'DOG_API_KEY', None)
        if api_key:
            headers['x-api-key'] = api_key
        else:
            logger.warning("DOG_API_KEY not configured in settings")
        
        return headers
    
    def search_breed(self, breed_name: str) -> Optional[Dict]:
        """
        Search for breed by name
        
        Args:
            breed_name: Breed name to search
            
        Returns:
            Breed data dict or None
        """
        try:
            endpoint = "/breeds/search"
            params = {'q': breed_name}
            
            logger.info(f"Searching for dog breed: {breed_name}")
            
            response = self.get(endpoint, params=params)
            
            if response and len(response) > 0:
                logger.info(f"Found dog breed: {breed_name}")
                return response[0]  # Return first match
            
            logger.warning(f"No dog breed found for: {breed_name}")
            return None
            
        except Exception as e:
            logger.error(f"Dog API search error: {e}")
            return None
    
    def fetch_breed_images(self, breed_id: int, limit: int = GALLERY_IMAGE_LIMIT) -> List[str]:
        """
        Fetch breed images
        
        Args:
            breed_id: The Dog API breed ID
            limit: Maximum number of images
            
        Returns:
            List of image URLs
        """
        try:
            endpoint = "/images/search"
            params = {
                'breed_ids': breed_id,
                'limit': limit,
                'size': 'med',  # medium size images
            }
            
            response = self.get(endpoint, params=params)
            
            if not response:
                return []
            
            # Extract and filter image URLs
            images = []
            for img in response:
                url = img.get('url')
                width = img.get('width', 0)
                height = img.get('height', 0)
                
                # Filter by quality
                if url and width >= MIN_IMAGE_WIDTH and height >= MIN_IMAGE_HEIGHT:
                    images.append(url)
            
            logger.info(f"Fetched {len(images)} dog images for breed_id={breed_id}")
            return images[:GALLERY_IMAGE_LIMIT]  # Limit results
            
        except Exception as e:
            logger.error(f"Error fetching dog images: {e}")
            return []
    
    def fetch_breed_info(self, breed_name: str) -> Dict[str, any]:
        """
        Main method: Fetch complete breed information
        
        Args:
            breed_name: Dog breed name
            
        Returns:
            Dict with breed characteristics and images
        """
        # Create sanitized cache key
        safe_name = breed_name.lower().replace(' ', '_')
        cache_key = f"dog_api_{safe_name}"
        cache_ttl = 3600  # 1 hour
        
        # Check cache
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"[DogAPI] Cache hit for: {breed_name}")
            return cached
        
        # Search for breed
        breed_data = self.search_breed(breed_name)
        
        if not breed_data:
            logger.warning(f"Dog API: No data found for '{breed_name}'")
            result = {
                'life_span': '',
                'temperament': '',
                'weight': '',
                'height': '',
                'gallery_images': [],
                'breed_group': '',
                'origin': '',
            }
            cache.set(cache_key, result, cache_ttl)
            return result
        
        # Extract breed ID
        breed_id = breed_data.get('id')
        
        # Fetch images
        gallery_images = []
        if breed_id:
            gallery_images = self.fetch_breed_images(breed_id)
        
        # Extract characteristics
        weight_metric = breed_data.get('weight', {}).get('metric', '')
        height_metric = breed_data.get('height', {}).get('metric', '')
        
        result = {
            'life_span': breed_data.get('life_span', ''),
            'temperament': breed_data.get('temperament', ''),
            'weight': f"{weight_metric} kg" if weight_metric else '',
            'height': f"{height_metric} cm" if height_metric else '',
            'gallery_images': gallery_images,
            'breed_group': breed_data.get('breed_group', ''),
            'origin': breed_data.get('origin', ''),
            'bred_for': breed_data.get('bred_for', ''),
        }
        
        # Cache result
        cache.set(cache_key, result, cache_ttl)
        logger.info(f"Successfully fetched dog breed info: {breed_name}")
        
        return result
        
        try:
            # Search for breed
            search_url = f"{self.BASE_URL}/breeds/search"
            params = {'q': breed_name}
            
            print(f"[DogAPI] Searching for: {breed_name}")
            print(f"[DogAPI] URL: {search_url}")
            print(f"[DogAPI] Headers: {self.headers}")
            
            response = requests.get(
                search_url, 
                params=params, 
                headers=self.headers,
                timeout=10
            )
            
            response.raise_for_status()
            breeds = response.json()
            
            if not breeds:
                print(f"Dog API: No data found for '{breed_name}'")
                return self._empty_response()
            
            breed = breeds[0]
            breed_id = breed.get('id')
            
            # Fetch images for this breed
            gallery_images = self._fetch_breed_images(breed_id) if breed_id else []
            
            # Structure the data
            result = {
                'temperament': breed.get('temperament', ''),
                'life_span': breed.get('life_span', ''),
                'weight': breed.get('weight', {}).get('metric', ''),
                'height': breed.get('height', {}).get('metric', ''),
                'bred_for': breed.get('bred_for', ''),
                'breed_group': breed.get('breed_group', ''),
                'origin': breed.get('origin', ''),
                'gallery_images': gallery_images,
                'reference_image': breed.get('reference_image_id', ''),
            }
            
            # Cache the result
            cache.set(cache_key, result, self.CACHE_TIMEOUT)
            print(f"[DogAPI] Successfully fetched data for '{breed_name}'")
            
            return result
            
        except requests.exceptions.HTTPError as e:
            print(f"[TheDogAPI] HTTP error: {e}")
            if e.response.status_code == 403:
                print(f"[TheDogAPI] 403 Forbidden - Check your API key in settings.py")
                print(f"[TheDogAPI] Current API key: {self.api_key[:20] if self.api_key else 'None'}...")
            try:
                print(f"[TheDogAPI] Response: {e.response.json()}")
            except:
                print(f"[TheDogAPI] Response: {e.response.text}")
            return self._empty_response()
            
        except requests.exceptions.RequestException as e:
            print(f"Dog API request error: {e}")
            return self._empty_response()
        
        except Exception as e:
            print(f"Dog API error: {e}")
            return self._empty_response()
    
    def _fetch_breed_images(self, breed_id, limit=5):
        """Fetch gallery images for a specific breed"""
        try:
            url = f"{self.BASE_URL}/images/search"
            params = {
                'breed_ids': breed_id,
                'limit': limit,
                'size': 'med'
            }
            
            response = requests.get(
                url, 
                params=params, 
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            images = response.json()
            return [img['url'] for img in images if 'url' in img]
            
        except Exception as e:
            print(f"Dog API image fetch error: {e}")
            return []
    
    def _empty_response(self):
        """Return empty structure when API fails"""
        return {
            'temperament': '',
            'life_span': '',
            'weight': '',
            'height': '',
            'bred_for': '',
            'breed_group': '',
            'origin': '',
            'gallery_images': [],
            'reference_image': '',
        }