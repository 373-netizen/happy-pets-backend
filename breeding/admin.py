#breeding/admin.py
from django.contrib import admin
from .models import BreedingSwipe, BreedingMatch, BreedingChatMessage


@admin.register(BreedingSwipe)
class BreedingSwipeAdmin(admin.ModelAdmin):
    list_display = ('user_pet', 'target_pet', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user_pet__name', 'target_pet__name')


@admin.register(BreedingMatch)
class BreedingMatchAdmin(admin.ModelAdmin):
    list_display = ('pet1', 'pet2', 'created_at', 'chat_unlocked')
    list_filter = ('created_at', 'chat_unlocked')
    search_fields = ('pet1__name', 'pet2__name')


@admin.register(BreedingChatMessage)
class BreedingChatMessageAdmin(admin.ModelAdmin):
    list_display = ('match', 'sender', 'read', 'created_at')
    list_filter = ('read', 'created_at')
    search_fields = ('sender__username',)
