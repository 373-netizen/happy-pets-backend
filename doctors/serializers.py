# doctors/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    DoctorProfile, DoctorAvailability, Consultation,
    ChatMessage, ConsultationNote, DoctorReview,
    FavoriteDoctor, QuickReply, DoctorEarnings
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class DoctorProfileListSerializer(serializers.ModelSerializer):
    """Serializer for doctor list view"""
    full_name = serializers.CharField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    
    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'full_name', 'specialization', 'profile_photo',
            'city', 'state', 'years_experience', 'video_call_fee',
            'chat_fee', 'is_online', 'average_rating', 'total_ratings',
            'total_consultations', 'is_accepting_consultations', 'is_favorited'
        ]
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoriteDoctor.objects.filter(user=request.user, doctor=obj).exists()
        return False


class DoctorProfileDetailSerializer(serializers.ModelSerializer):
    """Serializer for doctor detail view"""
    full_name = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'user', 'full_name', 'specialization', 'license_number',
            'years_experience', 'bio', 'profile_photo', 'phone', 'city',
            'state', 'country', 'video_call_fee', 'chat_fee', 'is_online',
            'is_accepting_consultations', 'total_consultations', 'average_rating',
            'total_ratings', 'reviews_count', 'is_favorited', 'created_at'
        ]
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoriteDoctor.objects.filter(user=request.user, doctor=obj).exists()
        return False
    
    def get_reviews_count(self, obj):
        return obj.reviews.count()


class DoctorProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for doctor registration"""
    
    class Meta:
        model = DoctorProfile
        fields = [
            'specialization', 'license_number', 'years_experience', 'bio',
            'license_photo', 'profile_photo', 'phone', 'city', 'state',
            'country', 'video_call_fee', 'chat_fee'
        ]
    
    def validate_license_number(self, value):
        if DoctorProfile.objects.filter(license_number=value).exists():
            raise serializers.ValidationError("This license number is already registered.")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = DoctorAvailability
        fields = ['id', 'day_of_week', 'day_name', 'start_time', 'end_time', 'is_active']


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    is_mine = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'sender', 'sender_name', 'message', 'image',
            'is_read', 'created_at', 'is_mine'
        ]
        read_only_fields = ['sender', 'created_at']
    
    def get_is_mine(self, obj):
        request = self.context.get('request')
        return request and obj.sender == request.user


class ConsultationListSerializer(serializers.ModelSerializer):
    """Serializer for consultation list view"""
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    doctor_photo = serializers.ImageField(source='doctor.profile_photo', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'consultation_id', 'doctor', 'doctor_name', 'doctor_photo',
            'user', 'user_name', 'pet', 'pet_name', 'consultation_type',
            'status', 'payment_status', 'amount', 'created_at', 'scheduled_at'
        ]


class ConsultationDetailSerializer(serializers.ModelSerializer):
    """Serializer for consultation detail view"""
    doctor = DoctorProfileListSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    messages_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'consultation_id', 'doctor', 'user', 'pet',
            'consultation_type', 'status', 'chief_complaint',
            'scheduled_at', 'amount', 'payment_status',
            'stripe_payment_intent_id', 'video_room_url',
            'video_room_name', 'messages_count', 'created_at',
            'started_at', 'ended_at', 'duration_minutes'
        ]
    
    def get_messages_count(self, obj):
        return obj.messages.count()


class ConsultationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating consultation"""
    
    class Meta:
        model = Consultation
        fields = [
            'doctor', 'pet', 'consultation_type', 'chief_complaint', 'scheduled_at'
        ]
    
    def validate(self, data):
        doctor = data.get('doctor')
        
        # Check if doctor is approved
        if doctor.status != 'approved':
            raise serializers.ValidationError("This doctor is not approved yet.")
        
        # Check if doctor is accepting consultations
        if not doctor.is_accepting_consultations:
            raise serializers.ValidationError("This doctor is not accepting consultations.")
        
        # Set amount based on consultation type
        if data['consultation_type'] == 'video':
            data['amount'] = doctor.video_call_fee
        else:
            data['amount'] = doctor.chat_fee
        
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class ConsultationNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationNote
        fields = [
            'id', 'consultation', 'diagnosis', 'treatment_plan',
            'prescriptions', 'follow_up_required', 'follow_up_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['doctor']


class DoctorReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = DoctorReview
        fields = [
            'id', 'doctor', 'consultation', 'user', 'user_name',
            'rating', 'review_text', 'would_recommend', 'created_at'
        ]
        read_only_fields = ['user']
    
    def validate(self, data):
        # Ensure consultation is completed
        consultation = data.get('consultation')
        if consultation.status != 'completed':
            raise serializers.ValidationError("Can only review completed consultations.")
        
        # Ensure user is the consultation patient
        if consultation.user != self.context['request'].user:
            raise serializers.ValidationError("You can only review your own consultations.")
        
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class FavoriteDoctorSerializer(serializers.ModelSerializer):
    doctor = DoctorProfileListSerializer(read_only=True)
    
    class Meta:
        model = FavoriteDoctor
        fields = ['id', 'doctor', 'created_at']


class QuickReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuickReply
        fields = ['id', 'title', 'message', 'created_at']
        read_only_fields = ['doctor']


class DoctorEarningsSerializer(serializers.ModelSerializer):
    consultation_id = serializers.CharField(source='consultation.consultation_id', read_only=True)
    
    class Meta:
        model = DoctorEarnings
        fields = [
            'id', 'consultation', 'consultation_id', 'gross_amount',
            'platform_fee_percentage', 'platform_fee', 'net_amount',
            'paid_out', 'payout_date', 'created_at'
        ]
        # doctors/serializers.py

class ConsultationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating consultation"""
    
    class Meta:
        model = Consultation
        fields = [
            'id',  # ADDED
            'doctor', 'pet', 'consultation_type', 'chief_complaint', 'scheduled_at'
        ]
        read_only_fields = ['id']  # ADDED
    
    def validate(self, data):
        doctor = data.get('doctor')
        
        # Check if doctor is approved
        if doctor.status != 'approved':
            raise serializers.ValidationError("This doctor is not approved yet.")
        
        # Check if doctor is accepting consultations
        if not doctor.is_accepting_consultations:
            raise serializers.ValidationError("This doctor is not accepting consultations.")
        
        # Set amount based on consultation type
        if data['consultation_type'] == 'video':
            data['amount'] = doctor.video_call_fee
        else:
            data['amount'] = doctor.chat_fee
        
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
    
    # ADDED: Return full details after creation
    def to_representation(self, instance):
        return {
            'id': instance.id,
            'consultation_id': str(instance.consultation_id),
            'doctor': instance.doctor.id,
            'pet': instance.pet.id,
            'user': instance.user.id,
            'consultation_type': instance.consultation_type,
            'chief_complaint': instance.chief_complaint,
            'scheduled_at': instance.scheduled_at,
            'amount': float(instance.amount),
            'status': instance.status,
            'payment_status': instance.payment_status,
            'created_at': instance.created_at
        }