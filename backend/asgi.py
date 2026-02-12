# backend/asgi.py
"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Initialize Django ASGI application early to ensure apps are loaded
django_asgi_app = get_asgi_application()

# Import routing patterns AFTER Django initialization
import chat.routing
import breeding.routing
import doctors.routing  
from breeding.middleware import TokenAuthMiddleware

# Combine all WebSocket URL patterns
all_websocket_patterns = (
    chat.routing.websocket_urlpatterns + 
    breeding.routing.websocket_urlpatterns +
    doctors.routing.websocket_urlpatterns 
)

# Apply both auth middlewares: TokenAuth wraps AuthMiddleware
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        TokenAuthMiddleware(
            AuthMiddlewareStack(
                URLRouter(all_websocket_patterns)
            )
        )
    ),
})