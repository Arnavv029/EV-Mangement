"""
Django settings for EV Station Slot Booking System
---------------------------------------------------
Key configurations:
- SQLite database (no PostgreSQL needed)
- JWT authentication (via djangorestframework-simplejwt)
- CORS enabled (so React frontend can talk to this backend)
- Custom User model with 'role' field (user / owner)
"""

import os
from pathlib import Path
from datetime import timedelta

# Load .env file if present (never commit real secrets)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass  # python-dotenv not required; set env vars manually in production


# ─── Base Directory ───────────────────────────────────────────────────────────
# This points to the 'backend/' folder.
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY = 'ev-booking-secret-key-change-this-in-production-abc123xyz'
DEBUG = True  # Set to False in production
ALLOWED_HOSTS = ['*']  # Allow all hosts during development

# ─── Installed Apps ───────────────────────────────────────────────────────────
# We add:
#   rest_framework       → Django REST Framework (DRF) for building APIs
#   rest_framework_simplejwt → JWT token authentication
#   corsheaders          → Allow React frontend to call our APIs
#   core                 → Our main app (models, views, etc.)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # Our app
    'core',
]

# ─── Middleware ────────────────────────────────────────────────────────────────
# CorsMiddleware MUST be placed at the very top (before CommonMiddleware)
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',     # ← CORS must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ev_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ev_backend.wsgi.application'

# ─── Database ─────────────────────────────────────────────────────────────────
# Using SQLite — Django's built-in database.
# The file 'db.sqlite3' will be created automatically in the backend/ folder.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ─── Custom User Model ────────────────────────────────────────────────────────
# We tell Django to use OUR custom user model (defined in core/models.py)
# instead of Django's default User. This is needed because we add a 'role' field.
AUTH_USER_MODEL = 'core.CustomUser'

# ─── Password Validation ──────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Internationalization ─────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'  # Indian Standard Time (IST)
USE_I18N = True
USE_TZ = True

# ─── Static & Media Files ─────────────────────────────────────────────────────
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'  # Uploaded images saved here

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Django REST Framework Configuration ──────────────────────────────────────
# This tells DRF to use JWT for authentication by default.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',  # All endpoints require login by default
    ),
}

# ─── JWT Configuration ────────────────────────────────────────────────────────
# ACCESS_TOKEN_LIFETIME  → How long the JWT token is valid (1 day for hackathon convenience)
# REFRESH_TOKEN_LIFETIME → How long before the user must log in again
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),  # Frontend sends: Authorization: Bearer <token>
}

# ─── CORS Configuration ───────────────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing) allows our React frontend (running on
# port 5173 or 3000) to make API requests to Django (running on port 8000).
# Without this, browsers block the requests for security reasons.
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',    # React (Create React App)
    'http://localhost:5173',    # React (Vite)
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
]
# Also allow all origins during development (set to False in production)
CORS_ALLOW_ALL_ORIGINS = True

# ─── Razorpay Payment Gateway ─────────────────────────────────────────────────
# Keys are loaded from backend/.env — never hardcode secrets here.
# Test keys from: https://dashboard.razorpay.com/app/keys
RAZORPAY_KEY_ID      = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET  = os.environ.get('RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')

