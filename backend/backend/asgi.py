"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

# Set the Django settings module path before any other imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import game.routing

# Initialize Django ASGI application early to ensure the app is loaded
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,  # regular HTTP requests go here
    "websocket": AuthMiddlewareStack(  # WebSockets go through this middleware
        URLRouter(game.routing.websocket_urlpatterns)  # connect WS routes
    ),
})
