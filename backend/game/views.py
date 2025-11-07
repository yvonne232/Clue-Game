from rest_framework import generics
from .models import Game, Player
from .serializers import GameSerializer, PlayerSerializer


# ---------------------------
# GAME API VIEWS
# ---------------------------

class GameListCreateView(generics.ListCreateAPIView):
    """GET all games or POST a new one."""
    queryset = Game.objects.all()
    serializer_class = GameSerializer


class GameRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """GET, PUT, PATCH, DELETE a specific game."""
    queryset = Game.objects.all()
    serializer_class = GameSerializer


# ---------------------------
# PLAYER API VIEWS
# ---------------------------

class PlayerListCreateView(generics.ListCreateAPIView):
    """GET all players or POST a new one."""
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer


class PlayerRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """GET, PUT, PATCH, DELETE a specific player."""
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer
