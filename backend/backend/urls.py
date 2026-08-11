"""
Restaurant Locator URL Configuration

API Structure:
  /api/restaurants/          → List restaurants, create, nearby search
  /api/restaurants/<id>/     → Restaurant detail
  /api/restaurants/nearby/   → Spatial: restaurants within radius
  /api/zones/                → Delivery zones
  /api/zones/check/          → Spatial: check if point is in any zone
  /api/orders/               → Orders
  /api/geo/search/           → Geocoding helper
  /admin/                    → Django admin with map widgets
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('restaurants.urls')),
    path('api/', include('zones.urls')),
    path('api/accounts/', include('accounts.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)