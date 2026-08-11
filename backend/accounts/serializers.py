from rest_framework import serializers
from .models import User, UserAddress

class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=6)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'email', 'first_name', 'last_name', 'role', 'date_joined']
        read_only_fields = ['phone_number', 'role', 'date_joined']


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['id', 'title', 'address_text', 'location', 'is_default']