#chat/views.py
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import ChatMessage, OnlineUser
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import os
from datetime import datetime

@api_view(['GET'])
@permission_classes([AllowAny])  # Allow unauthenticated access
def get_messages(request):
    """Get recent chat messages"""
    try:
        limit = int(request.GET.get('limit', 50))
        messages = ChatMessage.objects.all()[:limit]
        message_list = [msg.to_dict() for msg in reversed(messages)]
        
        return Response({
            'messages': message_list,
            'count': len(message_list)
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow unauthenticated access
def send_message(request):
    """Send a chat message (HTTP fallback)"""
    try:
        username = request.data.get('username', 'Anonymous')
        message = request.data.get('message', '')
        user_id = request.data.get('user_id')
        file_url = request.data.get('file_url')
        file_type = request.data.get('file_type')
        
        if not message and not file_url:
            return Response({
                'error': 'Message or file is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        chat_message = ChatMessage.objects.create(
            user=username,
            message=message,
            user_id=user_id,
            file_url=file_url,
            file_type=file_type
        )
        
        return Response({
            'message': chat_message.to_dict(),
            'status': 'success'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # Allow unauthenticated access
def upload_file(request):
    """
    Handle file uploads for chat (images and videos)
    """
    try:
        if 'file' not in request.FILES:
            return Response({
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        username = request.POST.get('username', 'Anonymous')
        
        # Validate file size (10MB max)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if file.size > max_size:
            return Response({
                'error': 'File size exceeds 10MB limit'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        allowed_types = {
            'image/jpeg': 'image',
            'image/jpg': 'image',
            'image/png': 'image',
            'image/gif': 'image',
            'image/webp': 'image',
            'video/mp4': 'video',
            'video/webm': 'video'
        }
        
        file_type_lower = file.content_type.lower()
        if file_type_lower not in allowed_types:
            return Response({
                'error': 'Invalid file type. Only images and videos are allowed.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Determine file type category
        file_category = allowed_types[file_type_lower]
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(file.name)[1]
        filename = f"chat_{username}_{timestamp}{file_extension}"
        
        # Save file to media/chat_uploads/
        file_path = f"chat_uploads/{filename}"
        saved_path = default_storage.save(file_path, ContentFile(file.read()))
        
        # Generate URL for the file
        file_url = request.build_absolute_uri(settings.MEDIA_URL + saved_path)
        
        print(f"✅ File uploaded: {filename}")
        print(f"📂 Path: {saved_path}")
        print(f"🔗 URL: {file_url}")
        print(f"🏷️ Type: {file_category}")
        
        return Response({
            'success': True,
            'file_url': file_url,
            'file_type': file_category,
            'filename': filename
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])  # Allow unauthenticated access
def get_online_count(request):
    """Get count of online users"""
    try:
        # Remove stale connections (older than 5 minutes)
        stale_time = timezone.now() - timezone.timedelta(minutes=5)
        OnlineUser.objects.filter(last_seen__lt=stale_time).delete()
        
        count = OnlineUser.objects.count()
        
        return Response({
            'count': count
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])  # Allow unauthenticated access (change to require auth in production)
def clear_messages(request):
    """Clear all chat messages (admin only)"""
    try:
        deleted_count = ChatMessage.objects.all().delete()[0]
        return Response({
            'status': 'success',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)