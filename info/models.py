"""
Breed model - stores aggregated data from multiple APIs
"""

from django.db import models
from django.core.validators import URLValidator
from django.utils import timezone
from info.constants import SPECIES_CHOICES


class Breed(models.Model):
    """
    Breed information aggregated from Wikipedia, Dog/Cat API, and YouTube
    
    Data Flow:
    1. User requests breed info via API
    2. Check if exists in DB (this model)
    3. If not, fetch from external APIs
    4. Store here and return
    """
    
    # ==================== Core Fields ====================
    
    name = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Breed name (e.g., 'Golden Retriever', 'Persian')"
    )
    
    species = models.CharField(
        max_length=20,
        choices=SPECIES_CHOICES,
        db_index=True,
        help_text="Animal species"
    )
    
    # ==================== Wikipedia Data ====================
    
    description = models.TextField(
        blank=True,
        help_text="Brief description from Wikipedia"
    )
    
    origin = models.CharField(
        max_length=200,
        blank=True,
        help_text="Country/region of origin"
    )
    
    wikipedia_url = models.URLField(
        blank=True,
        validators=[URLValidator()],
        help_text="Wikipedia page URL"
    )
    
    # ==================== Dog/Cat API Data ====================
    
    life_span = models.CharField(
        max_length=50,
        blank=True,
        help_text="Life span (e.g., '10-12 years')"
    )
    
    temperament = models.TextField(
        blank=True,
        help_text="Temperament/personality traits"
    )
    
    weight = models.CharField(
        max_length=100,
        blank=True,
        help_text="Weight range (e.g., '25-35 kg')"
    )
    
    height = models.CharField(
        max_length=100,
        blank=True,
        help_text="Height range (e.g., '55-60 cm')"
    )
    
    # ==================== Media Fields ====================
    
    main_image = models.URLField(
        blank=True,
        validators=[URLValidator()],
        help_text="Primary breed image URL"
    )
    
    gallery_images = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of image URLs for gallery"
    )
    
    youtube_videos = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of video objects: [{title, youtube_id, thumbnail}]"
    )
    
    # ==================== Metadata ====================
    
    is_verified = models.BooleanField(
        default=False,
        help_text="Manually verified by admin"
    )
    
    api_fetch_count = models.IntegerField(
        default=0,
        help_text="Number of times data was fetched from APIs"
    )
    
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="Last time data was updated"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When breed was first added to DB"
    )
    
    # ==================== Meta ====================
    
    class Meta:
        db_table = 'breed_info'
        ordering = ['name']
        verbose_name = 'Breed'
        verbose_name_plural = 'Breeds'
        
        # Composite unique constraint
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'species'],
                name='unique_breed_species'
            )
        ]
        
        # Performance indexes
        indexes = [
            models.Index(fields=['species', 'name']),
            models.Index(fields=['last_updated']),
            models.Index(fields=['is_verified']),
        ]
    
    # ==================== Methods ====================
    
    def __str__(self):
        return f"{self.name} ({self.get_species_display()})"
    
    def increment_fetch_count(self):
        """Increment API fetch counter"""
        self.api_fetch_count += 1
        self.save(update_fields=['api_fetch_count', 'last_updated'])
    
    def has_complete_data(self):
        """Check if breed has all essential data"""
        return all([
            self.description,
            self.main_image,
            self.gallery_images,
            self.youtube_videos,
        ])
    
    def get_cache_key(self):
        """Generate cache key for this breed"""
        from info.constants import BREED_CACHE_KEY_PREFIX
        return f"{BREED_CACHE_KEY_PREFIX}:{self.species}:{self.name.lower()}"
    
    def clear_cache(self):
        """Clear cache entry for this breed"""
        from django.core.cache import cache
        cache.delete(self.get_cache_key())
    
    def to_api_response(self):
        """
        Convert to clean API response format
        IMPORTANT: This hides internal structure from external APIs
        """
        return {
            'name': self.name,
            'species': self.species,
            'description': self.description,
            'origin': self.origin,
            'life_span': self.life_span,
            'temperament': self.temperament,
            'weight': self.weight,
            'height': self.height,
            'main_image': self.main_image,
            'gallery': self.gallery_images,
            'videos': self.youtube_videos,
            'wikipedia_url': self.wikipedia_url,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }