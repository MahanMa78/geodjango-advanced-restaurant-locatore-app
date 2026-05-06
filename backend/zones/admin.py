from django.contrib.gis import admin
from .models import DeliveryZone, ServiceArea


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.GISModelAdmin):
    """
    GEODJANGO: The PolygonField 'area' renders as a draw tool
    in the admin map. You can literally draw the delivery zone
    boundary by clicking on the map.
    """
    list_display = ['name', 'restaurant', 'delivery_fee', 'estimated_time', 'is_active']
    list_filter = ['restaurant', 'is_active']
    
    # Map configuration
    map_width = 900
    map_height = 600


@admin.register(ServiceArea)
class ServiceAreaAdmin(admin.GISModelAdmin):
    list_display = ['name', 'is_active', 'launch_date']