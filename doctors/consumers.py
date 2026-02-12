# doctors/consumers.py - COMPLETE WITH IMAGE SUPPORT

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Consultation, ChatMessage

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection"""
        self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
        self.room_group_name = f'chat_{self.consultation_id}'
        
        # Get user from scope (set by JWTAuthMiddleware)
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        # Verify user has access to this consultation
        has_access = await self.verify_consultation_access()
        if not has_access:
            await self.close(code=4003)
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to chat'
        }))
        
        print(f"✅ User {self.user.id} connected to consultation {self.consultation_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            print(f"❌ User disconnected from consultation {self.consultation_id}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            print(f"Error in receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def handle_chat_message(self, data):
        """Handle chat message - save to DB and broadcast"""
        message_text = data.get('message', '').strip()
        image_url = data.get('image')  # Image URL if uploaded via REST API
        
        # For text-only messages, save to database
        # For messages with images, they're already saved by REST API
        message_id = None
        created_at = None
        
        if not image_url and message_text:
            # Save text-only message to database
            message = await self.save_message(message_text, None)
            message_id = message.id
            created_at = message.created_at.isoformat()
        elif image_url:
            # Image messages are already saved via REST API
            # Just use the provided data for broadcasting
            created_at = data.get('created_at')
        
        # Broadcast to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': message_id,
                'message': message_text,
                'image': image_url,
                'sender_id': self.user.id,
                'sender_name': self.user.get_full_name() or self.user.username,
                'created_at': created_at
            }
        )
    
    async def handle_typing(self, data):
        """Handle typing indicator"""
        is_typing = data.get('is_typing', False)
        
        # Broadcast typing status to room (except sender)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name() or self.user.username,
                'is_typing': is_typing,
                'sender_channel': self.channel_name
            }
        )
    
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event.get('message_id'),
            'message': event.get('message'),
            'image': event.get('image'),
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'created_at': event.get('created_at')
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket (except to sender)"""
        # Don't send typing indicator back to the person who's typing
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing']
            }))
    
    @database_sync_to_async
    def verify_consultation_access(self):
        """Verify user has access to this consultation"""
        try:
            consultation = Consultation.objects.select_related('doctor__user').get(
                id=self.consultation_id
            )
            
            # User must be either the patient or the doctor
            return (
                consultation.user == self.user or 
                consultation.doctor.user == self.user
            )
        except Consultation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, message_text, image_path=None):
        """Save message to database"""
        consultation = Consultation.objects.get(id=self.consultation_id)
        
        message = ChatMessage.objects.create(
            consultation=consultation,
            sender=self.user,
            message=message_text,
            image=image_path
        )
        
        return message