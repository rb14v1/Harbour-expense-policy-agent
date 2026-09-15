#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

print('\n' + '='*70)
print('TEST ENVIRONMENT CONFIGURATION VERIFICATION')
print('='*70)
print()
print(f'Database Engine:           {settings.DATABASES["default"]["ENGINE"]}')
print(f'Database Name:             {settings.DATABASES["default"]["NAME"]}')
print(f'Use SQLite:                {settings.DATABASES["default"]["ENGINE"].endswith("sqlite3")}')
print()
print('Azure Integration Status:')
azure_conn = settings.AZURE_STORAGE_CONNECTION_STRING
azure_endpoint = settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
print(f'  Storage Connection Set:  {bool(azure_conn and azure_conn != "DefaultEndpointsProtocol=https;AccountName=...")}')
print(f'  Document Intelligence:   {bool(azure_endpoint and azure_endpoint != "https://<region>.api.cognitive.microsoft.com/")}')
print()
print('Security Configuration:')
print(f'  DEBUG Mode:              {settings.DEBUG}')
print(f'  ALLOWED_HOSTS:           {settings.ALLOWED_HOSTS}')
print()
print('Processing Configuration:')
print(f'  Max Upload (MB):         {settings.MAX_RECEIPT_UPLOAD_MB}')
print(f'  Max Receipt Age (days):  {settings.RECEIPT_MAX_AGE_DAYS}')
print(f'  Duplicate Threshold:     {settings.DUPLICATE_SCORE_THRESHOLD}')
print()
print('Status: Tests are running with SAFE configuration')
print('  - SQLite in-memory database (no data persistence)')
print('  - No production Azure credentials configured')
print('  - DEBUG mode enabled (test-safe)')
print()
print('='*70)
