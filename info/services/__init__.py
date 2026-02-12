"""
Service layer for external API integrations
"""

from .base_service import BaseAPIService
from .wikipedia_service import WikipediaService
from .dog_api_service import DogAPIService
from .cat_api_service import CatAPIService
from .youtube_service import YouTubeService
from .breed_aggregator import BreedAggregator

__all__ = [
    'BaseAPIService',
    'WikipediaService',
    'DogAPIService',
    'CatAPIService',
    'YouTubeService',
    'BreedAggregator',
]