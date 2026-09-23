from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from receipts.models import Receipt
from receipts.services import (
    HashingService,
    FileValidationService,
    NormalizationService,
    DuplicateService,
    PolicyService,
    ReceiptService,
)
from receipts.exceptions import UnsupportedFileTypeError, ReceiptTooLargeError
from datetime import datetime, timedelta, date
from decimal import Decimal
from unittest.mock import patch, MagicMock
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
        self.assertIn("corrupted", str(ctx.exception).lower())

    def test_pdf_missing_eof(self):
        pdf_content = b"%PDF-1.4\n" + (b"x" * 150) + b"\n1 0 obj\n<</Type/Catalog>>\nendobj\n"
        file = SimpleUploadedFile("receipt.pdf", pdf_content, content_type="application/pdf")
        with self.assertRaises(UnsupportedFileTypeError) as ctx:
            FileValidationService.validate(file, "receipt.pdf")
        self.assertIn("corrupted", str(ctx.exception).lower())

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


class CategoryDetectionTests(TestCase):
    def test_restaurant_dinner_detection(self):
        extracted = {
            'merchant': {'name': 'ABC Restaurant', 'address': None, 'phone': None},
            'line_items': [{'description': 'Dinner service', 'quantity': 1}],
            'invoice': {'invoice_number': None, 'transaction_date': None},
            'amounts': {'subtotal': None, 'tax': None, 'total': 1000, 'currency': 'USD'},
            'payment': {'method': None},
            'extraction': {},
        }
        result = ReceiptService.determine_category(extracted)
        self.assertIn('Dinner', result['category'])
        self.assertGreaterEqual(result['confidence'], 0.75)

    def test_hotel_detection(self):
        extracted = {
            'merchant': {'name': 'Hilton Hotel', 'address': None, 'phone': None},
            'line_items': [{'description': 'Room charge', 'quantity': 1}],
            'invoice': {'invoice_number': None, 'transaction_date': None},
            'amounts': {'subtotal': None, 'tax': None, 'total': 500, 'currency': 'USD'},
            'payment': {'method': None},
            'extraction': {},
        }
        result = ReceiptService.determine_category(extracted)
        self.assertEqual(result['category'], 'Accommodation/Hotel')
        self.assertGreaterEqual(result['confidence'], 0.75)

    def test_uber_detection(self):
        extracted = {
            'merchant': {'name': 'Uber', 'address': None, 'phone': None},
            'line_items': [{'description': 'Ride', 'quantity': 1}],
            'invoice': {'invoice_number': None, 'transaction_date': None},
            'amounts': {'subtotal': None, 'tax': None, 'total': 25, 'currency': 'USD'},
            'payment': {'method': None},
            'extraction': {},
        }
        result = ReceiptService.determine_category(extracted)
        self.assertEqual(result['category'], 'Transport: Taxis/Cab/Uber')
        self.assertGreaterEqual(result['confidence'], 0.75)

    def test_flight_detection(self):
        extracted = {
            'merchant': {'name': 'Airline Tickets', 'address': None, 'phone': None},
            'line_items': [{'description': 'Flight booking', 'quantity': 1}],
            'invoice': {'invoice_number': None, 'transaction_date': None},
            'amounts': {'subtotal': None, 'tax': None, 'total': 300, 'currency': 'USD'},
            'payment': {'method': None},
            'extraction': {},
        }
        result = ReceiptService.determine_category(extracted)
        self.assertEqual(result['category'], 'Transport: Flights')
        self.assertGreaterEqual(result['confidence'], 0.75)

    def test_software_detection(self):
        extracted = {
            'merchant': {'name': 'Adobe Software', 'address': None, 'phone': None},
            'line_items': [{'description': 'License', 'quantity': 1}],
            'invoice': {'invoice_number': None, 'transaction_date': None},
            'amounts': {'subtotal': None, 'tax': None, 'total': 600, 'currency': 'USD'},
            'payment': {'method': None},
            'extraction': {},
        }
        result = ReceiptService.determine_category(extracted)
        self.assertEqual(result['category'], 'Software')
        self.assertGreaterEqual(result['confidence'], 0.75)

    def test_low_confidence_handling(self):
        extracted = {
            'merchant': {'name': 'Unknown Store', 'address': None, 'phone': None},
            'line_items': [{'description': 'Item', 'quantity': 1}],
            'invoice': {'invoice_number': None, 'transaction_date': None},
            'amounts': {'subtotal': None, 'tax': None, 'total': 100, 'currency': 'USD'},
            'payment': {'method': None},
            'extraction': {},
        }
        result = ReceiptService.determine_category(extracted)
        self.assertEqual(result['category'], 'Other')
        self.assertLess(result['confidence'], 0.80)

    def test_empty_extraction_returns_other(self):
        result = ReceiptService.determine_category({})
        self.assertEqual(result['category'], 'Other')
        self.assertEqual(result['confidence'], 0.0)

    def test_category_result_has_required_fields(self):
        extracted = {
            'merchant': {'name': 'Restaurant', 'address': None, 'phone': None},
            'line_items': [],
            'invoice': {'invoice_number': None, 'transaction_date': None},
            'amounts': {'subtotal': None, 'tax': None, 'total': 50, 'currency': 'USD'},
            'payment': {'method': None},
            'extraction': {},
        }
        result = ReceiptService.determine_category(extracted)
        self.assertIn('category', result)
        self.assertIn('confidence', result)
        self.assertIn('reason', result)


