# breeding/views.py
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Max
from pets.models import Pet
from .models import BreedingSwipe, BreedingMatch, BreedingChatMessage


# ==================== AVAILABLE PETS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_pets(request):
    """Get pets available for breeding for a specific user pet"""
    user_pet_id = request.GET.get('user_pet_id')
    
    if not user_pet_id:
        return Response({
            'success': False,
            'error': 'user_pet_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user_pet = Pet.objects.get(id=user_pet_id, owner=request.user)
    except Pet.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Pet not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get pets user has already swiped on
    already_swiped = BreedingSwipe.objects.filter(
        user_pet=user_pet
    ).values_list('target_pet_id', flat=True)
    
    # Get available pets (excluding own pets, already swiped, and inactive)
    available = Pet.objects.filter(
        is_available_for_breeding=True,
        is_active=True
    ).exclude(
        owner=request.user
    ).exclude(
        id__in=already_swiped
    ).exclude(
        id=user_pet_id
    )
    
    # Optionally filter by species/breed compatibility
    if user_pet.species:
        available = available.filter(species=user_pet.species)
    
    pets_data = [{
        'id': pet.id,
        'name': pet.name,
        'breed': pet.breed,
        'species': pet.species,
        'age': pet.age,
        'gender': pet.gender,
        'weight': pet.weight,
        'color': pet.color,
        'photo': request.build_absolute_uri(pet.photo.url) if pet.photo else None,
        'owner_name': pet.owner.get_full_name() or pet.owner.username,
    } for pet in available]
    
    return Response({
        'success': True,
        'pets': pets_data
    })


# ==================== SWIPE ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def swipe(request):
    """Handle swipe action (like/pass)"""
    user_pet_id = request.data.get('user_pet_id')
    target_pet_id = request.data.get('target_pet_id')
    action = request.data.get('action')
    
    if not all([user_pet_id, target_pet_id, action]):
        return Response({
            'success': False,
            'error': 'Missing required fields'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if action not in ['like', 'pass']:
        return Response({
            'success': False,
            'error': 'Invalid action'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user_pet = Pet.objects.get(id=user_pet_id, owner=request.user)
        target_pet = Pet.objects.get(id=target_pet_id, is_available_for_breeding=True)
    except Pet.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Pet not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Create swipe
    swipe, created = BreedingSwipe.objects.get_or_create(
        user_pet=user_pet,
        target_pet=target_pet,
        defaults={'action': action}
    )
    
    if not created:
        swipe.action = action
        swipe.save()
    
    # Check for match if action is 'like'
    matched = False
    match_data = None
    
    if action == 'like':
        # Check if target pet has also liked user pet
        reverse_like = BreedingSwipe.objects.filter(
            user_pet=target_pet,
            target_pet=user_pet,
            action='like'
        ).exists()
        
        if reverse_like:
            # Create match (ensure proper ordering)
            pet1, pet2 = (user_pet, target_pet) if user_pet.id < target_pet.id else (target_pet, user_pet)
            
            match, match_created = BreedingMatch.objects.get_or_create(
                pet1=pet1,
                pet2=pet2
            )
            
            matched = True
            match_data = {
                'id': match.id,
                'pet_name': target_pet.name,
                'breed': target_pet.breed,
                'age': target_pet.age,
                'photo': request.build_absolute_uri(target_pet.photo.url) if target_pet.photo else None,
                'owner_name': target_pet.owner.get_full_name() or target_pet.owner.username,
                'user_pet_photo': request.build_absolute_uri(user_pet.photo.url) if user_pet.photo else None,
            }
    
    return Response({
        'success': True,
        'action': action,
        'matched': matched,
        'match_data': match_data
    })


# ==================== MATCHES ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def matches(request):
    """Get all matches for current user"""
    user_pets = Pet.objects.filter(owner=request.user)
    
    # Get all matches where user's pets are involved
    user_matches = BreedingMatch.objects.filter(
        Q(pet1__in=user_pets) | Q(pet2__in=user_pets)
    ).select_related('pet1', 'pet2', 'pet1__owner', 'pet2__owner').annotate(
        message_count=Count('messages'),
        last_message_time=Max('messages__created_at')
    )
    
    matches_data = []
    for match in user_matches:
        # Determine which pet is the user's and which is the match
        if match.pet1.owner == request.user:
            user_pet = match.pet1
            other_pet = match.pet2
        else:
            user_pet = match.pet2
            other_pet = match.pet1
        
        # Get unread message count
        unread_count = BreedingChatMessage.objects.filter(
            match=match,
            read=False
        ).exclude(sender=request.user).count()
        
        # Get last message
        last_message_obj = match.messages.order_by('-created_at').first()
        last_message = last_message_obj.message if last_message_obj else None
        
        matches_data.append({
            'id': match.id,
            'pet_name': other_pet.name,
            'breed': other_pet.breed,
            'species': other_pet.species,
            'age': other_pet.age,
            'gender': other_pet.gender,
            'pet_photo': request.build_absolute_uri(other_pet.photo.url) if other_pet.photo else None,
            'owner_name': other_pet.owner.get_full_name() or other_pet.owner.username,
            'user_pet_name': user_pet.name,
            'user_pet_photo': request.build_absolute_uri(user_pet.photo.url) if user_pet.photo else None,
            'matched_at': match.created_at.isoformat(),
            'unread_count': unread_count,
            'last_message': last_message,
            'last_message_time': match.last_message_time.isoformat() if match.last_message_time else None,
            'distance': None  # Add distance calculation if you have location data
        })
    
    return Response({
        'success': True,
        'matches': matches_data
    })


# ==================== CHAT MESSAGES ====================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def chat(request, match_id):
    """Get or send chat messages for a match"""
    try:
        # Verify user has access to this match
        user_pets = Pet.objects.filter(owner=request.user)
        match = BreedingMatch.objects.get(
            Q(id=match_id),
            Q(pet1__in=user_pets) | Q(pet2__in=user_pets)
        )
    except BreedingMatch.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Match not found or access denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        # Get all messages for this match
        messages = BreedingChatMessage.objects.filter(match=match).select_related('sender')
        
        messages_data = [{
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_name': msg.sender.get_full_name() or msg.sender.username,
            'message': msg.message,
            'created_at': msg.created_at.isoformat(),
            'read': msg.read,
            'is_own_message': msg.sender == request.user
        } for msg in messages]
        
        # Mark messages as read
        BreedingChatMessage.objects.filter(
            match=match,
            read=False
        ).exclude(sender=request.user).update(read=True)
        
        return Response({
            'success': True,
            'messages': messages_data
        })
    
    elif request.method == 'POST':
        # Send a new message
        message_text = request.data.get('message', '').strip()
        
        if not message_text:
            return Response({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        message = BreedingChatMessage.objects.create(
            match=match,
            sender=request.user,
            message=message_text
        )
        
        return Response({
            'success': True,
            'message': {
                'id': message.id,
                'sender_id': message.sender.id,
                'sender_name': message.sender.get_full_name() or message.sender.username,
                'message': message.message,
                'created_at': message.created_at.isoformat(),
                'read': message.read,
                'is_own_message': True
            }
        }, status=status.HTTP_201_CREATED)


# ==================== MARK AS READ ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_read(request, match_id):
    """Mark all messages in a match as read"""
    try:
        user_pets = Pet.objects.filter(owner=request.user)
        match = BreedingMatch.objects.get(
            Q(id=match_id),
            Q(pet1__in=user_pets) | Q(pet2__in=user_pets)
        )
    except BreedingMatch.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Match not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    updated = BreedingChatMessage.objects.filter(
        match=match,
        read=False
    ).exclude(sender=request.user).update(read=True)
    
    return Response({
        'success': True,
        'marked_read': updated
    })


# ==================== UNMATCH ====================
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unmatch(request, match_id):
    """Delete a match and all associated messages"""
    try:
        user_pets = Pet.objects.filter(owner=request.user)
        match = BreedingMatch.objects.get(
            Q(id=match_id),
            Q(pet1__in=user_pets) | Q(pet2__in=user_pets)
        )
    except BreedingMatch.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Match not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    match.delete()
    
    return Response({
        'success': True,
        'message': 'Unmatched successfully'
    })


# ==================== STATS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats(request):
    """Get breeding matchmaking stats for user"""
    user_pets = Pet.objects.filter(owner=request.user)
    
    # Total swipes made
    total_swipes = BreedingSwipe.objects.filter(user_pet__in=user_pets).count()
    
    # Total matches
    total_matches = BreedingMatch.objects.filter(
        Q(pet1__in=user_pets) | Q(pet2__in=user_pets)
    ).count()
    
    # Likes received
    likes_received = BreedingSwipe.objects.filter(
        target_pet__in=user_pets,
        action='like'
    ).count()
    
    return Response({
        'success': True,
        'total_swipes': total_swipes,
        'matches': total_matches,
        'likes_received': likes_received
    })


# ==================== NOTIFICATION PREFERENCES ====================
@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def notification_preferences(request):
    """
    GET: Retrieve user's notification preferences
    POST: Update user's notification preferences
    """
    try:
        if request.method == 'GET':
            # Get user's notification preference
            push_enabled = getattr(request.user, 'push_notifications_enabled', False)
            
            return Response({
                'success': True,
                'push_notifications_enabled': push_enabled,
            })
        
        elif request.method == 'POST':
            push_enabled = request.data.get('push_notifications_enabled', False)
            
            # Update preference on user model
            request.user.push_notifications_enabled = push_enabled
            request.user.save(update_fields=['push_notifications_enabled'])
            
            return Response({
                'success': True,
                'push_notifications_enabled': request.user.push_notifications_enabled,
                'message': 'Notification preferences updated'
            })
    
    except AttributeError:
        # Field doesn't exist on user model
        return Response({
            'success': False,
            'error': 'Notification preferences not supported. Please add push_notifications_enabled field to User model.'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)