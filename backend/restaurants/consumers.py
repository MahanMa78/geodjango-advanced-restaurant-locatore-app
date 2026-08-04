# backend/restaurants/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class OrderTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        When the frontend connects to ws://localhost:8000/ws/orders/<order_id>/
        """
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.room_group_name = f'order_tracking_{self.order_id}'

        # Joining the client to the dedicated group for this order in the Redis Channel Layer
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"✅ WebSocket Connected: User joined room {self.room_group_name}")

    async def disconnect(self, close_code):
        """
        When the user closes the page or the connection is lost
        """
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"❌ WebSocket Disconnected from room {self.room_group_name}")

    async def courier_location_update(self, event):
        """
        This method corresponds to the message sent by the Celery Task to the Channel Layer.
        It pushes the new courier location directly to the user's browser.
        """
        await self.send(text_data=json.dumps({
            'type': 'courier_location_update',
            'order_id': event['order_id'],
            'status': event['status'],
            'courier_lat': event['courier_lat'],
            'courier_lng': event['courier_lng'],
            'message': event.get('message', '')
        }))