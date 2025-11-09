import time

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction, OperationalError

from .models import Game, Player, Hallway, Solution
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
    MAX_DB_RETRIES = 3
    RETRY_SLEEP_SECONDS = 0.15
    TRANSIENT_VALUEERROR = "Save with update_fields did not affect any rows"

    def post(self, request, *args, **kwargs):
        game_name = request.data.get("game_name", "default")
        rounds = int(request.data.get("rounds", 20))

        summary = None
        for attempt in range(self.MAX_DB_RETRIES):
            try:
                manager = GameManager(game_name=game_name)
                summary = manager.run_game(max_rounds=rounds)
                break
            except OperationalError as exc:
                if "locked" in str(exc).lower() and attempt < self.MAX_DB_RETRIES - 1:
                    time.sleep(self.RETRY_SLEEP_SECONDS)
                    continue
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError as exc:
                if (
                    self.TRANSIENT_VALUEERROR in str(exc)
                    and attempt < self.MAX_DB_RETRIES - 1
                ):
                    time.sleep(self.RETRY_SLEEP_SECONDS)
                    continue
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if summary is None:
            return Response(
                {"detail": "Simulation could not be completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(summary, status=status.HTTP_200_OK)


class GameResetView(APIView):
    """POST to reset a game session back to its initial state."""

    permission_classes = [AllowAny]
    MAX_DB_RETRIES = 3
    RETRY_SLEEP_SECONDS = 0.15
    TRANSIENT_VALUEERROR = GameSimulationView.TRANSIENT_VALUEERROR

    def post(self, request, *args, **kwargs):
        game_name = request.data.get("game_name", "default")

        manager = None
        for attempt in range(self.MAX_DB_RETRIES):
            try:
                with transaction.atomic():
                    # Clear occupancy before recreating players
                    Hallway.objects.update(is_occupied=False)

                    # Remove existing game state (cascades to players)
                    Game.objects.filter(name=game_name).delete()
                    Solution.objects.all().delete()

                    manager = GameManager(game_name=game_name)
                break
            except OperationalError as exc:
                if "locked" in str(exc).lower() and attempt < self.MAX_DB_RETRIES - 1:
                    time.sleep(self.RETRY_SLEEP_SECONDS)
                    continue
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError as exc:
                if (
                    self.TRANSIENT_VALUEERROR in str(exc)
                    and attempt < self.MAX_DB_RETRIES - 1
                ):
                    time.sleep(self.RETRY_SLEEP_SECONDS)
                    continue
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if manager is None:
            return Response(
                {"detail": "Reset could not be completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "status": "reset",
                "game": game_name,
                "players": [p["name"] for p in manager.players],
            },
            status=status.HTTP_200_OK,
        )


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