class CategoryMasterTests(TestCase):
    def test_all_45_categories_exist(self):
        expected_categories = [
            'Accommodation/Hotel',
            'Australia - Mileage (KM) - electric vehicle',
            'Australia - Mileage (KM)- Petrol or diesel vehicle',
            'Bank Charges',
            'Client Entertainment',
            'Computer Peripherals',
            'Food: Breakfast or Lunch - Max Claim: €/$/AUD 15 / INR700',
            'Food: Dinner - Max Claim: €/$/AUD 45 / INR700',
            'Food: Per Diem - Max Claim: €/$/AUD 45 / INR 4000',
            'India - Mileage (KM) - electric vehicle - four wheeler',
            'India - Mileage (KM) - Petrol or diesel vehicle - four wheeler',
            'India - Mileage (KM) - Petrol or diesel vehicle - two wheeler',
            'India - Mileage (KM)- electric vehicle - two wheeler',
            'Other',
            'Phone Bills/Broadband',
            'Prepaid Accommodation',
            'Prepaid Car Rental & Fuel',
            'Prepaid Flights',
            'Prepaid Luas/Bus/Train',
            'Prepaid Other',
            'Print & Postage',
            'ROI - Mileage (KM) - electric vehicle - Lower Mileage Rate',
            'ROI - Mileage (KM) - electric vehicle - Upper Mileage Rate',
            'ROI - Mileage (KM) - Petrol or diesel vehicle - Lower Mileage Rate',
            'ROI - Mileage (KM) - Petrol or diesel vehicle - Upper Mileage Rate',
            'Slovenia - Mileage (KM) - electric vehicle - Residential',
            'Slovenia - Mileage (KM) - Petrol or diesel vehicle - Non-Residential',
            'Slovenia - Mileage (KM) - Petrol or diesel vehicle - Residential',
            'Slovenia - Mileage (KM)- electric vehicle - Non-Residential',
            'Software',
            'Spain - Mileage (KM) - electric vehicle',
            'Spain - Mileage (KM)- Petrol or diesel vehicle',
            'Stationery Consumables',
            'Training',
            'Transport: Car Rental & Fuel',
            'Transport: Flights',
            'Transport: Luas/Bus/Train',
            'Transport: Taxis/Cab/Uber',
            'Travel Other incl. Parking & Tolls',
            'UK - Mileage (miles) - electric vehicle - Lower Mileage Rate',
            'UK - Mileage (miles) - electric vehicle - Upper Mileage Rate',
            'UK - Mileage (miles) - Petrol or diesel vehicle - Lower Mileage Rate',
            'UK - Mileage (miles) - Petrol or diesel vehicle - Upper Mileage Rate',
            'USA - Mileage (miles) - electric vehicle',
            'USA - Mileage (miles)- Petrol or diesel vehicle',
        ]

        actual_categories = [choice[0] for choice in Receipt.CATEGORY_CHOICES]
        self.assertEqual(len(actual_categories), 45)
        self.assertEqual(sorted(actual_categories), sorted(expected_categories))

    def test_other_is_default_category(self):
        receipt = Receipt.objects.create(
            owner="test",
            original_filename="test.pdf",
            blob_name="receipts/test/uuid/test.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
        )
        self.assertEqual(receipt.category, 'Other')

    def test_receipt_accepts_all_45_categories(self):
        categories = [choice[0] for choice in Receipt.CATEGORY_CHOICES]
        for i, category in enumerate(categories):
            receipt = Receipt.objects.create(
                owner="test",
                original_filename=f"test{i}.pdf",
                blob_name=f"receipts/test/uuid{i}/test{i}.pdf",
                mime_type="application/pdf",
                file_size=1000,
                sha256_hash=f"hash{i}",
                category=category,
            )
            self.assertEqual(receipt.category, category)

    def test_old_9_categories_not_in_choices(self):
        old_categories = [
            'Accommodation',
            'Meals',
            'Travel',
            'Transportation',
            'Car Rental',
            'Fuel',
            'Office Supplies',
        ]

        actual_categories = [choice[0] for choice in Receipt.CATEGORY_CHOICES]
        for old_cat in old_categories:
            self.assertNotIn(old_cat, actual_categories)


