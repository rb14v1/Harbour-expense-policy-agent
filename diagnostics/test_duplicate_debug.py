#!/usr/bin/env python
"""Test duplicate detection with debug output."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['USE_SQLITE'] = 'True'
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from receipts.services import ReceiptService
import hashlib

def sha256_file(path):
    """Calculate SHA-256 of a file."""
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

# Clear database before test
from receipts.models import Receipt
Receipt.objects.all().delete()
print("✅ Database cleared\n")

# Test files
test_file_1 = "data/sample_receipts/test_receipt.pdf"
test_file_2 = "data/sample_receipts/test_receipt_unique.pdf"

# Calculate expected hashes
hash_1 = sha256_file(test_file_1)
hash_2 = sha256_file(test_file_2)

print(f"Expected SHA-256 for test_receipt.pdf:        {hash_1}")
print(f"Expected SHA-256 for test_receipt_unique.pdf: {hash_2}")
print(f"Hashes are different: {hash_1 != hash_2}\n")
print("=" * 100)

# Upload 1: First PDF
print("\n\n📋 TEST 1: UPLOADING test_receipt.pdf (First upload - should NOT be duplicate)")
print("=" * 100)

with open(test_file_1, 'rb') as f:
    file_obj = SimpleUploadedFile(
        name="test_receipt.pdf",
        content=f.read(),
        content_type="application/pdf"
    )

    service = ReceiptService()
    receipt_1 = service.create_and_upload_receipt(
        file_obj=file_obj,
        filename="test_receipt.pdf",
        owner="test-user"
    )

    print(f"\n✅ Upload 1 Result:")
    print(f"   Receipt ID: {receipt_1.id}")
    print(f"   Status: {receipt_1.status}")
    print(f"   Stored SHA-256: {receipt_1.sha256_hash}")
    print(f"   Expected: {hash_1}")
    print(f"   Match: {receipt_1.sha256_hash == hash_1}")

# Upload 2: Different PDF
print("\n\n📋 TEST 2: UPLOADING test_receipt_unique.pdf (Different file - should NOT be duplicate)")
print("=" * 100)

with open(test_file_2, 'rb') as f:
    file_obj = SimpleUploadedFile(
        name="test_receipt_unique.pdf",
        content=f.read(),
        content_type="application/pdf"
    )

    service = ReceiptService()
    receipt_2 = service.create_and_upload_receipt(
        file_obj=file_obj,
        filename="test_receipt_unique.pdf",
        owner="test-user"
    )

    print(f"\n✅ Upload 2 Result:")
    print(f"   Receipt ID: {receipt_2.id}")
    print(f"   Status: {receipt_2.status}")
    print(f"   Stored SHA-256: {receipt_2.sha256_hash}")
    print(f"   Expected: {hash_2}")
    print(f"   Match: {receipt_2.sha256_hash == hash_2}")

# Upload 3: First PDF again (should be exact duplicate)
print("\n\n📋 TEST 3: UPLOADING test_receipt.pdf AGAIN (Same file - SHOULD be duplicate)")
print("=" * 100)

with open(test_file_1, 'rb') as f:
    file_obj = SimpleUploadedFile(
        name="test_receipt.pdf",
        content=f.read(),
        content_type="application/pdf"
    )

    service = ReceiptService()
    receipt_3 = service.create_and_upload_receipt(
        file_obj=file_obj,
        filename="test_receipt.pdf",
        owner="test-user"
    )

    print(f"\n✅ Upload 3 Result:")
    print(f"   Receipt ID: {receipt_3.id}")
    print(f"   Status: {receipt_3.status}")
    print(f"   Stored SHA-256: {receipt_3.sha256_hash}")
    print(f"   Expected: {hash_1}")
    print(f"   Match: {receipt_3.sha256_hash == hash_1}")

# Summary
print("\n\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"\nUpload 1 (test_receipt.pdf):")
print(f"  Status: {receipt_1.status} (Expected: QUEUED_FOR_OCR or similar, NOT EXACT_DUPLICATE)")
print(f"  SHA-256: {receipt_1.sha256_hash[:32]}...")

print(f"\nUpload 2 (test_receipt_unique.pdf - DIFFERENT FILE):")
print(f"  Status: {receipt_2.status} (Expected: QUEUED_FOR_OCR or similar, NOT EXACT_DUPLICATE)")
print(f"  SHA-256: {receipt_2.sha256_hash[:32]}...")
print(f"  ⚠️  This MUST NOT be marked as EXACT_DUPLICATE!")

print(f"\nUpload 3 (test_receipt.pdf AGAIN - SAME FILE as Upload 1):")
print(f"  Status: {receipt_3.status} (Expected: EXACT_DUPLICATE)")
print(f"  SHA-256: {receipt_3.sha256_hash[:32]}...")
print(f"  Exact duplicate of: {receipt_3.exact_duplicate_of_id}")

print("\n" + "=" * 100)
