#'info/admin.py'
"""
Django Admin configuration for Breed Information System
Provides rich admin interface with filters, search, and custom actions
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Breed


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    """
    Advanced admin interface for Breed model
    Features: search, filters, custom actions, image preview, bulk operations
    """
    
    # List Display
    list_display = [
        'name',
        'species',
        'image_preview',
        'has_description',
        'gallery_count',
        'video_count',
        'is_verified',
        'last_updated',
        'fetch_count',
    ]
    
    # List Filters
    list_filter = [
        'species',
        'is_verified',
        'last_updated',
        ('main_image', admin.EmptyFieldListFilter),
        ('description', admin.EmptyFieldListFilter),
    ]
    
    # Search
    search_fields = [
        'name',
        'description',
        'origin',
        'temperament',
    ]
    
    # Ordering
    ordering = ['-last_updated', 'name']
    
    # Read-only fields
    readonly_fields = [
        'last_updated',
        'api_fetch_count',
        'created_at',
        'image_preview_large',
        'gallery_preview',
        'videos_preview',
        'cache_info',
    ]
    
    # Fieldsets for detail view
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'species',
                'is_verified',
            )
        }),
        ('Description & Origin', {
            'fields': (
                'description',
                'origin',
                'wikipedia_url',
            )
        }),
        ('Characteristics', {
            'fields': (
                'life_span',
                'temperament',
                'weight',
                'height',
            ),
            'classes': ('collapse',),
        }),
        ('Media', {
            'fields': (
                'main_image',
                'image_preview_large',
                'gallery_images',
                'gallery_preview',
                'youtube_videos',
                'videos_preview',
            )
        }),
        ('Metadata', {
            'fields': (
                'api_fetch_count',
                'last_updated',
                'created_at',
                'cache_info',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # Actions
    actions = [
        'mark_as_verified',
        'mark_as_unverified',
        'refresh_from_apis',
        'clear_cache',
    ]
    
    # Pagination
    list_per_page = 25
    
    # ==================== Custom Display Methods ====================
    
    @admin.display(description='Image', ordering='main_image')
    def image_preview(self, obj):
        """Show small thumbnail in list view"""
        if obj.main_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.main_image
            )
        return format_html('<span style="color: #999;">No Image</span>')
    
    @admin.display(description='Large Preview')
    def image_preview_large(self, obj):
        """Show large image in detail view"""
        if obj.main_image:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 400px; border-radius: 8px;" />',
                obj.main_image
            )
        return format_html('<span style="color: #999;">No main image</span>')
    
    @admin.display(description='Gallery')
    def gallery_preview(self, obj):
        """Show gallery images as thumbnails"""
        if not obj.gallery_images:
            return format_html('<span style="color: #999;">No gallery images</span>')
        
        html = '<div style="display: flex; flex-wrap: wrap; gap: 8px;">'
        for img_url in obj.gallery_images[:8]:  # Show first 8
            html += f'''
                <img src="{img_url}" 
                     style="width: 80px; height: 80px; object-fit: cover; border-radius: 4px;" 
                     title="{img_url}" />
            '''
        
        if len(obj.gallery_images) > 8:
            html += f'<div style="padding: 10px; color: #666;">+{len(obj.gallery_images) - 8} more</div>'
        
        html += '</div>'
        return format_html(html)
    
    @admin.display(description='Videos')
    def videos_preview(self, obj):
        """Show YouTube video thumbnails with links"""
        if not obj.youtube_videos:
            return format_html('<span style="color: #999;">No videos</span>')
        
        html = '<div style="display: flex; flex-direction: column; gap: 12px;">'
        for video in obj.youtube_videos[:4]:  # Show first 4
            video_id = video.get('youtube_id', '')
            thumbnail = video.get('thumbnail', '')
            title = video.get('title', 'Untitled')
            
            html += f'''
                <div style="display: flex; gap: 10px; align-items: center;">
                    <img src="{thumbnail}" 
                         style="width: 120px; height: 90px; object-fit: cover; border-radius: 4px;" />
                    <div>
                        <strong>{title[:60]}...</strong><br/>
                        <a href="https://youtube.com/watch?v={video_id}" target="_blank" 
                           style="color: #447e9b;">Watch on YouTube →</a>
                    </div>
                </div>
            '''
        
        html += '</div>'
        return format_html(html)
    
    @admin.display(description='Has Description', boolean=True)
    def has_description(self, obj):
        """Show if breed has description"""
        return bool(obj.description)
    
    @admin.display(description='Gallery Count')
    def gallery_count(self, obj):
        """Count of gallery images"""
        count = len(obj.gallery_images) if obj.gallery_images else 0
        if count == 0:
            return format_html('<span style="color: #999;">0</span>')
        return count
    
    @admin.display(description='Videos')
    def video_count(self, obj):
        """Count of YouTube videos"""
        count = len(obj.youtube_videos) if obj.youtube_videos else 0
        if count == 0:
            return format_html('<span style="color: #999;">0</span>')
        return count
    
    @admin.display(description='API Calls')
    def fetch_count(self, obj):
        """Number of times data was fetched from APIs"""
        if obj.api_fetch_count == 0:
            return format_html('<span style="color: #999;">0</span>')
        return obj.api_fetch_count
    
    @admin.display(description='Cache Info')
    def cache_info(self, obj):
        """Show cache status"""
        from django.core.cache import cache
        from info.constants import BREED_CACHE_KEY_PREFIX
        
        cache_key = f"{BREED_CACHE_KEY_PREFIX}:{obj.species}:{obj.name.lower()}"
        is_cached = cache.get(cache_key) is not None
        
        if is_cached:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Cached</span>'
            )
        return format_html(
            '<span style="color: orange;">Not in cache</span>'
        )
    
    # ==================== Custom Actions ====================
    
    @admin.action(description='Mark selected breeds as verified')
    def mark_as_verified(self, request, queryset):
        """Mark breeds as manually verified"""
        updated = queryset.update(is_verified=True)
        self.message_user(
            request,
            f'{updated} breed(s) marked as verified.',
            level='success'
        )
    
    @admin.action(description='Mark selected breeds as unverified')
    def mark_as_unverified(self, request, queryset):
        """Remove verification status"""
        updated = queryset.update(is_verified=False)
        self.message_user(
            request,
            f'{updated} breed(s) marked as unverified.',
            level='warning'
        )
    
    @admin.action(description='Refresh data from APIs (careful!)')
    def refresh_from_apis(self, request, queryset):
        """
        Re-fetch data from external APIs
        WARNING: This will make API calls for each selected breed
        """
        from info.services.breed_aggregator import BreedAggregator
        
        success_count = 0
        error_count = 0
        
        for breed in queryset:
            try:
                aggregator = BreedAggregator()
                updated_data = aggregator.fetch_breed_data(
                    breed_name=breed.name,
                    species=breed.species,
                    force_refresh=True
                )
                
                # Update breed with new data
                for key, value in updated_data.items():
                    if hasattr(breed, key):
                        setattr(breed, key, value)
                
                breed.save()
                success_count += 1
                
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f'Error refreshing {breed.name}: {str(e)}',
                    level='error'
                )
        
        if success_count > 0:
            self.message_user(
                request,
                f'Successfully refreshed {success_count} breed(s).',
                level='success'
            )
        
        if error_count > 0:
            self.message_user(
                request,
                f'Failed to refresh {error_count} breed(s).',
                level='warning'
            )
    
    @admin.action(description='Clear cache for selected breeds')
    def clear_cache(self, request, queryset):
        """Clear cache entries for selected breeds"""
        from django.core.cache import cache
        from info.constants import BREED_CACHE_KEY_PREFIX
        
        cleared = 0
        for breed in queryset:
            cache_key = f"{BREED_CACHE_KEY_PREFIX}:{breed.species}:{breed.name.lower()}"
            if cache.delete(cache_key):
                cleared += 1
        
        self.message_user(
            request,
            f'Cleared cache for {cleared} breed(s).',
            level='success'
        )
    
    # ==================== Custom Queryset ====================
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        # Add any annotations here if needed
        return qs


# Optional: Inline admin for future Pet integration
class BreedInline(admin.TabularInline):
    """
    Inline for showing breed info in Pet admin
    (Use this in your pets/admin.py if needed)
    """
    model = Breed
    extra = 0
    fields = ['name', 'species', 'image_preview', 'description']
    readonly_fields = ['image_preview']
    can_delete = False
    
    def image_preview(self, obj):
        if obj.main_image:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; object-fit: cover;" />',
                obj.main_image
            )
        return '-'
    image_preview.short_description = 'Image'