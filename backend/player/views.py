from django.shortcuts import render
from django.http import JsonResponse
from .models import Player
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# Create your views here.
def player(request):
    player = Player()
    player.save()
    return JsonResponse({
        "message": "Player endpoint reached, creating new player",
        "player": player.id,
        "player_name": player.name
    })

def get_player_by_id(request, player_id):
    try:
        player = Player.objects.get(id=player_id)
        return JsonResponse({
            "player": player.id,
            "name": player.name,
            "position": player.position,
            "isActive": player.isActivePlayer,
            "cards": player.get_cards_list()
        })
    except Player.DoesNotExist:
        return JsonResponse({"error": "Player not found"}, status=404)

@csrf_exempt
@require_http_methods(["POST"])  
def get_all_players(request):
    if request.method == 'POST':
        # Get all players
        players = Player.objects.all()
        players_data = []
        for player in players:
            players_data.append(json.dumps({
                "player_id": player.id,
                "name": player.name,
                "position": player.position,
                "isActive": player.isActivePlayer
            }))

        # Broadcast to all connected clients
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "game_room",
            {
                "type": "broadcast_players",
                "players": players_data
            }
        )
        response = JsonResponse({"message": "Player list broadcast initiated"})
        response["Access-Control-Allow-Origin"] = "http://localhost:5173"
        return response
    return JsonResponse({"error": "Method not allowed"}, status=405)