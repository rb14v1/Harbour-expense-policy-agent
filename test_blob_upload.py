#!/usr/bin/env python
"""Test Blob upload through the fixed BlobService."""

import requests
import sys

print("=" * 80)
print("BLOB UPLOAD TEST - Testing ContentSettings Fix")
print("=" * 80)

receipt_path = "data/sample_receipts/test_receipt.pdf"

print(f"\nUploading: {receipt_path}")
print("Target: http://localhost:8000/api/v1/receipts/upload/\n")

try:
    with open(receipt_path, 'rb') as f:
        files = {'file': f}
        data = {'owner': 'test-user'}

        response = requests.post(
            'http://localhost:8000/api/v1/receipts/upload/',
            files=files,
            data=data,
            timeout=30
        )

    print(f"Status Code: {response.status_code}")
    print(f"\nResponse JSON:")
    import json
    result = response.json()
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 80)

    if response.status_code in [200, 201]:
        receipt_id = result.get('receipt_id')
        status = result.get('status')
        message = result.get('message')

        print(f"✅ UPLOAD SUCCEEDED")
        print(f"\n Receipt ID: {receipt_id}")
        print(f"   Status: {status}")
        print(f"   Message: {message}")

        if "Blob upload failed" in message or "blob" in message.lower():
            print(f"\n❌ Blob upload still failing: {message}")
            sys.exit(1)
        else:
            print(f"\n✅ ContentSettings fix appears to be working!")
            sys.exit(0)
    else:
        print(f"❌ Upload failed with status {response.status_code}")
        print(result)
        sys.exit(1)

except requests.exceptions.ConnectionError:
    print("❌ Could not connect to Django server")
    print("   Make sure 'python manage.py runserver 127.0.0.1:8000' is running")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)}")
    sys.exit(1)
