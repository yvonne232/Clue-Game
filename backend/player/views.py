from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.
def player(request):
    return JsonResponse({
        "message": "Player endpoint reached",
    })