from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductCategory, Brand, ProductImage, SavedProduct, ProductView


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'parent', 'product_count']
    list_filter = ['parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'website', 'product_count']
    search_fields = ['name', 'description']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'brand', 'species', 'price',
        'stock', 'rating_display', 'is_trending', 'is_featured',
        'view_count', 'save_count', 'created_at'
    ]
    list_filter = [
        'species', 'category', 'brand', 'is_trending',
        'is_featured', 'is_available', 'created_at'
    ]
    search_fields = ['name', 'description', 'tags']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['view_count', 'save_count', 'rating', 'review_count', 'created_at', 'updated_at']
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category', 'brand')
        }),
        ('Pricing', {
            'fields': ('price', 'original_price')
        }),
        ('Pet Information', {
            'fields': ('species', 'suitable_breeds', 'age_group')
        }),
        ('Media', {
            'fields': ('image', 'image_url')
        }),
        ('Inventory', {
            'fields': ('stock', 'is_available')
        }),
        ('Platform Links', {
            'fields': ('platform_links',)
        }),
        ('SEO & Discovery', {
            'fields': ('tags',)
        }),
        ('Statistics', {
            'fields': ('rating', 'review_count', 'view_count', 'save_count'),
            'classes': ('collapse',)
        }),
        ('Flags', {
            'fields': ('is_trending', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def rating_display(self, obj):
        if obj.rating > 0:
            stars = '⭐' * int(obj.rating)
            return format_html(
                '<span title="{} ({} reviews)">{} {}</span>',
                obj.rating,
                obj.review_count,
                stars,
                obj.rating
            )
        return '-'
    rating_display.short_description = 'Rating'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on new products
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SavedProduct)
class SavedProductAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']
    date_hierarchy = 'created_at'


@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'session_id', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__name', 'user__username', 'session_id']
    date_hierarchy = 'created_at'
    readonly_fields = ['product', 'user', 'session_id', 'created_at']
