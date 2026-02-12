# adoption/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ShelterViewSet, 
    AdoptablePetViewSet, 
    AdoptionApplicationViewSet, 
    FavoriteViewSet, 
    AdoptionStatsView, 
    PetStatsBySpeciesView,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'shelters', ShelterViewSet, basename='shelter')
router.register(r'pets', AdoptablePetViewSet, basename='pet')
router.register(r'applications', AdoptionApplicationViewSet, basename='application')
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = [
    # Router URLs (includes all ViewSet routes)
    path('', include(router.urls)),
    
    # Statistics endpoints
    path('stats/', AdoptionStatsView.as_view(), name='adoption-stats'),
    path('stats/species/', PetStatsBySpeciesView.as_view(), name='pet-stats-species'),
]

"""
═══════════════════════════════════════════════════════════════════
COMPLETE API ENDPOINTS DOCUMENTATION
═══════════════════════════════════════════════════════════════════

BASE URL: /api/adoption/

─────────────────────────────────────────────────────────────────
SHELTER ENDPOINTS
─────────────────────────────────────────────────────────────────

List Shelters (Public)
GET     /api/adoption/shelters/
Query Params:
  - status: Filter by status (pending, approved, rejected)
  - verified: Filter by verified status (true/false)
  - city: Filter by city name
  - state: Filter by state
  - is_active: Filter by active status (true/false)
  - search: Search by name, description, city, state
  - ordering: Order by created_at, name, city

Create Shelter (Authenticated)
POST    /api/adoption/shelters/
Body: FormData with fields from ShelterCreateUpdateSerializer

Get Shelter Details (Public)
GET     /api/adoption/shelters/{slug}/

Update Shelter (Owner/Admin)
PUT     /api/adoption/shelters/{slug}/
PATCH   /api/adoption/shelters/{slug}/

Delete Shelter (Owner/Admin)
DELETE  /api/adoption/shelters/{slug}/

Get My Shelters (Authenticated)
GET     /api/adoption/shelters/my_shelters/

Get Shelter Pets (Public)
GET     /api/adoption/shelters/{slug}/pets/
Query Params:
  - status: Filter by pet status (available, pending, adopted)


─────────────────────────────────────────────────────────────────
PET ENDPOINTS
─────────────────────────────────────────────────────────────────

List Pets (Public)
GET     /api/adoption/pets/
Query Params: See full list in views.py AdoptablePetViewSet

Create Pet (Shelter Owner/Admin)
POST    /api/adoption/pets/

Get Pet Details (Public)
GET     /api/adoption/pets/{id}/

Update Pet (Shelter Owner/Admin)
PUT     /api/adoption/pets/{id}/
PATCH   /api/adoption/pets/{id}/

Delete Pet (Shelter Owner/Admin)
DELETE  /api/adoption/pets/{id}/

Get Featured Pets (Public)
GET     /api/adoption/pets/featured/

Get Urgent Pets (Public)
GET     /api/adoption/pets/urgent/

Toggle Favorite (Authenticated)
POST    /api/adoption/pets/{id}/toggle_favorite/


─────────────────────────────────────────────────────────────────
APPLICATION ENDPOINTS
─────────────────────────────────────────────────────────────────

List Applications (Authenticated)
GET     /api/adoption/applications/

Create Application (Authenticated)
POST    /api/adoption/applications/

Get Application Details (Authenticated)
GET     /api/adoption/applications/{id}/

Update Application (Applicant/Shelter Owner)
PUT     /api/adoption/applications/{id}/
PATCH   /api/adoption/applications/{id}/

Delete Application (Applicant)
DELETE  /api/adoption/applications/{id}/

Get My Applications (Authenticated)
GET     /api/adoption/applications/my_applications/

Get Shelter Applications (Shelter Owner)
GET     /api/adoption/applications/shelter_applications/

Approve Application (Shelter Owner)
POST    /api/adoption/applications/{id}/approve/

Reject Application (Shelter Owner)
POST    /api/adoption/applications/{id}/reject/

Withdraw Application (Applicant)
POST    /api/adoption/applications/{id}/withdraw/


─────────────────────────────────────────────────────────────────
FAVORITE ENDPOINTS
─────────────────────────────────────────────────────────────────

List Favorites (Authenticated)
GET     /api/adoption/favorites/

Get Favorite Details (Authenticated)
GET     /api/adoption/favorites/{id}/


─────────────────────────────────────────────────────────────────
STATISTICS ENDPOINTS
─────────────────────────────────────────────────────────────────

Get Overall Statistics (Public)
GET     /api/adoption/stats/

Get Species Statistics (Public)
GET     /api/adoption/stats/species/
"""