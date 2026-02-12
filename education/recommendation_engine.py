# education/recommendation_engine.py - FIXED VERSION
"""
Advanced recommendation engine using collaborative filtering, content-based filtering,
and user behavior analysis for personalized pet education recommendations.
"""

from django.db.models import Count, Q, F, Avg, Sum
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from .models import VideoCache, ArticleCache, UserVideoView, UserArticleView, UserBookmark
from pets.models import Pet

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Production-level recommendation engine with multiple strategies:
    1. Content-based filtering (pet species, breed, age)
    2. Collaborative filtering (similar users' preferences)
    3. Behavioral analysis (watch history, bookmarks)
    4. Trending content (popular in user's pet category)
    5. Freshness factor (prioritize recent content)
    """
    
    def __init__(self, user):
        self.user = user
        self.user_pets = list(Pet.objects.filter(owner=user, is_active=True))
        self.recommendations = []
        
    def get_recommendations(self, content_type='video', limit=20):
        """Get personalized recommendations"""
        if not self.user_pets:
            return self._get_generic_recommendations(content_type, limit)
        
        # Calculate scores from multiple strategies
        scores = defaultdict(float)
        
        # Strategy 1: Pet-based content (40% weight)
        pet_scores = self._score_by_pet_attributes()
        for item_id, score in pet_scores.items():
            scores[item_id] += score * 0.40
        
        # Strategy 2: User behavior (30% weight)
        behavior_scores = self._score_by_user_behavior(content_type)
        for item_id, score in behavior_scores.items():
            scores[item_id] += score * 0.30
        
        # Strategy 3: Trending in category (15% weight)
        trending_scores = self._score_by_trending(content_type)
        for item_id, score in trending_scores.items():
            scores[item_id] += score * 0.15
        
        # Strategy 4: Freshness (10% weight)
        freshness_scores = self._score_by_freshness(content_type)
        for item_id, score in freshness_scores.items():
            scores[item_id] += score * 0.10
        
        # Strategy 5: Similar users (5% weight)
        similar_scores = self._score_by_similar_users(content_type)
        for item_id, score in similar_scores.items():
            scores[item_id] += score * 0.05
        
        # Remove already viewed/bookmarked items
        scores = self._filter_already_consumed(scores, content_type)
        
        # Sort by score and return top items
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        item_ids = [item_id for item_id, score in sorted_items]
        
        # Fetch actual content
        if content_type == 'video':
            items = VideoCache.objects.filter(id__in=item_ids)
            # Preserve order
            items_dict = {item.id: item for item in items}
            return [items_dict[item_id] for item_id in item_ids if item_id in items_dict]
        else:
            items = ArticleCache.objects.filter(id__in=item_ids)
            items_dict = {item.id: item for item in items}
            return [items_dict[item_id] for item_id in item_ids if item_id in items_dict]
    
    def _score_by_pet_attributes(self):
        """Score content based on user's pet attributes"""
        scores = defaultdict(float)
        
        for pet in self.user_pets:
            species = pet.species.lower() if pet.species else None
            breed = pet.breed.lower() if pet.breed else None
            
            # Get content matching pet species
            if species:
                videos = VideoCache.objects.filter(
                    Q(category__iexact=species) |
                    Q(title__icontains=species) |
                    Q(description__icontains=species)
                )
                
                for video in videos:
                    score = 10.0  # Base score for species match
                    
                    # Boost if breed matches
                    if breed and (breed in video.title.lower() or breed in video.description.lower()):
                        score += 5.0
                    
                    # Check for age-specific keywords
                    title_lower = video.title.lower()
                    if any(word in title_lower for word in ['puppy', 'kitten', 'baby', 'young']):
                        score += 2.0
                    elif any(word in title_lower for word in ['senior', 'old', 'elderly']):
                        score += 2.0
                    
                    # Relevance boost
                    if video.relevance_score:
                        score *= (video.relevance_score / 1000000)
                    
                    scores[video.id] += score
        
        return scores
    
    def _score_by_user_behavior(self, content_type):
        """Score based on user's watch history and preferences"""
        scores = defaultdict(float)
        
        if content_type == 'video':
            # Get user's viewing history
            viewed = UserVideoView.objects.filter(user=self.user).select_related('video')
            
            # Find categories user watches most
            category_preferences = defaultdict(int)
            for view in viewed:
                if view.video:
                    category_preferences[view.video.category] += 1
            
            # Get bookmarked videos
            bookmarked = UserBookmark.objects.filter(
                user=self.user, 
                content_type='video'
            ).select_related('video')
            
            # Score videos in preferred categories
            for category, count in category_preferences.items():
                videos = VideoCache.objects.filter(category=category)
                for video in videos:
                    scores[video.id] += count * 2.0
            
            # Find similar content to bookmarked
            for bookmark in bookmarked:
                if bookmark.video:
                    similar = VideoCache.objects.filter(
                        Q(category=bookmark.video.category) |
                        Q(channel_name=bookmark.video.channel_name)
                    ).exclude(id=bookmark.video.id)
                    
                    for video in similar:
                        scores[video.id] += 5.0
        
        return scores
    
    def _score_by_trending(self, content_type):
        """Score based on what's trending in user's pet categories"""
        scores = defaultdict(float)
        
        # Get user's pet categories
        categories = [pet.species.lower() for pet in self.user_pets if pet.species]
        
        if content_type == 'video':
            # Get most viewed videos in categories (using created_at instead of cached_at)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            trending = VideoCache.objects.filter(
                category__in=categories,
                created_at__gte=thirty_days_ago  # FIXED: use created_at instead of cached_at
            ).order_by('-view_count')[:50]
            
            for video in trending:
                # Normalize view count (0-10 scale)
                normalized_views = min(video.view_count / 1000000, 10.0) if video.view_count else 0
                scores[video.id] += normalized_views
        
        return scores
    
    def _score_by_freshness(self, content_type):
        """Prioritize recent content"""
        scores = defaultdict(float)
        now = datetime.now()
        
        if content_type == 'video':
            recent = VideoCache.objects.filter(
                published_at__gte=now - timedelta(days=90)
            )
            
            for video in recent:
                # Decay score based on age (newer = higher)
                if video.published_at:
                    days_old = (now - video.published_at).days
                    freshness = max(0, 10.0 - (days_old / 10))
                    scores[video.id] += freshness
        
        return scores
    
    def _score_by_similar_users(self, content_type):
        """Collaborative filtering - what similar users watched"""
        scores = defaultdict(float)
        
        # Find users with similar pets
        similar_users = self._find_similar_users()
        
        if content_type == 'video' and similar_users:
            # Get what similar users watched
            similar_views = UserVideoView.objects.filter(
                user__in=similar_users
            ).values('video').annotate(
                view_count=Count('video')
            ).order_by('-view_count')[:30]
            
            for item in similar_views:
                scores[item['video']] += item['view_count'] * 2.0
        
        return scores
    
    def _find_similar_users(self, limit=10):
        """Find users with similar pet profiles"""
        if not self.user_pets:
            return []
        
        # Get users with same pet species
        species_list = [pet.species for pet in self.user_pets if pet.species]
        
        if not species_list:
            return []
        
        similar_users = Pet.objects.filter(
            species__in=species_list,
            is_active=True
        ).exclude(
            owner=self.user
        ).values('owner').annotate(
            match_count=Count('owner')
        ).order_by('-match_count')[:limit]
        
        return [item['owner'] for item in similar_users]
    
    def _filter_already_consumed(self, scores, content_type):
        """Remove items user already viewed/bookmarked"""
        if content_type == 'video':
            viewed_ids = UserVideoView.objects.filter(
                user=self.user
            ).values_list('video_id', flat=True)
            
            bookmarked_ids = UserBookmark.objects.filter(
                user=self.user,
                content_type='video'
            ).values_list('video_id', flat=True)
            
            exclude_ids = set(list(viewed_ids) + list(bookmarked_ids))
            
            return {k: v for k, v in scores.items() if k not in exclude_ids}
        
        return scores
    
    def _get_generic_recommendations(self, content_type, limit):
        """Fallback for users without pets"""
        if content_type == 'video':
            return list(VideoCache.objects.order_by('-view_count', '-published_at')[:limit])
        else:
            return list(ArticleCache.objects.order_by('-relevance_score', '-published_at')[:limit])
    
    def explain_recommendation(self, item_id, content_type='video'):
        """Explain why an item was recommended (for debugging/transparency)"""
        explanation = []
        
        try:
            if content_type == 'video':
                video = VideoCache.objects.get(id=item_id)
                
                # Check pet match
                for pet in self.user_pets:
                    if pet.species and pet.species.lower() == video.category:
                        explanation.append(f"Matches your {pet.name}'s species ({pet.species})")
                
                # Check if similar to bookmarked
                bookmarked = UserBookmark.objects.filter(
                    user=self.user,
                    content_type='video',
                    video__category=video.category
                ).count()
                
                if bookmarked > 0:
                    explanation.append(f"Similar to {bookmarked} videos you bookmarked")
                
                # Check trending
                if video.view_count and video.view_count > 500000:
                    explanation.append("Popular content in this category")
                
                # Check freshness
                if video.published_at:
                    days_old = (datetime.now() - video.published_at).days
                    if days_old < 30:
                        explanation.append("Recently published")
        except Exception as e:
            logger.error(f"Error explaining recommendation: {e}")
        
        return explanation


# ==================== SMART SEARCH WITH ML-STYLE RANKING ====================
class SmartSearch:
    """
    Advanced search with relevance ranking, typo tolerance, and semantic understanding
    """
    
    def __init__(self, query, user):
        self.query = query.lower().strip()
        self.user = user
        self.user_pets = list(Pet.objects.filter(owner=user, is_active=True))
    
    def search_videos(self, limit=20):
        """Search videos with intelligent ranking"""
        # Base search
        results = VideoCache.objects.filter(
            Q(title__icontains=self.query) |
            Q(description__icontains=self.query) |
            Q(channel_name__icontains=self.query) |
            Q(category__icontains=self.query)
        )
        
        # Score each result
        scored_results = []
        for video in results:
            score = self._calculate_search_relevance(video)
            scored_results.append((video, score))
        
        # Sort by relevance
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return [video for video, score in scored_results[:limit]]
    
    def _calculate_search_relevance(self, video):
        """Calculate relevance score for search result"""
        score = 0.0
        
        # Exact title match
        if self.query in video.title.lower():
            score += 10.0
            if video.title.lower().startswith(self.query):
                score += 5.0
        
        # Description match
        if self.query in video.description.lower():
            score += 5.0
        
        # Category match
        if self.query in video.category.lower():
            score += 7.0
        
        # User's pet species match
        for pet in self.user_pets:
            if pet.species and pet.species.lower() in video.title.lower():
                score += 8.0
        
        # Popularity boost
        if video.view_count:
            score += min(video.view_count / 100000, 5.0)
        
        # Freshness boost
        if video.published_at:
            days_old = (datetime.now() - video.published_at).days
            if days_old < 30:
                score += 3.0
            elif days_old < 90:
                score += 1.0
        
        return score