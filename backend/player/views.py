from django.shortcuts import render
from django.http import JsonResponse
from .models import Player

# Create your views here.
def player(request):
    player = Player()
    player.save()
    return JsonResponse({
        "message": "Player endpoint reached, creating new player",
        "player": player.name
    })