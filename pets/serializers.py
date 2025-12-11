from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Pet, Appointment, Vaccination, HealthRecord, Reminder

User = get_user_model()


class PetSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    photo = serializers.ImageField(required=False, allow_null=True)
    health_records = serializers.SerializerMethodField()

    class Meta:
        model = Pet
        fields = [
            'id', 'name', 'species', 'breed', 'date_of_birth', 'age',
            'gender', 'color', 'weight', 'photo', 'microchip_number',
            'medical_notes', 'allergies', 'current_medications',
            'is_available_for_breeding', 'is_active', 'owner_name',
            'created_at', 'updated_at', 'health_records'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner_name', 'health_records']

    def get_health_records(self, obj):
        # Include latest health records for the pet
        records = obj.health_records.order_by('-date')[:5]

        return HealthRecordSerializer(records, many=True).data

    def create(self, validated_data):
        user = self.context['request'].user
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("You must be logged in to add a pet.")
        validated_data['owner'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if instance.owner != user:
            raise serializers.ValidationError("You can only update your own pets.")
        return super().update(instance, validated_data)


class AppointmentSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    is_upcoming = serializers.ReadOnlyField()

    class Meta:
        model = Appointment
        fields = [
            'id', 'pet', 'pet_name', 'title', 'type', 'date', 'time',
            'duration', 'location', 'address', 'veterinarian_name',
            'clinic_phone', 'notes', 'status', 'is_upcoming',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_pet(self, value):
        user = self.context['request'].user
        if value.owner != user:
            raise serializers.ValidationError("You can only create appointments for your own pets.")
        return value


class VaccinationSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    days_until_due = serializers.ReadOnlyField()

    class Meta:
        model = Vaccination
        fields = [
            'id', 'pet', 'pet_name', 'vaccine_name', 'vaccine_type',
            'due_date', 'administered_date', 'next_due_date', 'completed',
            'veterinarian_name', 'clinic_name', 'notes', 'is_overdue',
            'days_until_due', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_pet(self, value):
        user = self.context['request'].user
        if value.owner != user:
            raise serializers.ValidationError("You can only create vaccinations for your own pets.")
        return value


class ReminderSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True, allow_null=True)
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        model = Reminder
        fields = [
            'id', 'pet', 'pet_name', 'title', 'description', 'type',
            'remind_at', 'completed', 'completed_at', 'recurring',
            'recurring_frequency', 'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'completed_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context['request'].user
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("You must be logged in to create a reminder.")
        validated_data['user'] = user
        return super().create(validated_data)

    def validate_pet(self, value):
        user = self.context['request'].user
        if value and value.owner != user:
            raise serializers.ValidationError("You can only create reminders for your own pets.")
        return value


class HealthRecordSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)

    class Meta:
        model = HealthRecord
        fields = [
            'id', 'pet', 'pet_name', 'type', 'title', 'description',
            'date', 'veterinarian_name', 'clinic_name', 'diagnosis',
            'treatment', 'medications', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_pet(self, value):
        user = self.context['request'].user
        if value.owner != user:
            raise serializers.ValidationError("You can only create health records for your own pets.")
        return value
