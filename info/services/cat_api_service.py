"""
Cat API Service - Fetches breed data from TheCatAPI.com
"""

import requests
from django.conf import settings
from django.core.cache import cache

class CatAPIService:
    BASE_URL = "https://api.thecatapi.com/v1"
    CACHE_TIMEOUT = 86400  # 24 hours
    
    def __init__(self):
        self.api_key = getattr(settings, 'CAT_API_KEY', None)
        
        # CRITICAL: Set up headers with API key
        self.headers = {
            'x-api-key': self.api_key
        } if self.api_key else {}
        
        if not self.api_key:
            print("⚠️  WARNING: CAT_API_KEY not found in settings")
    
    def fetch_breed_info(self, breed_name):
        """
        Fetch comprehensive breed data from TheCatAPI
        
        Args:
            breed_name (str): Name of the cat breed
            
        Returns:
            dict: Breed information including temperament, stats, images
        """
        # Check cache first
        cache_key = f'cat_api:{breed_name.lower()}'
        cached_data = cache.get(cache_key)
        if cached_data:
            print(f"[CatAPI] Using cached data for '{breed_name}'")
            return cached_data
        
        try:
            # Search for breed
            search_url = f"{self.BASE_URL}/breeds/search"
            params = {'q': breed_name}
            
            print(f"[CatAPI] Searching for: {breed_name}")
            
            response = requests.get(
                search_url, 
                params=params, 
                headers=self.headers,
                timeout=10
            )
            
            response.raise_for_status()
            breeds = response.json()
            
            if not breeds:
                print(f"Cat API: No data found for '{breed_name}'")
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
                'origin': breed.get('origin', ''),
                'description': breed.get('description', ''),
                'intelligence': breed.get('intelligence', 0),
                'affection_level': breed.get('affection_level', 0),
                'energy_level': breed.get('energy_level', 0),
                'gallery_images': gallery_images,
                'reference_image': breed.get('reference_image_id', ''),
            }
            
            # Cache the result
            cache.set(cache_key, result, self.CACHE_TIMEOUT)
            print(f"[CatAPI] Successfully fetched data for '{breed_name}'")
            
            return result
            
        except requests.exceptions.HTTPError as e:
            print(f"[TheCatAPI] HTTP error: {e}")
            if e.response.status_code == 403:
                print(f"[TheCatAPI] 403 Forbidden - Check your API key in settings.py")
                print(f"[TheCatAPI] Current API key: {self.api_key[:20] if self.api_key else 'None'}...")
            try:
                print(f"[TheCatAPI] Response: {e.response.json()}")
            except:
                print(f"[TheCatAPI] Response: {e.response.text}")
            return self._empty_response()
            
        except requests.exceptions.RequestException as e:
            print(f"Cat API request error: {e}")
            return self._empty_response()
        
        except Exception as e:
            print(f"Cat API error: {e}")
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
            print(f"Cat API image fetch error: {e}")
            return []
    
    def _empty_response(self):
        """Return empty structure when API fails"""
        return {
            'temperament': '',
            'life_span': '',
            'weight': '',
            'origin': '',
            'description': '',
            'intelligence': 0,
            'affection_level': 0,
            'energy_level': 0,
            'gallery_images': [],
            'reference_image': '',
        }