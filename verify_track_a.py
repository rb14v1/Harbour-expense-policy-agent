#!/usr/bin/env python
"""
Track A Receipt Ingestion & Storage Verification Script

This script directly executes the Track A flow:
1. File validation
2. Receipt creation
3. SHA-256 hashing
4. Exact duplicate check
5. Azure Blob upload
6. PostgreSQL Receipt record

Usage:
    python verify_track_a.py [test_receipt_path]

Example:
    python verify_track_a.py data/sample_receipts/test_receipt.pdf
"""

import os
import sys
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from receipts.services import ReceiptService
from receipts.exceptions import BlobUploadError
import traceback


def create_test_receipt_file():
    """Create a minimal PDF-like test receipt file."""
    # Minimal PDF header
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources 4 0 R /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >>
endobj
5 0 obj
<< >>
stream
BT
/F1 12 Tf
50 750 Td
(Test Receipt) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
0000000288 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
360
%%EOF
"""
    return pdf_content


def print_result(receipt, error=None):
    """Print formatted Track A result."""
    print("\n" + "=" * 60)
    print("TRACK A RESULT")
    print("=" * 60)

    if error:
        print(f"\n❌ ERROR: {error}\n")
        return

    if receipt:
        print(f"\nReceipt ID:               {receipt.id}")
        print(f"Original filename:        {receipt.original_filename}")
        print(f"Owner:                    {receipt.owner}")
        print(f"File size:                {receipt.file_size} bytes")
        print(f"MIME type:                {receipt.mime_type}")
        print(f"SHA-256:                  {receipt.sha256_hash}")
        print(f"Status:                   {receipt.status}")
        print(f"Blob name:                {receipt.blob_name}")

        if receipt.exact_duplicate_of:
            print(f"Exact duplicate:          YES")
            print(f"Exact duplicate of:       {receipt.exact_duplicate_of.id}")
            print(f"Duplicate reason:         {receipt.duplicate_reason}")
        else:
            print(f"Exact duplicate:          NO")
            print(f"Exact duplicate of:       None")

        print(f"\nDatabase status:          PERSISTED")
        print(f"Created at:               {receipt.created_at}")

    print("\n" + "=" * 60)


def main():
    # Get test receipt path from command line or use default
    test_receipt_path = sys.argv[1] if len(sys.argv) > 1 else None

    if test_receipt_path:
        # Use provided file
        path = Path(test_receipt_path)
        if not path.exists():
            print_result(None, f"File not found: {test_receipt_path}")
            return 1

        filename = path.name
        with open(path, 'rb') as f:
            file_content = f.read()
    else:
        # Create test receipt in memory
        filename = "test_receipt.pdf"
        file_content = create_test_receipt_file()

    print(f"\n📋 Testing Track A with file: {filename}")
    print(f"📦 File size: {len(file_content)} bytes")
    print("🚀 Executing Track A flow...")

    try:
        # Create Django UploadedFile
        file_obj = SimpleUploadedFile(
            name=filename,
            content=file_content,
            content_type="application/pdf"
        )

        # Execute Track A
        service = ReceiptService()
        receipt = service.create_and_upload_receipt(
            file_obj=file_obj,
            filename=filename,
            owner="test-user"
        )

        print_result(receipt)
        return 0

    except BlobUploadError as e:
        print_result(None, f"Azure Blob Upload Failed: {str(e)}\n\n"
                           "⚠️  CONFIGURATION MISSING:\n"
                           "   AZURE_STORAGE_CONNECTION_STRING is not properly configured.\n"
                           "   Set it in .env file to enable Blob Storage.\n"
                           f"\n   Details: {str(e)}")
        return 1

    except Exception as e:
        print_result(None, f"{type(e).__name__}: {str(e)}")
        print(f"\n📍 Full Traceback:")
        print("-" * 60)
        traceback.print_exc()
        print("-" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
