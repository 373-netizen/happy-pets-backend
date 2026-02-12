# education/models.py
from django.db import models
from django.conf import settings


class VideoCache(models.Model):
    """Cache YouTube videos to reduce API calls and work offline"""
    video_id = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    thumbnail_url = models.URLField(max_length=500)  # Reduced from default
    channel_name = models.CharField(max_length=200)
    channel_id = models.CharField(max_length=100)
    published_at = models.DateTimeField()
    duration = models.CharField(max_length=20, blank=True)
    view_count = models.BigIntegerField(default=0)
    like_count = models.BigIntegerField(default=0)
    category = models.CharField(max_length=100, blank=True)  # dog, cat, bird, etc.
    tags = models.JSONField(default=list, blank=True)
    
    # Search optimization
    search_query = models.CharField(max_length=200, db_index=True)  # Original query that fetched this
    relevance_score = models.FloatField(default=0.0)
    
    # Cache management
    last_updated = models.DateTimeField(auto_now=True)
    times_viewed = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'education_video_cache'
        ordering = ['-relevance_score', '-published_at']
        indexes = [
            models.Index(fields=['category', '-published_at']),
            models.Index(fields=['search_query', '-relevance_score']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.video_id})"


class ArticleCache(models.Model):
    """Cache articles to reduce API calls and work offline"""
    # FIXED: Changed unique to db_index only, add hash for uniqueness
    url = models.URLField(max_length=500, db_index=True)  # Not unique due to MySQL limit
    url_hash = models.CharField(max_length=64, unique=True, db_index=True)  # MD5/SHA hash for uniqueness
    
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)  # Full article text if available
    image_url = models.URLField(max_length=500, blank=True)
    source = models.CharField(max_length=200)  # Website name
    author = models.CharField(max_length=200, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    read_time = models.IntegerField(null=True, blank=True)  # Minutes
    category = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Search optimization
    search_query = models.CharField(max_length=200, db_index=True)
    relevance_score = models.FloatField(default=0.0)
    
    # Cache management
    last_updated = models.DateTimeField(auto_now=True)
    times_viewed = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'education_article_cache'
        ordering = ['-relevance_score', '-published_at']
        indexes = [
            models.Index(fields=['category', '-published_at']),
            models.Index(fields=['search_query', '-relevance_score']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Auto-generate url_hash from url"""
        if not self.url_hash:
            import hashlib
            self.url_hash = hashlib.md5(self.url.encode()).hexdigest()
        super().save(*args, **kwargs)


class UserVideoView(models.Model):
    """Track which videos users have watched"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='video_views')
    video = models.ForeignKey(VideoCache, on_delete=models.CASCADE, related_name='user_views')
    watched_at = models.DateTimeField(auto_now_add=True)
    watch_duration = models.IntegerField(default=0)  # Seconds watched
    
    class Meta:
        db_table = 'education_user_video_views'
        unique_together = ('user', 'video')
        indexes = [
            models.Index(fields=['user', '-watched_at']),
        ]


class UserArticleView(models.Model):
    """Track which articles users have read"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='article_views')
    article = models.ForeignKey(ArticleCache, on_delete=models.CASCADE, related_name='user_views')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'education_user_article_views'
        unique_together = ('user', 'article')
        indexes = [
            models.Index(fields=['user', '-viewed_at']),
        ]


class UserBookmark(models.Model):
    """Allow users to bookmark videos and articles"""
    CONTENT_TYPES = [
        ('video', 'Video'),
        ('article', 'Article'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    video = models.ForeignKey(VideoCache, on_delete=models.CASCADE, null=True, blank=True, related_name='bookmarks')
    article = models.ForeignKey(ArticleCache, on_delete=models.CASCADE, null=True, blank=True, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'education_user_bookmarks'
        indexes = [
            models.Index(fields=['user', 'content_type', '-created_at']),
        ]
    
    def __str__(self):
        if self.content_type == 'video':
            return f"{self.user.username} - {self.video.title}"
        return f"{self.user.username} - {self.article.title}"