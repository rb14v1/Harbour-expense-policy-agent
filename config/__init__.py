import os

if os.getenv('CELERY_ENABLED', 'false').lower() == 'true':
    from celery_app import app as celery_app
    __all__ = ('celery_app',)
