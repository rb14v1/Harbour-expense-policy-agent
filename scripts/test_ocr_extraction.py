#!/usr/bin/env python
"""
Standalone OCR extraction test script.

Tests the OCR & Structured Data module end-to-end WITHOUT:
- PostgreSQL / Django ORM
- Teams integration
- Duplicate detection
- Policy processing
- Blob Storage

Reuses existing:
- DocumentIntelligenceService (Azure Document Intelligence integration)
- NormalizationService (normalized 10-field JSON schema)
- Existing .env configuration

Usage:
    python scripts/test_ocr_extraction.py <path-to-receipt-file>

Example:
    python scripts/test_ocr_extraction.py data/sample_receipt.pdf
    python scripts/test_ocr_extraction.py data/sample_receipt.jpg

Expected output:
    - Raw extracted fields from Azure Document Intelligence
    - Final normalized 10-field JSON
    - Error details if any step fails

Author: Claude Code
"""

import os
import sys
import json
import logging
from pathlib import Path
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# Configure Django settings before importing models/services
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from receipts.services.document_intelligence_service import DocumentIntelligenceService
from receipts.services.normalization_service import NormalizationService
from receipts.exceptions import DocumentExtractionError, ReceiptNormalizationError


# Configure logging for this script
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def determine_content_type(file_path: str) -> str:
    """Determine MIME type from file extension."""
    ext = Path(file_path).suffix.lower()
    mime_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
    }
    return mime_types.get(ext, 'application/octet-stream')


def read_receipt_file(file_path: str) -> bytes:
    """Read receipt file as bytes."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Receipt file not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    with open(path, 'rb') as f:
        return f.read()


def print_section(title: str) -> None:
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(f"{title:^80}")
    print(f"{'='*80}\n")


def print_extracted(extracted: dict) -> None:
    """Print extracted fields in readable format."""
    print("MERCHANT INFORMATION:")
    merchant = extracted.get('merchant', {})
    print(f"  Name:    {merchant.get('name')}")
    print(f"  Address: {merchant.get('address')}")
    print(f"  Phone:   {merchant.get('phone')}")

    print("\nINVOICE INFORMATION:")
    invoice = extracted.get('invoice', {})
    print(f"  Invoice #: {invoice.get('invoice_number')}")
    print(f"  Date:      {invoice.get('transaction_date')}")

    print("\nAMOUNTS:")
    amounts = extracted.get('amounts', {})
    print(f"  Subtotal: {amounts.get('subtotal')}")
    print(f"  Tax:      {amounts.get('tax')}")
    print(f"  Total:    {amounts.get('total')}")
    print(f"  Currency: {amounts.get('currency')}")

    print("\nPAYMENT METHOD:")
    payment = extracted.get('payment', {})
    print(f"  Method: {payment.get('method')}")

    line_items = extracted.get('line_items', [])
    if line_items:
        print(f"\nLINE ITEMS ({len(line_items)}):")
        for i, item in enumerate(line_items, 1):
            print(f"  Item {i}:")
            print(f"    Description: {item.get('description')}")
            print(f"    Quantity:    {item.get('quantity')}")
            print(f"    Unit Price:  {item.get('unit_price')}")
            print(f"    Amount:      {item.get('amount')}")

    extraction = extracted.get('extraction', {})
    print(f"\nEXTRACTION METADATA:")
    print(f"  Provider: {extraction.get('provider')}")
    print(f"  Model:    {extraction.get('model')}")


def print_normalized(normalized: dict) -> None:
    """Print normalized 10-field contract."""
    print("10-FIELD NORMALIZED CONTRACT:")
    print(f"  vendor_name:                 {normalized.get('vendor_name')}")
    print(f"  vendor_normalized:           {normalized.get('vendor_normalized')}")
    print(f"  invoice_number:              {normalized.get('invoice_number')}")
    print(f"  invoice_number_normalized:   {normalized.get('invoice_number_normalized')}")
    print(f"  transaction_date:            {normalized.get('transaction_date')}")
    print(f"  subtotal:                    {normalized.get('subtotal')}")
    print(f"  tax_amount:                  {normalized.get('tax_amount')}")
    print(f"  total_amount:                {normalized.get('total_amount')}")
    print(f"  currency:                    {normalized.get('currency')}")
    print(f"  payment_method:              {normalized.get('payment_method')}")


def print_json(data: dict, label: str) -> None:
    """Print data as formatted JSON."""
    print(f"\n{label}:")
    print(json.dumps(data, indent=2, default=str))


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_ocr_extraction.py <path-to-receipt-file>")
        print("\nExample:")
        print("  python scripts/test_ocr_extraction.py data/sample_receipt.pdf")
        print("  python scripts/test_ocr_extraction.py data/sample_receipt.jpg")
        sys.exit(1)

    receipt_path = sys.argv[1]

    print_section("OCR EXTRACTION TEST")
    print(f"Receipt file: {receipt_path}\n")

    # Step 1: Read file
    try:
        logger.info("Reading receipt file...")
        file_bytes = read_receipt_file(receipt_path)
        content_type = determine_content_type(receipt_path)
        logger.info(f"✓ Read {len(file_bytes)} bytes (type: {content_type})")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"✗ File error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Unexpected error reading file: {str(e)}")
        sys.exit(1)

    # Step 2: Extract with Azure Document Intelligence
    try:
        logger.info("Calling Azure Document Intelligence...")
        service = DocumentIntelligenceService()
        extracted = service.analyze_receipt(content=file_bytes, content_type=content_type)
        logger.info("✓ Extraction successful")
    except DocumentExtractionError as e:
        logger.error(f"✗ Azure Document Intelligence error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Extraction error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Print extracted data
    print_section("EXTRACTED DATA FROM AZURE")
    print_extracted(extracted)

    # Step 3: Normalize
    try:
        logger.info("Normalizing extracted data...")
        normalized = NormalizationService.normalize(extracted)
        logger.info("✓ Normalization successful")
    except ReceiptNormalizationError as e:
        logger.error(f"✗ Normalization error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Normalization error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Print normalized data
    print_section("NORMALIZED DATA (10-FIELD CONTRACT)")
    print_normalized(normalized)

    # Step 4: Print JSON outputs for reference
    print_section("FULL JSON OUTPUTS")
    print_json(extracted, "RAW EXTRACTED")
    print_json(normalized, "NORMALIZED (10-FIELD)")

    # Step 5: Validation
    print_section("VALIDATION")

    required_fields = {
        'vendor_name', 'vendor_normalized', 'invoice_number',
        'invoice_number_normalized', 'transaction_date', 'subtotal',
        'tax_amount', 'total_amount', 'currency', 'payment_method'
    }

    missing_fields = required_fields - set(normalized.keys())
    if missing_fields:
        logger.warning(f"⚠ Missing fields: {missing_fields}")
    else:
        logger.info("✓ All 10 required fields present")

    non_null_fields = {k: v for k, v in normalized.items() if v is not None}
    null_count = len(normalized) - len(non_null_fields)
    logger.info(f"✓ {len(non_null_fields)}/10 fields populated ({null_count} null)")

    print_section("SUCCESS")
    print("OCR extraction and normalization completed successfully.\n")
    print("The normalized data is ready for:")
    print("  - Database persistence")
    print("  - Duplicate detection")
    print("  - Policy evaluation")
    print()


if __name__ == '__main__':
    main()
