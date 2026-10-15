#!/usr/bin/env python
"""Test the exact duplicate detection fix with A, B, C, D scenarios."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['USE_SQLITE'] = 'True'
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from receipts.services import ReceiptService
from receipts.models import Receipt
from receipts.exceptions import BlobUploadError
import hashlib

def sha256_file(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

# Clear database
Receipt.objects.all().delete()
print("=" * 80)
print("EXACT DUPLICATE DETECTION FIX VERIFICATION")
print("=" * 80)
print("\n✅ Database cleared\n")

# Test files
file_1_path = "data/sample_receipts/test_receipt.pdf"
file_2_path = "data/sample_receipts/test_receipt_unique.pdf"

hash_1 = sha256_file(file_1_path)
hash_2 = sha256_file(file_2_path)

print(f"Test file 1: test_receipt.pdf")
print(f"  SHA-256: {hash_1[:32]}...\n")

print(f"Test file 2: test_receipt_unique.pdf")
print(f"  SHA-256: {hash_2[:32]}...\n")

# ===== TEST A: First PDF upload =====
print("=" * 80)
print("TEST A: Upload brand-new PDF (test_receipt.pdf)")
print("=" * 80)
print("Expected: NOT duplicate\n")

receipt_a = None
try:
    with open(file_1_path, 'rb') as f:
        file_obj = SimpleUploadedFile(
            name="test_receipt.pdf",
            content=f.read(),
            content_type="application/pdf"
        )
        service = ReceiptService()
        receipt_a = service.create_and_upload_receipt(
            file_obj=file_obj,
            filename="test_receipt.pdf",
            owner="test-user"
        )
except BlobUploadError as e:
    # Blob upload fails due to missing Azure creds, but duplicate check already passed
    # Get the receipt from DB to check its status at the point of Blob upload attempt
    receipts = Receipt.objects.all().order_by('-created_at')
    if receipts:
        receipt_a = receipts[0]
        print(f"Note: Blob upload failed (expected - no Azure creds), but duplicate check passed")

if receipt_a:
    print(f"Result:")
    print(f"  Receipt ID: {receipt_a.id}")
    print(f"  Status: {receipt_a.status}")
    print(f"  Is duplicate: {receipt_a.exact_duplicate_of is not None}")

    if receipt_a.status == "QUEUED_FOR_OCR" and receipt_a.exact_duplicate_of is None:
        print("✅ PASS: First upload is NOT marked as duplicate\n")
    else:
        print(f"❌ FAIL: Expected status QUEUED_FOR_OCR, got {receipt_a.status}\n")
else:
    print("❌ FAIL: Could not create receipt\n")

# ===== TEST B: Same PDF again =====
print("=" * 80)
print("TEST B: Upload same PDF again (test_receipt.pdf)")
print("=" * 80)
print("Expected: EXACT_DUPLICATE\n")

receipt_b = None
try:
    with open(file_1_path, 'rb') as f:
        file_obj = SimpleUploadedFile(
            name="test_receipt.pdf",
            content=f.read(),
            content_type="application/pdf"
        )
        service = ReceiptService()
        receipt_b = service.create_and_upload_receipt(
            file_obj=file_obj,
            filename="test_receipt.pdf",
            owner="test-user"
        )
except BlobUploadError:
    receipts = Receipt.objects.all().order_by('-created_at')
    if len(receipts) >= 2:
        receipt_b = receipts[0]

if receipt_b:
    print(f"Result:")
    print(f"  Receipt ID: {receipt_b.id}")
    print(f"  Status: {receipt_b.status}")
    print(f"  Exact duplicate of: {receipt_b.exact_duplicate_of_id}")

    if receipt_b.status == "EXACT_DUPLICATE" and receipt_b.exact_duplicate_of_id == receipt_a.id:
        print(f"✅ PASS: Second upload correctly marked as EXACT_DUPLICATE of {receipt_a.id}\n")
    else:
        print(f"❌ FAIL: Expected EXACT_DUPLICATE of {receipt_a.id}, got status {receipt_b.status}\n")
else:
    print("❌ FAIL: Could not create receipt\n")

# ===== TEST C: Different PDF =====
print("=" * 80)
print("TEST C: Upload different PDF (test_receipt_unique.pdf)")
print("=" * 80)
print("Expected: NOT duplicate\n")

receipt_c = None
try:
    with open(file_2_path, 'rb') as f:
        file_obj = SimpleUploadedFile(
            name="test_receipt_unique.pdf",
            content=f.read(),
            content_type="application/pdf"
        )
        service = ReceiptService()
        receipt_c = service.create_and_upload_receipt(
            file_obj=file_obj,
            filename="test_receipt_unique.pdf",
            owner="test-user"
        )
except BlobUploadError:
    receipts = Receipt.objects.all().order_by('-created_at')
    if len(receipts) >= 3:
        receipt_c = receipts[0]

if receipt_c:
    print(f"Result:")
    print(f"  Receipt ID: {receipt_c.id}")
    print(f"  Status: {receipt_c.status}")
    print(f"  Is duplicate: {receipt_c.exact_duplicate_of is not None}")

    if receipt_c.status == "QUEUED_FOR_OCR" and receipt_c.exact_duplicate_of is None:
        print("✅ PASS: Different file is NOT marked as duplicate\n")
    else:
        print(f"❌ FAIL: Expected status QUEUED_FOR_OCR, got {receipt_c.status}\n")
else:
    print("❌ FAIL: Could not create receipt\n")

# ===== TEST D: Same different PDF again =====
print("=" * 80)
print("TEST D: Upload same different PDF again (test_receipt_unique.pdf)")
print("=" * 80)
print("Expected: EXACT_DUPLICATE\n")

receipt_d = None
try:
    with open(file_2_path, 'rb') as f:
        file_obj = SimpleUploadedFile(
            name="test_receipt_unique.pdf",
            content=f.read(),
            content_type="application/pdf"
        )
        service = ReceiptService()
        receipt_d = service.create_and_upload_receipt(
            file_obj=file_obj,
            filename="test_receipt_unique.pdf",
            owner="test-user"
        )
except BlobUploadError:
    receipts = Receipt.objects.all().order_by('-created_at')
    if len(receipts) >= 4:
        receipt_d = receipts[0]

if receipt_d:
    print(f"Result:")
    print(f"  Receipt ID: {receipt_d.id}")
    print(f"  Status: {receipt_d.status}")
    print(f"  Exact duplicate of: {receipt_d.exact_duplicate_of_id}")

    if receipt_d.status == "EXACT_DUPLICATE" and receipt_d.exact_duplicate_of_id == receipt_c.id:
        print(f"✅ PASS: Second upload of different file correctly marked as EXACT_DUPLICATE of {receipt_c.id}\n")
    else:
        print(f"❌ FAIL: Expected EXACT_DUPLICATE of {receipt_c.id}, got status {receipt_d.status}\n")
else:
    print("❌ FAIL: Could not create receipt\n")

# ===== SUMMARY =====
print("=" * 80)
print("SUMMARY")
print("=" * 80)

results = {
    "A (First PDF - should NOT be duplicate)": receipt_a.status == "QUEUED_FOR_OCR" and receipt_a.exact_duplicate_of is None,
    "B (Same PDF again - should be EXACT_DUPLICATE)": receipt_b.status == "EXACT_DUPLICATE" and receipt_b.exact_duplicate_of_id == receipt_a.id,
    "C (Different PDF - should NOT be duplicate)": receipt_c.status == "QUEUED_FOR_OCR" and receipt_c.exact_duplicate_of is None,
    "D (Same different PDF - should be EXACT_DUPLICATE)": receipt_d.status == "EXACT_DUPLICATE" and receipt_d.exact_duplicate_of_id == receipt_c.id,
}

all_pass = True
for test, passed in results.items():
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test}")
    if not passed:
        all_pass = False

print("\n" + "=" * 80)
if all_pass:
    print("🎉 ALL TESTS PASS - FIX IS WORKING CORRECTLY")
else:
    print("⚠️  SOME TESTS FAILED - FIX NEEDS ADJUSTMENT")
print("=" * 80)
