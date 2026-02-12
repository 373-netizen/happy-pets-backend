# education/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum, F
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import VideoCache, ArticleCache, UserVideoView, UserArticleView, UserBookmark


# ==================== VIDEO CACHE ADMIN ====================
@admin.register(VideoCache)
class VideoCacheAdmin(admin.ModelAdmin):
    list_display = [
        'video_thumbnail',
        'title_display',
        'channel_name',
        'category',
        'view_count_display',
        'duration',
        'times_viewed',
        'published_date',
        'cached_date',
        'watch_on_youtube'
    ]
    
    list_filter = [
        'category',
        'created_at',
        'last_updated',
        'published_at'
    ]
    
    search_fields = [
        'title',
        'description',
        'channel_name',
        'video_id',
        'search_query',
        'tags'
    ]
    
    readonly_fields = [
        'video_id',
        'video_preview',
        'statistics_display',
        'created_at',
        'last_updated',
        'times_viewed'
    ]
    
    fieldsets = (
        ('Video Information', {
            'fields': (
                'video_id',
                'video_preview',
                'title',
                'description',
                'thumbnail_url'
            )
        }),
        ('Channel Information', {
            'fields': (
                'channel_name',
                'channel_id'
            )
        }),
        ('Metadata', {
            'fields': (
                'published_at',
                'duration',
                'category',
                'tags'
            )
        }),
        ('Statistics', {
            'fields': (
                'statistics_display',
                'view_count',
                'like_count',
                'times_viewed'
            )
        }),
        ('Search & Relevance', {
            'fields': (
                'search_query',
                'relevance_score'
            )
        }),
        ('Cache Information', {
            'fields': (
                'created_at',
                'last_updated'
            ),
            'classes': ('collapse',)
        })
    )
    
    list_per_page = 25
    date_hierarchy = 'published_at'
    
    def video_thumbnail(self, obj):
        """Display video thumbnail in list view"""
        if obj.thumbnail_url:
            return format_html(
                '<img src="{}" width="120" height="68" style="border-radius: 8px; object-fit: cover;" />',
                obj.thumbnail_url
            )
        return "No thumbnail"
    video_thumbnail.short_description = "Thumbnail"
    
    def title_display(self, obj):
        """Display title with truncation"""
        max_length = 60
        if len(obj.title) > max_length:
            return f"{obj.title[:max_length]}..."
        return obj.title
    title_display.short_description = "Title"
    
    def view_count_display(self, obj):
        """Format view count with colors"""
        if obj.view_count >= 1000000:
            color = "#22c55e"  # Green
            text = f"{obj.view_count / 1000000:.1f}M"
        elif obj.view_count >= 100000:
            color = "#3b82f6"  # Blue
            text = f"{obj.view_count / 1000:.0f}K"
        elif obj.view_count >= 10000:
            color = "#f59e0b"  # Orange
            text = f"{obj.view_count / 1000:.1f}K"
        else:
            color = "#6b7280"  # Gray
            text = str(obj.view_count)
        
        return format_html(
            '<span style="color: {}; font-weight: 600;">👁️ {}</span>',
            color,
            text
        )
    view_count_display.short_description = "Views"
    view_count_display.admin_order_field = 'view_count'
    
    def published_date(self, obj):
        """Format published date"""
        return obj.published_at.strftime("%b %d, %Y") if obj.published_at else "N/A"
    published_date.short_description = "Published"
    published_date.admin_order_field = 'published_at'
    
    def cached_date(self, obj):
        """Format cached date"""
        return obj.created_at.strftime("%b %d, %Y") if obj.created_at else "N/A"
    cached_date.short_description = "Cached On"
    cached_date.admin_order_field = 'created_at'
    
    def watch_on_youtube(self, obj):
        """Link to watch video on YouTube"""
        return format_html(
            '<a href="https://www.youtube.com/watch?v={}" target="_blank" '
            'style="background: #ff0000; color: white; padding: 6px 12px; '
            'border-radius: 6px; text-decoration: none; font-weight: 600;">▶️ Watch</a>',
            obj.video_id
        )
    watch_on_youtube.short_description = "Actions"
    
    def video_preview(self, obj):
        """Display video embed preview"""
        if obj.video_id:
            return format_html(
                '<div style="max-width: 560px;">'
                '<iframe width="560" height="315" '
                'src="https://www.youtube.com/embed/{}" '
                'frameborder="0" allow="accelerometer; autoplay; clipboard-write; '
                'encrypted-media; gyroscope; picture-in-picture" allowfullscreen '
                'style="border-radius: 12px;"></iframe>'
                '</div>',
                obj.video_id
            )
        return "No video ID"
    video_preview.short_description = "Video Preview"
    
    def statistics_display(self, obj):
        """Display formatted statistics"""
        stats_html = f"""
        <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; font-family: monospace;">
            <div style="margin-bottom: 8px;">
                <strong>👁️ Views:</strong> {obj.view_count:,}
            </div>
            <div style="margin-bottom: 8px;">
                <strong>👍 Likes:</strong> {obj.like_count:,}
            </div>
            <div style="margin-bottom: 8px;">
                <strong>📊 Relevance Score:</strong> {obj.relevance_score:,.0f}
            </div>
            <div>
                <strong>👥 Times Viewed (Our Platform):</strong> {obj.times_viewed}
            </div>
        </div>
        """
        return mark_safe(stats_html)
    statistics_display.short_description = "Statistics"
    
    actions = ['update_relevance_score', 'mark_as_trending']
    
    def update_relevance_score(self, request, queryset):
        """Recalculate relevance scores"""
        for video in queryset:
            video.relevance_score = (video.view_count * 0.7) + (video.like_count * 0.3)
            video.save()
        self.message_user(request, f"Updated relevance scores for {queryset.count()} videos")
    update_relevance_score.short_description = "Update relevance scores"
    
    def mark_as_trending(self, request, queryset):
        """Mark videos as trending (increase relevance)"""
        queryset.update(relevance_score=models.F('relevance_score') * 1.5)
        self.message_user(request, f"Marked {queryset.count()} videos as trending")
    mark_as_trending.short_description = "Mark as trending"


