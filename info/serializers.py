"""
Serializers for Breed API endpoints
"""

from rest_framework import serializers
from info.models import Breed
from info.constants import SPECIES_CHOICES


class YouTubeVideoSerializer(serializers.Serializer):
    """Embedded serializer for YouTube videos"""
    title = serializers.CharField()
    youtube_id = serializers.CharField()
    thumbnail = serializers.URLField()
    url = serializers.SerializerMethodField()
    
    def get_url(self, obj):
        return f"https://www.youtube.com/watch?v={obj.get('youtube_id', '')}"


class BreedListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for breed listing
    Used in GET /api/breeds/
    """
    species_display = serializers.CharField(source='get_species_display', read_only=True)
    has_complete_data = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Breed
        fields = [
            'id',
            'name',
            'species',
            'species_display',
            'main_image',
            'description',
            'has_complete_data',
            'last_updated',
        ]
        read_only_fields = fields


class BreedDetailSerializer(serializers.ModelSerializer):
    """
    Complete serializer for breed details
    Used in GET /api/breeds/<id>/ or /api/breeds/<name>/
    """
    species_display = serializers.CharField(source='get_species_display', read_only=True)
    videos = YouTubeVideoSerializer(source='youtube_videos', many=True, read_only=True)
    gallery_count = serializers.SerializerMethodField()
    video_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Breed
        fields = [
            'id',
            'name',
            'species',
            'species_display',
            'description',
            'origin',
            'life_span',
            'temperament',
            'weight',
            'height',
            'main_image',
            'gallery_images',
            'videos',
            'gallery_count',
            'video_count',
            'wikipedia_url',
            'is_verified',
            'last_updated',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_gallery_count(self, obj):
        return len(obj.gallery_images) if obj.gallery_images else 0
    
    def get_video_count(self, obj):
        return len(obj.youtube_videos) if obj.youtube_videos else 0


class BreedCreateSerializer(serializers.Serializer):
    """
    Serializer for creating/fetching breed data
    Used in POST /api/breeds/fetch/
    """
    name = serializers.CharField(
        max_length=200,
        required=True,
        help_text="Breed name to fetch (e.g., 'Golden Retriever')"
    )
    species = serializers.ChoiceField(
        choices=SPECIES_CHOICES,
        required=True,
        help_text="Species type"
    )
    force_refresh = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Force re-fetch from APIs even if data exists"
    )
    
    def validate_name(self, value):
        """Normalize breed name"""
        return value.strip().title()


class BreedSearchSerializer(serializers.Serializer):
    """
    Serializer for search parameters
    Used in GET /api/breeds/search/
    """
    q = serializers.CharField(
        required=False,
        help_text="Search query for breed name"
    )
    species = serializers.ChoiceField(
        choices=SPECIES_CHOICES,
        required=False,
        help_text="Filter by species"
    )
    verified_only = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Only return verified breeds"
    )