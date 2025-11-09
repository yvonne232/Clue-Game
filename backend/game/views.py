import time

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction, OperationalError
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Game, Player, Hallway, Solution
from .models.lobby import Lobby
from .models.lobby_player import LobbyPlayer
from .serializers import GameSerializer, PlayerSerializer, LobbySerializer
from game.game_engine.game_manager import GameManager

from rest_framework.decorators import api_view
from django.http import JsonResponse
from .models import Lobby
from .serializers import LobbySerializer

# ---------------------------
# LOBBY API VIEWS
# ---------------------------

@api_view(['POST'])
def create_player(request):
    try:
        with transaction.atomic():
            # Clear any existing players who don't have a valid session
            old_id = request.data.get('old_player_id')
            if old_id:
                try:
                    old_player = LobbyPlayer.objects.get(id=old_id)
                    # Check if the old player was in a lobby
                    old_lobby = old_player.lobby
                    
                    # Remove them from their lobby
                    if old_lobby:
                        # Remove player from the lobby
                        old_player.lobby = None
                        old_player.save()
                        
                        # Check if the lobby is now empty
                        if old_lobby.lobby_players.count() == 0:
                            old_lobby.is_active = False
                            old_lobby.save()
                            
                except LobbyPlayer.DoesNotExist:
                    pass

            # Create the new player
            player = LobbyPlayer.objects.create()
            return JsonResponse({
                'id': player.id
            })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

from django.db import transaction
from django.core.exceptions import ValidationError

@api_view(['POST'])
def create_new_lobby(request):
    print("request received to create lobby")
    try:
        name = request.data.get('name')
        player_id = request.data.get('player_id')
        
        print(f"Creating lobby with name: {name} and player_id: {player_id}")
        
        if not player_id:
            print("No player_id provided in request")
            return JsonResponse({'error': 'player_id is required'}, status=400)
            
        if not name:
            print("No name provided in request")
            return JsonResponse({'error': 'name is required'}, status=400)
        
        with transaction.atomic():
            try:
                # First, get the player and ensure they're not in another lobby
                print(f"Looking up player with id: {player_id}")
                player = LobbyPlayer.objects.get(id=player_id)
                print(f"Found player: {player.id}")
            except LobbyPlayer.DoesNotExist:
                print(f"Player with id {player_id} not found in database")
                return JsonResponse({'error': 'Player not found'}, status=404)
            
            if player.lobby is not None:
                print(f"Player {player_id} is already in lobby {player.lobby.id}")
                return JsonResponse({
                    'error': 'Player is already in another lobby'
                }, status=400)
            
            # Create the lobby
            print(f"Creating new lobby with name: {name}")
            lobby = Lobby.objects.create(name=name)
            print(f"Created lobby with id: {lobby.id}")
            
            # Add the player to the lobby
            print(f"Adding player {player_id} to lobby {lobby.id}")
            player.lobby = lobby
            player.save()
            
            # Re-fetch the lobby with players
            lobby = Lobby.objects.prefetch_related('lobby_players').get(id=lobby.id)
            print(f"Player count: {lobby.lobby_players.count()}")
            print(f"Players: {list(lobby.lobby_players.all().values('id', 'lobby_id'))}")
            
            serializer = LobbySerializer(lobby)
            serialized_data = serializer.data
            print(f"Serialized data: {serialized_data}")
            
            # Broadcast update to all connected clients
            # broadcast_lobby_update()
            
            return JsonResponse(serialized_data)
    except LobbyPlayer.DoesNotExist:
        return JsonResponse({'error': 'Player not found'}, status=404)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@api_view(['GET'])
# def broadcast_lobby_update():
#     """Helper function to broadcast lobby updates to all connected clients"""
#     try:
#         channel_layer = get_channel_layer()
#         lobbies = Lobby.objects.filter(is_active=True).prefetch_related('lobby_players')
#         serializer = LobbySerializer(lobbies, many=True)
#         lobby_data = serializer.data
        
#         print(f"Broadcasting lobby update: {lobby_data}")
        
#         async_to_sync(channel_layer.group_send)(
#             "lobbies",
#             {
#                 "type": "send_lobby_update",
#             }
#         )
#     except Exception as e:
#         print(f"Error broadcasting lobby update: {e}")

