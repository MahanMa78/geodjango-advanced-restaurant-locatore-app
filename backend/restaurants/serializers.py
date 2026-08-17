"""
restaurants/serializers.py

GEODJANGO CONCEPT: GeoJSON Serialization

GeoFeatureModelSerializer (from djangorestframework-gis) automatically:
  1. Wraps the response in a GeoJSON FeatureCollection
  2. Puts the geometry field in the GeoJSON "geometry" key
  3. Puts all other fields in "properties"

This is exactly what Leaflet and Mapbox expect.

Output format:
{
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "id": 1,
            "geometry": {
                "type": "Point",
                "coordinates": [3.3792, 6.5244]  ← [longitude, latitude]
            },
            "properties": {
                "name": "The Bistro",
                "rating": "4.5",
                ...
            }
        }
    ]
}
"""

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import Point
from .models import OrderItem, Restaurant, Category, MenuItem , Courier, Order


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon']


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'restaurant', 'name', 'description', 'price', 'category', 'is_available', 'image_url']
        read_only_fields = ['id']

class RestaurantListSerializer(GeoFeatureModelSerializer):
    """
    GEODJANGO: GeoFeatureModelSerializer for list/map views.
    
    The geo_field = 'location' tells the serializer which field
    contains the geometry. This field becomes the GeoJSON geometry,
    while everything else goes into properties.
    
    Leaflet.js will read this GeoJSON and automatically place
    a marker at the coordinates.
    """
    category_name = serializers.SerializerMethodField()
    category_icon = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        geo_field = 'location'  # ← The geometry field — becomes GeoJSON geometry
        fields = [
            'id', 'name', 'address', 'rating', 'price_range',
            'delivery_time_min', 'delivery_fee', 'minimum_order',
            'is_open', 'is_featured', 'image_url',
            'category_name', 'category_icon', 'distance_km',
        ]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_category_icon(self, obj):
        return obj.category.icon if obj.category else '🍽️'
    
    def get_distance_km(self, obj):
        """
        If the queryset was annotated with distance (from a nearby search),
        return it in kilometers rounded to 1 decimal place.
        """
        if hasattr(obj, 'distance') and obj.distance is not None:
            return round(obj.distance.km, 1)
        return None


class RestaurantDetailSerializer(GeoFeatureModelSerializer):
    """
    Full restaurant detail including menu items.
    A comprehensive serializer for the creation 
    and editing of restaurant information by the owner.
    """
    category = CategorySerializer(source='category' ,read_only=True)
    menu_items = MenuItemSerializer(many=True, read_only=True)
    lat = serializers.FloatField(write_only=True, required=False)
    lng = serializers.FloatField(write_only=True, required=False)
    
    class Meta:
        model = Restaurant
        geo_field = 'location'
        fields = [
            'id', 'name', 'description', 'address', 'phone',
            'category', 'rating', 'price_range',
            'delivery_time_min', 'delivery_fee', 'minimum_order',
            'is_open', 'is_featured', 'image_url',
            'menu_items', 'created_at',
        ]
        read_only_fields = ['id', 'owner', 'rating', 'created_at']


    def create(self, validated_data):
        lat = validated_data.pop('lat', None)
        lng = validated_data.pop('lng', None)
        if lat is not None and lng is not None:
            validated_data['location'] = Point(lng, lat, srid=4326)
        
        # Registering the current user as the restaurant owner
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        lat = validated_data.pop('lat', None)
        lng = validated_data.pop('lng', None)
        if lat is not None and lng is not None:
            instance.location = Point(lng, lat, srid=4326)
        return super().update(instance, validated_data)


class RestaurantWriteSerializer(serializers.ModelSerializer):
    """
    For creating/updating restaurants.
    Accepts latitude and longitude as separate fields,
    and combines them into a PointField.
    """
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)
    
    class Meta:
        model = Restaurant
        fields = [
            'name', 'description', 'address', 'phone',
            'category', 'rating', 'price_range',
            'delivery_time_min', 'delivery_fee', 'minimum_order',
            'is_open', 'is_featured', 'image_url',
            'latitude', 'longitude',
        ]
    
    def validate(self, data):
        lat = data.pop('latitude')
        lng = data.pop('longitude')
        
        # Validate coordinate ranges
        if not (-90 <= lat <= 90):
            raise serializers.ValidationError({'latitude': 'Must be between -90 and 90'})
        if not (-180 <= lng <= 180):
            raise serializers.ValidationError({'longitude': 'Must be between -180 and 180'})
        
        # GEODJANGO: Create a Point geometry from lat/lng
        # Remember: Point takes (longitude, latitude) — x then y
        from django.contrib.gis.geos import Point
        data['location'] = Point(lng, lat, srid=4326)
        
        return data

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'item_name', 'price', 'quantity', 'total_price']


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for displaying the complete order invoice"""
    items = OrderItemSerializer(many=True, read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    courier_name = serializers.CharField(source='courier.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'restaurant', 'restaurant_name',
            'courier', 'courier_name', 'status', 'status_display',
            'delivery_address', 'delivery_fee', 'total_amount',
            'items', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'created_at']