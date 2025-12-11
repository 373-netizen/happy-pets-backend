# pets/models.py

from django.db import models
from django.conf import settings
from datetime import date
from django.utils import timezone


class Pet(models.Model):
    SPECIES_CHOICES = [
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('bird', 'Bird'),
        ('other', 'Other'),
    ]
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('unknown', 'Unknown'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_pets'
    )
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=20, choices=SPECIES_CHOICES, default='dog')
    breed = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unknown')
    color = models.CharField(max_length=100, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    photo = models.ImageField(upload_to='pet_photos/', null=True, blank=True)
    microchip_number = models.CharField(max_length=50, blank=True)
    medical_notes = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    is_available_for_breeding = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    


    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.species})"

    @property
    def age(self):
        if not self.date_of_birth:
            return "Unknown"
        today = date.today()
        months = (today.year - self.date_of_birth.year) * 12 + (today.month - self.date_of_birth.month)
        years = months // 12
        remaining_months = months % 12
        if years == 0:
            return f"{remaining_months} month{'s' if remaining_months != 1 else ''}"
        elif remaining_months == 0:
            return f"{years} year{'s' if years != 1 else ''}"
        else:
            return f"{years}y {remaining_months}m"


class Appointment(models.Model):
    APPOINTMENT_TYPES = [
        ('medical', 'Medical'),
        ('grooming', 'Grooming'),
        ('training', 'Training'),
        ('checkup', 'Checkup'),
        ('vaccination', 'Vaccination'),
        ('surgery', 'Surgery'),
        ('emergency', 'Emergency'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('missed', 'Missed'),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='appointments')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=APPOINTMENT_TYPES, default='checkup')
    date = models.DateField()
    time = models.TimeField()
    duration = models.IntegerField(default=30)
    location = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    veterinarian_name = models.CharField(max_length=100, blank=True)
    clinic_phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f"{self.title} - {self.pet.name} on {self.date}"

    @property
    def is_upcoming(self):
        from datetime import datetime
        appointment_datetime = datetime.combine(self.date, self.time)
        return appointment_datetime > datetime.now() and self.status == 'scheduled'


class Vaccination(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='vaccinations')
    vaccine_name = models.CharField(max_length=200)
    vaccine_type = models.CharField(max_length=100, blank=True)
    due_date = models.DateField()
    administered_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    veterinarian_name = models.CharField(max_length=100, blank=True)
    clinic_name = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.vaccine_name} for {self.pet.name}"

    @property
    def is_overdue(self):
        return date.today() > self.due_date and not self.completed

    @property
    def days_until_due(self):
        return (self.due_date - date.today()).days


class Reminder(models.Model):
    REMINDER_TYPES = [
        ('medication', 'Medication'),
        ('feeding', 'Feeding'),
        ('exercise', 'Exercise'),
        ('grooming', 'Grooming'),
        ('appointment', 'Appointment'),
        ('vaccination', 'Vaccination'),
        ('general', 'General'),
    ]
    FREQUENCY_CHOICES = [
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='reminders', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=REMINDER_TYPES, default='general')
    remind_at = models.DateTimeField()
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    recurring = models.BooleanField(default=False)
    recurring_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['remind_at']

    def __str__(self):
        return f"{self.title} - {self.remind_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def is_overdue(self):
        return timezone.now() > self.remind_at and not self.completed

    def mark_as_completed(self):
        self.completed = True
        self.completed_at = timezone.now()
        self.save()


class HealthRecord(models.Model):
    RECORD_TYPES = [
        ('checkup', 'Regular Checkup'),
        ('surgery', 'Surgery'),
        ('illness', 'Illness'),
        ('injury', 'Injury'),
        ('test', 'Test Result'),
        ('dental', 'Dental'),
        ('other', 'Other'),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='health_records')
    type = models.CharField(max_length=20, choices=RECORD_TYPES, default='checkup')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    veterinarian_name = models.CharField(max_length=100, blank=True)
    clinic_name = models.CharField(max_length=200, blank=True)
    diagnosis = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.title} - {self.pet.name} on {self.date}"
