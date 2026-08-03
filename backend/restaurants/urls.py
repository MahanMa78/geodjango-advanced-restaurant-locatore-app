from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, CategoryViewSet, ReverseGeocodeView  , RestaurantRouteView

router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet, basename='restaurant')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
    path('restaurants/<int:pk>/route/', RestaurantRouteView.as_view(), name='restaurant-route'),
    path('geocoding/reverse/', ReverseGeocodeView.as_view(), name='reverse-geocode'),
]