class CategoryAPITests(TestCase):
    def test_categories_endpoint_returns_45_categories(self):
        from django.test import Client
        client = Client()
        response = client.get('/api/v1/receipts/categories/', {
            'X-Requested-With': 'XMLHttpRequest'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('categories', data)
        self.assertEqual(len(data['categories']), 45)

    def test_set_category_valid(self):
        from rest_framework.test import APIClient
        receipt = Receipt.objects.create(
            owner="cat-test",
            original_filename="test.pdf",
            blob_name="receipts/cat-test/uuid/test.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="cathash",
            category="Other",
        )

        client = APIClient()
        response = client.post(
            f'/api/v1/receipts/{receipt.id}/set_category/?owner=cat-test',
            {'category': 'Accommodation/Hotel'},
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        receipt.refresh_from_db()
        self.assertEqual(receipt.category, 'Accommodation/Hotel')
        self.assertEqual(receipt.category_confidence, 1.0)

    def test_set_category_invalid(self):
        from rest_framework.test import APIClient
        receipt = Receipt.objects.create(
            owner="cat-test",
            original_filename="test.pdf",
            blob_name="receipts/cat-test/uuid/test.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="cathash2",
            category="Other",
        )

        client = APIClient()
        response = client.post(
            f'/api/v1/receipts/{receipt.id}/set_category/?owner=cat-test',
            {'category': 'Invalid Category'},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

    def test_set_category_unauthorized(self):
        from rest_framework.test import APIClient
        receipt = Receipt.objects.create(
            owner="other-owner",
            original_filename="test.pdf",
            blob_name="receipts/other-owner/uuid/test.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="cathash3",
            category="Other",
        )

        client = APIClient()
        response = client.post(
            f'/api/v1/receipts/{receipt.id}/set_category/?owner=cat-test',
            {'category': 'Accommodation/Hotel'},
            format='json'
        )

        self.assertEqual(response.status_code, 403)


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


class UploadErrorHandlingTests(TestCase):
    """Tests for error message propagation in upload flow."""

    def test_empty_file_error(self):
        """Empty file should return specific error message."""
        from django.test import Client
        client = Client()
        
        file = SimpleUploadedFile("empty.pdf", b"", content_type="application/pdf")
        response = client.post(
            '/api/v1/receipts/upload/',
            {'file': file, 'owner': 'test-user'},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('errors', data)
        self.assertIn('file', data['errors'])
        self.assertTrue(any('empty' in str(err).lower() for err in data['errors']['file']))

    def test_unsupported_extension_error(self):
        """Unsupported file extension should return specific error."""
        from django.test import Client
        client = Client()
        
        file = SimpleUploadedFile("receipt.txt", b"not a receipt", content_type="text/plain")
        response = client.post(
            '/api/v1/receipts/upload/',
            {'file': file, 'owner': 'test-user'},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('errors', data)
        self.assertIn('file', data['errors'])
        error_msg = str(data['errors']['file'][0]).lower()
        self.assertIn('unsupported', error_msg)

    def test_file_too_large_error(self):
        """File exceeding 50MB absolute maximum should return size-specific error."""
        from django.test import Client

        client = Client()
        large_pdf = b"%PDF-1.4\n" + (b"x" * (51 * 1024 * 1024))
        file = SimpleUploadedFile("huge.pdf", large_pdf, content_type="application/pdf")

        response = client.post(
            '/api/v1/receipts/upload/',
            {'file': file, 'owner': 'test-user'},
            format='multipart'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('errors', data)
        error_msg = str(data['errors']['file'][0]).lower()
        self.assertIn('too large', error_msg)
        self.assertIn('50', error_msg)

    def test_invalid_pdf_header_error(self):
        """Invalid PDF header should return specific error."""
        from django.test import Client
        client = Client()
        
        file = SimpleUploadedFile("notpdf.pdf", b"This is not a PDF", content_type="application/pdf")
        response = client.post(
            '/api/v1/receipts/upload/',
            {'file': file, 'owner': 'test-user'},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('errors', data)
        error_msg = str(data['errors']['file'][0]).lower()
        self.assertIn('pdf', error_msg)

    def test_blank_image_error(self):
        """Mostly white image should return blank-specific error."""
        from django.test import Client
        from PIL import Image
        import io
        
        client = Client()
        
        img = Image.new('RGB', (100, 100), color=(255, 255, 255))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        file = SimpleUploadedFile("blank.png", img_bytes.read(), content_type="image/png")
        response = client.post(
            '/api/v1/receipts/upload/',
            {'file': file, 'owner': 'test-user'},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('errors', data)
        error_msg = str(data['errors']['file'][0]).lower()
        self.assertIn('blank', error_msg)

    def test_pdf_zero_pages_error(self):
        """PDF with zero pages should return empty PDF error."""
        from django.test import Client
        client = Client()
        
        pdf_content = (
            b"%PDF-1.4\n"
            b"1 0 obj\n"
            b"<</Type/Catalog/Pages 2 0 R>>\n"
            b"endobj\n"
            b"2 0 obj\n"
            b"<</Type/Pages/Kids[]/Count 0>>\n"
            b"endobj\n"
            b"xref\n"
            b"0 3\n"
            b"0000000000 65535 f\n"
            b"0000000009 00000 n\n"
            b"0000000074 00000 n\n"
            b"trailer\n"
            b"<</Size 3/Root 1 0 R>>\n"
            b"startxref\n"
            b"127\n"
            b"%%EOF"
        )
        file = SimpleUploadedFile("empty.pdf", pdf_content, content_type="application/pdf")
        response = client.post(
            '/api/v1/receipts/upload/',
            {'file': file, 'owner': 'test-user'},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('errors', data)
        error_msg = str(data['errors']['file'][0]).lower()
        self.assertIn('zero pages', error_msg.lower())

    def test_ocr_failure_sets_failed_status(self):
        """OCR failure should set FAILED status with clear message."""
        from unittest.mock import patch
        from receipts.services import ReceiptService
        from receipts.exceptions import DocumentExtractionError
        
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
        
        receipt = Receipt.objects.create(
            owner='test-user',
            original_filename='test.pdf',
            blob_name='receipts/test-user/uuid/test.pdf',
            mime_type='application/pdf',
            file_size=len(pdf_content),
            sha256_hash='testhash123',
            status='QUEUED_FOR_OCR'
        )
        
        service = ReceiptService()
        with patch.object(service.blob_service, 'download', return_value=pdf_content):
            with patch.object(service.doc_intel_service, 'analyze_receipt') as mock_analyze:
                mock_analyze.side_effect = DocumentExtractionError("OCR service unavailable")
                
                result = service.process_receipt(str(receipt.id))
        
        self.assertEqual(result.status, 'FAILED')
        self.assertIn('couldn\'t read', result.processing_message.lower())
        self.assertIn('blurry', result.processing_message.lower())


class FileSizeCompressionThresholdTests(TestCase):
    """Tests for file size compression threshold (5 MB) and absolute maximum (50 MB)."""

    def _create_valid_minimal_pdf(self, size_bytes):
        """Create a valid minimal PDF of approximately the specified size by padding base PDF."""
        base_pdf = (
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

        if len(base_pdf) >= size_bytes:
            return base_pdf[:size_bytes]

        padding_size = size_bytes - len(base_pdf)
        padding = b"x" * padding_size
        return base_pdf + padding

    def test_file_5mb_accepted_no_compression(self):
        """File at 5 MB threshold should be accepted without compression triggering."""
        from receipts.services import ReceiptService

        service = ReceiptService()
        pdf_5mb = self._create_valid_minimal_pdf(5 * 1024 * 1024)
        file_obj = SimpleUploadedFile("receipt_5mb.pdf", pdf_5mb, content_type="application/pdf")

        receipt = service.create_and_upload_receipt(file_obj, "receipt_5mb.pdf", owner="test-user")

        self.assertIsNotNone(receipt.id)
        self.assertEqual(receipt.file_size, 5 * 1024 * 1024)

    def test_file_above_5mb_accepted_with_compression(self):
        """File above 5 MB should be accepted and compression applied during processing."""
        from receipts.services import ReceiptService

        service = ReceiptService()
        pdf_6mb = self._create_valid_minimal_pdf(5 * 1024 * 1024 + 512 * 1024)
        file_obj = SimpleUploadedFile("receipt_6mb.pdf", pdf_6mb, content_type="application/pdf")

        receipt = service.create_and_upload_receipt(file_obj, "receipt_6mb.pdf", owner="test-user")

        expected_size = 5 * 1024 * 1024 + 512 * 1024
        self.assertEqual(receipt.file_size, expected_size, "Original file size should be preserved")

    def test_file_above_50mb_rejected(self):
        """File above 50 MB absolute maximum should be rejected."""
        from django.test import Client

        client = Client()
        pdf_51mb = b"%PDF-1.4\n" + (b"x" * (51 * 1024 * 1024))
        file = SimpleUploadedFile("receipt_51mb.pdf", pdf_51mb, content_type="application/pdf")

        response = client.post(
            '/api/v1/receipts/upload/',
            {'file': file, 'owner': 'test-user'},
            format='multipart'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('errors', data)
        error_msg = str(data['errors']['file'][0]).lower()
        self.assertIn('too large', error_msg)
        self.assertIn('50', error_msg)

    def test_original_bytes_preserved_in_blob(self):
        """Original file bytes should be preserved in Blob Storage."""
        from receipts.services import ReceiptService

        service = ReceiptService()
        pdf_6mb = self._create_valid_minimal_pdf(6 * 1024 * 1024)
        file_obj = SimpleUploadedFile("receipt_6mb.pdf", pdf_6mb, content_type="application/pdf")

        receipt = service.create_and_upload_receipt(file_obj, "receipt_6mb.pdf", owner="test-user")

        downloaded = service.blob_service.download(receipt.blob_name)
        self.assertEqual(len(downloaded), 6 * 1024 * 1024, "Blob should contain original uncompressed bytes")

    def test_sha256_from_original_bytes(self):
        """SHA-256 hash should be calculated from original file bytes, not compressed copy."""
        from receipts.services import ReceiptService, HashingService

        service = ReceiptService()
        hashing = HashingService()
        pdf_6mb = self._create_valid_minimal_pdf(6 * 1024 * 1024)
        file_obj = SimpleUploadedFile("receipt_6mb.pdf", pdf_6mb, content_type="application/pdf")

        receipt = service.create_and_upload_receipt(file_obj, "receipt_6mb.pdf", owner="test-user")

        file_obj.seek(0)
        expected_hash = hashing.sha256(file_obj)
        self.assertEqual(receipt.sha256_hash, expected_hash, "SHA-256 must be from original bytes")


class FinancePendingReceiptWorkflowTests(TestCase):
    """Tests for Part 1: Finance-pending receipt workflow."""

    @patch('receipts.services.receipt_service.BlobService')
    @patch('receipts.services.receipt_service.DocumentIntelligenceService')
    def test_policy_pass_sets_needs_review_status(self, mock_doc_intel_class, mock_blob_class):
        """After policy passes, receipt should be NEEDS_REVIEW (not APPROVED)."""
        # Mock blob service to return dummy PDF bytes
        mock_blob = MagicMock()
        mock_blob.download.return_value = b"%PDF-1.4\nDummy PDF content"
        mock_blob_class.return_value = mock_blob

        # Mock document intelligence to return valid extracted data in required structure
        mock_doc_intel = MagicMock()
        mock_doc_intel.analyze_receipt.return_value = {
            'merchant': {'name': 'Test Vendor'},
            'amounts': {'total': 100.00, 'currency': 'USD'},
            'invoice': {'transaction_date': (date.today() - timedelta(days=10)).isoformat()},
            'payment': {'method': 'Cash'},
            'extraction': {'provider': 'azure_ai_document_intelligence'},
        }
        mock_doc_intel_class.return_value = mock_doc_intel

        receipt = Receipt.objects.create(
            owner="finance-user",
            original_filename="receipt.pdf",
            blob_name="receipts/finance-user/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
            transaction_date=date.today() - timedelta(days=10),
            total_amount=Decimal("100.00"),
            currency="USD",
            vendor_name="Test Vendor",
            normalized_json={"vendor_name": "Test Vendor"},
        )

        from receipts.services import ReceiptService
        service = ReceiptService()
        result = service.process_receipt(str(receipt.id))

        self.assertEqual(result.status, 'NEEDS_REVIEW', "Policy-passing receipt should be NEEDS_REVIEW for Finance review")
        self.assertEqual(result.policy_status, 'APPROVED', "Policy status should be APPROVED")
        self.assertIn("Finance review", result.processing_message)

    @patch('receipts.services.receipt_service.BlobService')
    @patch('receipts.services.receipt_service.DocumentIntelligenceService')
    def test_policy_fail_sets_rejected_status(self, mock_doc_intel_class, mock_blob_class):
        """Policy failure should still set REJECTED (final)."""
        # Mock blob service to return dummy PDF bytes
        mock_blob = MagicMock()
        mock_blob.download.return_value = b"%PDF-1.4\nDummy PDF content"
        mock_blob_class.return_value = mock_blob

        # Mock document intelligence to return valid extracted data in required structure
        # Receipt is 40 days old, which should fail the 35-day policy
        mock_doc_intel = MagicMock()
        mock_doc_intel.analyze_receipt.return_value = {
            'merchant': {'name': 'Test Vendor'},
            'amounts': {'total': 100.00, 'currency': 'USD'},
            'invoice': {'transaction_date': (date.today() - timedelta(days=40)).isoformat()},
            'payment': {'method': 'Cash'},
            'extraction': {'provider': 'azure_ai_document_intelligence'},
        }
        mock_doc_intel_class.return_value = mock_doc_intel

        receipt = Receipt.objects.create(
            owner="finance-user",
            original_filename="receipt.pdf",
            blob_name="receipts/finance-user/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
            transaction_date=date.today() - timedelta(days=40),
            total_amount=Decimal("100.00"),
            currency="USD",
            vendor_name="Test Vendor",
            normalized_json={"vendor_name": "Test Vendor"},
        )

        from receipts.services import ReceiptService
        service = ReceiptService()
        result = service.process_receipt(str(receipt.id))

        self.assertEqual(result.status, 'REJECTED', "Policy-failing receipt should be REJECTED (final)")
        self.assertEqual(result.policy_status, 'REJECTED', "Policy status should be REJECTED")

    def test_needs_review_is_not_final(self):
        """NEEDS_REVIEW status should not be in the final states."""
        receipt = Receipt.objects.create(
            owner="finance-user",
            original_filename="receipt.pdf",
            blob_name="receipts/finance-user/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
            transaction_date=date.today() - timedelta(days=10),
            total_amount=Decimal("100.00"),
            currency="USD",
            vendor_name="Test Vendor",
            status="NEEDS_REVIEW",
            normalized_json={"vendor_name": "Test Vendor"},
        )

        self.assertFalse(receipt.is_final(), "NEEDS_REVIEW should not be a final state")

    def test_approved_is_final(self):
        """APPROVED status should be final."""
        receipt = Receipt.objects.create(
            owner="finance-user",
            original_filename="receipt.pdf",
            blob_name="receipts/finance-user/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
            status="APPROVED",
        )

        self.assertTrue(receipt.is_final(), "APPROVED should be a final state")

    def test_rejected_is_final(self):
        """REJECTED status should be final."""
        receipt = Receipt.objects.create(
            owner="finance-user",
            original_filename="receipt.pdf",
            blob_name="receipts/finance-user/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
            status="REJECTED",
        )

        self.assertTrue(receipt.is_final(), "REJECTED should be a final state")
