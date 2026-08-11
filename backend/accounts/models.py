from .managers import UserManager
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.gis.db import models as gis_models
from django.utils import timezone
from datetime import timedelta


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('CUSTOMER', 'کاربر عادی'),
        ('RESTAURANT_OWNER', 'مدیر رستوران'),
        ('COURIER', 'پیک موتوری'),
        ('ADMIN', 'مدیر سیستم'),
    )

    phone_number = models.CharField(max_length=15, unique=True, verbose_name="Phone Number")
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name="Email")
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CUSTOMER')
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.phone_number} ({self.get_role_display()})"


class OTPCode(models.Model):
    phone_number = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() < self.created_at + timedelta(minutes=2)

    def __str__(self):
        return f"{self.phone_number} -> {self.code}"


class UserAddress(models.Model):
    """Saving the user's selected locations on the map (home, work, etc.)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    title = models.CharField(max_length=50)  # e.g.: Home, Office
    address_text = models.TextField()
    location = gis_models.PointField(srid=4326, geography=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.phone_number} - {self.title}"