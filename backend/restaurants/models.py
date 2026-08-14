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
from django.conf import settings


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
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='restaurants',
        null=True, blank=True,
        verbose_name="مدیر رستوران"
    )
    
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
    


class PricingConfig(models.Model):
    """
    Dispatch System Dynamic Pricing Settings
    This model is designed as a Singleton to ensure there is always an active configuration within the system.
    """
    name = models.CharField(
        max_length=100, 
        default="Default pricing settings",
        verbose_name="Setting Name"
    )
    base_fee = models.IntegerField(
        default=15000, 
        help_text="Base delivery fee (IRR)",
        verbose_name="Base Fee"
    )
    per_km_rate = models.IntegerField(
        default=5000, 
        help_text="Delivery fee per kilometer (IRR)",
        verbose_name="Rate per Kilometer"
    )
    lunch_peak_multiplier = models.DecimalField(
        max_digits=3, decimal_places=2, default=1.25,
        validators=[MinValueValidator(1.0), MaxValueValidator(3.0)],
        verbose_name="Lunch Peak Multiplier (12:00 to 15:30)"
    )
    dinner_peak_multiplier = models.DecimalField(
        max_digits=3, decimal_places=2, default=1.30,
        validators=[MinValueValidator(1.0), MaxValueValidator(3.0)],
        verbose_name="Dinner Peak Multiplier (19:00 to 22:30)"
    )
    condition_multiplier = models.DecimalField(
        max_digits=3, decimal_places=2, default=1.00,
        validators=[MinValueValidator(1.0), MaxValueValidator(3.0)],
        help_text="Condition multiplier for special conditions like rain, snow, or heavy traffic (1.0 = normal)",
        verbose_name="Special Conditions/Weather Coefficient"
    )
    min_fee = models.IntegerField(
        default=20000, 
        help_text="Minimum delivery fee (IRR)",
        verbose_name="Minimum Delivery Fee"
    )
    max_fee = models.IntegerField(
        default=150000, 
        help_text="Maximum delivery fee (IRR)",
        verbose_name="Maximum Delivery Fee"
    )
    is_active = models.BooleanField(default=True, verbose_name="active")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated")

    class Meta:
        verbose_name = "Pricing Settings"
        verbose_name_plural = "Pricing Settings"

    def __str__(self):
        return f"{self.name} - (base: {self.base_fee} | per km: {self.per_km_rate})"

    @classmethod
    def get_active_config(cls):
        """
        Retrieves the active settings; creates a default instance if none exists.
        """
        config = cls.objects.filter(is_active=True).first()
        if not config:
            config = cls.objects.create()
        return config


class Courier(models.Model):
    "Courier / Motorcycle Delivery Rider Model"
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courier_profile',
        null=True, blank=True
    )

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    is_available = models.BooleanField(default=True)
    # Courier's live location on the map
    current_location = models.PointField(srid=4326, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({'free' if self.is_available else 'busy'})"



class Order(models.Model):
    """Order Placement and Tracking Status Model"""
    STATUS_CHOICES = [
        ('PENDING', 'Awaiting approval'),
        ('PREPARING', 'Preparing'),
        ('ON_THE_WAY', 'Out for delivery via courier'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        null=True, blank=True
    )
    
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    courier = models.ForeignKey(Courier, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    # Order delivery destination fields 
    delivery_location = models.PointField(srid=4326, geography=True, help_text="User's delivery destination coordinates")
    delivery_address = models.CharField(max_length=255, blank=True, help_text="Human readable address from geocoding")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_amount = models.DecimalField(max_digits=12, decimal_places=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.restaurant.name} ({self.get_status_display()})"


class OrderItem(models.Model):
    """Items purchased in each order (itemized invoice)"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    item_name = models.CharField(max_length=150, help_text="Name of the item at the time of purchase")
    price = models.DecimalField(max_digits=12, decimal_places=0, help_text="Unit price at the time of purchase")
    quantity = models.PositiveIntegerField(default=1, help_text="Quantity ordered")

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.item_name} (Order #{self.order.id})"