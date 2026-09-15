from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from receipts.models import Receipt
from receipts.services import (
    HashingService,
    FileValidationService,
    NormalizationService,
    DuplicateService,
    PolicyService,
)
from receipts.exceptions import UnsupportedFileTypeError, ReceiptTooLargeError
from datetime import datetime, timedelta, date
from decimal import Decimal
import io


class FileValidationServiceTests(TestCase):
    def test_valid_pdf(self):
        file = SimpleUploadedFile("receipt.pdf", b"fake pdf", content_type="application/pdf")
        FileValidationService.validate(file, "receipt.pdf")

    def test_valid_jpg(self):
        file = SimpleUploadedFile("receipt.jpg", b"fake jpg", content_type="image/jpeg")
        FileValidationService.validate(file, "receipt.jpg")

    def test_invalid_extension(self):
        file = SimpleUploadedFile("receipt.txt", b"fake txt", content_type="text/plain")
        with self.assertRaises(UnsupportedFileTypeError):
            FileValidationService.validate(file, "receipt.txt")

    @override_settings(MAX_RECEIPT_UPLOAD_MB=5)
    def test_oversized_file(self):
        file = SimpleUploadedFile(
            "receipt.pdf",
            b"x" * (6 * 1024 * 1024),
            content_type="application/pdf"
        )
        with self.assertRaises(ReceiptTooLargeError):
            FileValidationService.validate(file, "receipt.pdf")


class HashingServiceTests(TestCase):
    def test_sha256_hash(self):
        content = b"test content"
        file_obj = io.BytesIO(content)
        hash_value = HashingService.sha256(file_obj)
        self.assertEqual(len(hash_value), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_value))

    def test_same_content_same_hash(self):
        content = b"test content"
        file_obj1 = io.BytesIO(content)
        file_obj2 = io.BytesIO(content)
        hash1 = HashingService.sha256(file_obj1)
        hash2 = HashingService.sha256(file_obj2)
        self.assertEqual(hash1, hash2)

    def test_different_content_different_hash(self):
        file_obj1 = io.BytesIO(b"content1")
        file_obj2 = io.BytesIO(b"content2")
        hash1 = HashingService.sha256(file_obj1)
        hash2 = HashingService.sha256(file_obj2)
        self.assertNotEqual(hash1, hash2)


class NormalizationServiceTests(TestCase):
    def test_normalize_vendor_name(self):
        extracted = {
            "merchant": {"name": "ABC RESTAURANT PVT LTD", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": None},
            "amounts": {"subtotal": None, "tax": None, "total": None, "currency": None},
            "payment": {"method": None},
            "line_items": [],
            "extraction": {},
        }
        normalized = NormalizationService.normalize(extracted)
        self.assertEqual(normalized['merchant']['name'], "abc restaurant pvt ltd")

    def test_normalize_date(self):
        extracted = {
            "merchant": {"name": "ABC", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": "2026-09-01T10:30:00Z"},
            "amounts": {"subtotal": None, "tax": None, "total": None, "currency": None},
            "payment": {"method": None},
            "line_items": [],
            "extraction": {},
        }
        normalized = NormalizationService.normalize(extracted)
        self.assertEqual(normalized['invoice']['transaction_date'], "2026-09-01")

    def test_normalize_currency(self):
        extracted = {
            "merchant": {"name": None, "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": None},
            "amounts": {"subtotal": None, "tax": None, "total": None, "currency": "inr"},
            "payment": {"method": None},
            "line_items": [],
            "extraction": {},
        }
        normalized = NormalizationService.normalize(extracted)
        self.assertEqual(normalized['amounts']['currency'], "INR")


class DuplicateServiceTests(TestCase):
    def setUp(self):
        self.receipt1 = Receipt.objects.create(
            owner="user1",
            original_filename="receipt1.pdf",
            blob_name="receipts/user1/uuid/receipt1.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
            status="UNIQUE",
            vendor_name="ABC Restaurant",
            vendor_normalized="abc restaurant",
            invoice_number="INV-001",
            invoice_number_normalized="inv-001",
            transaction_date=date(2026, 9, 1),
            total_amount=Decimal("1000.00"),
            currency="INR",
            normalized_json={
                "merchant": {"name": "abc restaurant"},
                "invoice": {
                    "invoice_number": "inv-001",
                    "transaction_date": "2026-09-01"
                },
                "amounts": {
                    "total": 1000.00,
                    "tax": 100.00,
                    "currency": "INR"
                },
            },
        )

    def test_find_exact_duplicate(self):
        dup = DuplicateService.find_exact_duplicate("abc123", "user1")
        self.assertEqual(dup.id, self.receipt1.id)

    def test_find_exact_duplicate_not_found(self):
        dup = DuplicateService.find_exact_duplicate("xyz789", "user1")
        self.assertIsNone(dup)

    def test_duplicate_score_same_invoice_and_vendor(self):
        receipt2 = Receipt.objects.create(
            owner="user1",
            original_filename="receipt2.pdf",
            blob_name="receipts/user1/uuid/receipt2.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="def456",
            status="UNIQUE",
            normalized_json={
                "merchant": {"name": "abc restaurant"},
                "invoice": {
                    "invoice_number": "inv-001",
                    "transaction_date": "2026-09-01"
                },
                "amounts": {
                    "total": 1000.00,
                    "tax": 100.00,
                    "currency": "INR"
                },
            },
        )

        result = DuplicateService.evaluate_semantic_duplicate(receipt2)
        self.assertTrue(result['is_duplicate'])
        self.assertGreaterEqual(result['score'], 60)


class PolicyServiceTests(TestCase):
    def test_receipt_within_age_limit(self):
        receipt = Receipt.objects.create(
            owner="user1",
            original_filename="receipt.pdf",
            blob_name="receipts/user1/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
            transaction_date=date.today() - timedelta(days=10),
        )
        result = PolicyService.evaluate(receipt)
        self.assertEqual(result['status'], 'APPROVED')
        self.assertTrue(result['rules'][0]['passed'])

    @override_settings(RECEIPT_MAX_AGE_DAYS=35)
    def test_receipt_exceeds_age_limit(self):
        receipt = Receipt.objects.create(
            owner="user1",
            original_filename="receipt.pdf",
            blob_name="receipts/user1/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
            transaction_date=date.today() - timedelta(days=40),
        )
        result = PolicyService.evaluate(receipt)
        self.assertEqual(result['status'], 'REJECTED')
        self.assertFalse(result['rules'][0]['passed'])
