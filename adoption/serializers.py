# adoption/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Shelter, AdoptablePet, AdoptionApplication, Favorite

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class ShelterListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for shelter lists"""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    total_pets = serializers.IntegerField(read_only=True)
    available_pets = serializers.IntegerField(read_only=True)
    full_address = serializers.CharField(read_only=True)
    
    class Meta:
        model = Shelter
        fields = [
            'id', 'name', 'slug', 'owner_username', 'city', 'state', 
            'full_address', 'status', 'verified', 'logo', 'total_pets', 
            'available_pets', 'created_at'
        ]


class ShelterDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single shelter"""
    owner = UserSerializer(read_only=True)
    total_pets = serializers.IntegerField(read_only=True)
    available_pets = serializers.IntegerField(read_only=True)
    full_address = serializers.CharField(read_only=True)
    
    class Meta:
        model = Shelter
        fields = '__all__'
        read_only_fields = ['slug', 'created_at', 'updated_at', 'approved_at']


class ShelterCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating shelters"""
    
    class Meta:
        model = Shelter
        exclude = ['owner', 'slug', 'status', 'verified', 'approved_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        # Owner is set in the view
        return super().create(validated_data)
    
    def validate_phone(self, value):
        if value and len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value
    
    def validate_capacity(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("Capacity must be at least 1")
        return value


class AdoptablePetListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for pet lists"""
    shelter_name = serializers.CharField(source='shelter.name', read_only=True)
    shelter_city = serializers.CharField(source='shelter.city', read_only=True)
    shelter_state = serializers.CharField(source='shelter.state', read_only=True)
    age_display = serializers.CharField(read_only=True)
    good_with = serializers.ListField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = AdoptablePet
        fields = [
            'id', 'name', 'species', 'breed', 'age', 'age_display', 'size', 
            'gender', 'color', 'primary_image', 'shelter_name', 'shelter_city', 
            'shelter_state', 'status', 'adoption_fee', 'personality_traits', 
            'good_with', 'featured', 'urgent', 'is_favorited', 'created_at'
        ]
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, pet=obj).exists()
        return False
    def get_primary_image(self, obj):
        request = self.context.get('request')

        if obj.primary_image:
           if request:
              return request.build_absolute_uri(obj.primary_image.url)
           return obj.primary_image.url
           return None



class AdoptablePetDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single pet"""

    shelter = ShelterListSerializer(read_only=True)
    age_display = serializers.ReadOnlyField()
    good_with = serializers.ReadOnlyField()

    is_favorited = serializers.SerializerMethodField()
    total_applications = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    all_images = serializers.SerializerMethodField()

    class Meta:
        model = AdoptablePet
        fields = '__all__'
        read_only_fields = ['views', 'created_at', 'updated_at']

    # ✅ FAVORITE CHECK
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, pet=obj).exists()
        return False

    # ✅ APPLICATION COUNT
    def get_total_applications(self, obj):
        return obj.applications.count()

    # ✅ PRIMARY IMAGE URL
    def get_primary_image(self, obj):
        request = self.context.get('request')

        if obj.primary_image:
            if request:
                return request.build_absolute_uri(obj.primary_image.url)
            return obj.primary_image.url

        return None

    # ✅ ALL IMAGES LIST
    def get_all_images(self, obj):
        request = self.context.get('request')
        images = []

        image_fields = [
            obj.primary_image,
            obj.image_2,
            obj.image_3,
            obj.image_4,
        ]

        for img in image_fields:
            if img:
                if request:
                    images.append(request.build_absolute_uri(img.url))
                else:
                    images.append(img.url)

        return images


class AdoptablePetCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating pets"""
    
    class Meta:
        model = AdoptablePet
        exclude = ['views', 'featured', 'urgent', 'is_active']

        read_only_fields = ['created_at', 'updated_at', 'date_adopted']
    
    def validate(self, data):
        # Ensure shelter belongs to the user
        request = self.context.get('request')
        shelter = data.get('shelter')
        
        if shelter and request:
            # Check if user owns this shelter or is admin
            if not request.user.is_staff and shelter.owner != request.user:
                raise serializers.ValidationError({
                    'shelter': 'You can only add pets to your own shelters'
                })
            
            # Check if shelter is approved
            if shelter.status != 'approved':
                raise serializers.ValidationError({
                    'shelter': 'Shelter must be approved before adding pets'
                })
        
        # Validate age
        age = data.get('age', 0)
        if age < 1:
            raise serializers.ValidationError({'age': 'Age must be at least 1 month'})
        if age > 300:  # 25 years
            raise serializers.ValidationError({'age': 'Age seems unrealistic (max 300 months)'})
        
        # Validate weight
        weight = data.get('weight')
        if weight is not None and weight <= 0:
            raise serializers.ValidationError({'weight': 'Weight must be positive'})
        
        # Validate adoption fee
        adoption_fee = data.get('adoption_fee')
        if adoption_fee is not None and adoption_fee < 0:
            raise serializers.ValidationError({'adoption_fee': 'Adoption fee cannot be negative'})
        
        return data
    
    def validate_personality_traits(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Personality traits must be a list")
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 personality traits allowed")
        return value


class AdoptionApplicationSerializer(serializers.ModelSerializer):
    """Serializer for adoption applications"""
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    pet_species = serializers.CharField(source='pet.species', read_only=True)
    pet_image = serializers.ImageField(source='pet.primary_image', read_only=True)
    shelter_name = serializers.CharField(source='pet.shelter.name', read_only=True)
    applicant_username = serializers.CharField(source='applicant.username', read_only=True)
    
    class Meta:
        model = AdoptionApplication
        fields = '__all__'
        read_only_fields = ['applicant', 'submitted_at', 'updated_at', 'reviewed_by', 'reviewed_at']
    
    def validate(self, data):
        pet = data.get('pet')
        request = self.context.get('request')
        
        # Check if pet is available
        if pet and pet.status != 'available':
            raise serializers.ValidationError({
                'pet': 'This pet is not available for adoption'
            })
        
        # Check for duplicate applications (one active application per pet per user)
        if request and pet:
            existing = AdoptionApplication.objects.filter(
                pet=pet,
                applicant=request.user,
                status__in=['submitted', 'under_review']
            )
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            
            if existing.exists():
                raise serializers.ValidationError({
                    'pet': 'You already have a pending application for this pet'
                })
        
        # Validate phone numbers
        for field in ['phone', 'reference_1_phone', 'reference_2_phone', 'veterinarian_phone']:
            value = data.get(field)
            if value and len(value) < 10:
                raise serializers.ValidationError({
                    field: 'Phone number must be at least 10 digits'
                })
        
        # Validate household members
        household_adults = data.get('household_adults', 1)
        household_children = data.get('household_children', 0)
        if household_adults < 1:
            raise serializers.ValidationError({
                'household_adults': 'Must have at least 1 adult in household'
            })
        if household_children > 0 and not data.get('children_ages'):
            raise serializers.ValidationError({
                'children_ages': 'Please provide ages of children'
            })
        
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for favorites"""
    pet = AdoptablePetListSerializer(read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'pet', 'created_at']
        read_only_fields = ['created_at']


class ShelterStatsSerializer(serializers.Serializer):
    """Serializer for shelter statistics"""
    total_shelters = serializers.IntegerField()
    approved_shelters = serializers.IntegerField()
    pending_shelters = serializers.IntegerField()
    total_pets = serializers.IntegerField()
    available_pets = serializers.IntegerField()
    adopted_pets = serializers.IntegerField()
    pending_applications = serializers.IntegerField()


class PetStatsSerializer(serializers.Serializer):
    """Serializer for pet statistics by species"""
    species = serializers.CharField()
    count = serializers.IntegerField()