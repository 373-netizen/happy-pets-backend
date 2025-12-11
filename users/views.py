from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer
from django.core.files.base import ContentFile
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests
from django.utils import timezone
from django.db import models
from datetime import date
from.models import Message, Notification
from pets.models import Pet, Appointment, Vaccination, HealthRecord


User = get_user_model()

# --------------------------
# USER SERIALIZER HELPERS
# --------------------------
def get_user_data(user, request=None):
    serializer = UserSerializer(user, context={'request': request})
    return serializer.data


# --------------------------
# REGISTER
# --------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": get_user_data(user, request),
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --------------------------
# LOGIN
# --------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({"message": "Email and password are required"}, status=400)

    try:
        user = User.objects.get(email=email)
        if user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": get_user_data(user, request),
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            })
        else:
            return Response({"message": "Invalid credentials"}, status=401)
    except User.DoesNotExist:
        return Response({"message": "Invalid credentials"}, status=401)


# --------------------------
# GOOGLE LOGIN
# --------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    token = request.data.get('token') or request.data.get('credential')

    if not token:
        return Response({"message": "Access token required"}, status=400)

    try:
        GOOGLE_CLIENT_ID = "379410863733-go2iuv5hiuacqeirhk0edi0kobj3lkdm.apps.googleusercontent.com"
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo["email"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "first_name": idinfo.get("given_name", ""),
                "last_name": idinfo.get("family_name", "")
            }
        )

        picture = idinfo.get("picture")
        if picture and (created or not user.avatar or user.avatar.name == "avatars/default.png"):
            resp = requests.get(picture)
            if resp.status_code == 200:
                user.avatar.save(f"{user.username}_g.jpg", ContentFile(resp.content), save=True)

        refresh = RefreshToken.for_user(user)
        return Response({
            "user": get_user_data(user, request),
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })

    except Exception:
        return Response({"message": "Invalid Google token"}, status=401)


# --------------------------
# UPDATE PROFILE
# --------------------------
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    data = request.data.copy()

    if "avatar" in request.FILES:
        data["avatar"] = request.FILES["avatar"]
    elif data.get("avatar") in [None, "", "null"]:
        data["avatar"] = None

    serializer = UserSerializer(user, data=data, partial=True, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response({
            "user": get_user_data(user, request),
            "message": "Profile updated successfully"
        })
    return Response(serializer.errors, status=400)


# --------------------------
# CHANGE PASSWORD
# --------------------------
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    current = request.data.get("currentPassword")
    new = request.data.get("newPassword")

    if not current or not new:
        return Response({"message": "Both current and new password required"}, status=400)

    if not user.check_password(current):
        return Response({"message": "Incorrect current password"}, status=400)

    user.set_password(new)
    user.save()
    return Response({"message": "Password updated"})


# --------------------------
# UPDATE LOCATION
# --------------------------
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_location(request):
    user = request.user
    location = request.data.get("location")

    if not location:
        return Response({"error": "location required"}, status=400)

    user.location = location
    user.latitude = request.data.get("latitude")
    user.longitude = request.data.get("longitude")
    user.save()

    return Response({"message": "Location updated"})


# --------------------------
# APPOINTMENTS
# --------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def appointment_list_create(request):
    if request.method == 'GET':
        appointments = Appointment.objects.filter(owner=request.user)
        return Response({"appointments": [
            {
                "id": a.id,
                "title": a.title,
                "type": a.type,
                "date": a.date.strftime("%Y-%m-%d"),
                "time": a.time.strftime("%H:%M"),
                "duration": a.duration,
                "location": a.location,
                "address": a.address,
                "pet_id": a.pet.id,
                "pet_name": a.pet.name,
                "veterinarian_name": a.veterinarian_name,
                "clinic_phone": a.clinic_phone,
                "notes": a.notes,
                "status": a.status,
                "is_upcoming": a.is_upcoming
            } for a in appointments
        ]})

    if request.method == 'POST':
        try:
            pet = Pet.objects.get(id=request.data["pet_id"], owner=request.user)
            apt = Appointment.objects.create(
                owner=request.user,
                pet=pet,
                title=request.data["title"],
                type=request.data.get("type", "checkup"),
                date=request.data["date"],
                time=request.data["time"],
                duration=request.data.get("duration", 30),
                location=request.data.get("location"),
                address=request.data.get("address", ""),
                veterinarian_name=request.data.get("veterinarian_name", ""),
                clinic_phone=request.data.get("clinic_phone", ""),
                notes=request.data.get("notes", "")
            )
            return Response({"message": "Appointment created", "id": apt.id}, status=201)
        except Exception as e:
            return Response({"message": str(e)}, status=400)


# --------------------------
# VACCINATIONS
# --------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def vaccination_list_create(request):
    if request.method == 'GET':
        vaccinations = Vaccination.objects.filter(pet__owner=request.user)
        return Response({"vaccinations": [
            {
                "id": v.id,
                "vaccine_name": v.vaccine_name,
                "vaccine_type": v.vaccine_type,
                "due_date": v.due_date.strftime("%Y-%m-%d"),
                "administered_date": v.administered_date.strftime("%Y-%m-%d") if v.administered_date else None,
                "next_due_date": v.next_due_date.strftime("%Y-%m-%d") if v.next_due_date else None,
                "completed": v.completed,
                "is_overdue": v.is_overdue,
                "days_until_due": v.days_until_due,
                "pet_id": v.pet.id,
                "pet_name": v.pet.name
            } for v in vaccinations
        ]})

    if request.method == 'POST':
        try:
            pet = Pet.objects.get(id=request.data["pet_id"], owner=request.user)
            Vaccination.objects.create(
                pet=pet,
                vaccine_name=request.data["vaccine_name"],
                vaccine_type=request.data.get("vaccine_type", ""),
                due_date=request.data["due_date"],
                veterinarian_name=request.data.get("veterinarian_name", ""),
                clinic_name=request.data.get("clinic_name", ""),
                notes=request.data.get("notes", "")
            )
            return Response({"message": "Vaccination created"}, status=201)
        except Exception as e:
            return Response({"message": str(e)}, status=400)


# --------------------------
# MESSAGES
# --------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def message_list_create(request):
    if request.method == 'GET':
        messages = Message.objects.filter(
            models.Q(sender=request.user) | models.Q(receiver=request.user)
        ).order_by('-created_at')

        return Response({"messages": [
            {
                "id": m.id,
                "sender_id": m.sender.id,
                "sender_name": m.sender.username,
                "receiver_id": m.receiver.id,
                "receiver_name": m.receiver.username,
                "subject": m.subject,
                "content": m.content,
                "read": m.read,
                "created_at": m.created_at.strftime("%Y-%m-%d %H:%M"),
                "is_sent_by_me": m.sender == request.user
            } for m in messages
        ]})

    if request.method == 'POST':
        receiver = User.objects.get(id=request.data["receiver_id"])
        msg = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            subject=request.data.get("subject", ""),
            content=request.data["content"]
        )
        Notification.objects.create(
            user=receiver,
            type="message",
            title="New Message",
            message=f"{request.user.username} sent you a message",
            link=f"/messages/{msg.id}"
        )
        return Response({"message": "Message sent"}, status=201)


