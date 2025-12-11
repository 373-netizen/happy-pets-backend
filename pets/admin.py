from django.contrib import admin
from .models import Pet, Appointment, Vaccination, HealthRecord

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ['name', 'species', 'breed', 'owner', 'is_active', 'created_at']
    list_filter = ['species', 'is_active', 'created_at']
    search_fields = ['name', 'breed', 'owner__username']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'pet', 'owner', 'date', 'time', 'type', 'status']
    list_filter = ['type', 'status', 'date']
    search_fields = ['title', 'pet__name', 'owner__username']

@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ['vaccine_name', 'pet', 'due_date', 'completed', 'is_overdue']
    list_filter = ['completed', 'due_date']
    search_fields = ['vaccine_name', 'pet__name']

@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ['title', 'pet', 'type', 'date', 'created_at']
    list_filter = ['type', 'date']
    search_fields = ['title', 'pet__name', 'diagnosis']
