"""
URL Configuration for Info App
Place this in: info/urls.py
"""

from django.urls import path
from . import views

urlpatterns = [
    # Dog Breeds
    path('dog-breeds/', views.dog_breeds_list, name='dog-breeds-list'),
    path('breeds/dog/<slug:slug>/', views.dog_breed_detail, name='dog-breed-detail'),
    
    # Cat Breeds
    path('cat-breeds/', views.cat_breeds_list, name='cat-breeds-list'),
    path('breeds/cat/<slug:slug>/', views.cat_breed_detail, name='cat-breed-detail'),
    
    # Bird Species
    path('bird-breeds/', views.bird_breeds_list, name='bird-breeds-list'),
    path('breeds/bird/<slug:slug>/', views.bird_breed_detail, name='bird-breed-detail'),  # ← ADD THIS!
    

    # Exotic Pets
    path('exotic-pets/', views.exotic_pets_list, name='exotic-pets-list'),
    path('exotic/<slug:slug>/', views.exotic_pet_detail, name='exotic-pet-detail'),
]