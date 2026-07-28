"""
zones/models.py

GEODJANGO CONCEPT: PolygonField & Spatial Containment

Delivery zones are the perfect use case for PolygonField.
They demonstrate:
  - Storing polygon geometry (area shapes)
  - contains() lookup — is this user point inside this zone?
  - Transform CRS projection for metric area calculations (SRID 3857)
"""

from django.contrib.gis.db import models


class DeliveryZone(models.Model):
    """
    A delivery zone is a polygon area within which a restaurant delivers.
    
    GEODJANGO: PolygonField stores a closed polygon geometry.
    """
    
    name = models.CharField(max_length=100)
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        related_name='delivery_zones'
    )
    
    # ─────────────────────────────────────────────────────────
    # GEODJANGO: PolygonField
    # Stores a polygon (closed area shape)
    # geography=True enables accurate area and intersection calculations
    # ─────────────────────────────────────────────────────────
    area = models.PolygonField(
        srid=4326,
        geography=True,
        help_text='Draw the delivery zone boundary on the map'
    )
    
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, default=15000)
    min_order = models.DecimalField(max_digits=12, decimal_places=2, default=50000)
    estimated_time = models.IntegerField(default=30, help_text='Minutes')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['restaurant', 'name']
    
    def __str__(self):
        return f'{self.restaurant.name} — {self.name}'
    
    @property
    def area_sq_km(self):
        """
        Calculate zone area in square kilometers.
        
        GEODJANGO: Transform to Web Mercator (SRID 3857) projection for metric measurement.
        """
        if self.area:
            # Transform to metric projection for accurate measurement
            projected = self.area.transform(3857, clone=True)
            return round(projected.area / 1_000_000, 2)  # m² to km²
        return None


class ServiceArea(models.Model):
    """
    A broader service area — the city/region boundary where the service operates.
    Demonstrates MultiPolygonField for complex city boundaries.
    """
    
    name = models.CharField(max_length=100)
    
    # GEODJANGO: MultiPolygonField — for areas with multiple disconnected parts
    boundary = models.MultiPolygonField(
        srid=4326,
        geography=True,
        help_text='The full service area boundary (can include multiple polygons)'
    )
    
    is_active = models.BooleanField(default=True)
    launch_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name