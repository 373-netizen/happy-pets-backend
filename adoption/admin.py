from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import Shelter, AdoptablePet, AdoptionApplication, Favorite


# =========================
# Shelter Admin
# =========================
@admin.register(Shelter)
class ShelterAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'owner_username', 'city', 'state',
        'status_badge', 'total_pets_count',
        'verified', 'created_at'
    ]
    list_filter = [
        'status', 'verified', 'is_active', 'non_profit',
        'state', 'created_at'
    ]
    search_fields = [
        'name', 'owner__username', 'email',
        'city', 'registration_number'
    ]
    readonly_fields = [
        'slug', 'created_at', 'updated_at',
        'total_pets_display', 'available_pets_display'
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'name', 'slug', 'email', 'phone', 'description')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'zip_code', 'country', 'latitude', 'longitude')
        }),
        ('Media', {
            'fields': ('logo', 'cover_image', 'website')
        }),
        ('Details', {
            'fields': ('established_year', 'capacity', 'non_profit', 'registration_number')
        }),
        ('Status & Verification', {
            'fields': ('status', 'verified', 'is_active', 'approved_at')
        }),
        ('Statistics', {
            'fields': ('total_pets_display', 'available_pets_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_shelters', 'reject_shelters', 'verify_shelters']

    def owner_username(self, obj):
        return obj.owner.username
    owner_username.short_description = 'Owner'

    def status_badge(self, obj):
        colors = {
            'approved': '#10b981',
            'pending': '#f59e0b',
            'rejected': '#ef4444',
            'suspended': '#6b7280'
        }
        return format_html(
            '<span style="background:{};color:white;padding:5px 12px;'
            'border-radius:12px;font-weight:600;font-size:11px;">{}</span>',
            colors.get(obj.status, '#6b7280'),
            obj.get_status_display().upper()
        )
    status_badge.short_description = 'Status'

    def total_pets_count(self, obj):
        return obj.total_pets
    total_pets_count.short_description = 'Total Pets'

    def total_pets_display(self, obj):
        return obj.total_pets
    total_pets_display.short_description = 'Total Pets'

    def available_pets_display(self, obj):
        return obj.available_pets
    available_pets_display.short_description = 'Available Pets'

    def approve_shelters(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='approved', approved_at=timezone.now())
        self.message_user(request, f'{updated} shelter(s) approved.')

    def reject_shelters(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} shelter(s) rejected.')

    def verify_shelters(self, request, queryset):
        updated = queryset.update(verified=True)
        self.message_user(request, f'{updated} shelter(s) verified.')


# =========================
# Adoptable Pet Admin
# =========================
@admin.register(AdoptablePet)
class AdoptablePetAdmin(admin.ModelAdmin):

    list_display = [
        'name', 'species', 'breed', 'shelter_name',
        'status_badge', 'age_display_admin',
        'gender', 'featured', 'urgent',
        'views', 'created_at'
    ]
    list_filter = [
        'species', 'status', 'size', 'gender',
        'featured', 'urgent', 'spayed_neutered',
        'vaccinated', 'good_with_kids',
        'good_with_dogs', 'good_with_cats',
        'created_at'
    ]
    search_fields = ['name', 'breed', 'shelter__name', 'color']
    readonly_fields = ['created_at', 'updated_at', 'views', 'all_images_display']

    fieldsets = (
        ('Basic Information', {
            'fields': ('shelter', 'name', 'species', 'breed', 'mixed_breed', 'description')
        }),
        ('Physical Characteristics', {
            'fields': ('age', 'size', 'gender', 'color', 'weight')
        }),
        ('Medical & Health', {
            'fields': (
                'spayed_neutered', 'vaccinated', 'microchipped',
                'house_trained', 'special_needs', 'medical_history'
            )
        }),
        ('Behavior & Compatibility', {
            'fields': (
                'good_with_kids', 'good_with_dogs',
                'good_with_cats', 'activity_level',
                'personality_traits'
            )
        }),
        ('Media', {
            'fields': (
                'primary_image', 'image_2', 'image_3',
                'image_4', 'video_url', 'all_images_display'
            )
        }),
        ('Availability & Pricing', {
            'fields': ('status', 'adoption_fee', 'date_adopted')
        }),
        ('Featured & Metadata', {
            'fields': ('featured', 'urgent', 'is_active', 'views')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'mark_as_available', 'mark_as_adopted',
        'mark_as_featured', 'unmark_featured'
    ]

    def shelter_name(self, obj):
        return obj.shelter.name
    shelter_name.short_description = 'Shelter'

    def status_badge(self, obj):
        colors = {
            'available': '#10b981',
            'pending': '#f59e0b',
            'adopted': '#3b82f6',
            'fostered': '#8b5cf6',
            'medical_hold': '#ef4444',
            'unavailable': '#6b7280'
        }
        return format_html(
            '<span style="background:{};color:white;padding:5px 12px;'
            'border-radius:12px;font-weight:600;font-size:11px;">{}</span>',
            colors.get(obj.status, '#6b7280'),
            obj.get_status_display().upper()
        )
    status_badge.short_description = 'Status'

    def age_display_admin(self, obj):
        return obj.age_display
    age_display_admin.short_description = 'Age'

    def all_images_display(self, obj):
        images_html = ''
        for img_url in obj.all_images:
            images_html += (
                f'<img src="{img_url}" '
                f'style="width:150px;height:150px;'
                f'object-fit:cover;margin:5px;border-radius:8px;" />'
            )
        return mark_safe(images_html) if images_html else 'No images'
    all_images_display.short_description = 'All Images'

    def mark_as_available(self, request, queryset):
        updated = queryset.update(status='available')
        self.message_user(request, f'{updated} pet(s) marked available.')

    def mark_as_adopted(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            status='adopted',
            date_adopted=timezone.now().date()
        )
        self.message_user(request, f'{updated} pet(s) adopted.')

    def mark_as_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} pet(s) featured.')

    def unmark_featured(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f'{updated} pet(s) unfeatured.')


# =========================
# Adoption Application Admin
# =========================
@admin.register(AdoptionApplication)
class AdoptionApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'applicant_name', 'pet_name',
        'status_badge', 'email',
        'phone', 'submitted_at'
    ]
    list_filter = [
        'status', 'housing_type',
        'own_or_rent', 'submitted_at'
    ]
    search_fields = [
        'first_name', 'last_name',
        'email', 'phone', 'pet__name'
    ]
    readonly_fields = ['submitted_at', 'updated_at']

    def applicant_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def pet_name(self, obj):
        return obj.pet.name

    def status_badge(self, obj):
        colors = {
            'submitted': '#f59e0b',
            'under_review': '#3b82f6',
            'approved': '#10b981',
            'rejected': '#ef4444',
            'withdrawn': '#6b7280'
        }
        return format_html(
            '<span style="background:{};color:white;padding:5px 12px;'
            'border-radius:12px;font-weight:600;font-size:11px;">{}</span>',
            colors.get(obj.status, '#6b7280'),
            obj.get_status_display().upper()
        )


# =========================
# Favorite Admin
# =========================
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'pet', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'pet__name']
    readonly_fields = ['created_at']
