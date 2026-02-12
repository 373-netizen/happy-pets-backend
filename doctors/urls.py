# doctors/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DoctorProfileViewSet,
    ConsultationViewSet,
    ChatMessageViewSet,
    DoctorReviewViewSet,
    FavoriteDoctorViewSet,
    QuickReplyViewSet,
    DoctorStatsView
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'profiles', DoctorProfileViewSet, basename='doctor-profile')
router.register(r'consultations', ConsultationViewSet, basename='consultation')
router.register(r'messages', ChatMessageViewSet, basename='message')
router.register(r'reviews', DoctorReviewViewSet, basename='review')
router.register(r'favorites', FavoriteDoctorViewSet, basename='favorite')
router.register(r'quick-replies', QuickReplyViewSet, basename='quick-reply')

# Define URL patterns
urlpatterns = [
    # Router URLs - includes all viewset endpoints
    path('', include(router.urls)),
    
    # Additional API views
    path('stats/', DoctorStatsView.as_view(), name='doctor-stats'),
]

# Available endpoints:
# GET/POST    /api/doctors/profiles/
# GET/PUT     /api/doctors/profiles/{id}/
# GET         /api/doctors/profiles/me/
# POST        /api/doctors/profiles/{id}/toggle_online/
# GET/POST    /api/doctors/profiles/{id}/availability/
#
# GET/POST    /api/doctors/consultations/
# GET/PUT     /api/doctors/consultations/{id}/
# POST        /api/doctors/consultations/{id}/create_payment_intent/
# POST        /api/doctors/consultations/{id}/confirm_payment/
# POST        /api/doctors/consultations/{id}/start/
# POST        /api/doctors/consultations/{id}/complete/
# POST        /api/doctors/consultations/{id}/cancel/
#
# GET/POST    /api/doctors/messages/
# GET/PUT     /api/doctors/messages/{id}/
#
# GET/POST    /api/doctors/reviews/
# GET/PUT     /api/doctors/reviews/{id}/
#
# GET/POST    /api/doctors/favorites/
# DELETE      /api/doctors/favorites/{id}/
#
# GET/POST    /api/doctors/quick-replies/
# GET/PUT/DEL /api/doctors/quick-replies/{id}/
#
# GET         /api/doctors/stats/