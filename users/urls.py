from django.urls import path
from .views import (
    register, login, google_login, update_profile, change_password, update_location,
    appointment_list_create, vaccination_list_create,
    message_list_create, notification_list,
    health_record_list_create, health_record_detail
)

urlpatterns = [
    # 🔹 Auth
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('google-login/', google_login, name='google_login'),

    # 🔹 Profile
    path('update/', update_profile, name='update_profile'),
    path('change-password/', change_password, name='change_password'),
    path("update-location/", update_location, name="update_location"),

    # 🔹 Appointments
    path('appointments/', appointment_list_create, name='appointment_list_create'),

    # 🔹 Vaccinations
    path('vaccinations/', vaccination_list_create, name='vaccination_list_create'),

    # 🔹 Messages
    path('messages/', message_list_create, name='message_list_create'),

    # 🔹 Notifications
    path('notifications/', notification_list, name='notification_list'),

    # 🔹 Health Records
    path('health-records/', health_record_list_create, name='health_record_list_create'),
    path('health-records/<int:record_id>/', health_record_detail, name='health_record_detail'),
]
