"""
Breed Aggregator Service
Combines data from all external APIs into a single response
This is the orchestration layer
"""

import logging
from typing import Dict
from django.core.cache import cache

from info.services.wikipedia_service import WikipediaService
from info.services.dog_api_service import DogAPIService
from info.services.cat_api_service import CatAPIService
from info.constants import BREED_CACHE_KEY_PREFIX, BREED_CACHE_TTL
from info.exceptions import BreedNotFoundException, InvalidSpeciesException

logger = logging.getLogger(__name__)


class BreedAggregator:
    """
    Aggregates breed data from multiple APIs:
    1. Wikipedia → description + main image
    2. Dog/Cat API → characteristics + gallery
    3. YouTube → REMOVED (now handled in views.py to avoid quota issues)
    
    Returns a unified data structure
    """
    
    def __init__(self):
        self.wikipedia_service = WikipediaService()
        self.dog_api_service = DogAPIService()
        self.cat_api_service = CatAPIService()
        # YouTube service removed - handled in views.py now
    
    def _get_cache_key(self, breed_name: str, species: str) -> str:
        """Generate cache key for breed data"""
        safe_name = breed_name.lower().replace(' ', '_').replace(':', '_')
        return f"breed_info_{species}_{safe_name}"
    
    def fetch_breed_data(
        self,
        breed_name: str,
        species: str,
        force_refresh: bool = False
    ) -> Dict[str, any]:
        """
        Main aggregation method
        
        Workflow:
        1. Check cache (unless force_refresh)
        2. Fetch from Wikipedia
        3. Fetch from Dog/Cat API (based on species)
        4. Merge all data
        5. Cache result
        6. Return unified response
        
        Args:
            breed_name: Breed name
            species: Species type (dog, cat, etc.)
            force_refresh: Skip cache and re-fetch
            
        Returns:
            Dict with merged breed data
            
        Raises:
            BreedNotFoundException: If breed not found in any API
            InvalidSpeciesException: If species is invalid
        """
        
        # Validate species
        from info.constants import SPECIES_CHOICES
        valid_species = [choice[0] for choice in SPECIES_CHOICES]
        if species not in valid_species:
            raise InvalidSpeciesException(species)
        
        # Check cache first
        cache_key = self._get_cache_key(breed_name, species)
        if not force_refresh:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Returning cached breed data: {breed_name}")
                return cached_data
        
        logger.info(f"Fetching breed data from APIs: {breed_name} ({species})")
        
        # Initialize result
        merged_data = {
            'name': breed_name,
            'species': species,
            'description': '',
            'origin': '',
            'life_span': '',
            'temperament': '',
            'weight': '',
            'height': '',
            'main_image': None,
            'gallery_images': [],
            'youtube_videos': [],  # Will be populated by views.py
            'wikipedia_url': '',
        }
        
        # Track if we found any data
        found_any_data = False
        
        # ==================== STEP 1: Wikipedia ====================
        try:
            logger.info(f"[1/2] Fetching Wikipedia data for: {breed_name}")
            wiki_data = self.wikipedia_service.fetch_breed_info(breed_name)
            
            if wiki_data.get('description'):
                found_any_data = True
                merged_data['description'] = wiki_data['description']
                merged_data['wikipedia_url'] = wiki_data.get('wikipedia_url', '')
                
                # Use Wikipedia image as main image if available
                if wiki_data.get('main_image'):
                    merged_data['main_image'] = wiki_data['main_image']
                
                # Use Wikipedia origin if available
                if wiki_data.get('origin'):
                    merged_data['origin'] = wiki_data['origin']
            
            logger.info(f"Wikipedia data fetched: {bool(wiki_data.get('description'))}")
            
        except Exception as e:
            logger.error(f"Wikipedia fetch failed: {e}")
        
        # ==================== STEP 2: Dog/Cat API ====================
        try:
            logger.info(f"[2/2] Fetching {species} API data for: {breed_name}")
            
            # Select appropriate service
            if species == 'dog':
                api_service = self.dog_api_service
            elif species == 'cat':
                api_service = self.cat_api_service
            else:
                logger.info(f"No specific API for species: {species}")
                api_service = None
            
            if api_service:
                api_data = api_service.fetch_breed_info(breed_name)
                
                if api_data.get('temperament'):
                    found_any_data = True
                    merged_data['life_span'] = api_data.get('life_span', '')
                    merged_data['temperament'] = api_data.get('temperament', '')
                    merged_data['weight'] = api_data.get('weight', '')
                    merged_data['height'] = api_data.get('height', '')
                    
                    # Use gallery images
                    gallery = api_data.get('gallery_images', [])
                    if gallery:
                        merged_data['gallery_images'] = gallery
                        
                        # Use first gallery image as main if no Wikipedia image
                        if not merged_data['main_image'] and len(gallery) > 0:
                            merged_data['main_image'] = gallery[0]
                    
                    # Override origin if API provides it (Cat API)
                    if api_data.get('origin') and not merged_data['origin']:
                        merged_data['origin'] = api_data['origin']
                    
                    # Override description if API provides it (Cat API)
                    if api_data.get('description') and not merged_data['description']:
                        merged_data['description'] = api_data['description']
                
                logger.info(f"{species.title()} API data fetched: {bool(api_data.get('temperament'))}")
            
        except Exception as e:
            logger.error(f"{species.title()} API fetch failed: {e}")
        
        # ==================== YouTube - SKIPPED ====================
        # YouTube videos are now generated in views.py without API calls
        # to avoid quota limits. This prevents the 403 errors you were seeing.
        logger.info(f"YouTube videos will be generated by views.py (no API call)")
        
        # ==================== Validation ====================
        
        if not found_any_data:
            logger.warning(f"No data found for breed: {breed_name}")
            raise BreedNotFoundException(breed_name, species)
        
        # ==================== Cache Result ====================
        
        cache.set(cache_key, merged_data, BREED_CACHE_TTL)
        logger.info(f"Cached breed data: {cache_key}")
        
        logger.info(
            f"Successfully aggregated breed data: {breed_name} "
            f"(description: {bool(merged_data['description'])}, "
            f"images: {len(merged_data['gallery_images'])})"
        )
        
        return merged_data