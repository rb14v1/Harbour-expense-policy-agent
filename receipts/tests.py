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
        pdf_content = (
            b"%PDF-1.4\n"
            b"%\xE2\xE3\xCF\xD3\n"
            b"1 0 obj\n"
            b"<</Type/Catalog/Pages 2 0 R>>\n"
            b"endobj\n"
            b"2 0 obj\n"
            b"<</Type/Pages/Kids[3 0 R]/Count 1>>\n"
            b"endobj\n"
            b"3 0 obj\n"
            b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>\n"
            b"endobj\n"
            b"xref\n"
            b"0 4\n"
            b"0000000000 65535 f\n"
            b"0000000009 00000 n\n"
            b"0000000074 00000 n\n"
            b"0000000133 00000 n\n"
            b"trailer\n"
            b"<</Size 4/Root 1 0 R>>\n"
            b"startxref\n"
            b"190\n"
            b"%%EOF"
        )
        file = SimpleUploadedFile("receipt.pdf", pdf_content, content_type="application/pdf")
        FileValidationService.validate(file, "receipt.pdf")

    def test_valid_jpg(self):
        jpg_content = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"JFIF" + (b"x" * 200) + bytes([0xFF, 0xD9])
        file = SimpleUploadedFile("receipt.jpg", jpg_content, content_type="image/jpeg")
        with self.assertRaises(UnsupportedFileTypeError):
            FileValidationService.validate(file, "receipt.jpg")

    def test_valid_png(self):
        png_header = b'\x89PNG\r\n\x1a\n'
        file = SimpleUploadedFile("receipt.png", png_header + (b"x" * 200), content_type="image/png")
        with self.assertRaises(UnsupportedFileTypeError):
            FileValidationService.validate(file, "receipt.png")

    def test_invalid_extension(self):
        file = SimpleUploadedFile("receipt.txt", b"fake txt", content_type="text/plain")
        with self.assertRaises(UnsupportedFileTypeError):
            FileValidationService.validate(file, "receipt.txt")

    def test_empty_file(self):
        file = SimpleUploadedFile("receipt.pdf", b"", content_type="application/pdf")
        with self.assertRaises(UnsupportedFileTypeError) as ctx:
            FileValidationService.validate(file, "receipt.pdf")
        self.assertIn("empty", str(ctx.exception).lower())

    def test_invalid_pdf_header(self):
        file = SimpleUploadedFile("receipt.pdf", b"NOTAPDF content", content_type="application/pdf")
        with self.assertRaises(UnsupportedFileTypeError) as ctx:
            FileValidationService.validate(file, "receipt.pdf")
        self.assertIn("pdf", str(ctx.exception).lower())

    def test_pdf_missing_endobj(self):
        pdf_content = b"%PDF-1.4\n" + (b"x" * 150) + b"\n1 0 obj\n<</Type/Catalog>>\n%%EOF"
        file = SimpleUploadedFile("receipt.pdf", pdf_content, content_type="application/pdf")
        with self.assertRaises(UnsupportedFileTypeError) as ctx:
            FileValidationService.validate(file, "receipt.pdf")
        self.assertIn("obj", str(ctx.exception).lower())

    def test_pdf_missing_eof(self):
        pdf_content = b"%PDF-1.4\n" + (b"x" * 150) + b"\n1 0 obj\n<</Type/Catalog>>\nendobj\n"
        file = SimpleUploadedFile("receipt.pdf", pdf_content, content_type="application/pdf")
        with self.assertRaises(UnsupportedFileTypeError) as ctx:
            FileValidationService.validate(file, "receipt.pdf")
        self.assertIn("eof", str(ctx.exception).lower())

    def test_invalid_jpeg_header(self):
        file = SimpleUploadedFile("receipt.jpg", b"NOTAJPG" + b"content", content_type="image/jpeg")
        with self.assertRaises(UnsupportedFileTypeError) as ctx:
            FileValidationService.validate(file, "receipt.jpg")
        self.assertIn("jpeg", str(ctx.exception).lower())

    def test_invalid_png_header(self):
        file = SimpleUploadedFile("receipt.png", b"NOTAPNG" + b"content", content_type="image/png")
        with self.assertRaises(UnsupportedFileTypeError) as ctx:
            FileValidationService.validate(file, "receipt.png")
        self.assertIn("png", str(ctx.exception).lower())

    @override_settings(MAX_RECEIPT_UPLOAD_MB=5)
    def test_oversized_file(self):
        pdf_content = b"%PDF-1.4\n" + (b"x" * (6 * 1024 * 1024))
        file = SimpleUploadedFile(
            "receipt.pdf",
            pdf_content,
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
        self.assertEqual(normalized['vendor_name'], "ABC RESTAURANT PVT LTD")
        self.assertEqual(normalized['vendor_normalized'], "abc restaurant pvt ltd")

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
        self.assertEqual(normalized['transaction_date'], "2026-09-01")

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
        self.assertEqual(normalized['currency'], "INR")


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
                "vendor_name": "ABC Restaurant",
                "vendor_normalized": "abc restaurant",
                "invoice_number": "INV-001",
                "invoice_number_normalized": "inv-001",
                "transaction_date": "2026-09-01",
                "subtotal": None,
                "tax_amount": 100.00,
                "total_amount": 1000.00,
                "currency": "INR",
                "payment_method": None,
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
            vendor_name="ABC Restaurant",
            vendor_normalized="abc restaurant",
            invoice_number="INV-001",
            invoice_number_normalized="inv-001",
            transaction_date=date(2026, 9, 1),
            total_amount=Decimal("1000.00"),
            currency="INR",
            normalized_json={
                "vendor_name": "ABC Restaurant",
                "vendor_normalized": "abc restaurant",
                "invoice_number": "INV-001",
                "invoice_number_normalized": "inv-001",
                "transaction_date": "2026-09-01",
                "subtotal": None,
                "tax_amount": 100.00,
                "total_amount": 1000.00,
                "currency": "INR",
                "payment_method": None,
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


class ReceiptListSerializerTests(TestCase):
    def test_receipt_list_includes_category(self):
        receipt = Receipt.objects.create(
            owner="user1",
            original_filename="receipt.pdf",
            blob_name="receipts/user1/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
            category="Meals",
        )
        from receipts.serializers import ReceiptListSerializer
        serializer = ReceiptListSerializer(receipt)
        self.assertIn('category', serializer.data)
        self.assertEqual(serializer.data['category'], 'Meals')

    def test_receipt_list_includes_processing_message(self):
        receipt = Receipt.objects.create(
            owner="user1",
            original_filename="receipt.pdf",
            blob_name="receipts/user1/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
            processing_message="Receipt has been validated and approved.",
        )
        from receipts.serializers import ReceiptListSerializer
        serializer = ReceiptListSerializer(receipt)
        self.assertIn('processing_message', serializer.data)
        self.assertEqual(serializer.data['processing_message'], 'Receipt has been validated and approved.')

    def test_receipt_detail_includes_all_fields(self):
        receipt = Receipt.objects.create(
            owner="user1",
            original_filename="receipt.pdf",
            blob_name="receipts/user1/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
            vendor_name="Test Vendor",
            category="Travel",
            processing_message="Test message",
            duplicate_reason="Test duplicate reason",
        )
        from receipts.serializers import ReceiptDetailSerializer
        serializer = ReceiptDetailSerializer(receipt)
        data = serializer.data
        self.assertIn('category', data)
        self.assertIn('processing_message', data)
        self.assertIn('duplicate_reason', data)
        self.assertEqual(data['category'], 'Travel')


class ReceiptPreviewTests(TestCase):
    def setUp(self):
        Receipt.objects.all().delete()
        self.pdf_content = (
            b"%PDF-1.4\n"
            b"%\xE2\xE3\xCF\xD3\n"
            b"1 0 obj\n"
            b"<</Type/Catalog/Pages 2 0 R>>\n"
            b"endobj\n"
            b"2 0 obj\n"
            b"<</Type/Pages/Kids[3 0 R]/Count 1>>\n"
            b"endobj\n"
            b"3 0 obj\n"
            b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>\n"
            b"endobj\n"
            b"xref\n"
            b"0 4\n"
            b"0000000000 65535 f\n"
            b"0000000009 00000 n\n"
            b"0000000074 00000 n\n"
            b"0000000133 00000 n\n"
            b"trailer\n"
            b"<</Size 4/Root 1 0 R>>\n"
            b"startxref\n"
            b"190\n"
            b"%%EOF"
        )

    def test_receipt_list_filtering_by_status(self):
        from django.test import Client
        Receipt.objects.filter(owner="test-filter-status").delete()

        receipt1 = Receipt.objects.create(
            owner="test-filter-status",
            original_filename="receipt1.pdf",
            blob_name="receipts/test-filter-status/uuid1/receipt1.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="hash-status-1",
            status="APPROVED",
        )
        receipt2 = Receipt.objects.create(
            owner="test-filter-status",
            original_filename="receipt2.pdf",
            blob_name="receipts/test-filter-status/uuid2/receipt2.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="hash-status-2",
            status="REJECTED",
        )

        client = Client()
        response = client.get('/api/v1/receipts/?owner=test-filter-status&status=APPROVED')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        results = data['results'] if isinstance(data, dict) and 'results' in data else data
        approved_count = len([r for r in results if r['status'] == 'APPROVED'])
        self.assertGreaterEqual(approved_count, 1)
        self.assertTrue(any(r['status'] == 'APPROVED' for r in results))

    def test_receipt_list_filtering_by_category(self):
        from django.test import Client
        Receipt.objects.filter(owner="test-filter-category").delete()

        receipt1 = Receipt.objects.create(
            owner="test-filter-category",
            original_filename="receipt1.pdf",
            blob_name="receipts/test-filter-category/uuid1/receipt1.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="hash-cat-1",
            category="Meals",
        )
        receipt2 = Receipt.objects.create(
            owner="test-filter-category",
            original_filename="receipt2.pdf",
            blob_name="receipts/test-filter-category/uuid2/receipt2.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="hash-cat-2",
            category="Travel",
        )

        client = Client()
        response = client.get('/api/v1/receipts/?owner=test-filter-category&category=Meals')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        results = data['results'] if isinstance(data, dict) and 'results' in data else data
        meals_count = len([r for r in results if r['category'] == 'Meals'])
        self.assertGreaterEqual(meals_count, 1)
        self.assertTrue(any(r['category'] == 'Meals' for r in results))

    def test_receipt_preview_missing_receipt_returns_404(self):
        from django.test import Client
        client = Client()
        response = client.get('/api/v1/receipts/00000000-0000-0000-0000-000000000000/preview/?owner=default-user')
        self.assertEqual(response.status_code, 404)

    def test_receipt_preview_unauthorized_access(self):
        from django.test import Client
        receipt = Receipt.objects.create(
            owner="other-user",
            original_filename="receipt.pdf",
            blob_name="receipts/other-user/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
        )

        client = Client()
        response = client.get(f'/api/v1/receipts/{receipt.id}/preview/?owner=default-user')
        self.assertEqual(response.status_code, 403)

    def test_receipt_preview_no_blob_returns_404(self):
        from django.test import Client
        receipt = Receipt.objects.create(
            owner="default-user",
            original_filename="receipt.pdf",
            blob_name="",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
        )

        client = Client()
        response = client.get(f'/api/v1/receipts/{receipt.id}/preview/?owner=default-user')
        self.assertEqual(response.status_code, 404)

    def test_receipt_preview_successful_pdf_response(self):
        from django.test import Client
        from unittest.mock import patch

        pdf_content = (
            b"%PDF-1.4\n"
            b"%\xE2\xE3\xCF\xD3\n"
            b"1 0 obj\n"
            b"<</Type/Catalog/Pages 2 0 R>>\n"
            b"endobj\n"
        )

        receipt = Receipt.objects.create(
            owner="preview-test",
            original_filename="test.pdf",
            blob_name="receipts/preview-test/uuid/test.pdf",
            mime_type="application/pdf",
            file_size=len(pdf_content),
            sha256_hash="abc123preview",
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = pdf_content
            response = client.get(f'/api/v1/receipts/{receipt.id}/preview/?owner=preview-test')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertIn('inline', response['Content-Disposition'])

    def test_receipt_preview_blob_error_returns_json_error(self):
        from django.test import Client
        from unittest.mock import patch
        from receipts.exceptions import BlobUploadError

        receipt = Receipt.objects.create(
            owner="error-test",
            original_filename="receipt.pdf",
            blob_name="receipts/error-test/uuid/nonexistent.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="error123",
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.side_effect = BlobUploadError("Blob not found")
            response = client.get(f'/api/v1/receipts/{receipt.id}/preview/?owner=error-test')

            self.assertEqual(response.status_code, 404)
            data = response.json()
            self.assertIn('error', data)

    def test_receipt_preview_exact_duplicate_follows_relationship(self):
        from django.test import Client
        from unittest.mock import patch

        pdf_content = b"%PDF-1.4\ntest"

        original = Receipt.objects.create(
            owner="dup-test",
            original_filename="original.pdf",
            blob_name="receipts/dup-test/orig/original.pdf",
            mime_type="application/pdf",
            file_size=len(pdf_content),
            sha256_hash="original123",
            status="APPROVED",
        )

        duplicate = Receipt.objects.create(
            owner="dup-test",
            original_filename="duplicate.pdf",
            blob_name="",
            mime_type="application/pdf",
            file_size=len(pdf_content),
            sha256_hash="original123",
            status="EXACT_DUPLICATE",
            exact_duplicate_of=original,
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = pdf_content
            response = client.get(f'/api/v1/receipts/{duplicate.id}/preview/?owner=dup-test')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            mock_download.assert_called_with('receipts/dup-test/orig/original.pdf')

    def test_receipt_preview_exact_duplicate_unauthorized_original(self):
        from django.test import Client

        original = Receipt.objects.create(
            owner="other-owner",
            original_filename="original.pdf",
            blob_name="receipts/other-owner/orig/original.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="original123",
            status="APPROVED",
        )

        duplicate = Receipt.objects.create(
            owner="test-owner",
            original_filename="duplicate.pdf",
            blob_name="",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="original123",
            status="EXACT_DUPLICATE",
            exact_duplicate_of=original,
        )

        client = Client()
        response = client.get(f'/api/v1/receipts/{duplicate.id}/preview/?owner=test-owner')
        self.assertEqual(response.status_code, 403)

    def test_receipt_preview_semantic_duplicate_follows_relationship(self):
        from django.test import Client
        from unittest.mock import patch

        pdf_content = b"%PDF-1.4\ntest"

        original = Receipt.objects.create(
            owner="sem-test",
            original_filename="original.pdf",
            blob_name="receipts/sem-test/orig/original.pdf",
            mime_type="application/pdf",
            file_size=len(pdf_content),
            sha256_hash="hash1",
            status="APPROVED",
        )

        duplicate = Receipt.objects.create(
            owner="sem-test",
            original_filename="duplicate.pdf",
            blob_name="",
            mime_type="application/pdf",
            file_size=len(pdf_content),
            sha256_hash="hash2",
            status="SEMANTIC_DUPLICATE",
            semantic_duplicate_of=original,
            duplicate_score=95,
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = pdf_content
            response = client.get(f'/api/v1/receipts/{duplicate.id}/preview/?owner=sem-test')

            self.assertEqual(response.status_code, 200)
            mock_download.assert_called_with('receipts/sem-test/orig/original.pdf')

    def test_receipt_preview_rejected_with_own_blob(self):
        from django.test import Client
        from unittest.mock import patch

        pdf_content = b"%PDF-1.4\ntest"

        receipt = Receipt.objects.create(
            owner="reject-test",
            original_filename="receipt.pdf",
            blob_name="receipts/reject-test/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=len(pdf_content),
            sha256_hash="rejecthash",
            status="REJECTED",
            processing_message="Receipt rejected because: policy violation",
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = pdf_content
            response = client.get(f'/api/v1/receipts/{receipt.id}/preview/?owner=reject-test')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            mock_download.assert_called_with('receipts/reject-test/uuid/receipt.pdf')
