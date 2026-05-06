from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeliveryZoneViewSet, ServiceAreaViewSet

router = DefaultRouter()
router.register(r'zones', DeliveryZoneViewSet, basename='zone')
router.register(r'service-areas', ServiceAreaViewSet, basename='service-area')

urlpatterns = [
    path('', include(router.urls)),
]