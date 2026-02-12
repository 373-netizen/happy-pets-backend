# services/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import PetService, UserServiceReview, UserServiceFavorite, ServiceAppointment


@admin.register(PetService)
class PetServiceAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'category_badge',
        'google_rating_display',
        'total_ratings',
        'is_open_now',
        'times_viewed',
        'view_on_map'
    ]
    
    list_filter = [
        'category',
        'is_open_now',
        'business_status',
    ]
    
    search_fields = [
        'name',
        'address',
        'place_id'
    ]
    
    readonly_fields = [
        'place_id',
        'google_rating',
        'total_ratings',
        'times_viewed',
        'created_at',
        'last_updated'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('place_id', 'name', 'category')
        }),
        ('Location', {
            'fields': ('address', 'latitude', 'longitude')
        }),
        ('Contact', {
            'fields': ('phone_number', 'website')
        }),
        ('Ratings & Reviews', {
            'fields': ('google_rating', 'total_ratings')
        }),
        ('Business Details', {
            'fields': ('is_open_now', 'business_status', 'price_level')
        }),
        ('Statistics', {
            'fields': ('times_viewed', 'created_at', 'last_updated')
        })
    )
    
    def category_badge(self, obj):
        colors = {
            'vet': '#ef4444',
            'grooming': '#3b82f6',
            'spa': '#8b5cf6'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-weight: 600; font-size: 0.8125rem;">{}</span>',
            colors.get(obj.category, '#6b7280'),
            obj.get_category_display()
        )
    category_badge.short_description = 'Category'
    
    def google_rating_display(self, obj):
        if obj.google_rating:
            stars = '⭐' * int(obj.google_rating)
            return format_html(
                '<span style="color: #fbbf24; font-weight: 600;">{} {}</span>',
                stars,
                obj.google_rating
            )
        return '-'
    google_rating_display.short_description = 'Rating'
    google_rating_display.admin_order_field = 'google_rating'
    
    def view_on_map(self, obj):
        return format_html(
            '<a href="https://www.google.com/maps/search/?api=1&query={},{}" '
            'target="_blank" style="color: #3b82f6; font-weight: 600;">📍 Map</a>',
            obj.latitude,
            obj.longitude
        )
    view_on_map.short_description = 'Map'


@admin.register(UserServiceReview)
class UserServiceReviewAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'service',
        'rating_display',
        'created_at'
    ]
    
    list_filter = [
        'rating',
        'created_at'
    ]
    
    search_fields = [
        'user__username',
        'service__name',
        'review_text'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    def rating_display(self, obj):
        stars = '⭐' * obj.rating
        return format_html(
            '<span style="color: #fbbf24; font-weight: 600;">{}</span>', 
            stars
        )
    rating_display.short_description = 'Rating'
    rating_display.admin_order_field = 'rating'


@admin.register(UserServiceFavorite)
class UserServiceFavoriteAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'service', 
        'service_category',
        'created_at'
    ]
    
    list_filter = [
        'service__category', 
        'created_at'
    ]
    
    search_fields = [
        'user__username', 
        'service__name'
    ]
    
    readonly_fields = ['created_at']
    
    def service_category(self, obj):
        colors = {
            'vet': '#ef4444',
            'grooming': '#3b82f6',
            'spa': '#8b5cf6'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; '
            'border-radius: 8px; font-size: 0.75rem; font-weight: 600;">{}</span>',
            colors.get(obj.service.category, '#6b7280'),
            obj.service.get_category_display()
        )
    service_category.short_description = 'Category'


@admin.register(ServiceAppointment)
class ServiceAppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'service',
        'appointment_date',
        'status_badge',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'appointment_date',
        'service__category'
    ]
    
    search_fields = [
        'user__username',
        'service__name',
        'notes'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        ('Appointment Details', {
            'fields': ('user', 'service', 'appointment_date', 'status')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'confirmed': '#3b82f6',
            'completed': '#10b981',
            'cancelled': '#ef4444'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-weight: 600; font-size: 0.8125rem;">{}</span>',
            colors.get(obj.status, '#6b7280'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'