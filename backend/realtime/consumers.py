from channels.generic.websocket import AsyncWebsocketConsumer
import json

class HelloConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("hello_room", self.channel_name)
        await self.accept()
        await self.send(json.dumps({"message": "Connected to WebSocket!"}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("hello_room", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg = data.get("message", "")
        await self.send(json.dumps({"echo": f"You said: {msg}"}))

    async def broadcast(self, event):
        """Handles broadcasted messages from REST endpoint."""
        await self.send(json.dumps({"broadcast": event["text"]}))