# ==================== ARTICLE CACHE ADMIN ====================
@admin.register(ArticleCache)
class ArticleCacheAdmin(admin.ModelAdmin):
    list_display = [
        'article_image_display',
        'title_display',
        'source',
        'category',
        'read_time',
        'times_viewed',
        'published_date',
        'view_article'
    ]
    
    list_filter = [
        'category',
        'source',
        'created_at',
        'published_at'
    ]
    
    search_fields = [
        'title',
        'description',
        'content',
        'source',
        'author',
        'search_query'
    ]
    
    readonly_fields = [
        'url',
        'article_preview',
        'statistics_display',
        'created_at',
        'last_updated',
        'times_viewed'
    ]
    
    fieldsets = (
        ('Article Information', {
            'fields': (
                'url',
                'title',
                'description',
                'content',
                'article_preview'
            )
        }),
        ('Media', {
            'fields': (
                'image_url',
            )
        }),
        ('Author & Source', {
            'fields': (
                'source',
                'author',
                'published_at'
            )
        }),
        ('Metadata', {
            'fields': (
                'read_time',
                'category',
                'tags'
            )
        }),
        ('Search & Relevance', {
            'fields': (
                'search_query',
                'relevance_score'
            )
        }),
        ('Statistics', {
            'fields': (
                'statistics_display',
                'times_viewed'
            )
        }),
        ('Cache Information', {
            'fields': (
                'created_at',
                'last_updated'
            ),
            'classes': ('collapse',)
        })
    )
    
    list_per_page = 25
    date_hierarchy = 'published_at'
    
    def article_image_display(self, obj):
        """Display article image thumbnail"""
        if obj.image_url:
            return format_html(
                '<img src="{}" width="100" height="60" '
                'style="border-radius: 6px; object-fit: cover;" />',
                obj.image_url
            )
        return "📄"
    article_image_display.short_description = "Image"
    
    def title_display(self, obj):
        """Display title with truncation"""
        max_length = 70
        if len(obj.title) > max_length:
            return f"{obj.title[:max_length]}..."
        return obj.title
    title_display.short_description = "Title"
    
    def published_date(self, obj):
        """Format published date"""
        if obj.published_at:
            return obj.published_at.strftime("%b %d, %Y")
        return "N/A"
    published_date.short_description = "Published"
    published_date.admin_order_field = 'published_at'
    
    def view_article(self, obj):
        """Link to view article"""
        return format_html(
            '<a href="{}" target="_blank" '
            'style="background: #3b82f6; color: white; padding: 6px 12px; '
            'border-radius: 6px; text-decoration: none; font-weight: 600;">📖 Read</a>',
            obj.url
        )
    view_article.short_description = "Actions"
    
    def article_preview(self, obj):
        """Display article preview"""
        preview_html = f"""
        <div style="max-width: 800px; background: #f9fafb; padding: 20px; 
                    border-radius: 12px; border-left: 4px solid #3b82f6;">
            {f'<img src="{obj.image_url}" style="width: 100%; max-height: 300px; object-fit: cover; border-radius: 8px; margin-bottom: 16px;" />' if obj.image_url else ''}
            <h3 style="margin: 0 0 12px 0; color: #111827;">{obj.title}</h3>
            <p style="color: #6b7280; margin: 0 0 12px 0;">{obj.description[:300]}...</p>
            <div style="display: flex; gap: 16px; font-size: 14px; color: #9ca3af;">
                <span>📰 {obj.source}</span>
                {f'<span>✍️ {obj.author}</span>' if obj.author else ''}
                {f'<span>⏱️ {obj.read_time} min read</span>' if obj.read_time else ''}
            </div>
        </div>
        """
        return mark_safe(preview_html)
    article_preview.short_description = "Article Preview"
    
    def statistics_display(self, obj):
        """Display formatted statistics"""
        stats_html = f"""
        <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; font-family: monospace;">
            <div style="margin-bottom: 8px;">
                <strong>📊 Relevance Score:</strong> {obj.relevance_score:,.0f}
            </div>
            <div style="margin-bottom: 8px;">
                <strong>👥 Times Viewed:</strong> {obj.times_viewed}
            </div>
            <div>
                <strong>🔍 Search Query:</strong> {obj.search_query}
            </div>
        </div>
        """
        return mark_safe(stats_html)
    statistics_display.short_description = "Statistics"


