# products/category_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductCategoryViewSet, BrandViewSet

router = DefaultRouter()
router.register(r'categories', ProductCategoryViewSet, basename='category')
router.register(r'brands', BrandViewSet, basename='brand')

urlpatterns = [
    path('', include(router.urls)),
]