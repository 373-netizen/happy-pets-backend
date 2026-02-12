# services/urls.py
from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Main endpoint - Get nearby services
    path('nearby/', views.nearby_services, name='nearby-services'),
    
    # Service details
    path('<int:service_id>/', views.service_details, name='service-details'),
    
    # Reviews
    path('<int:service_id>/review/', views.add_review, name='add-review'),
    
    # Favorites
    path('<int:service_id>/favorite/', views.toggle_favorite, name='toggle-favorite'),
    path('favorites/', views.get_favorites, name='get-favorites'),
]