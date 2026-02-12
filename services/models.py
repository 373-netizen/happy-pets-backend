# services/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class ServiceCategory(models.TextChoices):
    """Categories for pet services"""
    VET = 'vet', 'Veterinary Hospital'
    GROOMING = 'grooming', 'Grooming Station'
    SPA = 'spa', 'Pet Spa'


class PetService(models.Model):
    """Store nearby pet services (vets, grooming, spas)"""
    
    # Google Places data
    place_id = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=ServiceCategory.choices)
    
    # Location
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    # Contact
    phone_number = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    # Rating & Reviews
    google_rating = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_ratings = models.IntegerField(default=0)
    
    # Additional info
    photo_reference = models.TextField(blank=True)
    opening_hours = models.JSONField(default=dict, blank=True)
    price_level = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(4)]
    )
    
    # Business details
    is_open_now = models.BooleanField(default=False)
    business_status = models.CharField(max_length=50, default='OPERATIONAL')
    
    # Cache management
    last_updated = models.DateTimeField(auto_now=True)
    times_viewed = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'pet_services'
        ordering = ['-google_rating', '-total_ratings']
        indexes = [
            models.Index(fields=['category', '-google_rating']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class UserServiceReview(models.Model):
    """User reviews for pet services"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='service_reviews'
    )
    service = models.ForeignKey(
        PetService, 
        on_delete=models.CASCADE, 
        related_name='user_reviews'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review_text = models.TextField(blank=True)
    photos = models.JSONField(default=list, blank=True)
    visit_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    helpful_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'user_service_reviews'
        unique_together = ('user', 'service')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.service.name} ({self.rating}★)"


class UserServiceFavorite(models.Model):
    """User's favorite pet services"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='favorite_services'
    )
    service = models.ForeignKey(
        PetService, 
        on_delete=models.CASCADE, 
        related_name='favorited_by'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_service_favorites'
        unique_together = ('user', 'service')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} → {self.service.name}"


class ServiceAppointment(models.Model):
    """Track appointments at pet services"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_appointments'
    )
    service = models.ForeignKey(
        PetService,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    appointment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_appointments'
        ordering = ['-appointment_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.service.name} on {self.appointment_date}"