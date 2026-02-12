# services/views.py
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Avg
from django.conf import settings
from decimal import Decimal
import requests
from math import radians, cos, sin, asin, sqrt
import logging

from .models import (
    PetService, UserServiceReview, UserServiceFavorite, 
    ServiceAppointment, ServiceCategory
)

logger = logging.getLogger(__name__)

# Google Places API Configuration (Optional - only if you want real data)
GOOGLE_PLACES_API_KEY = getattr(settings, 'GOOGLE_PLACES_API_KEY', '')
PLACES_NEARBY_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
PLACES_DETAILS_URL = 'https://maps.googleapis.com/maps/api/place/details/json'
PLACES_PHOTO_URL = 'https://maps.googleapis.com/maps/api/place/photo'


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula (returns km)"""
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    return round(km, 2)


# ==================== NEARBY SERVICES ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nearby_services(request):
    """Get nearby pet services based on user location"""
    try:
        user = request.user
        
        # Check if user has location data
        if not user.latitude or not user.longitude:
            return Response({
                'success': False,
                'error': 'Location not found. Please update your profile with location.',
                'services': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        category = request.GET.get('category', 'all')
        radius = int(request.GET.get('radius', 5000))  # meters
        use_cache = request.GET.get('use_cache', 'true').lower() == 'true'
        
        user_lat = float(user.latitude)
        user_lon = float(user.longitude)
        
        # Build category filter
        if category != 'all':
            category_filter = Q(category=category)
        else:
            category_filter = Q()
        
        # Get services from database
        lat_range = Decimal('0.1')  # ~11km
        lon_range = Decimal('0.1')
        
        cached_services = PetService.objects.filter(
            category_filter,
            latitude__gte=user.latitude - lat_range,
            latitude__lte=user.latitude + lat_range,
            longitude__gte=user.longitude - lon_range,
            longitude__lte=user.longitude + lon_range
        )
        
        # If Google API key is available and we need more data
        if GOOGLE_PLACES_API_KEY and (not use_cache or cached_services.count() < 5):
            if category == 'all':
                fetch_nearby_services_from_google(user_lat, user_lon, 'vet', radius)
                fetch_nearby_services_from_google(user_lat, user_lon, 'grooming', radius)
                fetch_nearby_services_from_google(user_lat, user_lon, 'spa', radius)
            else:
                fetch_nearby_services_from_google(user_lat, user_lon, category, radius)
            
            # Refresh
            cached_services = PetService.objects.filter(
                category_filter,
                latitude__gte=user.latitude - lat_range,
                latitude__lte=user.latitude + lat_range,
                longitude__gte=user.longitude - lon_range,
                longitude__lte=user.longitude + lon_range
            )
        
        # Calculate distances
        services_with_distance = []
        for service in cached_services:
            distance = calculate_distance(
                user_lat, user_lon,
                float(service.latitude), float(service.longitude)
            )
            
            if distance <= radius / 1000:
                user_review = UserServiceReview.objects.filter(
                    user=user, service=service
                ).first()
                
                is_favorited = UserServiceFavorite.objects.filter(
                    user=user, service=service
                ).exists()
                
                services_with_distance.append({
                    'id': service.id,
                    'place_id': service.place_id,
                    'name': service.name,
                    'category': service.category,
                    'category_display': service.get_category_display(),
                    'address': service.address,
                    'latitude': float(service.latitude),
                    'longitude': float(service.longitude),
                    'distance_km': distance,
                    'phone_number': service.phone_number,
                    'website': service.website,
                    'google_rating': float(service.google_rating) if service.google_rating else None,
                    'total_ratings': service.total_ratings,
                    'photo_url': get_photo_url(service.photo_reference) if service.photo_reference else None,
                    'opening_hours': service.opening_hours,
                    'price_level': service.price_level,
                    'is_open_now': service.is_open_now,
                    'business_status': service.business_status,
                    'user_review': {
                        'rating': user_review.rating,
                        'review_text': user_review.review_text
                    } if user_review else None,
                    'is_favorited': is_favorited,
                })
        
        services_with_distance.sort(key=lambda x: x['distance_km'])
        
        return Response({
            'success': True,
            'user_location': {
                'latitude': user_lat,
                'longitude': user_lon
            },
            'services': services_with_distance,
            'total': len(services_with_distance)
        })
        
    except Exception as e:
        logger.error(f"Error getting nearby services: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def fetch_nearby_services_from_google(lat, lon, category, radius=5000):
    """Fetch services from Google Places API (optional)"""
    if not GOOGLE_PLACES_API_KEY:
        logger.warning("Google Places API key not configured")
        return
    
    try:
        type_mapping = {
            'vet': 'veterinary_care',
            'grooming': 'pet_store',
            'spa': 'spa'
        }
        
        keywords = {
            'vet': 'veterinary hospital',
            'grooming': 'pet grooming',
            'spa': 'pet spa'
        }
        
        params = {
            'location': f"{lat},{lon}",
            'radius': radius,
            'type': type_mapping.get(category, 'veterinary_care'),
            'keyword': keywords.get(category, ''),
            'key': GOOGLE_PLACES_API_KEY
        }
        
        response = requests.get(PLACES_NEARBY_URL, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Google Places API error: {response.status_code}")
            return
        
        data = response.json()
        
        if data.get('status') != 'OK':
            logger.warning(f"Google Places API status: {data.get('status')}")
            return
        
        for place in data.get('results', []):
            try:
                place_id = place['place_id']
                details = get_place_details(place_id)
                
                PetService.objects.update_or_create(
                    place_id=place_id,
                    defaults={
                        'name': place.get('name', 'Unknown'),
                        'category': category,
                        'address': place.get('vicinity', ''),
                        'latitude': Decimal(str(place['geometry']['location']['lat'])),
                        'longitude': Decimal(str(place['geometry']['location']['lng'])),
                        'phone_number': details.get('formatted_phone_number', ''),
                        'website': details.get('website', ''),
                        'google_rating': Decimal(str(place.get('rating', 0))) if place.get('rating') else None,
                        'total_ratings': place.get('user_ratings_total', 0),
                        'photo_reference': place.get('photos', [{}])[0].get('photo_reference', '') if place.get('photos') else '',
                        'opening_hours': details.get('opening_hours', {}),
                        'price_level': place.get('price_level'),
                        'is_open_now': place.get('opening_hours', {}).get('open_now', False),
                        'business_status': place.get('business_status', 'OPERATIONAL'),
                    }
                )
            except Exception as e:
                logger.error(f"Error processing place: {e}")
                continue
        
        logger.info(f"Cached {len(data.get('results', []))} {category} services")
        
    except Exception as e:
        logger.error(f"Error fetching from Google Places: {e}")


def get_place_details(place_id):
    """Get detailed information about a place"""
    if not GOOGLE_PLACES_API_KEY:
        return {}
    
    try:
        params = {
            'place_id': place_id,
            'fields': 'formatted_phone_number,website,opening_hours',
            'key': GOOGLE_PLACES_API_KEY
        }
        
        response = requests.get(PLACES_DETAILS_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                return data.get('result', {})
        
        return {}
    except Exception as e:
        logger.error(f"Error getting place details: {e}")
        return {}


def get_photo_url(photo_reference, max_width=400):
    """Generate Google Places photo URL"""
    if not photo_reference or not GOOGLE_PLACES_API_KEY:
        return None
    
    return f"{PLACES_PHOTO_URL}?maxwidth={max_width}&photo_reference={photo_reference}&key={GOOGLE_PLACES_API_KEY}"


# ==================== SERVICE DETAILS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def service_details(request, service_id):
    """Get detailed information about a service"""
    try:
        service = get_object_or_404(PetService, id=service_id)
        user = request.user
        
        if user.latitude and user.longitude:
            distance = calculate_distance(
                float(user.latitude), float(user.longitude),
                float(service.latitude), float(service.longitude)
            )
        else:
            distance = None
        
        reviews = UserServiceReview.objects.filter(service=service).select_related('user')
        reviews_data = [{
            'id': review.id,
            'user_name': review.user.get_full_name() or review.user.username,
            'rating': review.rating,
            'review_text': review.review_text,
            'created_at': review.created_at.isoformat(),
        } for review in reviews]
        
        avg_user_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        
        is_favorited = UserServiceFavorite.objects.filter(
            user=user, service=service
        ).exists()
        
        service.times_viewed += 1
        service.save(update_fields=['times_viewed'])
        
        return Response({
            'success': True,
            'service': {
                'id': service.id,
                'name': service.name,
                'category': service.category,
                'address': service.address,
                'latitude': float(service.latitude),
                'longitude': float(service.longitude),
                'distance_km': distance,
                'phone_number': service.phone_number,
                'website': service.website,
                'google_rating': float(service.google_rating) if service.google_rating else None,
                'user_rating_avg': float(avg_user_rating) if avg_user_rating else None,
                'is_favorited': is_favorited,
            },
            'reviews': reviews_data
        })
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== FAVORITES ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_favorite(request, service_id):
    """Add or remove service from favorites"""
    try:
        service = get_object_or_404(PetService, id=service_id)
        user = request.user
        
        favorite, created = UserServiceFavorite.objects.get_or_create(
            user=user, service=service
        )
        
        if not created:
            favorite.delete()
            return Response({
                'success': True,
                'favorited': False,
                'message': 'Removed from favorites'
            })
        
        return Response({
            'success': True,
            'favorited': True,
            'message': 'Added to favorites'
        })
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, 
                       status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_favorites(request):
    """Get user's favorite services"""
    try:
        favorites = UserServiceFavorite.objects.filter(
            user=request.user
        ).select_related('service')
        
        favorites_data = []
        for fav in favorites:
            service = fav.service
            
            if request.user.latitude and request.user.longitude:
                distance = calculate_distance(
                    float(request.user.latitude), float(request.user.longitude),
                    float(service.latitude), float(service.longitude)
                )
            else:
                distance = None
            
            favorites_data.append({
                'id': fav.id,
                'service': {
                    'id': service.id,
                    'name': service.name,
                    'category': service.category,
                    'address': service.address,
                    'distance_km': distance,
                    'google_rating': float(service.google_rating) if service.google_rating else None,
                    'phone_number': service.phone_number,
                },
                'created_at': fav.created_at.isoformat()
            })
        
        return Response({
            'success': True,
            'favorites': favorites_data
        })
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== REVIEWS ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_review(request, service_id):
    """Add or update a review for a service"""
    try:
        service = get_object_or_404(PetService, id=service_id)
        user = request.user
        
        rating = request.data.get('rating')
        review_text = request.data.get('review_text', '')
        
        if not rating or rating < 1 or rating > 5:
            return Response({
                'success': False,
                'error': 'Rating must be between 1 and 5'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        review, created = UserServiceReview.objects.update_or_create(
            user=user,
            service=service,
            defaults={
                'rating': rating,
                'review_text': review_text,
            }
        )
        
        return Response({
            'success': True,
            'created': created,
            'review': {
                'id': review.id,
                'rating': review.rating,
                'review_text': review.review_text,
            }
        })
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, 
                       status=status.HTTP_400_BAD_REQUEST)