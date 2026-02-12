# pets/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PetViewSet,
    AppointmentViewSet,
    VaccinationViewSet,
    HealthRecordViewSet,
    ReminderViewSet,
    dashboard_stats,
    check_auth,
   
)

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'pets', PetViewSet, basename='pet')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'vaccinations', VaccinationViewSet, basename='vaccination')
router.register(r'health-records', HealthRecordViewSet, basename='healthrecord')
router.register(r'reminders', ReminderViewSet, basename='reminder')

# URL patterns
urlpatterns = [
    # Include all router URLs
    path('', include(router.urls)),

    # Dashboard stats endpoint
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),

    # Auth check endpoint
    path('auth/check/', check_auth, name='check-auth'),

   
]
