# backend/restaurants/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Addressing pattern for connecting to the order tracking WebSocket
    re_path(r'ws/orders/(?P<order_id>\d+)/$', consumers.OrderTrackingConsumer.as_asgi()),
]