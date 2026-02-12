# products/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, F, Min, Max
from django.core.cache import cache

from .models import Product, ProductCategory, Brand, SavedProduct, ProductView
from .serializers import (
    ProductListSerializer, ProductDetailSerializer,
    ProductCategorySerializer, BrandSerializer,
    SavedProductSerializer, SavedProductCreateSerializer
)
from .filters import ProductFilter, AdvancedProductFilter
from .recommendations import SmartRecommendationEngine
from .pagination import ProductPagination
import logging

logger = logging.getLogger(__name__)


class ProductCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for product categories with hierarchical support
    """
    queryset = ProductCategory.objects.filter(is_active=True)
    serializer_class = ProductCategorySerializer
    lookup_field = 'slug'
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """
        Optionally filter by:
        - parent category
        - species
        - category_type
        """
        queryset = super().get_queryset()
        
        # Filter by parent (get subcategories)
        parent_slug = self.request.query_params.get('parent')
        if parent_slug:
            try:
                parent = ProductCategory.objects.get(slug=parent_slug)
                queryset = queryset.filter(parent=parent)
            except ProductCategory.DoesNotExist:
                pass
        
        # Filter root categories (no parent)
        root_only = self.request.query_params.get('root_only')
        if root_only == 'true':
            queryset = queryset.filter(parent__isnull=True)
        
        # Filter by species
        species = self.request.query_params.get('species')
        if species:
            queryset = queryset.filter(Q(species=species) | Q(species='all'))
        
        # Filter by category type
        category_type = self.request.query_params.get('type')
        if category_type:
            queryset = queryset.filter(category_type=category_type)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Get all products in a category"""
        category = self.get_object()
        
        # Get products from this category and all subcategories
        category_ids = [category.id]
        subcategories = category.children.all()
        category_ids.extend([sub.id for sub in subcategories])
        
        products = Product.objects.filter(
            category_id__in=category_ids,
            is_available=True
        ).select_related('brand', 'category')
        
        # Apply additional filters
        filterset = ProductFilter(request.GET, queryset=products)
        products = filterset.qs
        
        # Paginate
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def recommendations(self, request, slug=None):
        """Get recommended products for this category"""
        category = self.get_object()
        
        engine = SmartRecommendationEngine(
            user=request.user if request.user.is_authenticated else None
        )
        
        recommendations = engine.get_category_recommendations(
            category=category,
            limit=int(request.query_params.get('limit', 12))
        )
        
        serializer = ProductListSerializer(
            recommendations,
            many=True,
            context={'request': request}
        )
        
        return Response(serializer.data)


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for brands
    """
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get all products by a brand"""
        brand = self.get_object()
        
        products = Product.objects.filter(
            brand=brand,
            is_available=True
        ).select_related('brand', 'category')
        
        # Apply filters
        filterset = ProductFilter(request.GET, queryset=products)
        products = filterset.qs
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for products with smart filtering and recommendations
    """
    queryset = Product.objects.filter(is_available=True).select_related('brand', 'category')
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'tags', 'brand__name']
    ordering_fields = ['price', 'rating', 'created_at', 'view_count', 'save_count']
    ordering = ['-is_featured', '-is_trending', '-rating']
    pagination_class = ProductPagination
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Track product views and return product details with recommendations"""
        instance = self.get_object()
        
        # Increment view count
        instance.increment_views()
        
        # Track user view for recommendations
        if request.user.is_authenticated:
            ProductView.objects.create(user=request.user, product=instance)
        else:
            session_id = request.session.session_key
            if not session_id:
                session_id = request.session.create()
            ProductView.objects.create(product=instance, session_id=session_id)
        
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Add context-aware recommendations
        engine = SmartRecommendationEngine(
            user=request.user if request.user.is_authenticated else None,
            session_id=request.session.session_key
        )
        
        recommendations = engine.get_recommendations(
            context_product=instance,
            limit=8
        )
        
        data['context_recommendations'] = ProductListSerializer(
            recommendations,
            many=True,
            context=self.context
        ).data
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """
        Get personalized product recommendations
        
        Query params:
        - species: Filter by pet species
        - limit: Number of recommendations (default: 12)
        """
        species = request.query_params.get('species')
        limit = int(request.query_params.get('limit', 12))
        
        engine = SmartRecommendationEngine(
            user=request.user if request.user.is_authenticated else None,
            session_id=request.session.session_key
        )
        
        recommendations = engine.get_recommendations(
            species=species,
            limit=limit
        )
        
        serializer = self.get_serializer(recommendations, many=True)
        
        return Response({
            'count': len(recommendations),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending products"""
        species = request.query_params.get('species')
        limit = int(request.query_params.get('limit', 12))
        
        query = Q(is_trending=True, is_available=True)
        if species:
            query &= Q(species=species)
        
        products = self.get_queryset().filter(query).order_by(
            '-view_count', '-rating'
        )[:limit]
        
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products"""
        species = request.query_params.get('species')
        limit = int(request.query_params.get('limit', 12))
        
        query = Q(is_featured=True, is_available=True)
        if species:
            query &= Q(species=species)
        
        products = self.get_queryset().filter(query).order_by('-rating')[:limit]
        
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """Get top rated products"""
        species = request.query_params.get('species')
        limit = int(request.query_params.get('limit', 12))
        
        query = Q(rating__gte=4.5, review_count__gte=10, is_available=True)
        if species:
            query &= Q(species=species)
        
        products = self.get_queryset().filter(query).order_by(
            '-rating', '-review_count'
        )[:limit]
        
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def filter_advanced(self, request):
        """
        Advanced filtering endpoint
        
        POST body example:
        {
            "species": "cat",
            "category_types": ["food", "toys"],
            "food_types": ["dry", "wet"],
            "toy_types": ["interactive", "puzzle"],
            "min_price": 10,
            "max_price": 50,
            "min_rating": 4.0,
            "tags": ["grain-free", "organic"],
            "age_group": "adult",
            "size": "all",
            "in_stock_only": true,
            "sort_by": "-rating"
        }
        """
        queryset = self.get_queryset()
        
        # Apply filters from request body
        filters = request.data
        
        # Species filter
        if filters.get('species'):
            queryset = queryset.filter(species=filters['species'])
        
        # Category types filter
        if filters.get('category_types'):
            queryset = queryset.filter(
                category__category_type__in=filters['category_types']
            )
        
        # Food type filter
        if filters.get('food_types'):
            queryset = queryset.filter(food_type__in=filters['food_types'])
        
        # Toy type filter
        if filters.get('toy_types'):
            queryset = queryset.filter(toy_type__in=filters['toy_types'])
        
        # Grooming type filter
        if filters.get('grooming_types'):
            queryset = queryset.filter(grooming_type__in=filters['grooming_types'])
        
        # Health type filter
        if filters.get('health_types'):
            queryset = queryset.filter(health_type__in=filters['health_types'])
        
        # Price range
        if filters.get('min_price'):
            queryset = queryset.filter(price__gte=filters['min_price'])
        if filters.get('max_price'):
            queryset = queryset.filter(price__lte=filters['max_price'])
        
        # Rating filter
        if filters.get('min_rating'):
            queryset = queryset.filter(rating__gte=filters['min_rating'])
        
        # Tags filter
        if filters.get('tags'):
            for tag in filters['tags']:
                queryset = queryset.filter(tags__icontains=tag)
        
        # Age group
        if filters.get('age_group'):
            queryset = queryset.filter(
                Q(age_group=filters['age_group']) | Q(age_group='all')
            )
        
        # Size suitability
        if filters.get('size'):
            queryset = queryset.filter(
                Q(size_suitability=filters['size']) | Q(size_suitability='all')
            )
        
        # Brand filter
        if filters.get('brands'):
            queryset = queryset.filter(brand_id__in=filters['brands'])
        
        # In stock only
        if filters.get('in_stock_only'):
            queryset = queryset.filter(stock__gt=0)
        
        # Sorting
        sort_by = filters.get('sort_by', '-rating')
        queryset = queryset.order_by(sort_by)
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def similar(self, request, slug=None):
        """Get similar products"""
        product = self.get_object()
        
        engine = SmartRecommendationEngine()
        similar = engine._get_similar_products(product, limit=8)
        
        serializer = self.get_serializer(similar, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def complementary(self, request, slug=None):
        """Get complementary products"""
        product = self.get_object()
        
        engine = SmartRecommendationEngine()
        complementary = engine._get_complementary_products(product, limit=8)
        
        serializer = self.get_serializer(complementary, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def save(self, request, slug=None):
        """Save/bookmark a product"""
        product = self.get_object()
        notes = request.data.get('notes', '')
        
        saved_product, created = SavedProduct.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'notes': notes}
        )
        
        if not created:
            saved_product.notes = notes
            saved_product.save()
        else:
            product.save_count = F('save_count') + 1
            product.save(update_fields=['save_count'])
        
        return Response({
            'message': 'Product saved successfully',
            'is_saved': True
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unsave(self, request, slug=None):
        """Remove product from saved"""
        product = self.get_object()
        
        deleted_count, _ = SavedProduct.objects.filter(
            user=request.user,
            product=product
        ).delete()
        
        if deleted_count:
            product.save_count = F('save_count') - 1
            product.save(update_fields=['save_count'])
        
        return Response({
            'message': 'Product removed from saved items',
            'is_saved': False
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def saved(self, request):
        """Get user's saved products"""
        saved_products = SavedProduct.objects.filter(
            user=request.user
        ).select_related('product', 'product__brand', 'product__category')
        
        page = self.paginate_queryset(saved_products)
        if page is not None:
            serializer = SavedProductSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = SavedProductSerializer(saved_products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def filter_options(self, request):
        """
        Get available filter options for the UI
        Returns all possible filter values
        """
        species = request.query_params.get('species')
        
        queryset = self.get_queryset()
        if species:
            queryset = queryset.filter(species=species)
        
        # Get unique values for filters
        categories = ProductCategory.objects.filter(
            products__in=queryset,
            is_active=True
        ).distinct().values('id', 'name', 'slug', 'category_type')
        
        brands = Brand.objects.filter(
            products__in=queryset
        ).distinct().values('id', 'name', 'slug')
        
        food_types = queryset.exclude(food_type='').values_list(
            'food_type', flat=True
        ).distinct()
        
        toy_types = queryset.exclude(toy_type='').values_list(
            'toy_type', flat=True
        ).distinct()
        
        grooming_types = queryset.exclude(grooming_type='').values_list(
            'grooming_type', flat=True
        ).distinct()
        
        health_types = queryset.exclude(health_type='').values_list(
            'health_type', flat=True
        ).distinct()
        
        # Get all tags
        all_tags = set()
        for product in queryset.values_list('tags', flat=True):
            if product:
                all_tags.update(product)
        
        return Response({
            'categories': list(categories),
            'brands': list(brands),
            'food_types': [{'value': ft, 'label': dict(Product._meta.get_field('food_type').choices).get(ft)} for ft in food_types],
            'toy_types': [{'value': tt, 'label': dict(Product._meta.get_field('toy_type').choices).get(tt)} for tt in toy_types],
            'grooming_types': [{'value': gt, 'label': dict(Product._meta.get_field('grooming_type').choices).get(gt)} for gt in grooming_types],
            'health_types': [{'value': ht, 'label': dict(Product._meta.get_field('health_type').choices).get(ht)} for ht in health_types],
            'tags': sorted(list(all_tags)),
           'price_range': {
                'min': queryset.aggregate(min_price=Min('price'))['min_price'] or 0,
                'max': queryset.aggregate(max_price=Max('price'))['max_price'] or 0
            }
        })
    # At the top with other imports
import logging
logger = logging.getLogger(__name__)

# In the ProductViewSet class, add this method:
def list(self, request, *args, **kwargs):
    """Override list to add debugging"""
    try:
        logger.info(f"Products list called with params: {request.query_params}")
        return super().list(request, *args, **kwargs)
    except Exception as e:
        logger.error(f"Products list error: {str(e)}", exc_info=True)
        from django.http import JsonResponse
        return JsonResponse({'error': str(e), 'detail': 'Error fetching products'}, status=400)