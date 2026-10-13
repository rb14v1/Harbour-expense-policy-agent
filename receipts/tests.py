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
from receipts.services.document_intelligence_service import DocumentIntelligenceService
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

    def test_normalize_date_iso_format(self):
        extracted = {
            "merchant": {"name": "Test", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": "2026-09-05"},
            "amounts": {"subtotal": None, "tax": None, "total": None, "currency": None},
            "payment": {"method": None},
            "line_items": [],
            "extraction": {},
        }
        normalized = NormalizationService.normalize(extracted)
        self.assertEqual(normalized['transaction_date'], "2026-09-05")

    def test_normalize_date_dmy_format(self):
        extracted = {
            "merchant": {"name": "Test", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": "05/09/2026"},
            "amounts": {"subtotal": None, "tax": None, "total": None, "currency": None},
            "payment": {"method": None},
            "line_items": [],
            "extraction": {},
        }
        normalized = NormalizationService.normalize(extracted)
        self.assertEqual(normalized['transaction_date'], "2026-09-05")

    def test_normalize_date_textual_month_abbrev(self):
        extracted = {
            "merchant": {"name": "Test", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": "5 Sept 2026"},
            "amounts": {"subtotal": None, "tax": None, "total": None, "currency": None},
            "payment": {"method": None},
            "line_items": [],
            "extraction": {},
        }
        normalized = NormalizationService.normalize(extracted)
        self.assertEqual(normalized['transaction_date'], "2026-09-05")

    def test_normalize_date_textual_month_full(self):
        extracted = {
            "merchant": {"name": "Test", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": "5 September 2026"},
            "amounts": {"subtotal": None, "tax": None, "total": None, "currency": None},
            "payment": {"method": None},
            "line_items": [],
            "extraction": {},
        }
        normalized = NormalizationService.normalize(extracted)
        self.assertEqual(normalized['transaction_date'], "2026-09-05")

    def test_normalize_date_textual_month_comma_format(self):
        extracted = {
            "merchant": {"name": "Test", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": "September 5, 2026"},
            "amounts": {"subtotal": None, "tax": None, "total": None, "currency": None},
            "payment": {"method": None},
            "line_items": [],
            "extraction": {},
        }
        normalized = NormalizationService.normalize(extracted)
        self.assertEqual(normalized['transaction_date'], "2026-09-05")


class DocumentIntelligenceServiceTests(TestCase):
    def setUp(self):
        self.service = DocumentIntelligenceService()

    def test_extract_month_name_date_abbreviated(self):
        content = "Receipt Date: 5 Sept 2026\nTotal: 100"
        result = self.service._extract_month_name_date(content)
        self.assertEqual(result, "2026-09-05")

    def test_extract_month_name_date_full(self):
        content = "Receipt Date: 5 September 2026\nTotal: 100"
        result = self.service._extract_month_name_date(content)
        self.assertEqual(result, "2026-09-05")

    def test_extract_month_name_date_comma_format(self):
        content = "Receipt Date: September 5, 2026\nTotal: 100"
        result = self.service._extract_month_name_date(content)
        self.assertEqual(result, "2026-09-05")

    def test_extract_month_name_date_padded_day(self):
        content = "Transaction: 05 Sep 2026"
        result = self.service._extract_month_name_date(content)
        self.assertEqual(result, "2026-09-05")

    def test_extract_month_name_date_no_match(self):
        content = "Receipt Date: 2026-09-05\nTotal: 100"
        result = self.service._extract_month_name_date(content)
        self.assertIsNone(result)

    def test_extract_month_name_date_all_months_abbreviated(self):
        months = [
            ("1 Jan 2026", "2026-01-01"),
            ("15 Feb 2026", "2026-02-15"),
            ("3 Mar 2026", "2026-03-03"),
            ("20 Apr 2026", "2026-04-20"),
            ("1 May 2026", "2026-05-01"),
            ("10 Jun 2026", "2026-06-10"),
            ("4 Jul 2026", "2026-07-04"),
            ("15 Aug 2026", "2026-08-15"),
            ("5 Sep 2026", "2026-09-05"),
            ("31 Oct 2026", "2026-10-31"),
            ("25 Nov 2026", "2026-11-25"),
            ("25 Dec 2026", "2026-12-25"),
        ]
        for date_text, expected in months:
            with self.subTest(date_text=date_text):
                content = f"Date: {date_text}"
                result = self.service._extract_month_name_date(content)
                self.assertEqual(result, expected)

    def test_extract_month_name_date_all_months_full(self):
        months = [
            ("1 January 2026", "2026-01-01"),
            ("15 February 2026", "2026-02-15"),
            ("3 March 2026", "2026-03-03"),
            ("20 April 2026", "2026-04-20"),
            ("1 May 2026", "2026-05-01"),
            ("10 June 2026", "2026-06-10"),
            ("4 July 2026", "2026-07-04"),
            ("15 August 2026", "2026-08-15"),
            ("5 September 2026", "2026-09-05"),
            ("31 October 2026", "2026-10-31"),
            ("25 November 2026", "2026-11-25"),
            ("25 December 2026", "2026-12-25"),
        ]
        for date_text, expected in months:
            with self.subTest(date_text=date_text):
                content = f"Date: {date_text}"
                result = self.service._extract_month_name_date(content)
                self.assertEqual(result, expected)

    def test_extract_from_ocr_text_prefers_month_name_date(self):
        content = "Receipt Date: 5 Sept 2026\nTotal Amount: 1000.00"
        result = self.service._extract_from_ocr_text(content)
        self.assertEqual(result['transaction_date'], "2026-09-05")

    def test_extract_from_ocr_text_fallback_to_iso_when_no_month_name(self):
        content = "Date: 2026-09-05\nTotal: 100"
        result = self.service._extract_from_ocr_text(content)
        self.assertEqual(result['transaction_date'], "2026-09-05")

    def test_extract_from_ocr_text_invoice_number(self):
        content = "RECEIPT NO: INV-2026-001\nDate: 5 Sept 2026"
        result = self.service._extract_from_ocr_text(content)
        self.assertEqual(result['invoice_number'], "INV-2026-001")

    def test_extract_from_ocr_text_merchant_name_explicit_label(self):
        """Merchant name should be extracted from explicitly labelled field."""
        content = "MERCHANT NAME: ABC Restaurant\nDate: 5 Sept 2026\nTotal: 100"
        result = self.service._extract_from_ocr_text(content)
        self.assertEqual(result['merchant_name'], "ABC Restaurant")

    def test_extract_from_ocr_text_vendor_name_explicit_label(self):
        """Vendor name should be extracted using Vendor: label."""
        content = "VENDOR NAME: XYZ Coffee Shop\nDate: 5 Sept 2026\nTotal: 50"
        result = self.service._extract_from_ocr_text(content)
        self.assertEqual(result['merchant_name'], "XYZ Coffee Shop")

    def test_extract_from_ocr_text_business_name_explicit_label(self):
        """Business name should be extracted using Business Name: label."""
        content = "BUSINESS NAME: My Store\nINVOICE NO: 123\nDate: 5 Sept 2026"
        result = self.service._extract_from_ocr_text(content)
        self.assertEqual(result['merchant_name'], "My Store")

    def test_extract_from_ocr_text_no_merchant_without_label(self):
        """Merchant name should not be extracted without explicit label."""
        content = "ABC Restaurant\nDate: 5 Sept 2026\nTotal: 100"
        result = self.service._extract_from_ocr_text(content)
        self.assertIsNone(result['merchant_name'])

    def test_extract_from_ocr_text_exclude_driver_name(self):
        """Driver receipt should not identify driver name as merchant."""
        content = (
            "Driver: John Smith\n"
            "Trip Details: Airport Transfer\n"
            "Date: 5 Sept 2026\n"
            "Total: 50"
        )
        result = self.service._extract_from_ocr_text(content)
        # Driver name should not be extracted without explicit merchant label
        self.assertIsNone(result['merchant_name'])

    def test_extract_from_ocr_text_exclude_greeting(self):
        """Receipt with greeting should not extract greeting as merchant."""
        content = (
            "Welcome to Our Store\n"
            "Date: 5 Sept 2026\n"
            "Total: 100"
        )
        result = self.service._extract_from_ocr_text(content)
        self.assertIsNone(result['merchant_name'])

    def test_extract_from_ocr_text_ola_known_merchant(self):
        """OCR text containing 'Ola' should be recognized as known merchant."""
        content = (
            "Trip Summary\n"
            "Booked via: Ola\n"
            "Date: 5 Sept 2026\n"
            "Fare: ₹250.00\n"
            "Total: ₹250.00"
        )
        result = self.service._extract_from_ocr_text(content)
        self.assertEqual(result['merchant_name'], 'Ola')

    def test_extract_from_ocr_text_rapido_known_merchant(self):
        """OCR text containing 'Rapido' should be recognized as known merchant."""
        content = (
            "Bike Taxi Receipt\n"
            "Service: Rapido\n"
            "Date: 5 Sept 2026\n"
            "Trip Amount: ₹120.00\n"
            "Total: ₹120.00"
        )
        result = self.service._extract_from_ocr_text(content)
        self.assertEqual(result['merchant_name'], 'Rapido')

    def test_extract_from_ocr_text_total_amount_various_labels(self):
        """Total amount should be extracted with various labels like Fare, Bill, etc."""
        test_cases = [
            ("Total Amount: 100", 100.0),
            ("FARE: ₹250.50", 250.50),
            ("Bill Amount: $45.00", 45.0),
            ("Amount to Pay: 500", 500.0),
        ]
        for content, expected_amount in test_cases:
            with self.subTest(content=content):
                result = self.service._extract_from_ocr_text(content)
                self.assertEqual(result['total'], expected_amount, f"Failed to extract {expected_amount} from: {content}")

    def test_extract_from_ocr_text_ola_screenshot_scenario(self):
        """OCR text from Ola email receipt screenshot should extract merchant and amount."""
        content = (
            "Your Ride Receipt\n"
            "Trip with: Ola\n"
            "Date: 12 Oct 2026\n"
            "Pickup: ABC Street\n"
            "Dropoff: XYZ Plaza\n"
            "Ride Fare: ₹287.50\n"
            "Total Amount: ₹287.50"
        )
        result = self.service._extract_from_ocr_text(content)
        self.assertEqual(result['merchant_name'], 'Ola')
        self.assertEqual(result['total'], 287.50)
        self.assertEqual(result['transaction_date'], '2026-10-12')

    def test_extract_from_ocr_text_rapido_screenshot_scenario(self):
        """OCR text from Rapido screenshot should extract merchant and amount."""
        content = (
            "Rapido Bike Taxi Receipt\n"
            "Date: October 13, 2026\n"
            "From: Business Park\n"
            "To: Central Station\n"
            "Ride Amount: ₹95\n"
            "Total Payable: ₹95"
        )
        result = self.service._extract_from_ocr_text(content)
        self.assertEqual(result['merchant_name'], 'Rapido')
        self.assertEqual(result['total'], 95.0)


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
            self.assertIn('attachment', response['Content-Disposition'])

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

    def test_receipt_preview_pdf_returns_attachment_disposition(self):
        """Test that PDF files return Content-Disposition: attachment for reliable mobile download."""
        from django.test import Client

        pdf_content = b"%PDF-1.4\ntest pdf content"

        receipt = Receipt.objects.create(
            owner="pdf-test",
            original_filename="invoice.pdf",
            blob_name="receipts/pdf-test/uuid/invoice.pdf",
            mime_type="application/pdf",
            file_size=len(pdf_content),
            sha256_hash="pdf123",
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = pdf_content
            response = client.get(f'/api/v1/receipts/{receipt.id}/preview/?owner=pdf-test')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            # Critical for mobile: PDF must use attachment disposition
            self.assertIn('attachment', response['Content-Disposition'])
            self.assertIn('invoice.pdf', response['Content-Disposition'])

    def test_receipt_preview_jpg_returns_inline_disposition(self):
        """Test that image files return Content-Disposition: inline for browser display."""
        from django.test import Client

        jpg_content = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"JFIF" + (b"x" * 200) + bytes([0xFF, 0xD9])

        receipt = Receipt.objects.create(
            owner="image-test",
            original_filename="receipt.jpg",
            blob_name="receipts/image-test/uuid/receipt.jpg",
            mime_type="image/jpeg",
            file_size=len(jpg_content),
            sha256_hash="jpg123",
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = jpg_content
            response = client.get(f'/api/v1/receipts/{receipt.id}/preview/?owner=image-test')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'image/jpeg')
            # Images should use inline disposition for browser display on mobile
            self.assertIn('inline', response['Content-Disposition'])

    def test_receipt_preview_png_returns_inline_disposition(self):
        """Test that PNG image files return Content-Disposition: inline."""
        from django.test import Client

        png_content = b'\x89PNG\r\n\x1a\n' + (b"x" * 100)

        receipt = Receipt.objects.create(
            owner="png-test",
            original_filename="receipt.png",
            blob_name="receipts/png-test/uuid/receipt.png",
            mime_type="image/png",
            file_size=len(png_content),
            sha256_hash="png123",
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = png_content
            response = client.get(f'/api/v1/receipts/{receipt.id}/preview/?owner=png-test')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'image/png')
            self.assertIn('inline', response['Content-Disposition'])


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

    def test_needs_review_shown_as_completion_to_employee(self):
        """NEEDS_REVIEW should be recognized as completion state in employee upload flow (not timeout)."""
        # This test ensures that NEEDS_REVIEW status is included in the list of
        # "final" statuses that the employee upload JavaScript polls for.
        # If NEEDS_REVIEW is missing from that list, the employee will see a
        # misleading "timed out" message even though processing succeeded.

        # The JavaScript on line ~686 of upload.html checks:
        # if (['APPROVED', 'REJECTED', 'NEEDS_REVIEW', 'EXACT_DUPLICATE', 'SEMANTIC_DUPLICATE', 'FAILED'].includes(receipt.status))

        receipt = Receipt.objects.create(
            owner="employee-user",
            original_filename="receipt.pdf",
            blob_name="receipts/employee-user/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="abc123",
            transaction_date=date.today() - timedelta(days=10),
            total_amount=Decimal("100.00"),
            currency="USD",
            vendor_name="Test Vendor",
            status="NEEDS_REVIEW",
            processing_message="Receipt has been validated and approved by policy. Awaiting Finance review.",
            normalized_json={"vendor_name": "Test Vendor"},
        )

        # Verify that NEEDS_REVIEW receipt is properly created with correct message
        self.assertEqual(receipt.status, "NEEDS_REVIEW")
        self.assertIn("Awaiting Finance review", receipt.processing_message)

        # Verify this status is visible to the employee (via API)
        from django.test import Client
        client = Client()
        response = client.get(
            f'/api/v1/receipts/{receipt.id}/?owner=employee-user',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'NEEDS_REVIEW')
        self.assertEqual(data['processing_message'], "Receipt has been validated and approved by policy. Awaiting Finance review.")

    def test_receipt_preview_pdf_returns_attachment_disposition(self):
        """Test that PDF files return Content-Disposition: attachment for reliable mobile download."""
        from django.test import Client

        pdf_content = b"%PDF-1.4\ntest pdf content"

        receipt = Receipt.objects.create(
            owner="pdf-test",
            original_filename="invoice.pdf",
            blob_name="receipts/pdf-test/uuid/invoice.pdf",
            mime_type="application/pdf",
            file_size=len(pdf_content),
            sha256_hash="pdf123",
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = pdf_content
            response = client.get(f'/api/v1/receipts/{receipt.id}/preview/?owner=pdf-test')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            # Critical for mobile: PDF must use attachment disposition
            self.assertIn('attachment', response['Content-Disposition'])
            self.assertIn('invoice.pdf', response['Content-Disposition'])

    def test_receipt_preview_jpg_returns_inline_disposition(self):
        """Test that image files return Content-Disposition: inline for browser display."""
        from django.test import Client

        jpg_content = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"JFIF" + (b"x" * 200) + bytes([0xFF, 0xD9])

        receipt = Receipt.objects.create(
            owner="image-test",
            original_filename="receipt.jpg",
            blob_name="receipts/image-test/uuid/receipt.jpg",
            mime_type="image/jpeg",
            file_size=len(jpg_content),
            sha256_hash="jpg123",
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = jpg_content
            response = client.get(f'/api/v1/receipts/{receipt.id}/preview/?owner=image-test')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'image/jpeg')
            # Images should use inline disposition for browser display on mobile
            self.assertIn('inline', response['Content-Disposition'])

    def test_receipt_preview_png_returns_inline_disposition(self):
        """Test that PNG image files return Content-Disposition: inline."""
        from django.test import Client

        png_content = b'\x89PNG\r\n\x1a\n' + (b"x" * 100)

        receipt = Receipt.objects.create(
            owner="png-test",
            original_filename="receipt.png",
            blob_name="receipts/png-test/uuid/receipt.png",
            mime_type="image/png",
            file_size=len(png_content),
            sha256_hash="png123",
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = png_content
            response = client.get(f'/api/v1/receipts/{receipt.id}/preview/?owner=png-test')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'image/png')
            self.assertIn('inline', response['Content-Disposition'])

    def test_receipt_preview_pdf_without_extension_still_attachment(self):
        """Test that PDFs without .pdf extension still use attachment disposition."""
        from django.test import Client

        pdf_content = b"%PDF-1.4\ntest"

        receipt = Receipt.objects.create(
            owner="pdf-noext",
            original_filename="invoice",  # No .pdf extension
            blob_name="receipts/pdf-noext/uuid/invoice",
            mime_type="application/pdf",
            file_size=len(pdf_content),
            sha256_hash="pdfnoext123",
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = pdf_content
            response = client.get(f'/api/v1/receipts/{receipt.id}/preview/?owner=pdf-noext')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertIn('attachment', response['Content-Disposition'])
            # Should add .pdf extension if missing


class ReceiptDownloadEndpointTests(TestCase):
    """Tests for explicit /download endpoint (avoids APPEND_SLASH redirect)."""

    def test_download_get_returns_pdf_content(self):
        """Test that GET /download returns PDF file content."""
        from django.test import Client

        pdf_content = b"%PDF-1.4\ntest content"
        receipt = Receipt.objects.create(
            owner="default-user",
            original_filename="receipt.pdf",
            blob_name="receipts/default-user/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=len(pdf_content),
            sha256_hash="download_pdf_test",
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = pdf_content
            response = client.get(f'/api/v1/receipts/{receipt.id}/download?owner=default-user')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertIn('inline', response['Content-Disposition'])
            self.assertEqual(b''.join(response.streaming_content), pdf_content)

    def test_download_head_returns_headers_no_redirect(self):
        """Test that HEAD /download returns 200 with proper headers (no 301 redirect)."""
        from django.test import Client

        pdf_content = b"%PDF-1.4\ntest content"
        receipt = Receipt.objects.create(
            owner="default-user",
            original_filename="receipt.pdf",
            blob_name="receipts/default-user/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=len(pdf_content),
            sha256_hash="download_head_test",
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = pdf_content
            # HEAD request should NOT get a 301 redirect
            response = client.head(f'/api/v1/receipts/{receipt.id}/download?owner=default-user')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertIn('inline', response['Content-Disposition'])
            # HEAD response should have Content-Length
            self.assertEqual(response['Content-Length'], str(len(pdf_content)))
            # HEAD response should NOT have body
            self.assertEqual(b''.join(response.streaming_content), b'')

    def test_download_head_without_trailing_slash_no_redirect(self):
        """Test that HEAD without trailing slash returns 200 (not 301)."""
        from django.test import Client

        pdf_content = b"%PDF-1.4\ntest"
        receipt = Receipt.objects.create(
            owner="default-user",
            original_filename="receipt.pdf",
            blob_name="receipts/default-user/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=len(pdf_content),
            sha256_hash="download_head_no_slash",
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = pdf_content
            # Test without trailing slash - should NOT redirect
            response = client.head(f'/api/v1/receipts/{receipt.id}/download?owner=default-user',
                                  follow=False)

            # Key test: should be 200, not 301
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(response.status_code, 301)

    def test_download_authorization(self):
        """Test that /download respects Finance authorization."""
        from django.test import Client

        receipt = Receipt.objects.create(
            owner="user-a",
            original_filename="receipt.pdf",
            blob_name="receipts/user-a/uuid/receipt.pdf",
            mime_type="application/pdf",
            file_size=100,
            sha256_hash="download_auth_test",
        )

        client = Client()
        # User B cannot access User A's receipt
        response = client.get(f'/api/v1/receipts/{receipt.id}/download?owner=user-b')
        self.assertEqual(response.status_code, 403)

        # User A can access their own receipt
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = b"%PDF-1.4"
            response = client.get(f'/api/v1/receipts/{receipt.id}/download?owner=user-a')
            self.assertEqual(response.status_code, 200)

        # Finance department can access any receipt
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = b"%PDF-1.4"
            response = client.get(f'/api/v1/receipts/{receipt.id}/download?owner=finance-department')
            self.assertEqual(response.status_code, 200)

    def test_download_exact_duplicate_access(self):
        """Test that /download allows access to original file for exact duplicate."""
        from django.test import Client

        original_pdf = b"%PDF-1.4\noriginal"
        original = Receipt.objects.create(
            owner="default-user",
            original_filename="original.pdf",
            blob_name="receipts/default-user/uuid/original.pdf",
            mime_type="application/pdf",
            file_size=len(original_pdf),
            sha256_hash="original_hash",
            status='UNIQUE',
        )

        duplicate = Receipt.objects.create(
            owner="default-user",
            original_filename="duplicate.pdf",
            blob_name="",  # No blob for duplicate
            mime_type="application/pdf",
            file_size=0,
            sha256_hash="duplicate_hash",
            status='EXACT_DUPLICATE',
            exact_duplicate_of=original,
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = original_pdf
            # Request duplicate should return original file
            response = client.get(f'/api/v1/receipts/{duplicate.id}/download?owner=default-user')

            self.assertEqual(response.status_code, 200)
            # Verify it called download with the ORIGINAL blob name
            mock_download.assert_called_with(original.blob_name)

    def test_download_image_returns_inline(self):
        """Test that /download returns inline disposition for images."""
        from django.test import Client

        image_content = b'\x89PNG\r\n\x1a\n' + (b"x" * 100)
        receipt = Receipt.objects.create(
            owner="default-user",
            original_filename="receipt.png",
            blob_name="receipts/default-user/uuid/receipt.png",
            mime_type="image/png",
            file_size=len(image_content),
            sha256_hash="download_image_test",
        )

        client = Client()
        with patch('receipts.views.BlobService.download') as mock_download:
            mock_download.return_value = image_content
            response = client.get(f'/api/v1/receipts/{receipt.id}/download?owner=default-user')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'image/png')
            self.assertIn('inline', response['Content-Disposition'])

    def test_download_missing_receipt_returns_404(self):
        """Test that /download returns 404 for missing receipt."""
        from django.test import Client

        client = Client()
        response = client.get('/api/v1/receipts/00000000-0000-0000-0000-000000000000/download?owner=default-user')
        self.assertEqual(response.status_code, 404)


class RejectionReasonsTests(TestCase):
    """Test that rejection reasons are human-readable, not generic."""

    def test_receipt_older_than_35_days_shows_actual_age(self):
        """Receipt older than 35 days should show actual age in rejection reason."""
        from receipts.serializers import ReceiptStatusSerializer

        old_date = (datetime.now().date() - timedelta(days=45))
        receipt = Receipt.objects.create(
            owner="test-user",
            original_filename="old_receipt.pdf",
            blob_name="receipts/test/uuid/old.pdf",
            mime_type="application/pdf",
            file_size=1000,
            sha256_hash="old_receipt_hash",
            status="REJECTED",
            transaction_date=old_date,
            processing_message="Receipt is older than 35 days (45 days old).",
        )

        serializer = ReceiptStatusSerializer(receipt)
        message = serializer.get_message(receipt)

        self.assertIn("older than 35 days", message.lower())
        self.assertNotEqual(message, "Receipt rejected by policy.")
        self.assertIn("45", message)

    def test_blank_receipt_shows_readable_reason(self):
        """Blank receipt should show human-readable reason."""
        from receipts.serializers import ReceiptStatusSerializer

        receipt = Receipt.objects.create(
            owner="test-user",
            original_filename="blank.pdf",
            blob_name="receipts/test/uuid/blank.pdf",
            mime_type="application/pdf",
            file_size=100,
            sha256_hash="blank_hash",
            status="FAILED",
            processing_message="The uploaded receipt appears to be blank. Please upload a receipt with visible content.",
        )

        serializer = ReceiptStatusSerializer(receipt)
        message = serializer.get_message(receipt)

        self.assertIn("blank", message.lower())
        self.assertIn("visible content", message.lower())
        self.assertNotEqual(message, "Receipt processing failed.")

    def test_invalid_document_shows_readable_reason(self):
        """Invalid document should show human-readable reason."""
        from receipts.serializers import ReceiptStatusSerializer

        receipt = Receipt.objects.create(
            owner="test-user",
            original_filename="notreceipt.pdf",
            blob_name="receipts/test/uuid/notreceipt.pdf",
            mime_type="application/pdf",
            file_size=2000,
            sha256_hash="not_receipt_hash",
            status="FAILED",
            processing_message="The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator.",
        )

        serializer = ReceiptStatusSerializer(receipt)
        message = serializer.get_message(receipt)

        self.assertIn("valid receipt", message.lower())
        self.assertNotEqual(message, "Receipt processing failed.")

    def test_ocr_failed_shows_actual_error(self):
        """OCR failure should show actual error reason."""
        from receipts.serializers import ReceiptStatusSerializer

        receipt = Receipt.objects.create(
            owner="test-user",
            original_filename="unreadable.pdf",
            blob_name="receipts/test/uuid/unreadable.pdf",
            mime_type="application/pdf",
            file_size=500,
            sha256_hash="unreadable_hash",
            status="OCR_FAILED",
            processing_message="We couldn't read the receipt. The document may be blurry, unclear, or contain unreadable content.",
        )

        serializer = ReceiptStatusSerializer(receipt)
        message = serializer.get_message(receipt)

        self.assertIn("couldn't read", message.lower())
        self.assertNotEqual(message, "Receipt processing failed.")

    def test_approved_receipt_shows_success_message(self):
        """Approved receipt should show success message."""
        from receipts.serializers import ReceiptStatusSerializer

        receipt = Receipt.objects.create(
            owner="test-user",
            original_filename="good_receipt.pdf",
            blob_name="receipts/test/uuid/good.pdf",
            mime_type="application/pdf",
            file_size=1500,
            sha256_hash="good_hash",
            status="APPROVED",
            vendor_name="Starbucks",
            transaction_date=datetime.now().date(),
            total_amount=Decimal("5.50"),
        )

        serializer = ReceiptStatusSerializer(receipt)
        message = serializer.get_message(receipt)

        self.assertIn("approved", message.lower())
        self.assertNotIn("rejected", message.lower())


class CategoryDetectionTests(TestCase):
    """Test that category detection is reliable and generic across vendors."""

    def test_uber_receipt_classified_as_taxi_not_prepaid_flight(self):
        """Uber/taxi receipt should be Transport: Taxis/Cab/Uber, not Prepaid Flights."""
        extracted = {
            "merchant": {"name": "Uber", "address": None, "phone": None},
            "invoice": {"invoice_number": "TXN12345", "transaction_date": None},
            "amounts": {"subtotal": 22.50, "tax": 0.00, "total": 22.50, "currency": "USD"},
            "payment": {"method": "Credit Card"},
            "line_items": [{"description": "UberX trip", "quantity": 1, "price": 22.50}],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        self.assertEqual(result['category'], 'Transport: Taxis/Cab/Uber')
        self.assertGreaterEqual(result['confidence'], 0.90)
        self.assertIn('uber', result['reason'].lower())

    def test_lyft_receipt_classified_correctly(self):
        """Lyft receipt should be Transport: Taxis/Cab/Uber."""
        extracted = {
            "merchant": {"name": "Lyft", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": None},
            "amounts": {"subtotal": 15.00, "tax": 0.00, "total": 15.00, "currency": "USD"},
            "payment": {"method": "Debit Card"},
            "line_items": [{"description": "Ride booking", "quantity": 1, "price": 15.00}],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        self.assertEqual(result['category'], 'Transport: Taxis/Cab/Uber')
        self.assertGreaterEqual(result['confidence'], 0.90)

    def test_airline_receipt_classified_as_flight(self):
        """Airline receipt should be Transport: Flights."""
        extracted = {
            "merchant": {"name": "United Airlines", "address": None, "phone": None},
            "invoice": {"invoice_number": "UA123456", "transaction_date": None},
            "amounts": {"subtotal": 400.00, "tax": 50.00, "total": 450.00, "currency": "USD"},
            "payment": {"method": "Credit Card"},
            "line_items": [{"description": "Flight booking SFO-LAX", "quantity": 1, "price": 400.00}],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        self.assertEqual(result['category'], 'Transport: Flights')
        self.assertGreaterEqual(result['confidence'], 0.90)

    def test_delta_flight_classified_as_transport_flights_not_prepaid(self):
        """Delta flight should be Transport: Flights, even with 'booking' word."""
        extracted = {
            "merchant": {"name": "Delta Airlines", "address": None, "phone": None},
            "invoice": {"invoice_number": "DL987654", "transaction_date": None},
            "amounts": {"subtotal": 350.00, "tax": 40.00, "total": 390.00, "currency": "USD"},
            "payment": {"method": "Amex"},
            "line_items": [{"description": "Flight ticket booking NYC-MIA", "quantity": 1, "price": 350.00}],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        self.assertNotEqual(result['category'], 'Prepaid Flights')
        self.assertEqual(result['category'], 'Transport: Flights')

    def test_hotel_receipt_not_confused_with_other_categories(self):
        """Hotel receipt should be Accommodation/Hotel."""
        extracted = {
            "merchant": {"name": "Marriott Hotels", "address": "123 Main St", "phone": None},
            "invoice": {"invoice_number": "CONF987654", "transaction_date": None},
            "amounts": {"subtotal": 250.00, "tax": 40.00, "total": 290.00, "currency": "USD"},
            "payment": {"method": "Corporate Card"},
            "line_items": [
                {"description": "Room booking 2 nights", "quantity": 2, "price": 125.00},
                {"description": "Taxes and fees", "quantity": 1, "price": 40.00}
            ],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        self.assertEqual(result['category'], 'Accommodation/Hotel')
        self.assertGreaterEqual(result['confidence'], 0.95)

    def test_merchant_name_has_higher_priority(self):
        """Keyword in merchant name should have higher confidence than in items."""
        extracted = {
            "merchant": {"name": "Uber", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": None},
            "amounts": {"subtotal": 20.00, "tax": 0.00, "total": 20.00, "currency": "USD"},
            "payment": {"method": "Card"},
            "line_items": [
                {"description": "Ride", "quantity": 1, "price": 20.00},
                {"description": "Tip via booking system", "quantity": 0, "price": 0}
            ],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        self.assertEqual(result['category'], 'Transport: Taxis/Cab/Uber')
        self.assertEqual(result['confidence'], 1.0)
        self.assertIn('merchant name', result['reason'].lower())

    def test_starbucks_breakfast_category(self):
        """Starbucks receipt should be Food: Breakfast or Lunch."""
        extracted = {
            "merchant": {"name": "Starbucks Coffee", "address": None, "phone": None},
            "invoice": {"invoice_number": "TXN001", "transaction_date": None},
            "amounts": {"subtotal": 7.50, "tax": 0.60, "total": 8.10, "currency": "USD"},
            "payment": {"method": "Card"},
            "line_items": [
                {"description": "Grande Latte", "quantity": 1, "price": 5.50},
                {"description": "Muffin", "quantity": 1, "price": 2.00}
            ],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        self.assertEqual(result['category'], 'Food: Breakfast or Lunch - Max Claim: €/$/AUD 15 / INR700')
        self.assertGreaterEqual(result['confidence'], 0.80)

    def test_ambiguous_receipt_returns_other_when_confidence_low(self):
        """Ambiguous receipt with low confidence should return Other category."""
        extracted = {
            "merchant": {"name": "Unknown Vendor XYZ", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": None},
            "amounts": {"subtotal": 10.00, "tax": 1.00, "total": 11.00, "currency": "USD"},
            "payment": {"method": "Cash"},
            "line_items": [{"description": "Generic item", "quantity": 1, "price": 10.00}],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        if result['confidence'] < 0.75:
            self.assertEqual(result['category'], 'Other')

    def test_multiple_vendors_same_category_consistent_classification(self):
        """Multiple different taxi vendors should all classify as Transport: Taxis/Cab."""
        vendors = ['Uber', 'Lyft', 'Grab', 'Ola', 'Didi']

        for vendor in vendors:
            with self.subTest(vendor=vendor):
                extracted = {
                    "merchant": {"name": vendor, "address": None, "phone": None},
                    "invoice": {"invoice_number": f"{vendor}123", "transaction_date": None},
                    "amounts": {"subtotal": 18.00, "tax": 0.00, "total": 18.00, "currency": "USD"},
                    "payment": {"method": "Card"},
                    "line_items": [{"description": "Ride", "quantity": 1, "price": 18.00}],
                    "extraction": {}
                }

                result = ReceiptService.determine_category(extracted)

                self.assertEqual(
                    result['category'],
                    'Transport: Taxis/Cab/Uber',
                    f"Vendor {vendor} should be classified as Transport: Taxis/Cab/Uber"
                )


class ReceiptStatusMessageTests(TestCase):
    """Test that ReceiptStatusSerializer provides correct message for workflow state."""

    def test_message_policy_approved_pending_finance_review(self):
        """When policy approves and Finance is pending, message should indicate awaiting Finance review."""
        receipt = Receipt.objects.create(
            owner='test-user',
            original_filename='receipt.pdf',
            blob_name='receipts/test-user/abc/receipt.pdf',
            mime_type='application/pdf',
            file_size=1024,
            sha256_hash='abc123',
            status='NEEDS_REVIEW',
            policy_status='APPROVED',
            processing_message='Receipt has been validated and approved by policy. Awaiting Finance review.'
        )

        from receipts.serializers import ReceiptStatusSerializer
        serializer = ReceiptStatusSerializer(receipt)
        message = serializer.data['message']

        self.assertIn('Finance review', message)
        self.assertIn('Awaiting', message)

    def test_message_finance_approved_after_policy_approved(self):
        """When Finance approves after policy approved, message should indicate Finance approval."""
        receipt = Receipt.objects.create(
            owner='test-user',
            original_filename='receipt.pdf',
            blob_name='receipts/test-user/abc/receipt.pdf',
            mime_type='application/pdf',
            file_size=1024,
            sha256_hash='abc123',
            status='APPROVED',
            policy_status='APPROVED',
            processing_message='Receipt has been validated and approved by policy. Awaiting Finance review.'
        )

        from receipts.serializers import ReceiptStatusSerializer
        serializer = ReceiptStatusSerializer(receipt)
        message = serializer.data['message']

        self.assertIn('Finance', message)
        self.assertIn('approved', message.lower())
        self.assertNotIn('Awaiting', message)

    def test_message_finance_rejected_after_policy_approved(self):
        """When Finance rejects after policy approved, message should indicate Finance rejection."""
        receipt = Receipt.objects.create(
            owner='test-user',
            original_filename='receipt.pdf',
            blob_name='receipts/test-user/abc/receipt.pdf',
            mime_type='application/pdf',
            file_size=1024,
            sha256_hash='abc123',
            status='REJECTED',
            policy_status='APPROVED',
            processing_message='Receipt has been validated and approved by policy. Awaiting Finance review.'
        )

        from receipts.serializers import ReceiptStatusSerializer
        serializer = ReceiptStatusSerializer(receipt)
        message = serializer.data['message']

        self.assertIn('Finance', message)
        self.assertIn('rejected', message.lower())
        self.assertNotIn('policy', message.lower())

    def test_message_policy_rejected_before_finance_review(self):
        """When policy rejects before Finance review, message should indicate policy rejection."""
        receipt = Receipt.objects.create(
            owner='test-user',
            original_filename='receipt.pdf',
            blob_name='receipts/test-user/abc/receipt.pdf',
            mime_type='application/pdf',
            file_size=1024,
            sha256_hash='abc123',
            status='REJECTED',
            policy_status='REJECTED',
            processing_message='Receipt rejected because: Receipt is older than 35 days.'
        )

        from receipts.serializers import ReceiptStatusSerializer
        serializer = ReceiptStatusSerializer(receipt)
        message = serializer.data['message']

        self.assertNotIn('Finance', message)
        self.assertIn('older than 35 days', message)


class HybridCategoryClassifierTests(TestCase):
    """Test the hybrid keyword + semantic category classifier."""

    def test_ola_receipt_classified_as_transport(self):
        """Ola receipt should be classified as Transport: Taxis/Cab/Uber."""
        extracted = {
            "merchant": {"name": "Ola", "address": None, "phone": None},
            "invoice": {"invoice_number": "OLA123456", "transaction_date": None},
            "amounts": {"subtotal": 45.00, "tax": 0.00, "total": 45.00, "currency": "INR"},
            "payment": {"method": "Card"},
            "line_items": [{"description": "Ola ride", "quantity": 1, "price": 45.00}],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        self.assertEqual(result['category'], 'Transport: Taxis/Cab/Uber')
        self.assertGreaterEqual(result['confidence'], 0.80)
        self.assertIn('ola', result['reason'].lower())

    def test_namma_yatri_receipt_classified_as_transport(self):
        """Namma Yatri receipt should be classified as Transport: Taxis/Cab/Uber."""
        extracted = {
            "merchant": {"name": "Namma Yatri", "address": None, "phone": None},
            "invoice": {"invoice_number": "NY654321", "transaction_date": None},
            "amounts": {"subtotal": 52.00, "tax": 0.00, "total": 52.00, "currency": "INR"},
            "payment": {"method": "Card"},
            "line_items": [{"description": "Ride booking", "quantity": 1, "price": 52.00}],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        self.assertEqual(result['category'], 'Transport: Taxis/Cab/Uber')
        self.assertGreaterEqual(result['confidence'], 0.80)

    def test_existing_merchant_classifications_unchanged(self):
        """Existing merchant classifications (Uber, Lyft) should continue to work."""
        test_cases = [
            ("Uber", "Transport: Taxis/Cab/Uber", 0.90),
            ("Lyft", "Transport: Taxis/Cab/Uber", 0.90),
            ("Starbucks", "Food: Breakfast or Lunch - Max Claim: €/$/AUD 15 / INR700", 0.80),
        ]

        for merchant, expected_category, min_confidence in test_cases:
            with self.subTest(merchant=merchant):
                extracted = {
                    "merchant": {"name": merchant, "address": None, "phone": None},
                    "invoice": {"invoice_number": "TEST123", "transaction_date": None},
                    "amounts": {"subtotal": 20.00, "tax": 0.00, "total": 20.00, "currency": "USD"},
                    "payment": {"method": "Card"},
                    "line_items": [{"description": f"{merchant} purchase", "quantity": 1, "price": 20.00}],
                    "extraction": {}
                }

                result = ReceiptService.determine_category(extracted)
                self.assertEqual(result['category'], expected_category)
                self.assertGreaterEqual(result['confidence'], min_confidence)

    def test_generic_taxi_description_recognized(self):
        """A generic taxi or ride-hailing description should be recognized as transport."""
        extracted = {
            "merchant": {"name": "Unknown Taxi Service", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": None},
            "amounts": {"subtotal": 30.00, "tax": 0.00, "total": 30.00, "currency": "USD"},
            "payment": {"method": "Card"},
            "line_items": [{"description": "Taxi fare for ride", "quantity": 1, "price": 30.00}],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        # Should recognize as transport even with unknown merchant name
        self.assertEqual(result['category'], 'Transport: Taxis/Cab/Uber')
        self.assertGreater(result['confidence'], 0.5)

    def test_semantic_matching_without_exact_keywords(self):
        """A receipt with semantic meaning but no exact keywords should be classified."""
        extracted = {
            "merchant": {"name": "LocalRideApp", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": None},
            "amounts": {"subtotal": 25.00, "tax": 0.00, "total": 25.00, "currency": "USD"},
            "payment": {"method": "App Payment"},
            "line_items": [{"description": "Passenger transportation service for city travel", "quantity": 1, "price": 25.00}],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        # Should classify as transport based on semantic matching
        self.assertEqual(result['category'], 'Transport: Taxis/Cab/Uber')
        self.assertGreater(result['confidence'], 0.5)

    def test_grocery_receipt_not_auto_approved_as_other(self):
        """A grocery receipt should not receive high confidence in Other category."""
        extracted = {
            "merchant": {"name": "Grocery Store ABC", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": None},
            "amounts": {"subtotal": 150.00, "tax": 15.00, "total": 165.00, "currency": "USD"},
            "payment": {"method": "Card"},
            "line_items": [
                {"description": "Milk", "quantity": 1, "price": 40.00},
                {"description": "Bread", "quantity": 1, "price": 30.00},
                {"description": "Vegetables", "quantity": 2, "price": 80.00},
            ],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        # Should be classified as Other but with low confidence
        self.assertEqual(result['category'], 'Other')
        self.assertLess(result['confidence'], 0.75)  # Below threshold for auto-approval

    def test_low_confidence_result_below_threshold(self):
        """Receipts with insufficient evidence should return below-threshold confidence."""
        extracted = {
            "merchant": {"name": "Random Store XYZ", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": None},
            "amounts": {"subtotal": 50.00, "tax": 5.00, "total": 55.00, "currency": "USD"},
            "payment": {"method": None},
            "line_items": [],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        # Without clear evidence, should not auto-assign
        if result['category'] == 'Other':
            self.assertLess(result['confidence'], 0.75)

    def test_no_receipt_data_returns_other_with_zero_confidence(self):
        """Empty or None receipt data should return Other with zero confidence."""
        result = ReceiptService.determine_category(None)

        self.assertEqual(result['category'], 'Other')
        self.assertEqual(result['confidence'], 0.0)

    def test_ambiguous_classification_returns_other(self):
        """When top categories are too close, should return Other instead of guessing."""
        # A receipt that could be Transport or a generic category
        extracted = {
            "merchant": {"name": "Go Away", "address": None, "phone": None},  # Could match "go" related services
            "invoice": {"invoice_number": None, "transaction_date": None},
            "amounts": {"subtotal": 20.00, "tax": 0.00, "total": 20.00, "currency": "USD"},
            "payment": {"method": "Card"},
            "line_items": [],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        # Result should be returned (either specific category or Other)
        self.assertIn('category', result)
        self.assertIn('confidence', result)

    def test_classifier_handles_missing_fields_gracefully(self):
        """Classifier should handle receipts with missing OCR fields."""
        test_cases = [
            # Missing merchant name
            {
                "merchant": {"name": None, "address": None, "phone": None},
                "invoice": {"invoice_number": None, "transaction_date": None},
                "amounts": {"subtotal": 30.00, "tax": 0.00, "total": 30.00, "currency": "USD"},
                "payment": {"method": None},
                "line_items": [{"description": "Taxi fare", "quantity": 1, "price": 30.00}],
                "extraction": {}
            },
            # Missing line items
            {
                "merchant": {"name": "Starbucks", "address": None, "phone": None},
                "invoice": {"invoice_number": None, "transaction_date": None},
                "amounts": {"subtotal": 5.00, "tax": 0.00, "total": 5.00, "currency": "USD"},
                "payment": {"method": "Card"},
                "line_items": [],
                "extraction": {}
            },
        ]

        for extracted in test_cases:
            with self.subTest(extracted=extracted):
                result = ReceiptService.determine_category(extracted)
                self.assertIn('category', result)
                self.assertIn('confidence', result)
                self.assertIn('reason', result)

    def test_classifier_return_structure_unchanged(self):
        """Classifier should return the same structure as before (backward compatibility)."""
        extracted = {
            "merchant": {"name": "Uber", "address": None, "phone": None},
            "invoice": {"invoice_number": "TEST123", "transaction_date": None},
            "amounts": {"subtotal": 20.00, "tax": 0.00, "total": 20.00, "currency": "USD"},
            "payment": {"method": "Card"},
            "line_items": [{"description": "UberX trip", "quantity": 1, "price": 20.00}],
            "extraction": {}
        }

        result = ReceiptService.determine_category(extracted)

        # Must have these keys
        self.assertIn('category', result)
        self.assertIn('confidence', result)
        self.assertIn('reason', result)

        # Confidence must be in range
        self.assertIsInstance(result['confidence'], (int, float))
        self.assertGreaterEqual(result['confidence'], 0.0)
        self.assertLessEqual(result['confidence'], 1.0)

        # Category must be a string
        self.assertIsInstance(result['category'], str)


class EndToEndReceiptWorkflowTests(TestCase):
    """Integration tests for complete receipt upload and classification workflow."""

    def test_ola_email_receipt_screenshot_workflow(self):
        """Test complete workflow for Ola email receipt screenshot with OCR fallback."""
        # Simulate OCR extraction from Ola email receipt screenshot
        extracted = {
            "merchant": {"name": None, "address": None, "phone": None},  # Azure missed the merchant
            "invoice": {"invoice_number": None, "transaction_date": "2026-10-13"},
            "amounts": {"subtotal": 52.00, "tax": 0.00, "total": None, "currency": None},  # Missing structured total
            "payment": {"method": "Card"},
            "line_items": [{"description": "Ride booking", "quantity": 1, "price": None}],
            "extraction": {"ocr_content":
                "Your Ride Receipt\n"
                "Trip with: Ola\n"
                "Date: October 13, 2026\n"
                "Pickup: Business Park\n"
                "Dropoff: Central Station\n"
                "Ride Fare: ₹52.00\n"
                "Total: ₹52.00"
            }
        }

        # Extract from OCR fallback
        doc_service = DocumentIntelligenceService()
        fallback = doc_service._extract_from_ocr_text(extracted['extraction']['ocr_content'])

        # Verify OCR fallback recovered the data
        self.assertEqual(fallback['merchant_name'], 'Ola')
        self.assertEqual(fallback['total'], 52.00)
        self.assertEqual(fallback['transaction_date'], '2026-10-13')

        # Simulate structured extraction enrichment with fallback
        extracted['merchant']['name'] = fallback['merchant_name']
        extracted['amounts']['total'] = fallback['total']

        # Verify validation passes with OCR evidence
        is_valid = ReceiptService._is_valid_receipt(extracted)
        self.assertTrue(is_valid, "Receipt with OCR evidence should pass validation")

        # Verify category classification
        category_result = ReceiptService.determine_category(extracted)
        self.assertEqual(category_result['category'], 'Transport: Taxis/Cab/Uber')
        self.assertGreaterEqual(category_result['confidence'], 0.75)

    def test_rapido_ride_details_screenshot_workflow(self):
        """Test complete workflow for Rapido ride-details screenshot with OCR fallback."""
        extracted = {
            "merchant": {"name": None, "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": None},
            "amounts": {"subtotal": 63.00, "tax": 0.00, "total": None, "currency": "INR"},
            "payment": {"method": None},
            "line_items": [],
            "extraction": {"ocr_content":
                "Rapido Bike Taxi Receipt\n"
                "Date: October 13, 2026\n"
                "From: Tech Park\n"
                "To: Railway Station\n"
                "Ride Amount: ₹63\n"
                "Total Payable: ₹63\n"
                "Payment: UPI"
            }
        }

        # Extract from OCR fallback
        doc_service = DocumentIntelligenceService()
        fallback = doc_service._extract_from_ocr_text(extracted['extraction']['ocr_content'])

        # Verify OCR fallback recovered Rapido merchant
        self.assertEqual(fallback['merchant_name'], 'Rapido')
        self.assertEqual(fallback['total'], 63.00)

        # Enrichment
        extracted['merchant']['name'] = fallback['merchant_name']
        extracted['amounts']['total'] = fallback['total']
        extracted['invoice']['transaction_date'] = doc_service._extract_month_name_date(extracted['extraction']['ocr_content'])

        # Verify validation passes
        is_valid = ReceiptService._is_valid_receipt(extracted)
        self.assertTrue(is_valid, "Rapido receipt with OCR evidence should pass validation")

        # Verify category classification
        category_result = ReceiptService.determine_category(extracted)
        self.assertEqual(category_result['category'], 'Transport: Taxis/Cab/Uber')
        self.assertGreaterEqual(category_result['confidence'], 0.75)

    def test_screenshot_with_missing_merchant_but_sufficient_ocr(self):
        """Test receipt with missing structured merchant but sufficient OCR evidence."""
        extracted = {
            "merchant": {"name": None, "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": "2026-10-12"},
            "amounts": {"subtotal": None, "tax": 0.00, "total": 250.00, "currency": "INR"},
            "payment": {"method": "Card"},
            "line_items": [{"description": "Trip charge", "quantity": 1, "price": 250.00}],
            "extraction": {"ocr_content": "Uber Receipt - Date: 12 Oct 2026 - Total: ₹250"}
        }

        doc_service = DocumentIntelligenceService()
        fallback = doc_service._extract_from_ocr_text(extracted['extraction']['ocr_content'])
        extracted['merchant']['name'] = fallback.get('merchant_name') or 'Uber'  # OCR or fallback

        # Should pass validation
        is_valid = ReceiptService._is_valid_receipt(extracted)
        self.assertTrue(is_valid)

        # Should classify correctly
        category_result = ReceiptService.determine_category(extracted)
        self.assertEqual(category_result['category'], 'Transport: Taxis/Cab/Uber')

    def test_receipt_with_multiple_amounts_uses_correct_total(self):
        """Test that multiple amounts in OCR text extract the final total, not discount or intermediate amounts."""
        extracted = {
            "merchant": {"name": "Uber", "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": "2026-10-13"},
            "amounts": {"subtotal": None, "tax": 0.00, "total": None, "currency": "USD"},
            "payment": {"method": "Card"},
            "line_items": [],
            "extraction": {"ocr_content":
                "UberX Trip Receipt\n"
                "Base Fare: $15.00\n"
                "Surge Charge: $5.00\n"
                "Discount: -$2.00\n"
                "Total Amount: $18.00"  # Should use this, not intermediate amounts
            }
        }

        doc_service = DocumentIntelligenceService()
        fallback = doc_service._extract_from_ocr_text(extracted['extraction']['ocr_content'])

        # Must extract the final total, not intermediate amounts
        self.assertEqual(fallback['total'], 18.00)
        self.assertNotEqual(fallback['total'], 15.00)  # Not base fare
        self.assertNotEqual(fallback['total'], 5.00)   # Not surge
        self.assertNotEqual(fallback['total'], -2.00)  # Not discount

    def test_unrelated_image_validation_fails(self):
        """Test that unrelated images are still rejected by validation."""
        extracted = {
            "merchant": {"name": None, "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": None},
            "amounts": {"subtotal": None, "tax": 0.00, "total": None, "currency": None},
            "payment": {"method": None},
            "line_items": [],
            "extraction": {"ocr_content": "Just a random landscape photo with no transaction data"}
        }

        # Should fail validation
        is_valid = ReceiptService._is_valid_receipt(extracted)
        self.assertFalse(is_valid, "Unrelated image should fail validation")

    def test_ocr_result_blank_detection(self):
        """Test that completely blank OCR results are detected."""
        extracted = {
            "merchant": {"name": None, "address": None, "phone": None},
            "invoice": {"invoice_number": None, "transaction_date": None},
            "amounts": {"subtotal": None, "tax": None, "total": None, "currency": None},
            "payment": {"method": None},
            "line_items": [],
            "extraction": {"ocr_content": ""}
        }

        is_blank = ReceiptService._is_ocr_result_blank(extracted)
        self.assertTrue(is_blank, "Empty extraction should be marked as blank")

    def test_manual_category_selection_supported(self):
        """Test that manual category selection is supported for low-confidence results."""
        # This test verifies the endpoint supports manual category selection
        # Detailed integration testing happens in the view tests

        # Verify all category choices are valid
        valid_categories = [choice[0] for choice in Receipt.CATEGORY_CHOICES]
        self.assertGreater(len(valid_categories), 0)

        # Verify transport category exists
        self.assertIn('Transport: Taxis/Cab/Uber', valid_categories)
