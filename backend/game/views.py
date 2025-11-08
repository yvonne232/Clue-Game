from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Game, Player
from .serializers import GameSerializer, PlayerSerializer
from game.game_engine.game_manager import GameManager


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


class GameSimulationView(APIView):
    """POST to trigger a full simulation and stream output over WebSocket."""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        game_name = request.data.get("game_name", "default")
        rounds = int(request.data.get("rounds", 20))

        try:
            manager = GameManager(game_name=game_name)
            summary = manager.run_game(max_rounds=rounds)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(summary, status=status.HTTP_200_OK)


class GameStateView(APIView):
    """GET the latest persisted state for a game."""

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        game_name = request.query_params.get("game_name", "default")
        try:
            game = Game.objects.get(name=game_name)
        except Game.DoesNotExist:
            return Response(
                {"detail": f"Game '{game_name}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        players = game.players.select_related("character_card", "current_room")
        payload = []
        for player in players:
            location = player.current_room.name if player.current_room else "Hallway"
            payload.append(
                {
                    "id": player.id,
                    "character": player.character_card.name if player.character_card else None,
                    "location": location,
                    "eliminated": player.is_eliminated,
                }
            )

        return Response(
            {
                "game": game.name,
                "is_active": game.is_active,
                "is_completed": game.is_completed,
                "players": payload,
            },
            status=status.HTTP_200_OK,
        )
