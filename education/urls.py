# education/urls.py - UPDATED WITH NEW ENDPOINTS
from django.urls import path
from . import views

app_name = 'education'

urlpatterns = [
    # Main endpoints
    path('recommendations/', views.recommendations, name='recommendations'),
    path('search/', views.search, name='search'),
    
    # Bookmarks
    path('bookmark/', views.bookmark, name='bookmark'),
    path('bookmarks/', views.get_bookmarks, name='get-bookmarks'),
    
    # NEW: View tracking for better recommendations
    path('track-view/', views.track_view, name='track-view'),
]