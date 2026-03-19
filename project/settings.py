import datetime
import os
from pathlib import Path
from .celery import app as celery_app
from decouple import config as env
from corsheaders.defaults import default_headers

# defining celery app
__all__ = ("celery_app",)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default=False, cast=bool)

# Environment detection
IS_PRODUCTION = env("ENVIRONMENT", default="development") == "production"

# Allowed Hosts
ALLOWED_HOSTS = ["*"]

# Core Django Apps
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# Third Party Apps
THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
    "cachalot",
    "modeltranslation",
]
# Local Apps
LOCAL_APPS = ["accounts"]


# Application definition
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Rest Framework Settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [],
    "DEFAULT_PAGINATION_CLASS": "core.services.pagination.CustomPageNumberPagination",
    "NON_FIELD_ERRORS_KEY": "error",
    "EXCEPTION_HANDLER": "core.services.exceptions.custom_exception_handler",
    "COMPACT_JSON": True,
    "DEFAULT_SCHEMA_CLASS": "core.services.schema.CustomSpectacularAutoSchema",
}


# Swagger Settings
SPECTACULAR_SETTINGS = {
    "TITLE": "API Documentation",
    "DESCRIPTION": "Documentation for the APIs provided by this project.",
    "VERSION": "v1",
    "SERVE_INCLUDE_SCHEMA": False,
    "DEFAULT_SCHEMA_CLASS": "core.services.schema.CustomSpectacularAutoSchema",
    # JWT Authentication
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "jwtAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": (
                    "**Enter only your JWT access token** (do NOT include 'Bearer' prefix).\n\n"
                    "The 'Bearer' prefix will be added automatically.\n\n"
                    "Example token: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`"
                ),
            }
        }
    },
    # Apply JWT auth globally
    "SECURITY": [{"jwtAuth": []}],
    # POSTPROCESSING hook for X-Language header and error responses
    "POSTPROCESSING_HOOKS": [
        "core.services.schema.preprocess_spectacular_hook",
    ],
    # UI Settings
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": False,
        "docExpansion": "none",  # Keep endpoints COLLAPSED
        "defaultModelsExpandDepth": -1,  # Expand ALL schema definitions
        "defaultModelExpandDepth": 4,  # Expand up to 4 levels deep in response schemas
        "filter": True,
        "displayRequestDuration": True,
    },
    # Component settings
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/apis/",
}

# JWT Settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(days=15),
    "REFRESH_TOKEN_LIFETIME": datetime.timedelta(days=30),
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middlewares.translate.LanguageMiddleware",
]

ROOT_URLCONF = "project.urls"

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

# Login URL
LOGIN_URL = "/admin/login/"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = "project.wsgi.application"

# ========================================
# DATABASE CONFIGURATION WITH ENVIRONMENT OPTIMIZATIONS
# ========================================

if env("USE_SQLITE", default=False, cast=bool):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "OPTIONS": {
                "timeout": 10,
            },
        }
    }
else:
    # Base database configuration
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB"),
            "USER": env("POSTGRES_USER"),
            "PASSWORD": env("POSTGRES_PASSWORD"),
            "HOST": env("DB_HOST"),
            "PORT": env("DB_PORT", default=5432, cast=int),
        }
    }

# ========================================
# CACHING CONFIGURATION (ENVIRONMENT-SPECIFIC)
# ========================================
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_CACHE_URL", default="redis://127.0.0.1:6379/1"),
    }
}

# CACHALOT Configuration
CACHALOT_ENABLED = env("CACHALOT_ENABLED", default=True, cast=bool)

if CACHALOT_ENABLED:
    # Default timeout for Cachalot
    CACHALOT_TIMEOUT = 1800 if IS_PRODUCTION else 900
    CACHALOT_CACHE = "default"

    # App-specific caching - your apps only
    CACHALOT_ONLY_CACHABLE_APPS = ["accounts"]

    # Tables to never cache
    CACHALOT_UNCACHABLE_TABLES = frozenset(
        [
            "django_session",
            "django_admin_log",
            "django_migrations",
            "django_content_type",
            "auth_permission",
        ]
    )

# ========================================
# CELERY CONFIGURATION (ENVIRONMENT-SPECIFIC)
# ========================================

CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
# ========================================
# STATIC FILES CONFIGURATION
# ========================================

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "staticfiles"),
]

# Static files finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# Media files configuration
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# File upload optimization
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB


# Email settings
EMAIL_SERVICE_ACTIVE = env("EMAIL_SERVICE_ACTIVE", default=True, cast=bool)
RESEND_API_KEY = env("RESEND_API_KEY")
DEFAULT_FROM_EMAIL = env("EMAIL_FROM")

# OTP Settings
OTP_EXPIRATION_TIME = 15  # in minutes

# ========================================
# SECURITY SETTINGS (ENVIRONMENT-SPECIFIC)
# ========================================

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_USER_LANGUAGE = "en"

LOCALE_PATHS = [
    os.path.join(BASE_DIR, "locale"),
]
# Define your three languages
LANGUAGES = (
    ("en", "English"),
    ("ar", "Arabic"),
)

MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_FALLBACK_LANGUAGES = ("en", "ar")

# Optional: Auto-populate from default language if translation missing
MODELTRANSLATION_AUTO_POPULATE = True

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Site URL
SITE_URL = env("SITE_URL")

# ========================================
# CORS & CSRF CONFIGURATION
# ========================================

# Trusted Origins - for CSRF protection
TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://epms.urbatech.io",
]

# CORS settings - Allow ALL origins
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True  # Allow cookies and auth headers
CORS_ALLOW_HEADERS = list(default_headers) + [
    "X-Language",
]

# CSRF settings
CSRF_TRUSTED_ORIGINS = TRUSTED_ORIGINS
CSRF_USE_SESSIONS = IS_PRODUCTION

# ========================================
# SECURITY CONFIGURATION (ENVIRONMENT-SPECIFIC)
# ========================================

if IS_PRODUCTION:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    # Production performance optimizations
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = "DENY"
