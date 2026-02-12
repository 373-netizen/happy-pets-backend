# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "global_chat"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        print(f"✅ WebSocket connected: {self.channel_name}")
        
        # Send last messages
        last_messages = await self.get_last_messages()
        await self.send(text_data=json.dumps({
            "type": "message_history",
            "messages": last_messages
        }))
        
        # Send user count update
        await self.update_user_count()

    async def disconnect(self, close_code):
        print(f"❌ WebSocket disconnected: {self.channel_name}, code: {close_code}")
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Update user count
        await self.update_user_count()

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get("type")
            
            # Handle different message types
            if message_type == "typing":
                # Broadcast typing indicator
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "typing_indicator",
                        "username": data.get("username"),
                        "is_typing": data.get("is_typing", False)
                    }
                )
                return
            
            if message_type == "get_history":
                # Send history again if requested
                last_messages = await self.get_last_messages()
                await self.send(text_data=json.dumps({
                    "type": "message_history",
                    "messages": last_messages
                }))
                return
            
            # Handle regular message
            message = data.get("message", "").strip()
            username = data.get("username", "Anonymous").strip()
            file_url = data.get("file_url")
            file_type = data.get("file_type")

            if not message and not file_url:
                return

            print(f"📨 Received: {username}: {message}")

            # Save message to database
            msg_obj = await self.save_message(username, message, file_url, file_type)

            # Broadcast to ALL users in the group (including sender)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": {
                        "id": msg_obj.id,
                        "username": username,
                        "message": message,
                        "timestamp": msg_obj.timestamp.isoformat(),
                        "file_url": file_url,
                        "file_type": file_type,
                    }
                }
            )
            
            print(f"✅ Message broadcasted to group")
            
        except Exception as e:
            print(f"❌ Error in receive: {e}")
            import traceback
            traceback.print_exc()
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Failed to process message"
            }))

    async def chat_message(self, event):
        """Handler for chat_message events from channel layer"""
        print(f"📤 Sending message to client: {event['message']}")
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": event["message"]
        }))

    async def typing_indicator(self, event):
        """Handler for typing indicator events"""
        await self.send(text_data=json.dumps({
            "type": "typing",
            "username": event["username"],
            "is_typing": event["is_typing"]
        }))

    async def update_user_count(self):
        """Send updated user count to all clients"""
        # Note: This is a simple implementation
        # For production, you'd want to track actual connections
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_count_update",
                "count": 1  # Placeholder - implement proper counting
            }
        )

    async def user_count_update(self, event):
        """Handler for user count updates"""
        await self.send(text_data=json.dumps({
            "type": "user_count",
            "count": event["count"]
        }))

    @database_sync_to_async
    def get_last_messages(self):
        """Fetch last 50 messages from database"""
        messages = ChatMessage.objects.order_by('-timestamp')[:50]
        messages = list(reversed(messages))
        
        return [
            {
                "id": m.id,
                "username": m.user,
                "message": m.message,
                "timestamp": m.timestamp.isoformat(),
                "file_url": getattr(m, 'file_url', None),
                "file_type": getattr(m, 'file_type', None),
            }
            for m in messages
        ]

    @database_sync_to_async
    def save_message(self, username, message, file_url=None, file_type=None):
        """Save message to database"""
        msg_data = {
            'user': username,
            'message': message,
        }
        
        # Add file fields if they exist in your model
        if hasattr(ChatMessage, 'file_url'):
            msg_data['file_url'] = file_url
        if hasattr(ChatMessage, 'file_type'):
            msg_data['file_type'] = file_type
            
        return ChatMessage.objects.create(**msg_data)