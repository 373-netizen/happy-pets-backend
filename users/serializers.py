# users/serializers.py

from rest_framework import serializers
from dj_rest_auth.serializers import LoginSerializer as DefaultLoginSerializer
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _

User = get_user_model()

# ----------------------
# Register Serializer
# ----------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'phone']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone=validated_data.get('phone', '')
        )
        return user


# ----------------------
# User Serializer (with full avatar URL)
# Supports reading and writing avatar files
# ----------------------
class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'location',
            'address', 'avatar', 'latitude', 'longitude'
        ]
        read_only_fields = ['id', 'email']

    def to_representation(self, instance):
        """Return full absolute URL for avatar when reading"""
        ret = super().to_representation(instance)
        if instance.avatar:
            request = self.context.get('request')
            if request:
                ret['avatar'] = request.build_absolute_uri(instance.avatar.url)
            else:
                ret['avatar'] = f"http://127.0.0.1:8000{instance.avatar.url}"
        else:
            ret['avatar'] = None
        return ret


# ----------------------
# Custom Login Serializer
# ----------------------
class CustomLoginSerializer(DefaultLoginSerializer):
    username = None
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not user:
                try:
                    user = User.objects.get(email=email)
                    if user.check_password(password) and user.is_active:
                        attrs['user'] = user
                        return attrs
                except User.DoesNotExist:
                    pass
                raise serializers.ValidationError(_("Invalid email or password."))

            if not user.is_active:
                raise serializers.ValidationError(_("User account is disabled."))
        else:
            raise serializers.ValidationError(_("Must include email and password."))

        attrs['user'] = user
        return attrs