def list_lobbies(request):
    print("Fetching active lobbies")
    with transaction.atomic():
        # Clean up any lobbies that have only disconnected players
        lobbies = Lobby.objects.filter(is_active=True).prefetch_related('lobby_players')
        for lobby in lobbies:
            # Check if any players in this lobby are still connected
            has_active_players = False
            current_player_ids = lobby.lobby_players.values_list('id', flat=True)
            
            if not current_player_ids:
                # No players at all, deactivate lobby
                lobby.is_active = False
                lobby.save()
                continue
                
            if current_player_ids:
                # If there are players, lobby stays active
                has_active_players = True
            
            if not has_active_players:
                lobby.is_active = False
                lobby.save()
        
        # Now get the final list of active lobbies
        lobbies = Lobby.objects.filter(is_active=True).prefetch_related('lobby_players')
        
        # Debug info
        for lobby in lobbies:
            print(f"Lobby {lobby.id}:")
            print(f"  Name: {lobby.name}")
            print(f"  Player count: {lobby.lobby_players.count()}")
            print(f"  Players: {list(lobby.lobby_players.all().values('id', 'lobby_id'))}")
        
        serializer = LobbySerializer(lobbies, many=True)
        response_data = {"lobbies": serializer.data}
        print(f"Response data: {response_data}")
        
        # Broadcast updates to all connected clients
        # broadcast_lobby_update()
        
        return JsonResponse(response_data)

@api_view(['POST'])
def join_lobby(request, lobby_id):
    print(f"Attempting to join lobby {lobby_id}")
    print(f"Request data: {request.data}")
    
    try:
        with transaction.atomic():
            try:
                lobby = Lobby.objects.get(id=lobby_id)
                print(f"Found lobby: {lobby}")
            except Lobby.DoesNotExist:
                print(f"Lobby {lobby_id} not found")
                return JsonResponse({
                    'error': f'Lobby {lobby_id} not found'
                }, status=404)
            
            player_id = request.data.get('player_id')
            if not player_id:
                print("No player_id provided")
                return JsonResponse({
                    'error': 'player_id is required'
                }, status=400)
            
            try:
                # Get the player and check if they're already in a lobby
                player = LobbyPlayer.objects.get(id=player_id)
                print(f"Found player: {player}")
            except LobbyPlayer.DoesNotExist:
                print(f"Player {player_id} not found")
                return JsonResponse({
                    'error': f'Player {player_id} not found'
                }, status=404)
            
            if player.lobby is not None:
                # If they're trying to join the same lobby they're already in, just return the lobby data
                if player.lobby.id == lobby.id:
                    print(f"Player {player_id} is rejoining their previous lobby {lobby.id}")
                    serializer = LobbySerializer(lobby)
                    return JsonResponse(serializer.data)
                else:
                    print(f"Player {player_id} is already in another lobby {player.lobby.id}")
                    return JsonResponse({
                        'error': 'Player is already in another lobby'
                    }, status=400)
            
            # Check if lobby is full
            current_count = lobby.lobby_players.count()
            print(f"Current players in lobby: {current_count}")
            if current_count >= 6:
                print(f"Lobby is full ({current_count}/6)")
                return JsonResponse({
                    'error': 'Lobby is full'
                }, status=400)
            
            # Add player to lobby
            player.lobby = lobby
            player.save()
            print(f"Added player {player_id} to lobby {lobby_id}")
            
            # Re-fetch the lobby with players
            lobby = Lobby.objects.prefetch_related('lobby_players').get(id=lobby.id)
            print(f"Player count after join: {lobby.lobby_players.count()}")
            print(f"Players in lobby: {list(lobby.lobby_players.all().values('id', 'lobby_id'))}")
            
            serializer = LobbySerializer(lobby)
            response_data = serializer.data
            print(f"Response data: {response_data}")
            
            # Broadcast update to all connected clients
            # broadcast_lobby_update()
            
            return JsonResponse(response_data)
    except Lobby.DoesNotExist:
        return JsonResponse({'error': 'Lobby not found'}, status=404)
    except LobbyPlayer.DoesNotExist:
        return JsonResponse({'error': 'Player not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@api_view(['POST'])
def leave_lobby(request, lobby_id):
    try:
        with transaction.atomic():
            lobby = Lobby.objects.get(id=lobby_id)
            player_id = request.data.get('player_id')
            
            # Get the player and remove them from the lobby
            player = LobbyPlayer.objects.get(id=player_id)
            if player.lobby_id != lobby.id:
                return JsonResponse({
                    'error': 'Player is not in this lobby'
                }, status=400)
            
            # Remove player from lobby
            player.lobby = None
            player.save()
            
            # Re-fetch the lobby
            lobby.refresh_from_db()
            
            # Check if lobby is empty
            if lobby.lobby_players.count() == 0:
                lobby.is_active = False
                lobby.save()
                return JsonResponse({'message': 'Lobby closed', 'success': True})
            
            serializer = LobbySerializer(lobby)
            response_data = {'success': True, **serializer.data}
            
            # Broadcast update to all connected clients
            # broadcast_lobby_update()
            
            return JsonResponse(response_data)
    except Lobby.DoesNotExist:
        return JsonResponse({'error': 'Lobby not found'}, status=404)
    except LobbyPlayer.DoesNotExist:
        return JsonResponse({'error': 'Player not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

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
