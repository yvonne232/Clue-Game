import json
import uuid

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from game.game_engine.session_registry import get_session, remove_session
from game.models import Game, LobbyPlayer


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"game_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        state = await self.get_game_state()
        if state:
            await self.send_json({"type": "game_state", "game_state": state})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type")

        if msg_type == "make_move":
            await self._handle_make_move(data)
        elif msg_type == "make_suggestion":
            await self._handle_make_suggestion(data)
        elif msg_type == "make_accusation":
            await self._handle_make_accusation(data)
        elif msg_type == "end_turn":
            await self._handle_end_turn(data)
        else:
            await self.send_json(
                {"type": "error", "message": f"Unsupported action: {msg_type}"}
            )

    async def _handle_make_move(self, data):
        player_id = data.get("player_id")
        if player_id is None:
            await self._send_error("Player ID is required for movement.")
            return

        result = await self._manager_call(
            "move_player",
            player_id=int(player_id),
            destination_name=data.get("destination"),
        )
        if not result.get("success"):
            await self._send_error(result.get("error", "Unable to move."))
            return

        if result.get("requires_choice"):
            payload = {
                "type": "move_options",
                "player_id": int(player_id),
                "options": result.get("options", []),
                "request_id": result.get("request_id") or str(uuid.uuid4()),
                "player_name": result.get("player_name"),
            }
            await self.send_json(payload)
            await self._broadcast_game_state()
            return

        await self._broadcast_game_state()

    async def _handle_make_suggestion(self, data):
        player_id = data.get("player_id")
        if player_id is None:
            await self._send_error("Player ID is required for suggestions.")
            return

        result = await self._manager_call(
            "make_suggestion_action",
            player_id=int(player_id),
            suspect=data.get("suspect"),
            weapon=data.get("weapon"),
        )
        if not result.get("success"):
            await self._send_error(result.get("error", "Suggestion failed."))
            return

        await self._broadcast_game_state()

    async def _handle_make_accusation(self, data):
        player_id = data.get("player_id")
        if player_id is None:
            await self._send_error("Player ID is required for accusations.")
            return

        result = await self._manager_call(
            "make_accusation_action",
            player_id=int(player_id),
            suspect=data.get("suspect"),
            weapon=data.get("weapon"),
            room=data.get("room"),
        )
        if not result.get("success"):
            await self._send_error(result.get("error", "Accusation failed."))
            return

        await self._broadcast_game_state()
        if result.get("game_over"):
            await self._remove_session()

    async def _handle_end_turn(self, data):
        player_id = data.get("player_id")
        if player_id is None:
            await self._send_error("Player ID is required to end a turn.")
            return

        result = await self._manager_call("end_turn", player_id=int(player_id))
        if not result.get("success"):
            await self._send_error(result.get("error", "Unable to end turn."))
            return

        await self._broadcast_game_state()
        if result.get("game_over"):
            await self._remove_session()

    async def _broadcast_game_state(self):
        state = await self.get_game_state()
        if not state:
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "forward_game_state",
                "game_state": state,
            },
        )

    async def forward_game_state(self, event):
        await self.send_json({"type": "game_state", "game_state": event["game_state"]})

    async def game_message(self, event):
        message = event.get("message")
        if message is None:
            return
        await self.send_json(
            {
                "type": "game_message",
                "message": message,
            }
        )

    async def _send_error(self, message: str):
        await self.send_json({"type": "error", "message": message})

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload))

    @database_sync_to_async
    def _manager_call(self, action: str, **kwargs):
        game_name = f"lobby_{self.room_name}"
        manager = get_session(game_name)
        if manager is None:
            return {"success": False, "error": "Game session is not initialized."}
        handler = getattr(manager, action, None)
        if handler is None:
            return {"success": False, "error": f"Unsupported action '{action}'."}
        return handler(**kwargs)

    @database_sync_to_async
    def _remove_session(self):
        remove_session(f"lobby_{self.room_name}")

    @database_sync_to_async
    def get_game_state(self):
        game_name = f"lobby_{self.room_name}"
        manager = get_session(game_name)
        if manager:
            return manager.serialize_state()

        game = Game.objects.filter(name=game_name).first()
        if not game:
            return None

        players = game.players.select_related("current_room", "current_hallway")
        player_states = []
        for player in players:
            location = (
                player.current_room.name
                if player.current_room
                else player.current_hallway.name
                if player.current_hallway
                else None
            )
            player_states.append(
                {
                    "id": player.id,
                    "name": player.character_name,
                    "location": location,
                    "location_type": (
                        "room"
                        if player.current_room
                        else "hallway"
                        if player.current_hallway
                        else None
                    ),
                    "eliminated": player.is_eliminated,
                    "arrived_via_suggestion": False,
                }
            )

        current = None
        if game.current_player:
            current = {
                "id": game.current_player.id,
                "name": game.current_player.character_name,
            }

        return {
            "players": player_states,
            "current_player": current,
            "turn_state": {
                "has_moved": False,
                "made_suggestion": False,
                "has_accused": False,
            },
            "is_completed": game.is_completed,
            "is_active": game.is_active,
            "is_over": game.is_completed and not game.is_active,
            "winner": None,
        }


class PlayerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        player = await self._create_player()
        self.player_id = player.id
        await self.send_json(
            {"type": "player_created", "player_id": self.player_id, "name": player.name}
        )

    async def disconnect(self, close_code):
        if hasattr(self, "player_id"):
            await self._delete_player()

    async def receive(self, text_data):
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            return
        if payload.get("type") == "ping":
            await self.send_json({"type": "pong"})

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload))

    @database_sync_to_async
    def _create_player(self):
        return LobbyPlayer.objects.create()

    @database_sync_to_async
    def _delete_player(self):
        LobbyPlayer.objects.filter(id=self.player_id).delete()