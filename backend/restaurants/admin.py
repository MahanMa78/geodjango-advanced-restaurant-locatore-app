"""
restaurants/admin.py

GEODJANGO CONCEPT: GIS Admin with Map Widgets

Using admin.GISModelAdmin instead of admin.ModelAdmin gives you:
  - An interactive OpenLayers map in the admin form
  - Click to place a Point
  - Draw polygons/lines directly on the map
  - Edit existing geometries visually
  - No need to type coordinate numbers!
"""

from django.contrib.gis import admin  # ← Import from gis, not regular admin
from .models import Restaurant, Category, MenuItem


@admin.register(Restaurant)
class RestaurantAdmin(admin.GISModelAdmin):
    """
    GISModelAdmin automatically adds a map widget for geometry fields.
    
    The 'location' PointField will render as an interactive map
    where you can click to place the restaurant's location.
    """
    
    list_display = [
        'name', 'category', 'rating', 'is_open', 
        'delivery_time_min', 'get_coordinates'
    ]
    list_filter = ['category', 'is_open', 'price_range', 'is_featured']
    search_fields = ['name', 'address']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Info', {
            'fields': ['name', 'description', 'category', 'image_url']
        }),
        ('Contact', {
            'fields': ['address', 'phone']
        }),
        ('Location', {
            'fields': ['location'],  # ← This becomes a map widget!
            'description': 'Click on the map to set the restaurant location'
        }),
        ('Business', {
            'fields': ['rating', 'price_range', 'delivery_time_min', 
                      'delivery_fee', 'minimum_order']
        }),
        ('Status', {
            'fields': ['is_open', 'is_featured']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_coordinates(self, obj):
        """Display lat/lng in list view"""
        if obj.location:
            return f'{obj.latitude:.4f}, {obj.longitude:.4f}'
        return '—'
    get_coordinates.short_description = 'Coordinates'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1


# Alternative: Register Restaurant with MenuItems inline
# admin.site.register(Restaurant, RestaurantAdmin)