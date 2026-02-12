# doctors/models.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import uuid
from decimal import Decimal  # ADD THIS IMPORT

class DoctorProfile(models.Model):
    """Veterinary doctor profile"""
    
    SPECIALIZATION_CHOICES = [
        ('general', 'General Veterinary Practice'),
        ('surgery', 'Veterinary Surgery'),
        ('internal_medicine', 'Internal Medicine'),
        ('dermatology', 'Veterinary Dermatology'),
        ('cardiology', 'Veterinary Cardiology'),
        ('oncology', 'Veterinary Oncology'),
        ('orthopedics', 'Orthopedic Surgery'),
        ('dentistry', 'Veterinary Dentistry'),
        ('emergency', 'Emergency & Critical Care'),
        ('exotic', 'Exotic Animals'),
        ('avian', 'Avian Medicine'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended')
    ]
    
    # User Reference
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='doctor_profile'
    )
    
    # Professional Information
    specialization = models.CharField(max_length=100, choices=SPECIALIZATION_CHOICES)
    license_number = models.CharField(max_length=50, unique=True)
    years_experience = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(50)])
    bio = models.TextField(help_text="Tell pet owners about yourself")
    
    # Verification Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_doctors'
    )
    rejection_reason = models.TextField(blank=True)
    
    # Documents
    license_photo = models.ImageField(upload_to='doctor_licenses/')
    profile_photo = models.ImageField(upload_to='doctor_photos/')
    
    # Contact Information
    phone = models.CharField(max_length=15)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='USA')
    
    # Pricing (in USD)
    video_call_fee = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0.00,
    blank=True,
    null=True
)

    chat_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Fee for chat consultation"
    )
    
    # Availability
    is_online = models.BooleanField(default=False)
    is_accepting_consultations = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    # Statistics
    total_consultations = models.IntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_ratings = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-average_rating', '-total_consultations']
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.get_specialization_display()}"
    
    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
    
    def update_rating(self):
        """Update average rating from all reviews"""
        ratings = self.reviews.all()
        if ratings.exists():
            self.total_ratings = ratings.count()
            self.average_rating = sum(r.rating for r in ratings) / self.total_ratings
            self.save(update_fields=['average_rating', 'total_ratings'])


class DoctorAvailability(models.Model):
    """Doctor's weekly availability schedule"""
    
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday')
    ]
    
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = ['doctor', 'day_of_week', 'start_time']
        verbose_name_plural = 'Doctor Availabilities'
    
    def __str__(self):
        return f"{self.doctor.full_name} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class Consultation(models.Model):
    """Consultation session (chat or video)"""
    
    TYPE_CHOICES = [
        ('chat', 'Chat Consultation'),
        ('video', 'Video Call')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid - Awaiting Start'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded')
    ]
    
    # Unique identifier
    consultation_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Participants
    doctor = models.ForeignKey(
        DoctorProfile, 
        on_delete=models.CASCADE, 
        related_name='consultations'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='consultations'
    )
    pet = models.ForeignKey(
        'pets.Pet', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='consultations'
    )
    
    # Consultation Details
    consultation_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Chief Complaint
    chief_complaint = models.TextField(help_text="What brings you here today?")
    
    # Scheduling (for video calls)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    
    # Payment
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    
    # Video Call Details
    video_room_url = models.CharField(max_length=500, blank=True)
    video_room_name = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.consultation_type.title()} - {self.user.username} with Dr. {self.doctor.full_name}"
    
    @property
    def duration_minutes(self):
        """Calculate consultation duration"""
        if self.started_at and self.ended_at:
            duration = self.ended_at - self.started_at
            return int(duration.total_seconds() / 60)
        return 0


class ChatMessage(models.Model):
    """Chat messages within a consultation"""
    
    consultation = models.ForeignKey(
        Consultation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    
    # Message Content
    message = models.TextField(blank=True)
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    
    # Read Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username}: {self.message[:50]}"


class ConsultationNote(models.Model):
    """Doctor's private notes for consultation"""
    
    consultation = models.OneToOneField(
        Consultation, 
        on_delete=models.CASCADE, 
        related_name='doctor_note'
    )
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)
    
    # Medical Notes
    diagnosis = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    prescriptions = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notes for {self.consultation}"


class DoctorReview(models.Model):
    """User reviews for doctors"""
    
    doctor = models.ForeignKey(
        DoctorProfile, 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    consultation = models.OneToOneField(
        Consultation, 
        on_delete=models.CASCADE, 
        related_name='review'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    
    # Rating
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1-5 stars"
    )
    
    # Optional Review Text
    review_text = models.TextField(blank=True)
    
    # Would Recommend
    would_recommend = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['doctor', 'consultation', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rating}★ review for Dr. {self.doctor.full_name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update doctor's average rating
        self.doctor.update_rating()


class FavoriteDoctor(models.Model):
    """User's favorite doctors"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='favorite_doctors'
    )
    doctor = models.ForeignKey(
        DoctorProfile, 
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'doctor']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} ❤️ Dr. {self.doctor.full_name}"


class QuickReply(models.Model):
    """Doctor's saved message templates"""
    
    doctor = models.ForeignKey(
        DoctorProfile, 
        on_delete=models.CASCADE,
        related_name='quick_replies'
    )
    title = models.CharField(max_length=100, help_text="Short title for this template")
    message = models.TextField(help_text="Template message")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Quick Replies'
        ordering = ['title']
    
    def __str__(self):
        return f"{self.doctor.full_name}: {self.title}"


class DoctorEarnings(models.Model):
    """Track doctor earnings per consultation"""
    
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='earnings')
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE)
    
    # Financial Details
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=20.00,
        help_text="Platform commission percentage"
    )
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        help_text="Amount paid to doctor"
    )
    
    # Payout Status
    paid_out = models.BooleanField(default=False)
    payout_date = models.DateField(null=True, blank=True)
    payout_reference = models.CharField(max_length=200, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Doctor Earnings'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"${self.net_amount} for Dr. {self.doctor.full_name}"
    
    def save(self, *args, **kwargs):
        """Calculate platform fee and net amount - FIXED"""
        if self.gross_amount:
            # Convert to Decimal to avoid type errors
            fee_percentage = Decimal(str(self.platform_fee_percentage))
            self.platform_fee = (self.gross_amount * fee_percentage) / Decimal('100')
            self.net_amount = self.gross_amount - self.platform_fee
        super().save(*args, **kwargs)