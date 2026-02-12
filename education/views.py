# education/views.py - FIXED VERSION WITH DETAILED DEBUGGING
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, F
from datetime import datetime, timedelta
import requests
import hashlib
from django.conf import settings
from pets.models import Pet
from .models import VideoCache, ArticleCache, UserVideoView, UserArticleView, UserBookmark
from .recommendation_engine import RecommendationEngine, SmartSearch
import logging

logger = logging.getLogger(__name__)

# YouTube API Configuration
YOUTUBE_API_KEY = getattr(settings, 'YOUTUBE_API_KEY', None)
YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
YOUTUBE_VIDEOS_URL = 'https://www.googleapis.com/youtube/v3/videos'


# ==================== RECOMMENDATIONS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommendations(request):
    """Get personalized recommendations using ML-style recommendation engine"""
    try:
        user_pets = Pet.objects.filter(owner=request.user, is_active=True)
        
        # Check if API key is configured
        if not YOUTUBE_API_KEY:
            logger.error("YOUTUBE_API_KEY not configured in settings")
            return Response({
                'success': False,
                'error': 'YouTube API key not configured. Please add YOUTUBE_API_KEY to settings.',
                'videos': [],
                'articles': [],
                'recommendations': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Initialize recommendation engine
        engine = RecommendationEngine(request.user)
        
        # Get video recommendations
        recommended_videos = engine.get_recommendations(content_type='video', limit=20)
        
        # Get article recommendations  
        recommended_articles = engine.get_recommendations(content_type='article', limit=15)
        
        # If no cached content, fetch from APIs
        if len(recommended_videos) < 10 and user_pets.exists():
            logger.info(f"Fetching videos for {user_pets.count()} pets")
            for pet in user_pets[:3]:  # Limit API calls
                if pet.species:
                    logger.info(f"Fetching videos for {pet.species}")
                    fetch_youtube_videos(f"{pet.species} care", pet.species.lower())
                    if pet.breed:
                        fetch_youtube_videos(f"{pet.breed} training", pet.species.lower())
            
            # Re-run recommendations
            recommended_videos = engine.get_recommendations(content_type='video', limit=20)
            logger.info(f"After fetching: {len(recommended_videos)} videos found")
        
        # Serialize data with explanation
        videos_data = []
        for video in recommended_videos:
            # Get recommendation explanation
            explanation = engine.explain_recommendation(video.id, 'video')
            
            videos_data.append({
                'id': video.id,
                'video_id': video.video_id,
                'title': video.title,
                'description': video.description,
                'thumbnail_url': video.thumbnail_url,
                'channel_name': video.channel_name,
                'published_at': video.published_at.isoformat() if video.published_at else None,
                'duration': video.duration,
                'view_count': video.view_count,
                'category': video.category,
                'why_recommended': explanation,
            })
        
        articles_data = [{
            'id': article.id,
            'url': article.url,
            'title': article.title,
            'description': article.description,
            'image_url': article.image_url,
            'source': article.source,
            'published_at': article.published_at.isoformat() if article.published_at else None,
            'read_time': article.read_time,
            'category': article.category,
        } for article in recommended_articles]
        
        return Response({
            'success': True,
            'videos': videos_data,
            'articles': articles_data,
            'recommendations': [f"{pet.name} ({pet.species})" for pet in user_pets],
            'recommendation_strategy': 'advanced_ml_based',
            'total_pets': user_pets.count(),
        })
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'videos': [],
            'articles': [],
            'recommendations': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== SMART SEARCH ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search(request):
    """Search with intelligent ranking and relevance"""
    query = request.data.get('query', '').strip()
    content_type = request.data.get('type', 'videos')
    
    if not query:
        return Response({
            'success': False,
            'error': 'Search query is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        if content_type == 'videos':
            logger.info(f"Searching videos for: {query}")
            
            # Use smart search engine
            smart_search = SmartSearch(query, request.user)
            ranked_videos = smart_search.search_videos(limit=20)
            
            logger.info(f"Found {len(ranked_videos)} cached videos")
            
            # If not enough results, fetch from YouTube
            if len(ranked_videos) < 5:
                logger.info("Fetching new videos from YouTube API")
                fetch_result = fetch_youtube_videos(query)
                
                if fetch_result:
                    # Re-run search
                    ranked_videos = smart_search.search_videos(limit=20)
                    logger.info(f"After fetching: {len(ranked_videos)} videos")
            
            # Track search for better recommendations
            _track_search(request.user, query, 'video')
            
            videos_data = [{
                'id': video.id,
                'video_id': video.video_id,
                'title': video.title,
                'description': video.description,
                'thumbnail_url': video.thumbnail_url,
                'channel_name': video.channel_name,
                'published_at': video.published_at.isoformat() if video.published_at else None,
                'duration': video.duration,
                'view_count': video.view_count,
                'category': video.category,
            } for video in ranked_videos]
            
            return Response({
                'success': True,
                'videos': videos_data,
                'query': query,
                'total_results': len(videos_data),
            })
        
        else:  # articles
            # Search articles with ranking
            articles = ArticleCache.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            ).order_by('-relevance_score', '-published_at')[:15]
            
            if len(articles) < 5:
                fetch_articles(query)
                articles = ArticleCache.objects.filter(
                    Q(title__icontains=query) |
                    Q(description__icontains=query)
                ).order_by('-relevance_score', '-published_at')[:15]
            
            articles_data = [{
                'id': article.id,
                'url': article.url,
                'title': article.title,
                'description': article.description,
                'image_url': article.image_url,
                'source': article.source,
                'published_at': article.published_at.isoformat() if article.published_at else None,
                'read_time': article.read_time,
                'category': article.category,
            } for article in articles]
            
            return Response({
                'success': True,
                'articles': articles_data,
                'query': query,
                'total_results': len(articles_data),
            })
            
    except Exception as e:
        logger.error(f"Error searching: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _track_search(user, query, content_type):
    """Track user searches for better recommendations"""
    pass


# ==================== VIEW TRACKING ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_view(request):
    """Track when user views a video (for better recommendations)"""
    try:
        video_id = request.data.get('video_id')
        watch_duration = request.data.get('watch_duration', 0)
        
        if not video_id:
            return Response({'success': False, 'error': 'video_id required'})
        
        video = get_object_or_404(VideoCache, id=video_id)
        
        # Create or update view record
        view, created = UserVideoView.objects.get_or_create(
            user=request.user,
            video=video,
            defaults={'watch_duration': watch_duration}
        )
        
        if not created:
            if watch_duration > view.watch_duration:
                view.watch_duration = watch_duration
                view.view_count = F('view_count') + 1
                view.save()
        
        # Increment video's view counter
        video.times_viewed = F('times_viewed') + 1
        video.save()
        
        return Response({
            'success': True,
            'message': 'View tracked',
            'total_views': view.view_count if not created else 1
        })
        
    except Exception as e:
        logger.error(f"Error tracking view: {e}")
        return Response({'success': False, 'error': str(e)})


# ==================== YOUTUBE API HELPER ====================
def fetch_youtube_videos(query, category='pet', max_results=10):
    """Fetch videos from YouTube API and cache them"""
    
    if not YOUTUBE_API_KEY:
        logger.error("YouTube API key not configured")
        return False
    
    try:
        logger.info(f"Fetching YouTube videos for query: {query}")
        
        # Search for videos
        search_params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': max_results,
            'order': 'relevance',
            'key': YOUTUBE_API_KEY,
            'relevanceLanguage': 'en',
            'safeSearch': 'moderate',
            'videoEmbeddable': 'true',
            'videoSyndicated': 'true'
        }
        
        logger.info(f"Making YouTube search request with params: {search_params}")
        search_response = requests.get(YOUTUBE_SEARCH_URL, params=search_params, timeout=15)
        
        logger.info(f"YouTube search response status: {search_response.status_code}")
        
        if search_response.status_code != 200:
            error_data = search_response.json() if search_response.text else {}
            logger.error(f"YouTube API search error: {search_response.status_code}")
            logger.error(f"Error response: {error_data}")
            return False
        
        search_data = search_response.json()
        items = search_data.get('items', [])
        logger.info(f"Found {len(items)} videos in search results")
        
        if not items:
            logger.warning(f"No videos found for query: {query}")
            return False
        
        video_ids = [item['id']['videoId'] for item in items]
        logger.info(f"Video IDs: {video_ids}")
        
        # Get detailed video information
        videos_params = {
            'part': 'snippet,contentDetails,statistics',
            'id': ','.join(video_ids),
            'key': YOUTUBE_API_KEY
        }
        
        logger.info("Fetching video details")
        videos_response = requests.get(YOUTUBE_VIDEOS_URL, params=videos_params, timeout=15)
        
        logger.info(f"YouTube videos response status: {videos_response.status_code}")
        
        if videos_response.status_code != 200:
            error_data = videos_response.json() if videos_response.text else {}
            logger.error(f"YouTube API videos error: {videos_response.status_code}")
            logger.error(f"Error response: {error_data}")
            return False
        
        videos_data = videos_response.json()
        video_items = videos_data.get('items', [])
        logger.info(f"Received details for {len(video_items)} videos")
        
        # Cache videos
        cached_count = 0
        for item in video_items:
            try:
                video_id = item['id']
                snippet = item['snippet']
                content_details = item.get('contentDetails', {})
                statistics = item.get('statistics', {})
                
                duration = content_details.get('duration', '')
                duration_formatted = parse_youtube_duration(duration)
                
                view_count = int(statistics.get('viewCount', 0))
                like_count = int(statistics.get('likeCount', 0))
                relevance_score = (view_count * 0.7) + (like_count * 0.3)
                
                # Handle published date
                published_at_str = snippet.get('publishedAt', '')
                if published_at_str:
                    try:
                        published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                        published_at = published_at.replace(tzinfo=None)
                    except Exception as e:
                        logger.warning(f"Error parsing date {published_at_str}: {e}")
                        published_at = datetime.now()
                else:
                    published_at = datetime.now()
                
                # Get thumbnail URL
                thumbnails = snippet.get('thumbnails', {})
                thumbnail_url = (
                    thumbnails.get('high', {}).get('url', '') or
                    thumbnails.get('medium', {}).get('url', '') or
                    thumbnails.get('default', {}).get('url', '')
                )
                
                video_obj, created = VideoCache.objects.update_or_create(
                    video_id=video_id,
                    defaults={
                        'title': snippet.get('title', '')[:500],
                        'description': snippet.get('description', '')[:1000],
                        'thumbnail_url': thumbnail_url[:500],
                        'channel_name': snippet.get('channelTitle', '')[:200],
                        'channel_id': snippet.get('channelId', '')[:100],
                        'published_at': published_at,
                        'duration': duration_formatted,
                        'view_count': view_count,
                        'like_count': like_count,
                        'category': category,
                        'tags': snippet.get('tags', [])[:20],
                        'search_query': query,
                        'relevance_score': relevance_score,
                    }
                )
                
                cached_count += 1
                logger.info(f"{'Created' if created else 'Updated'} video: {snippet.get('title', '')[:50]}")
                
            except Exception as e:
                logger.error(f"Error caching video {item.get('id', 'unknown')}: {e}", exc_info=True)
                continue
        
        logger.info(f"Successfully cached {cached_count}/{len(video_items)} videos for query: {query}")
        return True
        
    except requests.exceptions.Timeout:
        logger.error(f"YouTube API request timeout for query: {query}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"YouTube API request error: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Error fetching YouTube videos: {e}", exc_info=True)
        return False


def parse_youtube_duration(duration):
    """Convert PT15M33S to 15:33"""
    import re
    if not duration:
        return ''
    
    try:
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return ''
        
        hours, minutes, seconds = match.groups()
        hours = int(hours) if hours else 0
        minutes = int(minutes) if minutes else 0
        seconds = int(seconds) if seconds else 0
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
    except Exception:
        return ''


# ==================== ARTICLES HELPER ====================
def fetch_articles(query, category='pet', max_results=10):
    """Fetch articles using News API"""
    try:
        NEWS_API_KEY = getattr(settings, 'NEWS_API_KEY', None)
        
        if not NEWS_API_KEY:
            logger.warning("News API key not configured")
            return False
        
        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': f"{query} pet",
            'apiKey': NEWS_API_KEY,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': max_results
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"News API error: {response.status_code}")
            return False
        
        data = response.json()
        
        for article in data.get('articles', []):
            url_hash = hashlib.md5(article['url'].encode()).hexdigest()
            
            description = article.get('description', '')
            content = article.get('content', '')
            word_count = len((description + content).split())
            read_time = max(1, word_count // 200)
            
            # Handle published date
            published_at_str = article.get('publishedAt', '')
            if published_at_str:
                try:
                    published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                    published_at = published_at.replace(tzinfo=None)
                except Exception:
                    published_at = None
            else:
                published_at = None
            
            ArticleCache.objects.update_or_create(
                url_hash=url_hash,
                defaults={
                    'url': article['url'][:500],
                    'title': article['title'][:500],
                    'description': description[:1000],
                    'image_url': article.get('urlToImage', '')[:500] if article.get('urlToImage') else '',
                    'source': article['source']['name'][:200],
                    'author': article.get('author', '')[:200] if article.get('author') else '',
                    'published_at': published_at,
                    'read_time': read_time,
                    'search_query': query,
                    'category': category,
                    'relevance_score': 100.0,
                }
            )
        
        logger.info(f"Cached {len(data.get('articles', []))} articles for query: {query}")
        return True
        
    except Exception as e:
        logger.error(f"Error fetching articles: {e}", exc_info=True)
        return False


# ==================== BOOKMARKS ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bookmark(request):
    """Bookmark a video or article"""
    content_type = request.data.get('content_type')
    content_id = request.data.get('content_id')
    notes = request.data.get('notes', '')
    
    try:
        if content_type == 'video':
            video = get_object_or_404(VideoCache, id=content_id)
            bookmark_obj, created = UserBookmark.objects.get_or_create(
                user=request.user,
                content_type='video',
                video=video,
                defaults={'notes': notes}
            )
            
            # If not created, delete it (toggle bookmark)
            if not created:
                bookmark_obj.delete()
                return Response({
                    'success': True,
                    'created': False,
                    'message': 'Bookmark removed'
                })
        else:
            article = get_object_or_404(ArticleCache, id=content_id)
            bookmark_obj, created = UserBookmark.objects.get_or_create(
                user=request.user,
                content_type='article',
                article=article,
                defaults={'notes': notes}
            )
            
            if not created:
                bookmark_obj.delete()
                return Response({
                    'success': True,
                    'created': False,
                    'message': 'Bookmark removed'
                })
        
        return Response({
            'success': True,
            'created': True,
            'message': 'Bookmarked successfully'
        })
        
    except Exception as e:
        logger.error(f"Error bookmarking: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bookmarks(request):
    """Get user's bookmarks"""
    bookmarks = UserBookmark.objects.filter(user=request.user).order_by('-created_at')
    
    bookmarks_data = []
    for bookmark_obj in bookmarks:
        if bookmark_obj.content_type == 'video' and bookmark_obj.video:
            bookmarks_data.append({
                'id': bookmark_obj.id,
                'content_type': 'video',
                'video_id': bookmark_obj.video.video_id,
                'title': bookmark_obj.video.title,
                'thumbnail_url': bookmark_obj.video.thumbnail_url,
                'created_at': bookmark_obj.created_at.isoformat(),
                'notes': bookmark_obj.notes
            })
        elif bookmark_obj.content_type == 'article' and bookmark_obj.article:
            bookmarks_data.append({
                'id': bookmark_obj.id,
                'content_type': 'article',
                'title': bookmark_obj.article.title,
                'url': bookmark_obj.article.url,
                'image_url': bookmark_obj.article.image_url,
                'created_at': bookmark_obj.created_at.isoformat(),
                'notes': bookmark_obj.notes
            })
    
    return Response({
        'success': True,
        'bookmarks': bookmarks_data
    })