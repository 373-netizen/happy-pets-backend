from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # Show avatar preview in admin list
    list_display = ('email', 'username', 'is_staff', 'is_active', 'avatar_tag')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'groups')

    # Fields in detail view
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'location', 'address', 'avatar', 'latitude', 'longitude')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'password1', 'password2',
                'first_name', 'last_name', 'address', 'avatar',
                'is_staff', 'is_active', 'is_superuser', 'groups'
            ),
        }),
    )

    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    def avatar_tag(self, obj):
        """Display avatar image in admin list"""
        if obj.avatar:
            return format_html(
                '<img src="{}" width="50" style="border-radius:50%;" />',
                obj.avatar.url
            )
        return "-"
    avatar_tag.short_description = 'Avatar'
