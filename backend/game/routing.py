from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/game/(?P<room_name>\w+)/$", consumers.GameConsumer.as_asgi()),
    re_path(r"ws/player/$", consumers.PlayerConsumer.as_asgi()),
    # re_path(r"ws/lobbies/$", consumers.LobbyConsumer.as_asgi()),
]