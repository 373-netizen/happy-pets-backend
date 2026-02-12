# adoption/models.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify

class Shelter(models.Model):
    """Shelter model - users can register their own shelters"""
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shelters')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default='USA')
    
    # Location coordinates for mapping
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='shelters/logos/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='shelters/covers/', blank=True, null=True)
    
    # Shelter details
    established_year = models.PositiveIntegerField(null=True, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    non_profit = models.BooleanField(default=True)
    registration_number = models.CharField(max_length=100, blank=True)
    
    # Status and verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')  # CHANGED: default='approved'
    verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['city', 'state']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness
            counter = 1
            original_slug = self.slug
            while Shelter.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    @property
    def full_address(self):
        return f"{self.address}, {self.city}, {self.state} {self.zip_code}"
    
    @property
    def total_pets(self):
        return self.pets.count()
    
    @property
    def available_pets(self):
        return self.pets.filter(status='available').count()


class AdoptablePet(models.Model):
    """Pets available for adoption"""
    SPECIES_CHOICES = [
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('bird', 'Bird'),
        ('rabbit', 'Rabbit'),
        ('hamster', 'Hamster'),
        ('guinea_pig', 'Guinea Pig'),
        ('other', 'Other'),
    ]
    
    SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('pending', 'Pending Adoption'),
        ('adopted', 'Adopted'),
        ('fostered', 'In Foster Care'),
        ('medical_hold', 'Medical Hold'),
        ('unavailable', 'Unavailable'),
    ]
    
    ACTIVITY_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    ]
    
    # Basic Information
    shelter = models.ForeignKey(Shelter, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=20, choices=SPECIES_CHOICES)
    breed = models.CharField(max_length=100)
    mixed_breed = models.BooleanField(default=False)
    
    # Physical Characteristics
    age = models.PositiveIntegerField(help_text="Age in months")
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    color = models.CharField(max_length=100)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Weight in lbs")
    
    # Medical & Health
    spayed_neutered = models.BooleanField(default=False)
    vaccinated = models.BooleanField(default=False)
    microchipped = models.BooleanField(default=False)
    house_trained = models.BooleanField(default=False)
    special_needs = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    
    # Behavior & Compatibility
    good_with_kids = models.BooleanField(default=False)
    good_with_dogs = models.BooleanField(default=False)
    good_with_cats = models.BooleanField(default=False)
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_LEVEL_CHOICES, default='medium')
    
    # Descriptions
    description = models.TextField()
    personality_traits = models.JSONField(default=list, blank=True)  # e.g., ["Friendly", "Playful", "Calm"]
    
    # Media
    primary_image = models.ImageField(upload_to='adoptable_pets/')
    image_2 = models.ImageField(upload_to='adoptable_pets/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='adoptable_pets/', blank=True, null=True)
    image_4 = models.ImageField(upload_to='adoptable_pets/', blank=True, null=True)
    video_url = models.URLField(blank=True)
    
    # Status & Availability
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    adoption_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    date_available = models.DateField(auto_now_add=True)
    date_adopted = models.DateField(null=True, blank=True)
    
    # Metadata
    views = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)
    urgent = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-featured', '-urgent', '-created_at']
        indexes = [
            models.Index(fields=['species', 'status']),
            models.Index(fields=['shelter', 'status']),
            models.Index(fields=['-featured', '-created_at']),
        ]
        verbose_name = 'Adoptable Pet'
        verbose_name_plural = 'Adoptable Pets'
    
    def __str__(self):
        return f"{self.name} - {self.breed}"
    
    @property
    def age_display(self):
        """Convert age in months to human-readable format"""
        years = self.age // 12
        months = self.age % 12
        
        if years == 0:
            return f"{months} month{'s' if months != 1 else ''}"
        elif months == 0:
            return f"{years} year{'s' if years != 1 else ''}"
        else:
            return f"{years} year{'s' if years != 1 else ''}, {months} month{'s' if months != 1 else ''}"
    
    @property
    def all_images(self):
        """Get all available images"""
        images = [self.primary_image.url] if self.primary_image else []
        for img in [self.image_2, self.image_3, self.image_4]:
            if img:
                images.append(img.url)
        return images
    
    @property
    def good_with(self):
        """Return list of what pet is good with"""
        good_with_list = []
        if self.good_with_kids:
            good_with_list.append('children')
        if self.good_with_dogs:
            good_with_list.append('dogs')
        if self.good_with_cats:
            good_with_list.append('cats')
        return good_with_list


class AdoptionApplication(models.Model):
    """Application to adopt a pet"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    HOUSING_CHOICES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('condo', 'Condo'),
        ('other', 'Other'),
    ]
    
    # Application Details
    pet = models.ForeignKey(AdoptablePet, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='adoption_applications')
    status = models.CharField(
    max_length=20,
    choices=STATUS_CHOICES,
    default='pending'
)

    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    
    # Housing Information
    housing_type = models.CharField(max_length=20, choices=HOUSING_CHOICES)
    own_or_rent = models.CharField(max_length=10, choices=[('own', 'Own'), ('rent', 'Rent')])
    landlord_approval = models.BooleanField(default=False)
    yard_fenced = models.BooleanField(default=False)
    
    # Household Information
    household_adults = models.PositiveIntegerField(default=1)
    household_children = models.PositiveIntegerField(default=0)
    children_ages = models.CharField(max_length=100, blank=True)
    current_pets = models.TextField(blank=True, help_text="Describe current pets")
    
    # Experience & Care
    pet_experience = models.TextField(help_text="Describe your experience with pets")
    veterinarian_name = models.CharField(max_length=200, blank=True)
    veterinarian_phone = models.CharField(max_length=20, blank=True)
    
    # References
    reference_1_name = models.CharField(max_length=200)
    reference_1_phone = models.CharField(max_length=20)
    reference_1_relationship = models.CharField(max_length=100)
    reference_2_name = models.CharField(max_length=200, blank=True)
    reference_2_phone = models.CharField(max_length=20, blank=True)
    reference_2_relationship = models.CharField(max_length=100, blank=True)
    
    # Additional Information
    why_adopt = models.TextField(help_text="Why do you want to adopt this pet?")
    daily_schedule = models.TextField(help_text="Describe the pet's daily schedule")
    emergency_plan = models.TextField(blank=True)
    additional_notes = models.TextField(blank=True)
    
    # Admin Notes
    admin_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['pet', 'applicant', 'status']
    
    def __str__(self):
        return f"Application: {self.first_name} {self.last_name} - {self.pet.name}"


class Favorite(models.Model):
    """User's favorite pets"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_pets')
    pet = models.ForeignKey(AdoptablePet, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'pet']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.pet.name}"