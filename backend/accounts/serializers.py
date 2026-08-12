from rest_framework import serializers
from django.contrib.gis.geos import Point
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


class UserAddressSerializer(serializers.ModelSerializer):
    lat = serializers.FloatField(write_only=True)
    lng = serializers.FloatField(write_only=True)
    location_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserAddress
        fields = ['id', 'title', 'address_text', 'lat', 'lng', 'location_details', 'is_default']
        read_only_fields = ['id', 'is_default']

    def get_location_details(self, obj):
        if obj.location:
            return {
                "lat": obj.location.y,
                "lng": obj.location.x
            }
        return None

    def create(self, validated_data):
        lat = validated_data.pop('lat')
        lng = validated_data.pop('lng')
        # Creating a Point object for GeoDjango (coordinates as [x=lng, y=lat])
        validated_data['location'] = Point(lng, lat, srid=4326)
        # Automatically assign address to the current user
        validated_data['user'] = self.context['request'].user

        # If this is the user's first address, set it as default
        if not UserAddress.objects.filter(user=validated_data['user']).exists():
            validated_data['is_default'] = True

        return super().create(validated_data)