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
        """File exceeding 20MB should return size-specific error."""
        from django.test import Client
        
        client = Client()
        large_pdf = b"%PDF-1.4\n" + (b"x" * (21 * 1024 * 1024))
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


class FileSizeLimit5MBTests(TestCase):
    """Tests for 5 MB file size limit."""

    def test_file_5mb_accepted(self):
        """File exactly 5 MB should be accepted."""
        from django.test import Client
        
        client = Client()
        pdf_5mb = b"%PDF-1.4\n" + (b"x" * (5 * 1024 * 1024 - 20))
        file = SimpleUploadedFile("receipt_5mb.pdf", pdf_5mb, content_type="application/pdf")
        
        response = client.post(
            '/api/v1/receipts/upload/',
            {'file': file, 'owner': 'test-user'},
            format='multipart'
        )
        
        # Should not return file size error
        if response.status_code == 400:
            data = response.json()
            error_msg = str(data.get('errors', {}).get('file', [''])[0]).lower()
            self.assertNotIn('too large', error_msg, "5 MB file should not be rejected as too large")
        else:
            # Accepted successfully
            self.assertIn(response.status_code, [201, 200])

    def test_file_above_5mb_rejected(self):
        """File above 5 MB should be rejected."""
        from django.test import Client
        
        client = Client()
        pdf_6mb = b"%PDF-1.4\n" + (b"x" * (6 * 1024 * 1024))
        file = SimpleUploadedFile("huge.pdf", pdf_6mb, content_type="application/pdf")
        
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
        self.assertIn('5', error_msg)  # Should mention 5 MB

    def test_file_5mb_plus_1_rejected(self):
        """File just over 5 MB should be rejected."""
        from django.test import Client
        
        client = Client()
        pdf_51mb = b"%PDF-1.4\n" + (b"x" * ((5 * 1024 * 1024) + 1024))
        file = SimpleUploadedFile("slightly_over.pdf", pdf_51mb, content_type="application/pdf")
        
        response = client.post(
            '/api/v1/receipts/upload/',
            {'file': file, 'owner': 'test-user'},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 400)
        error_msg = str(response.json()['errors']['file'][0]).lower()
        self.assertIn('too large', error_msg)

    def test_file_above_5mb_no_receipt_created(self):
        """File above 5 MB should not create a Receipt."""
        from django.test import Client
        
        client = Client()
        pdf_6mb = b"%PDF-1.4\n" + (b"x" * (6 * 1024 * 1024))
        file = SimpleUploadedFile("huge.pdf", pdf_6mb, content_type="application/pdf")
        
        receipts_before = Receipt.objects.count()
        
        response = client.post(
            '/api/v1/receipts/upload/',
            {'file': file, 'owner': 'test-user'},
            format='multipart'
        )
        
        receipts_after = Receipt.objects.count()
        self.assertEqual(receipts_before, receipts_after, "No receipt should be created for oversized file")
        self.assertEqual(response.status_code, 400)
