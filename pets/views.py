# pets/views.py
from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import date, timedelta
from .models import Pet, Appointment, Vaccination, HealthRecord, Reminder
from .serializers import (
    PetSerializer, AppointmentSerializer, VaccinationSerializer,
    HealthRecordSerializer, ReminderSerializer
)
from rest_framework.views import APIView

# ----------------- PETS -----------------
class PetViewSet(viewsets.ModelViewSet):
    serializer_class = PetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'breed', 'species']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Pet.objects.filter(owner=self.request.user, is_active=True)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Add health records for each pet
        pets_with_health = []
        for pet_data in serializer.data:
            pet_id = pet_data['id']
            health_records = HealthRecord.objects.filter(pet_id=pet_id).order_by('-date')
            pet_data['health_records'] = HealthRecordSerializer(health_records, many=True).data
            pets_with_health.append(pet_data)

        return Response({
            'success': True,
            'count': queryset.count(),
            'pets': pets_with_health
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'message': 'Pet added successfully!',
            'pet': serializer.data
        }, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response({
            'success': True,
            'message': 'Pet deleted successfully!'
        }, status=status.HTTP_200_OK)


# ----------------- APPOINTMENTS -----------------
class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'location', 'veterinarian_name']
    ordering_fields = ['date', 'time']
    ordering = ['date', 'time']

    def get_queryset(self):
        queryset = Appointment.objects.filter(owner=self.request.user)
        # Filter upcoming
        if self.request.query_params.get('upcoming') == 'true':
            queryset = queryset.filter(date__gte=date.today(), status='scheduled')
        # Filter by pet
        pet_id = self.request.query_params.get('pet_id')
        if pet_id:
            queryset = queryset.filter(pet_id=pet_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'appointments': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'message': 'Appointment created successfully!',
            'appointment': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put'])
    def update_status(self, request, pk=None):
        appointment = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Appointment.STATUS_CHOICES):
            return Response({'success': False, 'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        appointment.status = new_status
        appointment.save()
        return Response({
            'success': True,
            'message': f'Appointment status updated to {new_status}',
            'appointment': AppointmentSerializer(appointment).data
        })


# ----------------- VACCINATIONS -----------------
class VaccinationViewSet(viewsets.ModelViewSet):
    serializer_class = VaccinationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['vaccine_name', 'vaccine_type']
    ordering_fields = ['due_date']
    ordering = ['due_date']

    def get_queryset(self):
        queryset = Vaccination.objects.filter(pet__owner=self.request.user)
        if self.request.query_params.get('completed') == 'false':
            queryset = queryset.filter(completed=False)
        pet_id = self.request.query_params.get('pet_id')
        if pet_id:
            queryset = queryset.filter(pet_id=pet_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'vaccinations': serializer.data
        })

    @action(detail=True, methods=['put'])
    def mark_completed(self, request, pk=None):
        vaccination = self.get_object()
        vaccination.completed = True
        vaccination.administered_date = request.data.get('administered_date', date.today())
        vaccination.save()
        return Response({
            'success': True,
            'message': 'Vaccination marked as completed',
            'vaccination': VaccinationSerializer(vaccination).data
        })


# ----------------- REMINDERS -----------------
class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['remind_at']
    ordering = ['remind_at']

    def get_queryset(self):
        queryset = Reminder.objects.filter(user=self.request.user)
        if self.request.query_params.get('completed') == 'false':
            queryset = queryset.filter(completed=False)
        pet_id = self.request.query_params.get('pet_id')
        if pet_id:
            queryset = queryset.filter(pet_id=pet_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'reminders': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'message': 'Reminder created successfully!',
            'reminder': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put'])
    def complete(self, request, pk=None):
        reminder = self.get_object()
        reminder.mark_as_completed()
        return Response({
            'success': True,
            'message': 'Reminder marked as completed',
            'reminder': ReminderSerializer(reminder).data
        })


# ----------------- HEALTH RECORDS -----------------
class HealthRecordViewSet(viewsets.ModelViewSet):
    serializer_class = HealthRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'diagnosis', 'treatment']
    ordering_fields = ['date']
    ordering = ['-date']

    def get_queryset(self):
        queryset = HealthRecord.objects.filter(pet__owner=self.request.user)
        pet_id = self.request.query_params.get('pet_id')
        if pet_id:
            queryset = queryset.filter(pet_id=pet_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'health_records': serializer.data
        })


# ----------------- DASHBOARD STATS -----------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    user = request.user
    today = date.today()
    pets = Pet.objects.filter(owner=user, is_active=True)
    upcoming_appointments = Appointment.objects.filter(owner=user, date__gte=today, status='scheduled').count()
    vaccines_due = Vaccination.objects.filter(pet__owner=user, completed=False, due_date__lte=today + timedelta(days=30)).count()
    pending_reminders = Reminder.objects.filter(user=user, completed=False, remind_at__lte=timezone.now() + timedelta(days=7)).count()
    recent_health_records = HealthRecord.objects.filter(pet__owner=user).order_by('-date')[:5]

    return Response({
        'success': True,
        'total_pets': pets.count(),
        'appointments_upcoming': upcoming_appointments,
        'vaccines_due': vaccines_due,
        'pending_reminders': pending_reminders,
        'recent_health_records': HealthRecordSerializer(recent_health_records, many=True).data
    })


# ----------------- AUTH CHECK -----------------
@api_view(['GET'])
@permission_classes([AllowAny])
def check_auth(request):
    if request.user.is_authenticated:
        return Response({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            }
        })
    else:
        return Response({
            'authenticated': False,
            'message': 'Please log in to access your pet care dashboard',
            'login_url': '/api/auth/login/',
            'signup_url': '/api/auth/registration/'
        })


# ----------------- BREEDING PLACEHOLDER -----------------
#class AvailableForBreedingView(APIView):
 #   permission_classes = [IsAuthenticated]

   # def get(self, request, *args, **kwargs):
    #    return Response({
     #       "success": True,
      #      "message": "Breeding functionality coming soon!"
       # }, status=status.HTTP_200_OK)
