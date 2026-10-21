# Scripts Directory

Standalone utility scripts for testing and development.

## test_ocr_extraction.py

Standalone OCR extraction test script for end-to-end testing WITHOUT database, Teams, or policy logic.

### Purpose

Test the OCR & Structured Data module in isolation:
- Load a local receipt image/PDF
- Extract fields using Azure Document Intelligence
- Normalize to the standard 10-field JSON schema
- Print both raw and normalized outputs

### What It Uses (Existing Code)

- `DocumentIntelligenceService` — Azure Document Intelligence integration
- `NormalizationService` — Normalization to 10-field contract
- `.env` configuration — Existing Azure credentials

### What It Does NOT Use

- ❌ PostgreSQL / Django ORM
- ❌ Teams integration
- ❌ Duplicate detection
- ❌ Policy processing
- ❌ Blob Storage
- ❌ Receipt model creation

### Prerequisites

1. **Azure credentials configured in `.env`**
   ```
   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://<region>.api.cognitive.microsoft.com/
   AZURE_DOCUMENT_INTELLIGENCE_KEY=<your-key>
   ```

2. **Python dependencies installed**
   ```bash
   pip install -r requirements.txt
   ```

3. **Receipt file available**
   - Supported formats: `.pdf`, `.jpg`, `.jpeg`, `.png`
   - Can be any valid receipt image/PDF

### Usage

```bash
python scripts/test_ocr_extraction.py <path-to-receipt>
```

#### Examples

```bash
# Test with a PDF receipt
python scripts/test_ocr_extraction.py data/sample_receipt.pdf

# Test with a JPG receipt
python scripts/test_ocr_extraction.py data/sample_receipt.jpg

# Test with a PNG receipt
python scripts/test_ocr_extraction.py data/sample_receipt.png
```

### Output

The script prints:

1. **EXTRACTED DATA FROM AZURE**
   - Merchant name, address, phone
   - Invoice number, transaction date
   - Amounts (subtotal, tax, total, currency)
   - Payment method
   - Line items (if any)

2. **NORMALIZED DATA (10-FIELD CONTRACT)**
   - All 10 fields in the standard contract:
     - `vendor_name` (original)
     - `vendor_normalized` (lowercase)
     - `invoice_number` (original)
     - `invoice_number_normalized` (uppercase, no formatting)
     - `transaction_date` (YYYY-MM-DD)
     - `subtotal` (float)
     - `tax_amount` (float)
     - `total_amount` (float)
     - `currency` (uppercase code: INR, USD, etc.)
     - `payment_method` (CARD, CASH, DIGITAL, etc.)

3. **FULL JSON OUTPUTS**
   - Raw extracted structure
   - Normalized 10-field JSON

4. **VALIDATION**
   - Checks all 10 fields present
   - Reports null vs. populated fields
   - Overall success/failure status

### Error Handling

The script handles these errors gracefully:

- **Missing file**: `FileNotFoundError` → clear message
- **Missing credentials**: Azure SDK error → "credentials not configured"
- **Azure API failure**: `DocumentExtractionError` → wrapped with details
- **Normalization failure**: `ReceiptNormalizationError` → with context

### Exit Codes

- `0` — Success
- `1` — File error, Azure error, or normalization error

### Example Output

```
================================================================================
                          OCR EXTRACTION TEST
================================================================================

Receipt file: data/sample_receipt.pdf

INFO: Reading receipt file...
✓ Read 125456 bytes (type: application/pdf)
INFO: Calling Azure Document Intelligence...
✓ Extraction successful
INFO: Normalizing extracted data...
✓ Normalization successful

================================================================================
                        EXTRACTED DATA FROM AZURE
================================================================================

MERCHANT INFORMATION:
  Name:    ABC Hotel
  Address: 123 Main St, New York, NY 10001
  Phone:   (555) 123-4567

INVOICE INFORMATION:
  Invoice #: INV-12345
  Date:      2026-09-01

AMOUNTS:
  Subtotal: 4000.0
  Tax:      720.0
  Total:    4720.0
  Currency: INR

PAYMENT METHOD:
  Method: Credit Card

EXTRACTION METADATA:
  Provider: azure_ai_document_intelligence
  Model:    prebuilt-receipt

================================================================================
                    NORMALIZED DATA (10-FIELD CONTRACT)
================================================================================

10-FIELD NORMALIZED CONTRACT:
  vendor_name:                 ABC Hotel
  vendor_normalized:           abc hotel
  invoice_number:              INV-12345
  invoice_number_normalized:   INV12345
  transaction_date:            2026-09-01
  subtotal:                    4000.0
  tax_amount:                  720.0
  total_amount:                4720.0
  currency:                    INR
  payment_method:              CARD

================================================================================
                          FULL JSON OUTPUTS
================================================================================

RAW EXTRACTED:
{
  "merchant": {
    "name": "ABC Hotel",
    ...
  },
  ...
}

NORMALIZED (10-FIELD):
{
  "vendor_name": "ABC Hotel",
  "vendor_normalized": "abc hotel",
  ...
}

================================================================================
                            VALIDATION
================================================================================

INFO: ✓ All 10 required fields present
INFO: ✓ 8/10 fields populated (2 null)

================================================================================
                              SUCCESS
================================================================================

OCR extraction and normalization completed successfully.

The normalized data is ready for:
  - Database persistence
  - Duplicate detection
  - Policy evaluation

```

### Testing with Sample Receipts

To test, you need a receipt image or PDF. You can:

1. **Use a real receipt** — Scan or photograph a real receipt
2. **Download a sample** — Many OCR service providers have test PDFs
3. **Create test data** — Use a receipt-like image/PDF for testing

Place it in the `data/` directory and run the script.

### Troubleshooting

#### "Azure Document Intelligence credentials not configured"
- Check `.env` has `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` and `AZURE_DOCUMENT_INTELLIGENCE_KEY`
- Verify credentials are valid in Azure portal

#### "Receipt file not found"
- Verify the file path is correct (relative to project root)
- Use absolute path if relative path doesn't work

#### "Failed to analyze receipt: ..."
- Check receipt file is valid (not corrupted)
- Try with a different receipt format (PDF vs. JPG)
- Verify Azure Document Intelligence is enabled and accessible

#### "Could not normalize receipt"
- Check normalization rules in `NormalizationService`
- Verify extracted data format is correct
- Check logs for specific field parsing issues

### Integration with Django ORM

To save normalized data to the database:

```python
from receipts.models import Receipt
from scripts.test_ocr_extraction import *  # reuse functions

# Extract and normalize
extracted = service.analyze_receipt(content, content_type)
normalized = NormalizationService.normalize(extracted)

# Save to Receipt model
receipt = Receipt.objects.create(
    id=uuid.uuid4(),
    owner='user@example.com',
    blob_name='receipts/user/uuid/filename.pdf',
    normalized_json=normalized,
    raw_document_intelligence_json=extracted,
    # ... etc
)
```

### Development Notes

The script reuses production code:
- **No mocking** — Uses real Azure Document Intelligence
- **No testing modifications** — Uses production NormalizationService
- **No test databases** — Purely file-based input/output
- **Error handling** — Same exceptions as production

This ensures the script tests actual behavior, not mocked behavior.
