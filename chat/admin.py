#chat/admin.py
from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ChatMessage, OnlineUser

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['user', 'message']
    ordering = ['-timestamp']

@admin.register(OnlineUser)
class OnlineUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'connected_at', 'last_seen']
    list_filter = ['connected_at']
    search_fields = ['username']
    ordering = ['-last_seen']