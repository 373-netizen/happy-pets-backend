# breeding/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import BreedingMatch, BreedingChatMessage
from pets.models import Pet
from django.db import models

User = get_user_model()


class BreedingChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.room_group_name = f'breeding_chat_{self.match_id}'
        self.user = self.scope['user']
        
        # Verify user has access to this match
        has_access = await self.verify_match_access()
        
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
            'type': 'connection',
            'message': 'Connected to chat',
            'match_id': self.match_id
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'message':
                message_text = data.get('message', '').strip()
                
                if not message_text:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Message cannot be empty'
                    }))
                    return
                
                # Save message to database
                message = await self.save_message(message_text)
                
                if message:
                    # Get other user for notification check
                    other_user = await self.get_other_user()
                    
                    # Broadcast message to room group
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': {
                                'id': message['id'],
                                'sender_id': message['sender_id'],
                                'sender_name': message['sender_name'],
                                'message': message['message'],
                                'created_at': message['created_at'],
                                'read': message['read'],
                                'is_own_message': False
                            },
                            'sender_id': self.user.id,
                            'other_user_id': other_user['id'] if other_user else None,
                            'push_enabled': other_user['push_enabled'] if other_user else False
                        }
                    )
            
            elif message_type == 'typing':
                is_typing = data.get('is_typing', False)
                
                # Broadcast typing status to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_status',
                        'is_typing': is_typing,
                        'user_id': self.user.id
                    }
                )
            
            elif message_type == 'read':
                # Mark messages as read
                await self.mark_messages_read()
                
                # Notify other user
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'read_receipt',
                        'user_id': self.user.id
                    }
                )
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def chat_message(self, event):
        message = event['message']
        sender_id = event.get('sender_id')
        
        # Mark if this is the user's own message
        message['is_own_message'] = (sender_id == self.user.id)
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message
        }))
    
    async def typing_status(self, event):
        user_id = event.get('user_id')
        
        # Don't send typing status to the sender
        if user_id != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'is_typing': event['is_typing']
            }))
    
    async def read_receipt(self, event):
        user_id = event.get('user_id')
        
        # Send read receipt to sender
        if user_id != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'read'
            }))
    
    @database_sync_to_async
    def verify_match_access(self):
        """Verify user has access to this match"""
        try:
            user_pets = Pet.objects.filter(owner=self.user)
            match = BreedingMatch.objects.filter(
                id=self.match_id
            ).filter(
                models.Q(pet1__in=user_pets) | models.Q(pet2__in=user_pets)
            ).first()
            
            return match is not None
        except Exception as e:
            print(f"Error verifying match access: {e}")
            return False
    
    @database_sync_to_async
    def save_message(self, message_text):
        """Save message to database"""
        try:
            from django.db.models import Q
            
            user_pets = Pet.objects.filter(owner=self.user)
            match = BreedingMatch.objects.get(
                Q(id=self.match_id),
                Q(pet1__in=user_pets) | Q(pet2__in=user_pets)
            )
            
            message = BreedingChatMessage.objects.create(
                match=match,
                sender=self.user,
                message=message_text
            )
            
            return {
                'id': message.id,
                'sender_id': message.sender.id,
                'sender_name': message.sender.get_full_name() or message.sender.username,
                'message': message.message,
                'created_at': message.created_at.isoformat(),
                'read': message.read
            }
        except Exception as e:
            print(f"Error saving message: {e}")
            return None
    
    @database_sync_to_async
    def get_other_user(self):
        """Get the other user in the match"""
        try:
            from django.db.models import Q
            
            user_pets = Pet.objects.filter(owner=self.user)
            match = BreedingMatch.objects.select_related('pet1__owner', 'pet2__owner').get(
                Q(id=self.match_id),
                Q(pet1__in=user_pets) | Q(pet2__in=user_pets)
            )
            
            # Get other user
            if match.pet1.owner == self.user:
                other_user = match.pet2.owner
            else:
                other_user = match.pet1.owner
            
            return {
                'id': other_user.id,
                'username': other_user.username,
                'push_enabled': getattr(other_user, 'push_notifications_enabled', False)
            }
        except Exception as e:
            print(f"Error getting other user: {e}")
            return None
    
    @database_sync_to_async
    def mark_messages_read(self):
        """Mark all unread messages in this match as read"""
        try:
            from django.db.models import Q
            
            user_pets = Pet.objects.filter(owner=self.user)
            match = BreedingMatch.objects.get(
                Q(id=self.match_id),
                Q(pet1__in=user_pets) | Q(pet2__in=user_pets)
            )
            
            BreedingChatMessage.objects.filter(
                match=match,
                read=False
            ).exclude(sender=self.user).update(read=True)
            
            return True
        except Exception as e:
            print(f"Error marking messages as read: {e}")
            return False


# Make sure to add the import at the top
from django.db import models