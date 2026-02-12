# products/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ProductCategoryViewSet, BrandViewSet

# Create two separate routers
products_router = DefaultRouter()
products_router.register(r'', ProductViewSet, basename='product')

# Create standalone routers for categories and brands that go to /api/ level
app_name = 'products'

urlpatterns = [
    # Products under /api/products/
    path('', include(products_router.urls)),
]