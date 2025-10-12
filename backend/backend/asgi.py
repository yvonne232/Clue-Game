"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import realtime.routing  # Import WebSocket routes

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Default Django ASGI app (normal HTTP)
django_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_app,  # regular HTTP requests go here
    "websocket": AuthMiddlewareStack(  # WebSockets go through this middleware
        URLRouter(realtime.routing.websocket_urlpatterns)  # connect WS routes
    ),
})
