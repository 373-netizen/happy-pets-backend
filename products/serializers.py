# products/serializers.py
from rest_framework import serializers
from django.db.models import Avg, Count, Q
from .models import Product, ProductCategory, Brand, ProductImage, SavedProduct, ProductView
from reviews.models import Review


class BrandSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = ['id', 'name', 'logo', 'description', 'website', 'product_count']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_available=True).count()


class ProductCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'slug', 'icon', 'description', 'parent', 'children', 'product_count']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_available=True).count()
    
    def get_children(self, obj):
        if obj.children.exists():
            return ProductCategorySerializer(obj.children.all(), many=True).data
        return []


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'order']


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists"""
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'slug', 'name', 'description', 'price', 'original_price',
            'discount_percentage', 'species', 'stock', 'is_available',
            'rating', 'review_count', 'is_trending', 'is_featured',
            'brand_name', 'category_name', 'tags', 'is_saved', 'primary_image',
            'platform_links'
        ]
    
    def get_discount_percentage(self, obj):
        if obj.original_price and obj.original_price > obj.price:
            return round(((obj.original_price - obj.price) / obj.original_price) * 100)
        return 0
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedProduct.objects.filter(user=request.user, product=obj).exists()
        return False
    
    def get_primary_image(self, obj):
        if obj.image_url:
            return obj.image_url
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        primary_img = obj.images.filter(is_primary=True).first()
        if primary_img:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_img.image.url)
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single product view"""
    brand = BrandSerializer(read_only=True)
    category = ProductCategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()
    rating_breakdown = serializers.SerializerMethodField()
    similar_products = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'slug', 'name', 'description', 'price', 'original_price',
            'discount_percentage', 'species', 'suitable_breeds', 'age_group',
            'image', 'image_url', 'images', 'stock', 'is_available',
            'platform_links', 'tags', 'rating', 'review_count', 
            'view_count', 'save_count', 'is_trending', 'is_featured',
            'brand', 'category', 'is_saved', 'recent_reviews',
            'rating_breakdown', 'similar_products', 'created_at', 'updated_at'
        ]
    
    def get_discount_percentage(self, obj):
        if obj.original_price and obj.original_price > obj.price:
            return round(((obj.original_price - obj.price) / obj.original_price) * 100)
        return 0
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedProduct.objects.filter(user=request.user, product=obj).exists()
        return False
    
    def get_recent_reviews(self, obj):
        from reviews.serializers import ReviewSerializer
        reviews = obj.reviews.filter(is_approved=True).select_related('user')[:5]
        return ReviewSerializer(reviews, many=True, context=self.context).data
    
    def get_rating_breakdown(self, obj):
        breakdown = obj.reviews.filter(is_approved=True).values('rating').annotate(
            count=Count('rating')
        ).order_by('-rating')
        
        result = {str(i): 0 for i in range(1, 6)}
        total = 0
        for item in breakdown:
            result[str(item['rating'])] = item['count']
            total += item['count']
        
        # Calculate percentages
        for rating in result:
            if total > 0:
                result[rating] = {
                    'count': result[rating],
                    'percentage': round((result[rating] / total) * 100, 1)
                }
            else:
                result[rating] = {'count': 0, 'percentage': 0}
        
        return result
    
    def get_similar_products(self, obj):
        similar = Product.objects.filter(
            Q(category=obj.category) | Q(species=obj.species),
            is_available=True
        ).exclude(id=obj.id).order_by('-rating')[:6]
        
        return ProductListSerializer(similar, many=True, context=self.context).data


class SavedProductSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = SavedProduct
        fields = ['id', 'product', 'notes', 'created_at']


class SavedProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedProduct
        fields = ['product', 'notes']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# For bulk operations
class ProductBulkSerializer(serializers.Serializer):
    products = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    action = serializers.ChoiceField(choices=['save', 'unsave'])