from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, CategoryViewSet ,restaurant_route

router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet, basename='restaurant')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
    path('restaurants/<int:pk>/route/', restaurant_route, name='restaurant-route'),
]