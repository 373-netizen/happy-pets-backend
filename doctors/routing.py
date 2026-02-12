# doctors/routing.py

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/doctors/chat/<int:consultation_id>/', consumers.ChatConsumer.as_asgi()),
]