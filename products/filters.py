# products/filters.py
import django_filters
from django.db.models import Q
from .models import Product, ProductCategory, Brand


class ProductFilter(django_filters.FilterSet):
    """
    Advanced filtering for products with granular options
    """
    
    # Text search
    search = django_filters.CharFilter(method='filter_search', label='Search')
    
    # Species filter
    species = django_filters.MultipleChoiceFilter(
        field_name='species',
        choices=Product._meta.get_field('species').choices,
        label='Pet Species'
    )
    
    # Category filters (hierarchical)
    category = django_filters.ModelMultipleChoiceFilter(
        queryset=ProductCategory.objects.all(),
        label='Categories'
    )
    category_type = django_filters.MultipleChoiceFilter(
        field_name='category__category_type',
        choices=ProductCategory._meta.get_field('category_type').choices,
        label='Category Type'
    )
    
    # Brand filter
    brand = django_filters.ModelMultipleChoiceFilter(
        queryset=Brand.objects.all(),
        label='Brands'
    )
    
    # Age group filter
    age_group = django_filters.MultipleChoiceFilter(
        field_name='age_group',
        choices=Product._meta.get_field('age_group').choices,
        label='Age Group'
    )
    
    # Size suitability filter
    size = django_filters.MultipleChoiceFilter(
        field_name='size_suitability',
        choices=Product._meta.get_field('size_suitability').choices,
        label='Size Suitability'
    )
    
    # APPEARANCE FILTERS (NEW - for frontend filtering)
    color = django_filters.CharFilter(
        field_name='color',
        lookup_expr='iexact',
        label='Color'
    )
    
    material = django_filters.CharFilter(
        field_name='material',
        lookup_expr='iexact',
        label='Material'
    )
    
    # FOOD SPECIFIC FILTERS
    food_type = django_filters.MultipleChoiceFilter(
        field_name='food_type',
        choices=[choice for choice in Product._meta.get_field('food_type').choices if choice[0]],
        label='Food Type'
    )
    
    # TOY SPECIFIC FILTERS
    toy_type = django_filters.MultipleChoiceFilter(
        field_name='toy_type',
        choices=[choice for choice in Product._meta.get_field('toy_type').choices if choice[0]],
        label='Toy Type'
    )
    
    # GROOMING SPECIFIC FILTERS
    grooming_type = django_filters.MultipleChoiceFilter(
        field_name='grooming_type',
        choices=[choice for choice in Product._meta.get_field('grooming_type').choices if choice[0]],
        label='Grooming Type'
    )
    
    # HEALTH SPECIFIC FILTERS
    health_type = django_filters.MultipleChoiceFilter(
        field_name='health_type',
        choices=[choice for choice in Product._meta.get_field('health_type').choices if choice[0]],
        label='Health Type'
    )
    
    # Price range filters
    min_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        label='Min Price'
    )
    max_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        label='Max Price'
    )
    price_range = django_filters.RangeFilter(
        field_name='price',
        label='Price Range'
    )
    
    # Rating filters
    min_rating = django_filters.NumberFilter(
        field_name='rating',
        lookup_expr='gte',
        label='Minimum Rating'
    )
    rating = django_filters.ChoiceFilter(
        field_name='rating',
        method='filter_rating_range',
        choices=[
            ('5', '5 Stars'),
            ('4', '4+ Stars'),
            ('3', '3+ Stars'),
            ('2', '2+ Stars'),
            ('1', '1+ Stars'),
        ],
        label='Rating'
    )
    
    # Tag filters
    tags = django_filters.CharFilter(
        method='filter_tags',
        label='Tags (comma-separated)'
    )
    has_tag = django_filters.CharFilter(
        method='filter_has_tag',
        label='Has Tag'
    )
    
    # Availability filters
    in_stock = django_filters.BooleanFilter(
        method='filter_in_stock',
        label='In Stock Only'
    )
    is_available = django_filters.BooleanFilter(
        field_name='is_available',
        label='Available'
    )
    
    # Special flags
    is_trending = django_filters.BooleanFilter(
        field_name='is_trending',
        label='Trending Only'
    )
    is_featured = django_filters.BooleanFilter(
        field_name='is_featured',
        label='Featured Only'
    )
    is_recommended = django_filters.BooleanFilter(
        field_name='is_recommended',
        label='Recommended'
    )
    
    # Sorting - SINGLE FIELD ONLY (No compound ordering)
    ordering = django_filters.OrderingFilter(
        fields=(
            ('price', 'price'),
            ('rating', 'rating'),
            ('review_count', 'reviews'),
            ('view_count', 'popularity'),
            ('created_at', 'newest'),
            ('name', 'name'),
            ('is_trending', 'trending'),
            ('is_featured', 'featured'),
        ),
        field_labels={
            'price': 'Price',
            '-price': 'Price (High to Low)',
            'rating': 'Rating (Low to High)',
            '-rating': 'Rating',
            'review_count': 'Reviews (Low to High)',
            '-review_count': 'Most Reviewed',
            'view_count': 'Popularity (Low to High)',
            '-view_count': 'Most Popular',
            'created_at': 'Oldest First',
            '-created_at': 'Newest',
            'name': 'Name (A-Z)',
            '-name': 'Name (Z-A)',
            'is_trending': 'Trending (Low to High)',
            '-is_trending': 'Trending',
            'is_featured': 'Featured (Low to High)',
            '-is_featured': 'Featured',
        }
    )
    
    class Meta:
        model = Product
        fields = []
    
    def filter_search(self, queryset, name, value):
        """
        Search across multiple fields
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(brand__name__icontains=value) |
            Q(category__name__icontains=value) |
            Q(tags__icontains=value)
        ).distinct()
    
    def filter_rating_range(self, queryset, name, value):
        """
        Filter by rating range (e.g., 4+ stars means >= 4.0)
        """
        if not value:
            return queryset
        
        try:
            min_rating = float(value)
            return queryset.filter(rating__gte=min_rating)
        except ValueError:
            return queryset
    
    def filter_tags(self, queryset, name, value):
        """
        Filter by multiple tags (comma-separated)
        Example: 'organic,grain-free,usa-made'
        """
        if not value:
            return queryset
        
        tags = [tag.strip() for tag in value.split(',')]
        query = Q()
        for tag in tags:
            query |= Q(tags__icontains=tag)
        
        return queryset.filter(query).distinct()
    
    def filter_has_tag(self, queryset, name, value):
        """
        Filter products that have a specific tag
        """
        if not value:
            return queryset
        
        return queryset.filter(tags__icontains=value)
    
    def filter_in_stock(self, queryset, name, value):
        """
        Filter for in-stock products
        """
        if value:
            return queryset.filter(stock__gt=0, is_available=True)
        return queryset


class AdvancedProductFilter:
    """
    Helper class for complex filtering logic
    Supports multiple filter combinations
    """
    
    @staticmethod
    def filter_by_user_preferences(queryset, user_preferences):
        """
        Filter products based on user preferences
        
        user_preferences example:
        {
            'species': 'cat',
            'favorite_categories': ['food', 'toys'],
            'price_range': [0, 50],
            'preferred_brands': ['Royal Canin', 'Hill's'],
            'dietary_preferences': ['grain-free', 'organic']
        }
        """
        if not user_preferences:
            return queryset
        
        # Filter by species
        if user_preferences.get('species'):
            queryset = queryset.filter(species=user_preferences['species'])
        
        # Filter by favorite categories
        if user_preferences.get('favorite_categories'):
            queryset = queryset.filter(
                category__category_type__in=user_preferences['favorite_categories']
            )
        
        # Filter by price range
        if user_preferences.get('price_range'):
            min_price, max_price = user_preferences['price_range']
            queryset = queryset.filter(price__gte=min_price, price__lte=max_price)
        
        # Filter by preferred brands
        if user_preferences.get('preferred_brands'):
            queryset = queryset.filter(brand__name__in=user_preferences['preferred_brands'])
        
        # Filter by dietary preferences (tags)
        if user_preferences.get('dietary_preferences'):
            for pref in user_preferences['dietary_preferences']:
                queryset = queryset.filter(tags__icontains=pref)
        
        return queryset.distinct()
    
    @staticmethod
    def get_complementary_products(product, limit=6):
        """
        Get products that complement the given product
        
        Example:
        - If user likes dry cat food → suggest wet cat food, cat treats, food bowls
        - If user likes cat toys → suggest more cat toys, catnip, cat treats
        """
        complementary = Product.objects.filter(
            species=product.species,
            is_available=True
        ).exclude(id=product.id)
        
        # Define complementary product logic
        if product.food_type == 'dry':
            # Suggest wet food, treats, bowls
            complementary = complementary.filter(
                Q(food_type='wet') |
                Q(category__category_type='treats') |
                Q(category__name__icontains='bowl')
            )
        
        elif product.food_type == 'wet':
            # Suggest dry food, treats
            complementary = complementary.filter(
                Q(food_type='dry') |
                Q(category__category_type='treats')
            )
        
        elif product.toy_type:
            # Suggest more toys and treats
            complementary = complementary.filter(
                Q(category__category_type='toys') |
                Q(category__category_type='treats')
            )
        
        elif product.grooming_type:
            # Suggest related grooming products
            complementary = complementary.filter(
                category__category_type='grooming'
            ).exclude(grooming_type=product.grooming_type)
        
        else:
            # Default: same category
            complementary = complementary.filter(category=product.category)
        
        return complementary.order_by('-rating', '-review_count')[:limit]