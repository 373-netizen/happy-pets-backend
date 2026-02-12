# doctors/views.py - WITH ENHANCED IMAGE HANDLING

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
import stripe
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Sum, Count, Avg
from PIL import Image
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import (
    DoctorProfile, DoctorAvailability, Consultation,
    ChatMessage, ConsultationNote, DoctorReview,
    FavoriteDoctor, QuickReply, DoctorEarnings
)
from .serializers import *

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


class DoctorProfileViewSet(viewsets.ModelViewSet):
    queryset = DoctorProfile.objects.filter(status='approved')
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['specialization', 'city', 'state', 'is_online', 'is_accepting_consultations']
    search_fields = ['user__first_name', 'user__last_name', 'bio', 'specialization']
    ordering_fields = ['average_rating', 'total_consultations', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DoctorProfileListSerializer
        elif self.action == 'create':
            return DoctorProfileCreateSerializer
        return DoctorProfileDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by minimum rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(average_rating__gte=float(min_rating))
        
        # Filter by price range
        max_video_fee = self.request.query_params.get('max_video_fee')
        if max_video_fee:
            queryset = queryset.filter(video_call_fee__lte=float(max_video_fee))
        
        max_chat_fee = self.request.query_params.get('max_chat_fee')
        if max_chat_fee:
            queryset = queryset.filter(chat_fee__lte=float(max_chat_fee))
        
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user's doctor profile"""
        try:
            profile = DoctorProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except DoctorProfile.DoesNotExist:
            return Response(
                {'error': 'Doctor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_online(self, request, pk=None):
        """Toggle doctor online status"""
        doctor = self.get_object()
        
        if doctor.user != request.user:
            return Response(
                {'error': 'You can only update your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        doctor.is_online = not doctor.is_online
        doctor.save()
        
        serializer = self.get_serializer(doctor)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'post'])
    def availability(self, request, pk=None):
        """Get or update doctor availability"""
        doctor = self.get_object()
        
        if request.method == 'GET':
            availabilities = doctor.availabilities.all()
            serializer = DoctorAvailabilitySerializer(availabilities, many=True)
            return Response(serializer.data)
        
        # POST - create availability
        if doctor.user != request.user:
            return Response(
                {'error': 'You can only update your own availability'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DoctorAvailabilitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(doctor=doctor)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConsultationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['consultation_type', 'status', 'payment_status']
    ordering_fields = ['created_at', 'scheduled_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConsultationCreateSerializer
        elif self.action == 'list':
            return ConsultationListSerializer
        return ConsultationDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Show consultations where user is either the patient or the doctor
        queryset = Consultation.objects.filter(
            models.Q(user=user) | models.Q(doctor__user=user)
        )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def create_payment_intent(self, request, pk=None):
        """Create Stripe payment intent"""
        consultation = self.get_object()
        
        # Verify user owns this consultation
        if consultation.user != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already paid
        if consultation.payment_status == 'paid':
            return Response(
                {'error': 'Consultation already paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create Stripe PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=int(consultation.amount * 100),  # Convert to cents
                currency='usd',
                metadata={
                    'consultation_id': str(consultation.consultation_id),
                    'user_id': request.user.id,
                    'doctor_id': consultation.doctor.id
                }
            )
            
            # Save payment intent ID
            consultation.stripe_payment_intent_id = intent.id
            consultation.save()
            
            return Response({
                'client_secret': intent.client_secret,
                'amount': consultation.amount
            })
        
        except stripe.error.StripeError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print(f"Payment intent error: {str(e)}")
            return Response(
                {'error': 'Failed to create payment intent'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def confirm_payment(self, request, pk=None):
        """Confirm payment and update consultation status"""
        try:
            consultation = self.get_object()
            
            # Verify user owns this consultation
            if consultation.user != request.user:
                return Response(
                    {'error': 'Not authorized'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if payment intent exists
            if not consultation.stripe_payment_intent_id:
                return Response(
                    {'error': 'No payment intent found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify payment with Stripe
            try:
                intent = stripe.PaymentIntent.retrieve(consultation.stripe_payment_intent_id)
                
                if intent.status != 'succeeded':
                    return Response(
                        {'error': f'Payment not succeeded. Status: {intent.status}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except stripe.error.StripeError as e:
                return Response(
                    {'error': f'Stripe error: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update consultation status
            consultation.payment_status = 'paid'
            consultation.status = 'paid'
            consultation.save()
            
            # Create earnings record
            try:
                DoctorEarnings.objects.get_or_create(
                    consultation=consultation,
                    defaults={
                        'doctor': consultation.doctor,
                        'gross_amount': consultation.amount,
                        'platform_fee_percentage': 20.00
                    }
                )
            except Exception as e:
                print(f"Error creating earnings: {str(e)}")
            
            # Update doctor stats
            try:
                consultation.doctor.total_consultations += 1
                consultation.doctor.save(update_fields=['total_consultations'])
            except Exception as e:
                print(f"Error updating doctor stats: {str(e)}")
            
            return Response({
                'success': True,
                'message': 'Payment confirmed successfully',
                'consultation_id': consultation.id,
                'status': consultation.status,
                'payment_status': consultation.payment_status
            })
        
        except Exception as e:
            import traceback
            print(f"Confirm payment error: {str(e)}")
            print(traceback.format_exc())
            
            return Response(
                {'error': f'Payment confirmation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start consultation"""
        consultation = self.get_object()
        
        # Only doctor or patient can start
        if consultation.user != request.user and consultation.doctor.user != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Must be paid
        if consultation.payment_status != 'paid':
            return Response(
                {'error': 'Consultation not paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create video room if video consultation
        if consultation.consultation_type == 'video' and not consultation.video_room_url:
            try:
                room = self.create_video_room(consultation)
                consultation.video_room_url = room['url']
                consultation.video_room_name = room['name']
            except Exception as e:
                print(f"Error creating video room: {str(e)}")
        
        consultation.status = 'active'
        consultation.started_at = timezone.now()
        consultation.save()
        
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)
    
    def create_video_room(self, consultation):
        """Create Daily.co video room"""
        daily_api_key = getattr(settings, 'DAILY_API_KEY', '')
        daily_domain = getattr(settings, 'DAILY_DOMAIN', '')
        
        if not daily_api_key or not daily_domain:
            raise Exception("Daily.co not configured")
        
        headers = {
            'Authorization': f'Bearer {daily_api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'properties': {
                'enable_chat': True,
                'enable_screenshare': True,
                'max_participants': 2,
                'exp': int(timezone.now().timestamp()) + 7200
            }
        }
        
        response = requests.post(
            'https://api.daily.co/v1/rooms',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to create room: {response.text}")
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete consultation"""
        consultation = self.get_object()
        
        if consultation.doctor.user != request.user:
            return Response(
                {'error': 'Only doctor can complete consultation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        consultation.status = 'completed'
        consultation.ended_at = timezone.now()
        consultation.save()
        
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel consultation"""
        consultation = self.get_object()
        
        if consultation.user != request.user and consultation.doctor.user != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reason = request.data.get('reason', '')
        
        if consultation.payment_status == 'paid' and consultation.stripe_payment_intent_id:
            try:
                stripe.Refund.create(payment_intent=consultation.stripe_payment_intent_id)
                consultation.payment_status = 'refunded'
            except stripe.error.StripeError as e:
                return Response(
                    {'error': f'Refund failed: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        consultation.status = 'cancelled'
        consultation.cancelled_at = timezone.now()
        consultation.cancellation_reason = reason
        consultation.save()
        
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)


class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        consultation_id = self.request.query_params.get('consultation')
        if consultation_id:
            return ChatMessage.objects.filter(consultation_id=consultation_id).order_by('created_at')
        return ChatMessage.objects.filter(
            models.Q(consultation__user=self.request.user) |
            models.Q(consultation__doctor__user=self.request.user)
        ).order_by('created_at')
    
    def create(self, request, *args, **kwargs):
        """Create message with image support and WebSocket notification"""
        try:
            # Validate consultation access
            consultation_id = request.data.get('consultation')
            if not consultation_id:
                return Response(
                    {'error': 'consultation field is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                consultation = Consultation.objects.get(id=consultation_id)
            except Consultation.DoesNotExist:
                return Response(
                    {'error': 'Consultation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verify user has access
            if consultation.user != request.user and consultation.doctor.user != request.user:
                return Response(
                    {'error': 'You do not have access to this consultation'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate and process image if present
            image = request.FILES.get('image')
            processed_image = None
            
            if image:
                # Validate file type
                valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
                ext = image.name.split('.')[-1].lower()
                if ext not in valid_extensions:
                    return Response(
                        {'error': f'Invalid file type. Allowed: {", ".join(valid_extensions)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate file size (5MB max)
                max_size = 5 * 1024 * 1024
                if image.size > max_size:
                    return Response(
                        {'error': 'Image size must be less than 5MB'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Process and compress image
                try:
                    img = Image.open(image)
                    
                    # Convert RGBA/LA/P to RGB
                    if img.mode in ('RGBA', 'LA', 'P'):
                        # Create white background for transparency
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    
                    # Resize if too large
                    max_dimension = 1920
                    if max(img.size) > max_dimension:
                        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                    
                    # Save compressed image
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=85, optimize=True)
                    output.seek(0)
                    
                    # Create new InMemoryUploadedFile
                    processed_image = InMemoryUploadedFile(
                        output, 
                        'ImageField', 
                        f"{image.name.split('.')[0]}.jpg",
                        'image/jpeg', 
                        output.tell(), 
                        None
                    )
                except Exception as e:
                    print(f"Image processing error: {str(e)}")
                    return Response(
                        {'error': 'Failed to process image'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Create message
            message_text = request.data.get('message', '').strip()
            
            # At least one of message or image must be present
            if not message_text and not processed_image:
                return Response(
                    {'error': 'Either message text or image is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save message to database
            message = ChatMessage.objects.create(
                consultation=consultation,
                sender=request.user,
                message=message_text,
                image=processed_image
            )
            
            # Notify via WebSocket
            try:
                channel_layer = get_channel_layer()
                room_group_name = f'chat_{consultation_id}'
                
                # Build full image URL if image exists
                image_url = None
                if message.image:
                    image_url = request.build_absolute_uri(message.image.url)
                
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        'type': 'chat_message',
                        'message_id': message.id,
                        'message': message.message,
                        'image': image_url,
                        'sender_id': request.user.id,
                        'sender_name': request.user.get_full_name() or request.user.username,
                        'created_at': message.created_at.isoformat()
                    }
                )
            except Exception as e:
                print(f"WebSocket notification error: {str(e)}")
                # Don't fail the request if WebSocket notification fails
            
            # Return serialized message
            serializer = self.get_serializer(message, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            import traceback
            print(f"Error creating message: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'Failed to create message: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DoctorReviewViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['doctor', 'rating']
    
    def get_queryset(self):
        return DoctorReview.objects.all()


class FavoriteDoctorViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteDoctorSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FavoriteDoctor.objects.filter(user=self.request.user)
    
    def create(self, request):
        doctor_id = request.data.get('doctor')
        
        if not doctor_id:
            return Response(
                {'error': 'doctor field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        
        favorite, created = FavoriteDoctor.objects.get_or_create(
            user=request.user,
            doctor=doctor
        )
        
        if not created:
            favorite.delete()
            return Response(
                {'message': 'Doctor removed from favorites'},
                status=status.HTTP_204_NO_CONTENT
            )
        
        serializer = self.get_serializer(favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuickReplyViewSet(viewsets.ModelViewSet):
    serializer_class = QuickReplySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return QuickReply.objects.filter(doctor__user=self.request.user)
    
    def perform_create(self, serializer):
        doctor = DoctorProfile.objects.get(user=self.request.user)
        serializer.save(doctor=doctor)


class DoctorStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get statistics for the logged-in doctor"""
        try:
            doctor = DoctorProfile.objects.get(user=request.user)
            
            # Get earnings stats
            earnings_stats = DoctorEarnings.objects.filter(doctor=doctor).aggregate(
                total_earnings=Sum('net_amount'),
                total_consultations=Count('id'),
                pending_payout=Sum('net_amount', filter=models.Q(paid_out=False))
            )
            
            # Get consultation stats
            consultation_stats = Consultation.objects.filter(doctor=doctor).aggregate(
                total=Count('id'),
                completed=Count('id', filter=models.Q(status='completed')),
                active=Count('id', filter=models.Q(status='active')),
                cancelled=Count('id', filter=models.Q(status='cancelled'))
            )
            
            return Response({
                'earnings': {
                    'total': earnings_stats['total_earnings'] or 0,
                    'pending_payout': earnings_stats['pending_payout'] or 0,
                    'total_consultations': earnings_stats['total_consultations'] or 0
                },
                'consultations': consultation_stats,
                'rating': {
                    'average': doctor.average_rating,
                    'total_reviews': doctor.total_ratings
                }
            })
            
        except DoctorProfile.DoesNotExist:
            return Response(
                {'error': 'Doctor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )