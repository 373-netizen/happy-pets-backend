"""
YouTube Data API Service
Fetches breed-related videos
"""

import logging
from typing import Dict, List
from django.conf import settings

from info.services.base_service import BaseAPIService
from info.constants import YOUTUBE_VIDEO_LIMIT
from info.exceptions import YouTubeAPIException

logger = logging.getLogger(__name__)


class YouTubeService(BaseAPIService):
    """
    Service for YouTube Data API v3
    
    API Docs: https://developers.google.com/youtube/v3
    Get API key from: https://console.cloud.google.com/
    """
    
    @property
    def base_url(self) -> str:
        return "https://www.googleapis.com/youtube/v3"
    
    @property
    def service_name(self) -> str:
        return "YouTube"
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            'Accept': 'application/json',
        }
    
    def search_videos(self, breed_name: str, species: str) -> List[Dict]:
        """
        Search for breed-related videos
        
        Args:
            breed_name: Breed name
            species: Species type (dog, cat, etc.)
            
        Returns:
            List of video dicts: [{title, youtube_id, thumbnail}]
        """
        api_key = getattr(settings, 'YOUTUBE_API_KEY', None)
        
        if not api_key:
            logger.warning("YouTube API key not configured")
            return []
        
        try:
            # Build search query
            search_query = f"{breed_name} {species} breed characteristics"
            
            endpoint = "/search"
            params = {
                'part': 'snippet',
                'q': search_query,
                'type': 'video',
                'maxResults': YOUTUBE_VIDEO_LIMIT,
                'order': 'relevance',
                'key': api_key,
                'videoEmbeddable': 'true',
                'safeSearch': 'strict',
            }
            
            response = self.get(endpoint, params=params)
            
            if not response or 'items' not in response:
                logger.warning(f"No YouTube videos found for: {breed_name}")
                return []
            
            # Extract video data
            videos = []
            for item in response['items']:
                video_id = item['id'].get('videoId')
                snippet = item.get('snippet', {})
                
                if video_id:
                    videos.append({
                        'title': snippet.get('title', ''),
                        'youtube_id': video_id,
                        'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                        'description': snippet.get('description', ''),
                        'channel': snippet.get('channelTitle', ''),
                    })
            
            logger.info(f"Fetched {len(videos)} YouTube videos for: {breed_name}")
            return videos[:YOUTUBE_VIDEO_LIMIT]
            
        except Exception as e:
            logger.error(f"YouTube API error: {e}")
            return []
    
    def fetch_breed_videos(self, breed_name: str, species: str) -> List[Dict]:
        """
        Main method: Fetch breed videos
        
        Args:
            breed_name: Breed name
            species: Species type
            
        Returns:
            List of video objects
        """
        return self.search_videos(breed_name, species)