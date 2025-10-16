from django.shortcuts import render
from django.http import JsonResponse
from .models import Player
import json

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
    
def get_all_players(request):
    players = Player.objects.all()
    players_data = []
    for player in players:
        players_data.append(json.dumps({
            "player_id": player.id,
            "name": player.name,
            "position": player.position,
            "isActive": player.isActivePlayer,
            "cards": player.get_cards_list()
        }))
    return JsonResponse({"players": players_data})