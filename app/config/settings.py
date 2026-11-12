import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

load_dotenv()


def _require_env(name, allow_empty=False):
    """Return a required environment variable or fail fast at startup."""
    value = os.getenv(name)
    if value is None or (not allow_empty and value.strip() == ''):
        raise ImproperlyConfigured(
            f"Required environment variable '{name}' is not set. See .env.example."
        )
    return value


BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = _require_env('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = _require_env('DJANGO_ALLOWED_HOSTS').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'corsheaders',
    'receipts',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

if os.getenv('USE_SQLITE', 'False') == 'True':
    DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': _require_env('POSTGRES_DB'),
            'USER': _require_env('POSTGRES_USER'),
            'PASSWORD': _require_env('POSTGRES_PASSWORD', allow_empty=True),
            'HOST': _require_env('POSTGRES_HOST'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': ['rest_framework.filters.SearchFilter'],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
}

CORS_ALLOWED_ORIGINS = _require_env('CORS_ALLOWED_ORIGINS').split(',')

MAX_RECEIPT_UPLOAD_MB = int(os.getenv('MAX_RECEIPT_UPLOAD_MB', '10'))
RECEIPT_MAX_AGE_DAYS = int(os.getenv('RECEIPT_MAX_AGE_DAYS', '35'))
DUPLICATE_SCORE_THRESHOLD = int(os.getenv('DUPLICATE_SCORE_THRESHOLD', '90'))
REVIEW_SCORE_THRESHOLD = int(os.getenv('REVIEW_SCORE_THRESHOLD', '75'))

AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
AZURE_STORAGE_CONTAINER_NAME = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'receipts')

AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
AZURE_DOCUMENT_INTELLIGENCE_KEY = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')

CELERY_BROKER_URL = _require_env('REDIS_URL')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
