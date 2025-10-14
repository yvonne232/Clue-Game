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
        # Store the connection with a temporary ID
        connection_tracker.add_connection(self.channel_name, None)
        
    def disconnect(self, close_code):
        # Clean up when client disconnects
        connection_tracker.remove_connection(self.channel_name)
        
    def receive_json(self, content):
        # Handle incoming messages
        if 'player_id' in content:
            # Update player ID when client identifies themselves
            connection_tracker.add_connection(self.channel_name, content['player_id'])
            
        # You can broadcast to specific clients using their channel_name
        self.send_json({
            'message': f'Received message from player {content.get("player_id")}'
        })