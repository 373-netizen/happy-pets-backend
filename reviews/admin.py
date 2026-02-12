from django.contrib import admin
from .models import Review, ReviewHelpful, ReviewImage


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 1


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'user', 'rating', 'is_verified_purchase',
        'is_approved', 'helpful_count', 'created_at'
    ]
    list_filter = [
        'rating', 'is_verified_purchase', 'is_approved', 'created_at'
    ]
    search_fields = ['product__name', 'user__username', 'title', 'comment']
    readonly_fields = ['helpful_count', 'created_at', 'updated_at']
    inlines = [ReviewImageInline]
    date_hierarchy = 'created_at'
    
    actions = ['approve_reviews', 'disapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = 'Approve selected reviews'
    
    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_reviews.short_description = 'Disapprove selected reviews'


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    list_display = ['review', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['review__product__name', 'user__username']
    date_hierarchy = 'created_at'












