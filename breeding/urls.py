# breeding/urls.py
from django.urls import path
from . import views

app_name = 'breeding'

urlpatterns = [
    # Matchmaking endpoints
    path('available-pets/', views.available_pets, name='available-pets'),
    path('swipe/', views.swipe, name='swipe'),
    path('matches/', views.matches, name='matches'),
    path('stats/', views.stats, name='stats'),
    
    # Chat endpoints
    path('chat/<int:match_id>/', views.chat, name='chat'),
    path('chat/<int:match_id>/read/', views.mark_as_read, name='mark-as-read'),
    
    # Match management
    path('unmatch/<int:match_id>/', views.unmatch, name='unmatch'),
    
    # Notification preferences - FIXED: removed 'breeding/' prefix
    path('notification-preferences/', views.notification_preferences, name='notification-preferences'),
]