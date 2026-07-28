"""
restaurants/models.py

GEODJANGO CONCEPT: Geometry Fields in Models

The key difference from normal Django models:
  - Import from django.contrib.gis.db instead of django.db
  - Use PointField, PolygonField, etc. for spatial data
  - geography=True enables accurate spherical distance calculations

SRID 4326 = WGS84 (standard GPS lat/lng coordinates)
"""

# ← This is the critical import. Use GIS models, not standard ones.
from django.contrib.gis.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    """Restaurant category (e.g., "Fast Food", "Pizza", "Iranian")"""
    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=10, default='🍽️')  # emoji icon
    
    class Meta:
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name


class Restaurant(models.Model):
    """
    Core model demonstrating:
    1. PointField — stores a single GPS location
    2. geography=True — enables accurate spherical distance queries
    3. SRID 4326 — WGS84 coordinate system (default for GPS)
    """
    
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=300)
    phone = models.CharField(max_length=20, blank=True)
    
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name='restaurants'
    )
    
    # ─────────────────────────────────────────────────────────────
    # GEODJANGO: PointField
    # Stores a single geographic coordinate (longitude, latitude)
    #
    # geography=True is IMPORTANT:
    #   - Without it: distance is calculated in degrees (wrong!)
    #   - With it: distance is calculated in meters on the sphere (correct!)
    #
    # srid=4326: WGS84 — the coordinate system used by GPS devices
    # ─────────────────────────────────────────────────────────────
    location = models.PointField(
        srid=4326,
        geography=True,
        help_text='Click the map to set restaurant location'
    )
    
    rating = models.DecimalField(
        max_digits=3, decimal_places=1,
        default=4.0,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)]
    )
    price_range = models.IntegerField(
        choices=[(1, '$'), (2, '$$'), (3, '$$$')],
        default=2
    )
    
    delivery_time_min = models.IntegerField(default=30, help_text='Minutes')
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, default=15000)
    minimum_order = models.DecimalField(max_digits=12, decimal_places=2, default=50000)
    
    is_open = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    image_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-rating', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def latitude(self):
        """Return latitude from the PointField"""
        return self.location.y  # y = latitude (vertical axis)
    
    @property
    def longitude(self):
        """Return longitude from the PointField"""
        return self.location.x  # x = longitude (horizontal axis)


class MenuItem(models.Model):
    """Menu items for each restaurant"""
    
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name='menu_items'
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=50, default='Main')
    is_available = models.BooleanField(default=True)
    image_url = models.URLField(blank=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f'{self.name} ({self.restaurant.name})'