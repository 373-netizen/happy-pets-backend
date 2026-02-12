# breeding/middleware.py (Updated version)
"""
WebSocket authentication middleware to support JWT token authentication
Works alongside Django's AuthMiddlewareStack
"""
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_string):
    """Get user from JWT token"""
    try:
        # Validate and decode the token
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']
        
        # Get the user
        user = User.objects.get(id=user_id)
        return user
    except (TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens
    This will override the user if a token is provided in the query string
    """
    
    async def __call__(self, scope, receive, send):
        # Parse query string for token
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        # If token is provided, authenticate with it
        # Otherwise, keep the user from AuthMiddlewareStack (session-based auth)
        if token:
            scope['user'] = await get_user_from_token(token)
        # If no token and user is AnonymousUser, leave it as is
        # This allows both token-based (breeding chat) and session-based (community chat) to work
        
        return await super().__call__(scope, receive, send)


def TokenAuthMiddlewareStack(inner):
    """
    Wrapper function to apply TokenAuthMiddleware
    """
    return TokenAuthMiddleware(inner)