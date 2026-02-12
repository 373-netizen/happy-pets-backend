# reviews/serializers.py
from rest_framework import serializers
from .models import Review, ReviewHelpful, ReviewImage
from django.contrib.auth import get_user_model

User = get_user_model()


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'created_at']


class ReviewUserSerializer(serializers.ModelSerializer):
    """Lightweight user serializer for reviews"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class ReviewSerializer(serializers.ModelSerializer):
    user = ReviewUserSerializer(read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)
    is_helpful = serializers.SerializerMethodField()
    user_can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'product', 'user', 'rating', 'title', 'comment',
            'helpful_count', 'is_verified_purchase', 'is_approved',
            'images', 'is_helpful', 'user_can_edit',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'helpful_count', 'is_verified_purchase', 'is_approved']
    
    def get_is_helpful(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ReviewHelpful.objects.filter(review=obj, user=request.user).exists()
        return False
    
    def get_user_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Separate serializer for creating reviews with image upload"""
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Review
        fields = ['product', 'rating', 'title', 'comment', 'images']
    
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        validated_data['user'] = self.context['request'].user
        
        review = Review.objects.create(**validated_data)
        
        # Create review images
        for image in images_data:
            ReviewImage.objects.create(review=review, image=image)
        
        return review


class ReviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']