# ==================== USER VIDEO VIEW ADMIN ====================
@admin.register(UserVideoView)
class UserVideoViewAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'video_title',
        'watched_at',
        'watch_duration_display'
    ]
    
    list_filter = [
        'watched_at',
        'video__category'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'video__title'
    ]
    
    readonly_fields = ['user', 'video', 'watched_at', 'watch_duration']
    
    date_hierarchy = 'watched_at'
    list_per_page = 50
    
    def video_title(self, obj):
        return obj.video.title[:60]
    video_title.short_description = "Video"
    
    def watch_duration_display(self, obj):
        """Format watch duration"""
        minutes = obj.watch_duration // 60
        seconds = obj.watch_duration % 60
        return f"{minutes}m {seconds}s"
    watch_duration_display.short_description = "Duration Watched"


# ==================== USER ARTICLE VIEW ADMIN ====================
@admin.register(UserArticleView)
class UserArticleViewAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'article_title',
        'viewed_at'
    ]
    
    list_filter = [
        'viewed_at',
        'article__category'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'article__title'
    ]
    
    readonly_fields = ['user', 'article', 'viewed_at']
    
    date_hierarchy = 'viewed_at'
    list_per_page = 50
    
    def article_title(self, obj):
        return obj.article.title[:60]
    article_title.short_description = "Article"


# ==================== USER BOOKMARK ADMIN ====================
@admin.register(UserBookmark)
class UserBookmarkAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'content_type',
        'content_title',
        'created_at',
        'has_notes'
    ]
    
    list_filter = [
        'content_type',
        'created_at'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'video__title',
        'article__title',
        'notes'
    ]
    
    readonly_fields = ['user', 'content_type', 'video', 'article', 'created_at']
    
    fieldsets = (
        ('Bookmark Information', {
            'fields': (
                'user',
                'content_type',
                'video',
                'article',
                'created_at'
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        })
    )
    
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    def content_title(self, obj):
        """Get title of bookmarked content"""
        if obj.content_type == 'video' and obj.video:
            return obj.video.title[:60]
        elif obj.content_type == 'article' and obj.article:
            return obj.article.title[:60]
        return "N/A"
    content_title.short_description = "Content"
    
    def has_notes(self, obj):
        """Check if bookmark has notes"""
        if obj.notes:
            return format_html(
                '<span style="color: #22c55e;">✓ Yes</span>'
            )
        return format_html(
            '<span style="color: #9ca3af;">✗ No</span>'
        )
    has_notes.short_description = "Notes"


# ==================== CUSTOM ADMIN SITE CONFIGURATION ====================
# Customize admin site header and title
admin.site.site_header = "Pet Education Admin"
admin.site.site_title = "Pet Education Admin Portal"
admin.site.index_title = "Welcome to Pet Education Administration"