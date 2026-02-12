import dj_database_url
import os
from pathlib import Path
from datetime import timedelta

# ============ Python 3.14 Compatibility Patch ============
import sys
if sys.version_info >= (3, 14):
    import django.template.context
    
    # Fix the __copy__ method for BaseContext
    original_base_context = django.template.context.BaseContext
    
    def patched_copy(self):
        duplicate = self.__class__()
        # Copy the dicts list properly
        if hasattr(self, '_dict_stack'):
            duplicate._dict_stack = self._dict_stack[:]
        duplicate.update(self)
        return duplicate
    
    original_base_context.__copy__ = patched_copy
    
    # Also patch RequestContext if needed
    request_context = django.template.context.RequestContext
    request_context.__copy__ = patched_copy
# ============ End of Patch ============

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


# Security
SECRET_KEY = "your-secret-key-here"
DEBUG = False

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'cache_data'),
        'TIMEOUT': 60 * 60 * 24 * 7,  # 7 days
        'OPTIONS': {
            'MAX_ENTRIES': 10000
        }
    }
}
# Installed apps
INSTALLED_APPS = [
     "daphne", 
     'channels',

    # Django default apps
    'jazzmin',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",  

    # Third-party apps
    "rest_framework",
    "rest_framework.authtoken",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    
    # Google provider
    'allauth.socialaccount.providers.google',
    "corsheaders",
     

    # Your apps
    "users",
    "pets",
    'chat',
    'breeding',
    'education',
    'services',
    'products',
    'reviews',
    'info',
    'adoption',
    'doctors',
    ]
SITE_ID = 1 

# ==================== API KEYS ====================
# Get your YouTube API key from: https://console.cloud.google.com/
YOUTUBE_API_KEY = 'AIzaSyBwulJHyQcHwsPagHMh-S51MUBfbOw90AU'


DOG_API_KEY = 'live_4AodKcm1BXsQrD1023NMLs5Ms2pClQSV0kbF3W8e6XFKja4xO239EZLIScVkFGJK'
CAT_API_KEY = 'live_OsWnjPorxBx0x0F4W43Mk1sE0aHObxLhmndtp1l3anHkq0Yc5EbRIJrCzuX8GE2H'


# Optional: Get News API key from: https://newsapi.org/
NEWS_API_KEY = '61570ce5c2544eeba7431d90b7b6a5d2'  # Free tier: 100 requests/day


# Middleware
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # cors first
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'allauth.account.middleware.AccountMiddleware',

]

# URL config
ROOT_URLCONF = "backend.urls"

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# Database (MySQL)
# Database (MySQL)
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.mysql",
#         "NAME": "happy_pets_db",
#         "USER": "root",
#         "PASSWORD": "shaikh@9121",
#         "HOST": "localhost",
#         "PORT": "3306",
#         "OPTIONS": {
#          'charset': 'utf8mb4',
#             "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
#         },
#     }
# }
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL")
    )
}

# Disable MariaDB version check for XAMPP compatibility


# Custom User model

AUTH_USER_MODEL = "users.CustomUser"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = False 

# Static & media files
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# CORS (for frontend React)
CORS_ALLOW_ALL_ORIGINS = True  # dev only

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# Simple JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
}

# Authentication backends (required for allauth)
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

# django-allauth (NEW FORMAT)
ACCOUNT_LOGIN_METHODS = {"email", "username"}   # both allowed
ACCOUNT_SIGNUP_FIELDS = {
    "username*": {},
    "email*": {},
    "password1*": {},
    "password2*": {},
}

ACCOUNT_EMAIL_VERIFICATION = "optional"


# dj-rest-auth settings (disable default token if using JWT)
REST_AUTH_TOKEN_MODEL = None

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

 #Channels Configuration
ASGI_APPLICATION = 'backend.asgi.application'  # Replace 'your_project_name' with your actual project name

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'  # Simple in-memory for development
        # For production, use Redis:
        # 'BACKEND': 'channels_redis.core.RedisChannelLayer',
        # 'CONFIG': {
        #     "hosts": [('127.0.0.1', 6379)],
        # },
    },
}

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB



# Create media directories on startup
CHAT_UPLOADS_DIR = os.path.join(MEDIA_ROOT, 'chat_uploads')
os.makedirs(CHAT_UPLOADS_DIR, exist_ok=True)


# WebSocket URL
ALLOWED_HOSTS = ['*']



# Create media directories on startup
CHAT_UPLOADS_DIR = os.path.join(MEDIA_ROOT, 'chat_uploads')
os.makedirs(CHAT_UPLOADS_DIR, exist_ok=True)

# Temporary placeholders (so your server starts)
STRIPE_PUBLIC_KEY = 'pk_test_51SzHeXLuFSfx6wEssQT9Iu2j0zHE41imQAMGuhiuwyPbflXlHiu3kf8KLc3RSeugJT4p2fRRa7mDeR6r1hZ4Iy9p00o5mdOHbA'
STRIPE_SECRET_KEY = 'sk_test_51SzHeXLuFSfx6wEsWyWY3f3rLUTrJHCIYkvcDRalledZrK2yHYvUwd12ouWXC9WJItrfbc0rRDZkW69C0W323bsS0000XLWqm5'
DAILY_API_KEY = '38ba3684aa7a13bfcf757d0fcdb817e21cf468b7694767e0e9e713a9f5f01e2e'
DAILY_DOMAIN = 'happy-pets.daily.co'  


os.makedirs(os.path.join(MEDIA_ROOT, 'chat_images'), exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, 'doctors/profiles'), exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, 'doctors/licenses'), exist_ok=True)

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
