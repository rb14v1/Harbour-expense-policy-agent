import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-key-not-for-production')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'receipts',
    'finance',
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
            'NAME': os.getenv('POSTGRES_DB', 'expense_policy'),
            'USER': os.getenv('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
            'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
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

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

MAX_RECEIPT_UPLOAD_MB = int(os.getenv('MAX_RECEIPT_UPLOAD_MB', '50'))
MAX_RECEIPT_COMPRESSION_THRESHOLD_MB = int(os.getenv('MAX_RECEIPT_COMPRESSION_THRESHOLD_MB', '5'))
RECEIPT_MAX_AGE_DAYS = int(os.getenv('RECEIPT_MAX_AGE_DAYS', '35'))
DUPLICATE_SCORE_THRESHOLD = int(os.getenv('DUPLICATE_SCORE_THRESHOLD', '90'))
REVIEW_SCORE_THRESHOLD = int(os.getenv('REVIEW_SCORE_THRESHOLD', '75'))

# Hybrid Category Classifier Configuration
CLASSIFIER_KEYWORD_WEIGHT = float(os.getenv('CLASSIFIER_KEYWORD_WEIGHT', '0.6'))
CLASSIFIER_SEMANTIC_WEIGHT = float(os.getenv('CLASSIFIER_SEMANTIC_WEIGHT', '0.4'))
CLASSIFIER_CONFIDENCE_THRESHOLD = float(os.getenv('CLASSIFIER_CONFIDENCE_THRESHOLD', '0.75'))
CLASSIFIER_AMBIGUITY_MARGIN = float(os.getenv('CLASSIFIER_AMBIGUITY_MARGIN', '0.10'))
CLASSIFIER_SEMANTIC_MODEL = os.getenv('CLASSIFIER_SEMANTIC_MODEL', 'all-MiniLM-L6-v2')

# File compression configuration
IMAGE_COMPRESSION_QUALITY = int(os.getenv('IMAGE_COMPRESSION_QUALITY', '75'))
IMAGE_MAX_PIXELS = int(os.getenv('IMAGE_MAX_PIXELS', '8000000'))
PDF_COMPRESSION_ENABLED = os.getenv('PDF_COMPRESSION_ENABLED', 'True').lower() == 'true'

# Django upload limits - allow files larger than application limit so we can return proper error
# Default Django values are ~2.5MB each, which reject large files before our validation
# Set to 10MB to allow our application validation (5MB limit) to handle the error response
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('FILE_UPLOAD_MAX_MEMORY_SIZE', '10485760'))
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('DATA_UPLOAD_MAX_MEMORY_SIZE', '10485760'))

AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
AZURE_STORAGE_CONTAINER_NAME = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'receipts')

AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
AZURE_DOCUMENT_INTELLIGENCE_KEY = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')

CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Teams / Azure Entra Configuration
TEAMS_APP_ID = os.getenv('CLIENT_ID', '')
TEAMS_APP_PASSWORD = os.getenv('CLIENT_SECRET', '')
TENANT_ID = os.getenv('TENANT_ID', '')
TEAMS_SERVICE_URL = os.getenv('TEAMS_SERVICE_URL', 'https://smba.trafficmanager.net/apis/')

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

# User Manual Configuration
MANUAL_BLOB_PATH = os.getenv('MANUAL_BLOB_PATH', 'documentation/expense_policy_agent_user_manual.html')
