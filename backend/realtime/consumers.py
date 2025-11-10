from channels.generic.websocket import AsyncWebsocketConsumer, JsonWebsocketConsumer
from asgiref.sync import async_to_sync
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

class PlayerTracker:
    """Tracks active WebSocket connections and their associated players"""
    def __init__(self):
        self.connections = {}  # Maps channel_name to player info
        
    def add_connection(self, channel_name, player_id):
        self.connections[channel_name] = {
            'player_id': player_id,
            'ready': False
        }
    
    def remove_connection(self, channel_name):
        if channel_name in self.connections:
            del self.connections[channel_name]
    
    def get_player_info(self, channel_name):
        return self.connections.get(channel_name)

# Global instance to track all connections
connection_tracker = PlayerTracker()

class GameConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.accept()
        # Add to game room group
        async_to_sync(self.channel_layer.group_add)(
            "game_room",
            self.channel_name
        )

    def disconnect(self, close_code):
        # Remove from game room group
        async_to_sync(self.channel_layer.group_discard)(
            "game_room",
            self.channel_name
        )
        connection_tracker.remove_connection(self.channel_name)

    def receive_json(self, content):
        """Handle incoming WebSocket messages"""
        msg_type = content.get('type')
        if msg_type == 'join_lobby':
            lobby_id = content.get('lobby_id')
            # Add to specific lobby group
            async_to_sync(self.channel_layer.group_add)(
                f"lobby_{lobby_id}",
                self.channel_name
            )
        elif msg_type == 'leave_lobby':
            lobby_id = content.get('lobby_id')
            # Remove from specific lobby group
            async_to_sync(self.channel_layer.group_discard)(
                f"lobby_{lobby_id}",
                self.channel_name
            )

    def broadcast_players(self, event):
        """Handle player list broadcasts"""
        self.send_json({
            "type": "player_list",
            "players": event["players"]
        })

    def game_started(self, event):
        """Handle game start notification"""
        self.send_json({
            "type": "game_started",
            "message": event["message"],
            "game_state": event["game_state"]
        })

    def game_state_update(self, event):
        """Handle game state updates"""
        self.send_json({
            "type": "game_state_update",
            "game_state": event["game_state"]
        })