#!/usr/bin/env python
"""End-to-end upload flow test with complete output capture."""

import requests
import json
import sys
import time

print("=" * 100)
print("END-TO-END RECEIPT UPLOAD FLOW TEST")
print("=" * 100)

# Test 1: New unique PDF
print("\n" + "=" * 100)
print("TEST 1: Upload NEW unique PDF")
print("=" * 100)

test_file = "data/sample_receipts/e2e_test_receipt.pdf"

# Create a unique test file
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
(E2E TEST - WALMART) Tj
0 -20 Td
(REC-E2E-2026) Tj
0 -20 Td
(2026-09-12) Tj
0 -20 Td
(Total: 45.99) Tj
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
376
%%EOF
"""

with open(test_file, 'wb') as f:
    f.write(pdf_content)

print(f"\n📋 Uploading NEW PDF: {test_file}")

time.sleep(1)  # Give server time to be ready

try:
    with open(test_file, 'rb') as f:
        files = {'file': f}
        data = {'owner': 'e2e-test-user'}

        print("Sending POST /api/v1/receipts/upload/...")
        response = requests.post(
            'http://localhost:8000/api/v1/receipts/upload/',
            files=files,
            data=data,
            timeout=60
        )

    print(f"\nStatus Code: {response.status_code}")
    result = response.json()
    print(f"\nResponse JSON:")
    print(json.dumps(result, indent=2))

    receipt_id_1 = result.get('receipt_id')
    status_1 = result.get('status')
    message_1 = result.get('message')

    print(f"\n✅ RESULT:")
    print(f"   Receipt ID: {receipt_id_1}")
    print(f"   Status: {status_1}")
    print(f"   Message: {message_1}")

    if status_1 not in ['QUEUED_FOR_OCR', 'UNIQUE', 'APPROVED', 'REJECTED']:
        if 'Duplicate' in message_1 or 'duplicate' in message_1:
            print(f"   ⚠️  First upload marked as duplicate (unexpected)")
        else:
            print(f"   ⚠️  Unexpected status for new file")
    else:
        print(f"   ✅ New file correctly proceeded")

except requests.exceptions.ConnectionError:
    print("❌ Could not connect to server")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Same PDF again
print("\n" + "=" * 100)
print("TEST 2: Upload SAME PDF again (should be EXACT_DUPLICATE)")
print("=" * 100)

print(f"\n📋 Uploading SAME PDF again")

time.sleep(1)

try:
    with open(test_file, 'rb') as f:
        files = {'file': f}
        data = {'owner': 'e2e-test-user'}

        print("Sending POST /api/v1/receipts/upload/...")
        response = requests.post(
            'http://localhost:8000/api/v1/receipts/upload/',
            files=files,
            data=data,
            timeout=60
        )

    print(f"\nStatus Code: {response.status_code}")
    result = response.json()
    print(f"\nResponse JSON:")
    print(json.dumps(result, indent=2))

    receipt_id_2 = result.get('receipt_id')
    status_2 = result.get('status')
    message_2 = result.get('message')

    print(f"\n✅ RESULT:")
    print(f"   Receipt ID: {receipt_id_2}")
    print(f"   Status: {status_2}")
    print(f"   Message: {message_2}")

    if status_2 == 'EXACT_DUPLICATE':
        print(f"   ✅ Correctly marked as EXACT_DUPLICATE")
    else:
        print(f"   ⚠️  Expected EXACT_DUPLICATE, got {status_2}")

except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Different PDF
print("\n" + "=" * 100)
print("TEST 3: Upload DIFFERENT PDF (should NOT be duplicate)")
print("=" * 100)

test_file_2 = "data/sample_receipts/e2e_test_receipt_2.pdf"

pdf_content_2 = b"""%PDF-1.4
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
(E2E TEST - STARBUCKS) Tj
0 -20 Td
(REC-STB-9999) Tj
0 -20 Td
(2026-09-13) Tj
0 -20 Td
(Total: 8.75) Tj
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
366
%%EOF
"""

with open(test_file_2, 'wb') as f:
    f.write(pdf_content_2)

print(f"\n📋 Uploading DIFFERENT PDF: {test_file_2}")

time.sleep(1)

try:
    with open(test_file_2, 'rb') as f:
        files = {'file': f}
        data = {'owner': 'e2e-test-user'}

        print("Sending POST /api/v1/receipts/upload/...")
        response = requests.post(
            'http://localhost:8000/api/v1/receipts/upload/',
            files=files,
            data=data,
            timeout=60
        )

    print(f"\nStatus Code: {response.status_code}")
    result = response.json()
    print(f"\nResponse JSON:")
    print(json.dumps(result, indent=2))

    receipt_id_3 = result.get('receipt_id')
    status_3 = result.get('status')
    message_3 = result.get('message')

    print(f"\n✅ RESULT:")
    print(f"   Receipt ID: {receipt_id_3}")
    print(f"   Status: {status_3}")
    print(f"   Message: {message_3}")

    if status_3 not in ['QUEUED_FOR_OCR', 'UNIQUE', 'APPROVED', 'REJECTED']:
        if 'Duplicate' in message_3 or 'duplicate' in message_3:
            print(f"   ⚠️  Different file marked as duplicate (unexpected)")
        else:
            print(f"   ⚠️  Unexpected status")
    else:
        print(f"   ✅ Different file correctly proceeded")

except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Same second PDF again
print("\n" + "=" * 100)
print("TEST 4: Upload SAME second PDF again (should be EXACT_DUPLICATE)")
print("=" * 100)

print(f"\n📋 Uploading SAME second PDF again")

time.sleep(1)

try:
    with open(test_file_2, 'rb') as f:
        files = {'file': f}
        data = {'owner': 'e2e-test-user'}

        print("Sending POST /api/v1/receipts/upload/...")
        response = requests.post(
            'http://localhost:8000/api/v1/receipts/upload/',
            files=files,
            data=data,
            timeout=60
        )

    print(f"\nStatus Code: {response.status_code}")
    result = response.json()
    print(f"\nResponse JSON:")
    print(json.dumps(result, indent=2))

    receipt_id_4 = result.get('receipt_id')
    status_4 = result.get('status')
    message_4 = result.get('message')

    print(f"\n✅ RESULT:")
    print(f"   Receipt ID: {receipt_id_4}")
    print(f"   Status: {status_4}")
    print(f"   Message: {message_4}")

    if status_4 == 'EXACT_DUPLICATE':
        print(f"   ✅ Correctly marked as EXACT_DUPLICATE")
    else:
        print(f"   ⚠️  Expected EXACT_DUPLICATE, got {status_4}")

except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"\n✅ TEST 1 (New PDF):              Status={status_1}")
print(f"✅ TEST 2 (Same again):          Status={status_2}")
print(f"✅ TEST 3 (Different PDF):       Status={status_3}")
print(f"✅ TEST 4 (Same different):      Status={status_4}")
print("\n" + "=" * 100)
