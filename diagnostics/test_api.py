#!/usr/bin/env python
"""
Test script for Expense Policy Agent API.
Tests core functionality without requiring Azure credentials.
"""

import os
import sys
import django
import requests
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from receipts.models import Receipt
from receipts.services import (
    FileValidationService,
    HashingService,
    NormalizationService,
    DuplicateService,
    PolicyService,
)
from datetime import date, timedelta
from decimal import Decimal


def test_file_validation():
    print("\n✓ Testing File Validation Service...")
    try:
        # Valid PDF
        class FakeFile:
            size = 1024
        FileValidationService.validate(FakeFile(), "receipt.pdf")
        print("  ✓ PDF validation passed")

        # Invalid file
        try:
            FileValidationService.validate(FakeFile(), "receipt.txt")
            print("  ✗ Should have rejected .txt file")
            return False
        except:
            print("  ✓ Correctly rejected invalid file type")

        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_hashing():
    print("\n✓ Testing Hashing Service...")
    try:
        content = b"test receipt content"
        file_obj = BytesIO(content)
        hash1 = HashingService.sha256(file_obj)
        print(f"  ✓ SHA-256 hash: {hash1}")

        file_obj.seek(0)
        hash2 = HashingService.sha256(file_obj)
        if hash1 == hash2:
            print("  ✓ Consistent hashing")
            return True
        else:
            print("  ✗ Hashes don't match")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_normalization():
    print("\n✓ Testing Normalization Service...")
    try:
        extracted = {
            "merchant": {
                "name": "ABC RESTAURANT",
                "address": None,
                "phone": None
            },
            "invoice": {
                "invoice_number": "INV-001",
                "transaction_date": "2026-09-01"
            },
            "amounts": {
                "subtotal": 100.00,
                "tax": 18.00,
                "total": 118.00,
                "currency": "inr"
            },
            "payment": {"method": None},
            "line_items": [],
            "extraction": {},
        }

        normalized = NormalizationService.normalize(extracted)

        checks = [
            ("Vendor normalized to lowercase", normalized['merchant']['name'] == "abc restaurant"),
            ("Currency normalized to uppercase", normalized['amounts']['currency'] == "INR"),
            ("Date formatted", normalized['invoice']['transaction_date'] == "2026-09-01"),
        ]

        all_passed = True
        for check_name, passed in checks:
            print(f"  {'✓' if passed else '✗'} {check_name}")
            all_passed = all_passed and passed

        return all_passed

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_duplicate_detection():
    print("\n✓ Testing Duplicate Detection...")
    try:
        Receipt.objects.all().delete()

        receipt1 = Receipt.objects.create(
            owner="test-user",
            original_filename="receipt1.pdf",
            blob_name="receipts/test/receipt1.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123def456",
            status="UNIQUE",
            vendor_name="ABC Restaurant",
            vendor_normalized="abc restaurant",
            invoice_number="INV-001",
            invoice_number_normalized="inv-001",
            transaction_date=date(2026, 9, 1),
            total_amount=Decimal("118.00"),
            currency="INR",
            normalized_json={
                "merchant": {"name": "abc restaurant"},
                "invoice": {
                    "invoice_number": "inv-001",
                    "transaction_date": "2026-09-01"
                },
                "amounts": {
                    "total": 118.00,
                    "tax": 18.00,
                    "currency": "INR"
                },
            },
        )

        dup = DuplicateService.find_exact_duplicate("abc123def456", "test-user")
        if dup and dup.id == receipt1.id:
            print("  ✓ Exact duplicate detection working")
        else:
            print("  ✗ Exact duplicate detection failed")
            return False

        receipt2 = Receipt.objects.create(
            owner="test-user",
            original_filename="receipt2.pdf",
            blob_name="receipts/test/receipt2.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="xyz789uvw123",
            status="UNIQUE",
            normalized_json={
                "merchant": {"name": "abc restaurant"},
                "invoice": {
                    "invoice_number": "inv-001",
                    "transaction_date": "2026-09-01"
                },
                "amounts": {
                    "total": 118.00,
                    "tax": 18.00,
                    "currency": "INR"
                },
            },
        )

        result = DuplicateService.evaluate_semantic_duplicate(receipt2)
        if result['is_duplicate']:
            print(f"  ✓ Semantic duplicate detected (score: {result['score']})")
            return True
        else:
            print(f"  ✗ Should have detected semantic duplicate (score: {result['score']})")
            return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_policy_validation():
    print("\n✓ Testing Policy Validation...")
    try:
        recent_receipt = Receipt.objects.create(
            owner="test-user",
            original_filename="recent.pdf",
            blob_name="receipts/test/recent.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="recent123",
            transaction_date=date.today() - timedelta(days=10),
        )

        result = PolicyService.evaluate(recent_receipt)
        if result['status'] == 'APPROVED' and result['rules'][0]['passed']:
            print("  ✓ Recent receipt approved")
        else:
            print("  ✗ Recent receipt should be approved")
            return False

        old_receipt = Receipt.objects.create(
            owner="test-user",
            original_filename="old.pdf",
            blob_name="receipts/test/old.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="old123",
            transaction_date=date.today() - timedelta(days=40),
        )

        result = PolicyService.evaluate(old_receipt)
        if result['status'] == 'REJECTED' and not result['rules'][0]['passed']:
            print("  ✓ Old receipt rejected (>35 days)")
            return True
        else:
            print("  ✗ Old receipt should be rejected")
            return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    print("=" * 60)
    print("EXPENSE POLICY AGENT - SERVICE TESTS")
    print("=" * 60)

    tests = [
        ("File Validation", test_file_validation),
        ("Hashing", test_hashing),
        ("Normalization", test_normalization),
        ("Duplicate Detection", test_duplicate_detection),
        ("Policy Validation", test_policy_validation),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ {name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print("=" * 60)
    print(f"Total: {passed}/{total} passed")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
