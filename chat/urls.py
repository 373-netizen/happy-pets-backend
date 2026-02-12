#chat/urls.py
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('messages/', views.get_messages, name='get_messages'),
    path('send/', views.send_message, name='send_message'),
    path('online/', views.get_online_count, name='online_count'),
    path('clear/', views.clear_messages, name='clear_messages'),
      path('upload/', views.upload_file, name='upload_file'), 
]