# --------------------------
# NOTIFICATIONS
# --------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
    return Response({
        "notifications": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "link": n.link,
                "read": n.read,
                "created_at": n.created_at.strftime("%Y-%m-%d %H:%M")
            } for n in notifications
        ],
        "unread_count": Notification.objects.filter(user=request.user, read=False).count()
    })


# --------------------------
# HEALTH RECORDS
# --------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def health_record_list_create(request):
    if request.method == 'GET':
        records = HealthRecord.objects.filter(pet__owner=request.user).order_by('-date')
        return Response({"health_records": [
            {
                "id": r.id,
                "pet_id": r.pet.id,
                "pet_name": r.pet.name,
                "date": r.date.strftime("%Y-%m-%d"),
                "type": r.type,
                "title": r.title,
                "description": r.description,
                "diagnosis": r.diagnosis,
                "treatment": r.treatment,
                "medications": r.medications,
                "veterinarian_name": r.veterinarian_name,
                "clinic_name": r.clinic_name,
                "notes": r.notes,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
            } for r in records
        ]})

    if request.method == 'POST':
        try:
            pet = Pet.objects.get(id=request.data["pet_id"], owner=request.user)
            HealthRecord.objects.create(
                pet=pet,
                date=request.data.get("date", date.today()),
                type=request.data.get("type", ""),
                title=request.data["title"],
                description=request.data.get("description", ""),
                diagnosis=request.data.get("diagnosis", ""),
                treatment=request.data.get("treatment", ""),
                medications=request.data.get("medications", ""),
                veterinarian_name=request.data.get("veterinarian_name", ""),
                clinic_name=request.data.get("clinic_name", ""),
                notes=request.data.get("notes", "")
            )
            return Response({"message": "Health record created"}, status=201)
        except Exception as e:
            return Response({"message": str(e)}, status=400)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def health_record_detail(request, record_id):
    """Retrieve, update, or delete a single health record"""

    try:
        record = HealthRecord.objects.get(id=record_id, pet__owner=request.user)
    except HealthRecord.DoesNotExist:
        return Response({"message": "Health record not found"}, status=404)

    if request.method == 'GET':
        return Response({
            "id": record.id,
            "pet_id": record.pet.id,
            "pet_name": record.pet.name,
            "date": record.date.strftime("%Y-%m-%d"),
            "type": record.type,
            "title": record.title,
            "description": record.description,
            "diagnosis": record.diagnosis,
            "treatment": record.treatment,
            "medications": record.medications,
            "veterinarian_name": record.veterinarian_name,
            "clinic_name": record.clinic_name,
            "notes": record.notes,
            "created_at": record.created_at.strftime("%Y-%m-%d %H:%M")
        })

    if request.method == 'PUT':
        for f in ["date", "type", "title", "description", "diagnosis", "treatment",
                  "medications", "veterinarian_name", "clinic_name", "notes"]:
            if f in request.data:
                setattr(record, f, request.data[f])
        record.save()
        return Response({"message": "Health record updated"})

    if request.method == 'DELETE':
        record.delete()
        return Response({"message": "Health record deleted"})
