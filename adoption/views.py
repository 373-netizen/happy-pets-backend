# adoption/views.py

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django.db.models import Q, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied


from .models import Shelter, AdoptablePet, AdoptionApplication, Favorite
from .serializers import (
    ShelterListSerializer, ShelterDetailSerializer, ShelterCreateUpdateSerializer,
    AdoptablePetListSerializer, AdoptablePetDetailSerializer, AdoptablePetCreateUpdateSerializer,
    AdoptionApplicationSerializer, FavoriteSerializer,
    ShelterStatsSerializer, PetStatsSerializer
)


class ShelterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shelters
    - List: Public (only approved & active shelters)
    - Detail: Public
    - Create: Authenticated users
    - Update/Delete: Owner or Admin only
    """
    queryset = Shelter.objects.all()
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'verified', 'city', 'state', 'is_active']
    search_fields = ['name', 'description', 'city', 'state']
    ordering_fields = ['created_at', 'name', 'city']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ShelterListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ShelterCreateUpdateSerializer
        return ShelterDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # For list view, only show approved & active shelters (unless user is staff or owner)
        if self.action == 'list':
            if not self.request.user.is_staff:
                if self.request.user.is_authenticated:
                    # Show approved shelters + user's own shelters
                    queryset = queryset.filter(
                        Q(status='approved', is_active=True) | 
                        Q(owner=self.request.user)
                    )
                else:
                    # Only approved & active shelters for anonymous users
                    queryset = queryset.filter(status='approved', is_active=True)
        
        return queryset
    
    def perform_create(self, serializer):
        # Set the owner to the current user and status to pending
        serializer.save(owner=self.request.user, status='pending')
    
    def perform_update(self, serializer):
        # Only owner or admin can update
        shelter = self.get_object()
        if not self.request.user.is_staff and shelter.owner != self.request.user:
            raise PermissionDenied("You don't have permission to update this shelter")
        serializer.save()
    
    def perform_destroy(self, instance):
        # Only owner or admin can delete
        if not self.request.user.is_staff and instance.owner != self.request.user:
            raise PermissionDenied("You don't have permission to delete this shelter")
        instance.delete()
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_shelters(self, request):
        """Get current user's shelters"""
        shelters = Shelter.objects.filter(owner=request.user)
        serializer = ShelterListSerializer(shelters, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def pets(self, request, slug=None):
        """Get all pets from this shelter"""
        shelter = self.get_object()
        
        # Debug logging
        print(f"🔍 Shelter: {shelter.name} (ID: {shelter.id}, Slug: {shelter.slug})")
        
        # Get all pets for this shelter
        pets = AdoptablePet.objects.filter(shelter=shelter, is_active=True)
        
        print(f"🐕 Found {pets.count()} pets for shelter {shelter.name}")
        if pets.exists():
            print(f"🐕 Pet names: {[p.name for p in pets]}")
        
        # Apply status filter if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            pets = pets.filter(status=status_filter)
            print(f"🔍 Filtered by status '{status_filter}': {pets.count()} pets")
        
        # Serialize the data
        serializer = AdoptablePetListSerializer(
            pets, many=True, context={'request': request}
        )
        
        print(f"📦 Serialized data count: {len(serializer.data)}")
        
        return Response(serializer.data)


class AdoptablePetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing adoptable pets
    - List/Detail: Public
    - Create: Authenticated users (must own a shelter)
    - Update/Delete: Shelter owner or Admin only
    """
    queryset = AdoptablePet.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'species', 'size', 'gender', 'status', 'shelter', 
        'good_with_kids', 'good_with_dogs', 'good_with_cats',
        'spayed_neutered', 'vaccinated', 'house_trained'
    ]
    search_fields = ['name', 'breed', 'description', 'shelter__name', 'shelter__city']
    ordering_fields = ['created_at', 'name', 'age', 'adoption_fee']
    ordering = ['-featured', '-urgent', '-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AdoptablePetListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AdoptablePetCreateUpdateSerializer
        return AdoptablePetDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # For list view, only show pets from approved shelters
        if self.action == 'list':
            if not self.request.user.is_staff:
                queryset = queryset.filter(shelter__status='approved', shelter__is_active=True)
        
        # Filter by age range
        min_age = self.request.query_params.get('min_age')
        max_age = self.request.query_params.get('max_age')
        if min_age:
            queryset = queryset.filter(age__gte=int(min_age))
        if max_age:
            queryset = queryset.filter(age__lte=int(max_age))
        
        # Filter by location
        city = self.request.query_params.get('city')
        state = self.request.query_params.get('state')
        if city:
            queryset = queryset.filter(shelter__city__icontains=city)
        if state:
            queryset = queryset.filter(shelter__state__icontains=state)
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Increment views when retrieving a pet"""
        instance = self.get_object()
        instance.views += 1
        instance.save(update_fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        # Validate that user owns the shelter
        shelter = serializer.validated_data.get('shelter')
        if not self.request.user.is_staff and shelter.owner != self.request.user:
            raise PermissionDenied("You can only add pets to your own shelters")
        
        if shelter.status != 'approved':
            raise PermissionDenied("Shelter must be approved before adding pets")
        
        serializer.save()
    
    def perform_update(self, serializer):
        pet = self.get_object()
        if not self.request.user.is_staff and pet.shelter.owner != self.request.user:
            raise PermissionDenied("You don't have permission to update this pet")
        serializer.save()
    
    def perform_destroy(self, instance):
        if not self.request.user.is_staff and instance.shelter.owner != self.request.user:
            raise PermissionDenied("You don't have permission to delete this pet")
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured pets"""
        pets = self.get_queryset().filter(featured=True, status='available')
        serializer = self.get_serializer(pets, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def urgent(self, request):
        """Get urgent adoption pets"""
        pets = self.get_queryset().filter(urgent=True, status='available')
        serializer = self.get_serializer(pets, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_favorite(self, request, pk=None):
        """Toggle favorite status for a pet"""
        pet = self.get_object()
        favorite, created = Favorite.objects.get_or_create(user=request.user, pet=pet)
        
        if not created:
            favorite.delete()
            return Response({'favorited': False, 'message': 'Removed from favorites'})
        
        return Response({'favorited': True, 'message': 'Added to favorites'})


class AdoptionApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing adoption applications
    - List: Authenticated users (own applications + shelter owner's applications)
    - Create: Authenticated users
    - Update: Applicant or shelter owner
    """
    queryset = AdoptionApplication.objects.all()
    serializer_class = AdoptionApplicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'pet', 'housing_type']
    ordering_fields = ['submitted_at', 'status']
    ordering = ['-submitted_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_staff:
            return queryset
        
        # Users see their own applications + applications for their shelter's pets
        return queryset.filter(
            Q(applicant=user) | Q(pet__shelter__owner=user)
        )
    
    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user, status='pending')
    
    @action(detail=False, methods=['get'])
    def my_applications(self, request):
        """Get current user's applications"""
        applications = self.get_queryset().filter(applicant=request.user)
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def shelter_applications(self, request):
        """Get applications for pets in user's shelters"""
        applications = self.get_queryset().filter(pet__shelter__owner=request.user)
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an application (shelter owner only)"""
        application = self.get_object()
        
        # Check if user owns the shelter
        if not request.user.is_staff and application.pet.shelter.owner != request.user:
            return Response(
                {'error': 'Only the shelter owner can approve applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        application.status = 'approved'
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save()
        
        # Mark pet as pending
        application.pet.status = 'pending'
        application.pet.save()
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an application (shelter owner only)"""
        application = self.get_object()
        
        if not request.user.is_staff and application.pet.shelter.owner != request.user:
            return Response(
                {'error': 'Only the shelter owner can reject applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        application.status = 'rejected'
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.admin_notes = request.data.get('admin_notes', '')
        application.save()
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Withdraw an application (applicant only)"""
        application = self.get_object()
        
        if application.applicant != request.user:
            return Response(
                {'error': 'You can only withdraw your own applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if application.status in ['approved', 'rejected']:
            return Response(
                {'error': 'Cannot withdraw an already processed application'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.status = 'withdrawn'
        application.save()
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)


class FavoriteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user favorites (read-only, use toggle_favorite on pet to add/remove)
    """
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('pet', 'pet__shelter')


# Statistics Views
from rest_framework.views import APIView

class AdoptionStatsView(APIView):
    """Get adoption statistics"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        stats = {
            'total_shelters': Shelter.objects.filter(status='approved', is_active=True).count(),
            'approved_shelters': Shelter.objects.filter(status='approved').count(),
            'pending_shelters': Shelter.objects.filter(status='pending').count(),
            'total_pets': AdoptablePet.objects.filter(is_active=True).count(),
            'available_pets': AdoptablePet.objects.filter(status='available', is_active=True).count(),
            'adopted_pets': AdoptablePet.objects.filter(status='adopted').count(),
            'pending_applications': AdoptionApplication.objects.filter(
                status__in=['submitted', 'under_review']
            ).count(),
        }
        
        serializer = ShelterStatsSerializer(stats)
        return Response(serializer.data)


class PetStatsBySpeciesView(APIView):
    """Get pet statistics grouped by species"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        stats = AdoptablePet.objects.filter(
            is_active=True, 
            status='available'
        ).values('species').annotate(count=Count('id')).order_by('-count')
        
        serializer = PetStatsSerializer(stats, many=True)
        return Response(serializer.data)