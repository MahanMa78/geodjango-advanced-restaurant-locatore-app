from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, CategoryViewSet, ReverseGeocodeView  , RestaurantRouteView , CreateOrderView , MenuItemViewSet , UserOrdersView

router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet, basename='restaurant')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'menu-items', MenuItemViewSet, basename='menu-item')

urlpatterns = [
    path('', include(router.urls)),
    path('restaurants/<int:pk>/route/', RestaurantRouteView.as_view(), name='restaurant-route'),
    path('geocoding/reverse/', ReverseGeocodeView.as_view(), name='reverse-geocode'),
    path('orders/create/', CreateOrderView.as_view(), name='create-order'),
    path('orders/my-orders/', UserOrdersView.as_view(), name='user-orders'),
]