from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import DeliveryZone, ServiceArea


class DeliveryZoneSerializer(GeoFeatureModelSerializer):
    """
    GEODJANGO: Serialize a PolygonField as GeoJSON.
    
    The frontend (Leaflet) will read this GeoJSON and draw
    the polygon directly on the map.
    
    GeoJSON output:
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[lng, lat], [lng, lat], ...]]
      },
      "properties": {
        "name": "Zone A",
        "delivery_fee": "500.00",
        ...
      }
    }
    """
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    area_sq_km = serializers.SerializerMethodField()
    
    class Meta:
        model = DeliveryZone
        geo_field = 'area'  # ← The PolygonField
        fields = [
            'id', 'name', 'restaurant', 'restaurant_name',
            'delivery_fee', 'min_order', 'estimated_time',
            'is_active', 'area_sq_km'
        ]
    
    def get_area_sq_km(self, obj):
        return obj.area_sq_km


class ServiceAreaSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = ServiceArea
        geo_field = 'boundary'
        fields = ['id', 'name', 'is_active', 'launch_date']