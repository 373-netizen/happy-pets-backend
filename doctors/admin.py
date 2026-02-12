# doctors/admin.py - FIXED

from django.contrib import admin
from .models import (
    DoctorProfile, DoctorAvailability, Consultation,
    ChatMessage, ConsultationNote, DoctorReview,
    FavoriteDoctor, QuickReply, DoctorEarnings
)


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'status', 'is_online', 'average_rating', 'total_consultations']
    list_filter = ['status', 'specialization', 'is_online', 'is_accepting_consultations']
    search_fields = ['user__email', 'user__username', 'license_number', 'bio']
    readonly_fields = ['average_rating', 'total_consultations', 'total_ratings', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'status', 'verified_at', 'verified_by', 'rejection_reason')
        }),
        ('Professional Info', {
            'fields': ('specialization', 'license_number', 'years_experience', 'bio')
        }),
        ('Documents', {
            'fields': ('license_photo', 'profile_photo')
        }),
        ('Contact', {
            'fields': ('phone', 'city', 'state', 'country')
        }),
        ('Pricing', {
            'fields': ('video_call_fee', 'chat_fee')
        }),
        ('Availability', {
            'fields': ('is_online', 'is_accepting_consultations')
        }),
        ('Statistics', {
            'fields': ('average_rating', 'total_consultations', 'total_ratings')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'day_of_week', 'start_time', 'end_time', 'is_active']
    list_filter = ['day_of_week', 'is_active']
    search_fields = ['doctor__user__email']


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['consultation_id', 'doctor', 'user', 'consultation_type', 'status', 'payment_status', 'amount', 'created_at']
    list_filter = ['consultation_type', 'status', 'payment_status', 'created_at']
    search_fields = ['consultation_id', 'user__email', 'doctor__user__email']
    readonly_fields = ['consultation_id', 'created_at', 'started_at', 'ended_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('consultation_id', 'doctor', 'user', 'pet', 'consultation_type')
        }),
        ('Status', {
            'fields': ('status', 'payment_status')
        }),
        ('Details', {
            'fields': ('chief_complaint', 'scheduled_at')
        }),
        ('Payment', {
            'fields': ('amount', 'stripe_payment_intent_id')
        }),
        ('Video Details', {
            'fields': ('video_room_url', 'video_room_name')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'ended_at', 'cancelled_at', 'cancellation_reason')
        })
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['consultation', 'sender', 'get_message_preview', 'has_image', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['message', 'sender__email', 'consultation__consultation_id']
    readonly_fields = ['created_at']  # FIXED: removed 'read_at'
    
    def get_message_preview(self, obj):
        if obj.message:
            return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
        return '[No text]'
    get_message_preview.short_description = 'Message'
    
    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Image'


@admin.register(ConsultationNote)
class ConsultationNoteAdmin(admin.ModelAdmin):
    list_display = ['consultation', 'doctor', 'follow_up_required', 'created_at']
    list_filter = ['follow_up_required', 'created_at']
    search_fields = ['consultation__consultation_id', 'doctor__user__email', 'diagnosis']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'user', 'rating', 'would_recommend', 'created_at']
    list_filter = ['rating', 'would_recommend', 'created_at']
    search_fields = ['doctor__user__email', 'user__email', 'review_text']
    readonly_fields = ['created_at']


@admin.register(FavoriteDoctor)
class FavoriteDoctorAdmin(admin.ModelAdmin):
    list_display = ['user', 'doctor', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'doctor__user__email']
    readonly_fields = ['created_at']


@admin.register(QuickReply)
class QuickReplyAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'title', 'created_at']
    list_filter = ['created_at']
    search_fields = ['doctor__user__email', 'title', 'message']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DoctorEarnings)
class DoctorEarningsAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'consultation', 'gross_amount', 'platform_fee', 'net_amount', 'paid_out', 'created_at']
    list_filter = ['paid_out', 'created_at']
    search_fields = ['doctor__user__email', 'consultation__consultation_id']
    readonly_fields = ['platform_fee', 'net_amount', 'created_at']
    
    fieldsets = (
        ('Consultation', {
            'fields': ('doctor', 'consultation')
        }),
        ('Financials', {
            'fields': ('gross_amount', 'platform_fee_percentage', 'platform_fee', 'net_amount')
        }),
        ('Payout', {
            'fields': ('paid_out', 'payout_date', 'payout_reference')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )