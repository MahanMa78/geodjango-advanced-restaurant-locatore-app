# backend/restaurants/tasks.py
import time
import requests
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.gis.geos import Point
from .models import Order, Courier

@shared_task
def simulate_courier_movement(order_id):
    """
    Simulates the movement of a courier from the restaurant to the user's delivery location.
    """
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return f"Order #{order_id} not found."

    restaurant = order.restaurant
    user_location = order.delivery_location

    # 1. Retrieve the actual OSRM route between the restaurant and the user.
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{restaurant.longitude},{restaurant.latitude};{user_location.x},{user_location.y}?overview=full&geometries=geojson"
    
    try:
        response = requests.get(osrm_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Extract the coordinates of the route points [lng, lat]
        coordinates = data['routes'][0]['geometry']['coordinates']
    except Exception as e:
        # In case of disconnection or error, we create a hypothetical direct route with 2 points
        coordinates = [
            [restaurant.longitude, restaurant.latitude],
            [user_location.x, user_location.y]
        ]

    # 2. Assign a courier or create a sample courier
    courier = order.courier
    if not courier:
        courier = Courier.objects.filter(is_available=True).first()
        if not courier:
            courier = Courier.objects.create(name="Courier Express", phone="09120000000", is_available=False)
        order.courier = courier

    # Change the order status to "ON_THE_WAY"
    order.status = 'ON_THE_WAY'
    order.save()

    channel_layer = get_channel_layer()
    room_group_name = f'order_tracking_{order_id}'

    # 3. Traversing Waypoints and Real-time Transmission via WebSocket
    total_points = len(coordinates)
    for index, (lng, lat) in enumerate(coordinates):
        # Update courier location
        courier.current_location = Point(lng, lat, srid=4326)
        courier.is_available = False
        courier.save()

        # Sending a message to the Redis Channel Layer
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'courier_location_update',
                'order_id': order.id,
                'status': order.status,
                'courier_lat': lat,
                'courier_lng': lng,
                'message': f'The courier is on the way. ({index + 1}/{total_points})'
            }
        )

        # 1.5-second pause between each step to create a smooth movement animation
        time.sleep(1.5)

    # 4. End of Route and Order Delivery
    order.status = 'DELIVERED'
    order.save()

    courier.is_available = True
    courier.save()

    # Send Final Delivery Message
    async_to_sync(channel_layer.group_send)(
        room_group_name,
        {
            'type': 'courier_location_update',
            'order_id': order.id,
            'status': order.status,
            'courier_lat': user_location.y,
            'courier_lng': user_location.x,
            'message': 'Order successfully delivered! 🎉'
        }
    )

    return f"Order #{order_id} tracking simulation completed successfully."