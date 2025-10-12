from django.shortcuts import render
from django.http import JsonResponse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def hello_world(request):
    return JsonResponse({"message": "Hello from Django API!"})

def broadcast_message(request):
    """Trigger a WebSocket broadcast from a REST API call."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "hello_room",  # all clients in this group will get this
        {
            "type": "broadcast",
            "text": "Hello from Django REST API via WebSocket!"
        }
    )
    return JsonResponse({"status": "Message broadcasted"})