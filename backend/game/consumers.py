import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models.lobby_player import LobbyPlayer
from .models.game import Game
from django.db.models import Q

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"game_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Send initial game state
        game_state = await self.get_game_state()
        if game_state:
            await self.send(text_data=json.dumps({
                "type": "game_state",
                "game_state": game_state
            }))

    async def disconnect(self, close_code):
        # Clean up the room if this was a server shutdown
        if close_code == 1001:  # Going away
            await self.cleanup_room()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    @database_sync_to_async
    def cleanup_room(self):
        """Clean up the room and associated players when server disconnects"""
        try:
            room_id = self.room_name
            # Clean up any lobbies and players associated with this room
            from game.models.lobby import Lobby
            from game.models.lobby_player import LobbyPlayer
            
            # Get the lobby for this room
            try:
                lobby = Lobby.objects.get(id=room_id)
                # Delete all associated players first
                LobbyPlayer.objects.filter(lobby=lobby).delete()
                # Then delete the lobby
                lobby.delete()
            except Lobby.DoesNotExist:
                pass
        except Exception as e:
            print(f"Error during room cleanup: {e}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type")

        if msg_type in ["make_move", "make_suggestion", "make_accusation"]:
            # Handle game actions
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "game_message",
                    "message": {
                        "type": msg_type,
                        "player_id": data.get("player_id")
                    }
                }
            )

            # Update game state after action
            game_state = await self.get_game_state()
            if game_state:
                await self.send(text_data=json.dumps({
                    "type": "game_state",
                    "game_state": game_state
                }))

    async def game_message(self, event):
        print(f"Game message received: {event}")  # Debug log
        
        # Ensure we have a message in the event
        if "message" not in event:
            print(f"Warning: No message in event {event}")  # Debug log
            return
            
        message = event["message"]
        print(f"Processing message: {message}")  # Debug log
            
        try:
            # Handle game started messages
            if isinstance(message, dict) and message.get("type") == "game.started":
                game_state = message.get("game_state", {})
                print(f"Sending game state: {game_state}")  # Debug log
                await self.send(text_data=json.dumps({
                    "type": "game_state",
                    "game_state": game_state
                }))
            
            # Handle game state messages
            elif isinstance(message, dict) and message.get("type") == "game_state":
                print(f"Sending direct game state: {message}")  # Debug log
                await self.send(text_data=json.dumps({
                    "type": "game_state",
                    "game_state": message.get("game_state", {})
                }))
            
            # Handle other dictionary messages
            elif isinstance(message, dict):
                print(f"Sending dict message: {message}")  # Debug log
                await self.send(text_data=json.dumps({
                    "type": message.get("type", "game_message"),
                    "message": message
                }))
            
            # Handle string or other messages
            else:
                print(f"Sending simple message: {message}")  # Debug log
                await self.send(text_data=json.dumps({
                    "type": "game_message",
                    "message": message
                }))
                
        except Exception as e:
            print(f"Error processing game message: {e}")  # Debug log
            # Send a basic error message that won't cause frontend issues
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(e)
            }))

    @database_sync_to_async
    def get_game_state(self):
        try:
            # Get game for this lobby
            game = Game.objects.filter(name=f"lobby_{self.room_name}").first()
            if not game:
                return None

            # Get all players in the game
            players = game.players.select_related('current_room', 'current_hallway')
            
            player_states = []
            for player in players:
                location = None
                if player.current_room:
                    location = player.current_room.name
                elif player.current_hallway:
                    location = player.current_hallway.name

                player_states.append({
                    "id": player.id,
                    "name": player.character_name,
                    "location": location,
                    "eliminated": player.is_eliminated
                })

            return {
                "players": player_states,
                "current_player": game.current_player.character_name if game.current_player else None,
                "is_completed": game.is_completed,
                "is_active": game.is_active
            }
        except Exception as e:
            print(f"Error getting game state: {e}")
            return None

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