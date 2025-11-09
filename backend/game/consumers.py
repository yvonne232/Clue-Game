import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models.lobby_player import LobbyPlayer

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"game_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({"message": f"Connected to {self.room_name}"}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg = data.get("message", "")
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "game_message", "message": msg},
        )

    async def game_message(self, event):
        await self.send(text_data=json.dumps({"message": event["message"]}))

class PlayerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        
        # Create a new player when a client connects
        player = await self.create_player()
        self.player_id = player.id
        
        # Send the player ID back to the client
        await self.send(text_data=json.dumps({
            'type': 'player_created',
            'player_id': self.player_id,
            'name': player.name
        }))

    async def disconnect(self, close_code):
        # Clean up player when client disconnects
        if hasattr(self, 'player_id'):
            await self.delete_player()

    @database_sync_to_async
    def create_player(self):
        return LobbyPlayer.objects.create()

    @database_sync_to_async
    def delete_player(self):
        LobbyPlayer.objects.filter(id=self.player_id).delete()

    async def receive(self, text_data):
        # Handle any messages from the client
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))
        except json.JSONDecodeError:
            pass