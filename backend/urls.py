from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', lambda request: HttpResponse("Welcome to Happy Pets Backend API 🐾")),
    path('admin/', admin.site.urls),

    # Authentication (REST)
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),

    # Social login (Google/Facebook)
    path('accounts/', include('allauth.urls')),  # 👈 Required for OAuth redirect URLs

    # Your custom app APIs
    path('api/', include('users.urls')),

    path("api/user/", include("users.urls")),

     path('admin/', admin.site.urls),

    path('api/', include('pets.urls')),
    
    path('api/auth/', include('dj_rest_auth.urls')),
    
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),

]

# Redirect after login/logout
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ✅ Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
