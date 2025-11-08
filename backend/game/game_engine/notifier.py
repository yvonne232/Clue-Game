# game/game_engine/notifier.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class Notifier:
    """Handles broadcasting messages to console and WebSocket clients."""

    @staticmethod
    def broadcast(message, room="default"):
        print(f"[Broadcast] {message}")

        try:
            layer = get_channel_layer()
            if layer is not None:
                async_to_sync(layer.group_send)(
                    f"game_{room}",
                    {"type": "chat_message", "message": message}
                )
        except Exception:
            pass
