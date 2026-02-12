# breeding/serializers.py
from rest_framework import serializers
from .models import BreedingSwipe, BreedingMatch, BreedingChatMessage
from pets.models import Pet


class PetBreedingSerializer(serializers.ModelSerializer):
    """Serializer for pets in breeding matchmaking"""
    age = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Pet
        fields = [
            'id', 'name', 'species', 'breed', 'gender', 
            'date_of_birth', 'age', 'weight', 'color', 
            'photo', 'owner_name'
        ]
    
    def get_age(self, obj):
        """Calculate age from date of birth"""
        if not obj.date_of_birth:
            return 'Unknown'
        
        from datetime import date
        today = date.today()
        born = obj.date_of_birth
        
        years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        
        if years == 0:
            months = today.month - born.month
            if months <= 0:
                months += 12
            return f"{months} month{'s' if months != 1 else ''}"
        
        return f"{years} year{'s' if years != 1 else ''}"
    
    def get_owner_name(self, obj):
        """Get owner's display name"""
        return obj.owner.get_full_name() or obj.owner.username


class BreedingSwipeSerializer(serializers.ModelSerializer):
    """Serializer for breeding swipes"""
    user_pet_name = serializers.CharField(source='user_pet.name', read_only=True)
    target_pet_name = serializers.CharField(source='target_pet.name', read_only=True)
    
    class Meta:
        model = BreedingSwipe
        fields = ['id', 'user_pet', 'user_pet_name', 'target_pet', 'target_pet_name', 'action', 'created_at']
        read_only_fields = ['created_at']


class BreedingMatchSerializer(serializers.ModelSerializer):
    """Serializer for breeding matches"""
    pet1_data = PetBreedingSerializer(source='pet1', read_only=True)
    pet2_data = PetBreedingSerializer(source='pet2', read_only=True)
    unread_messages = serializers.SerializerMethodField()
    
    class Meta:
        model = BreedingMatch
        fields = ['id', 'pet1', 'pet1_data', 'pet2', 'pet2_data', 'chat_unlocked', 'created_at', 'unread_messages']
        read_only_fields = ['created_at', 'chat_unlocked']
    
    def get_unread_messages(self, obj):
        """Get count of unread messages for current user"""
        request = self.context.get('request')
        if not request:
            return 0
        
        return BreedingChatMessage.objects.filter(
            match=obj,
            read=False
        ).exclude(sender=request.user).count()


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    is_own_message = serializers.SerializerMethodField()
    
    class Meta:
        model = BreedingChatMessage
        fields = ['id', 'match', 'sender', 'sender_name', 'message', 'created_at', 'read', 'is_own_message']
        read_only_fields = ['created_at', 'sender']
    
    def get_is_own_message(self, obj):
        """Check if message was sent by current user"""
        request = self.context.get('request')
        if not request:
            return False
        return obj.sender == request.user