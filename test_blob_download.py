#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.config.settings')
django.setup()

from receipts.models import Receipt
from receipts.services.blob_service import BlobService
import traceback

print("\n=== BLOB DOWNLOAD TEST ===\n")

receipt_ids = [
    '54316958-5096-43b5-9973-14aaa0918598',
    'aec17325-1955-4db1-8c94-f24e010d8d2f',
]

for receipt_id in receipt_ids:
    try:
        receipt = Receipt.objects.get(id=receipt_id)
        print(f"Receipt ID: {receipt_id}")
        print(f"  Blob name: {receipt.blob_name}")
        print(f"  Status: {receipt.status}")

        if not receipt.blob_name:
            print(f"  ERROR: No blob_name set!")
            continue

        blob_service = BlobService()
        try:
            file_bytes = blob_service.download(receipt.blob_name)
            print(f"  SUCCESS: Downloaded {len(file_bytes)} bytes")
        except Exception as e:
            print(f"  FAILED: {type(e).__name__}: {str(e)}")

    except Receipt.DoesNotExist:
        print(f"Receipt ID: {receipt_id} - NOT FOUND")
    except Exception as e:
        print(f"Receipt ID: {receipt_id} - ERROR: {str(e)}")

    print()
