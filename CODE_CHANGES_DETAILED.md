# Detailed Code Changes

## File 1: receipts/services/receipt_service.py

### Change 1: Import logging at module level
**Location**: Line 4
```python
# BEFORE:
import uuid
import json
import io
from django.utils import timezone

# AFTER:
import uuid
import json
import io
import logging
from django.utils import timezone
```

### Change 2: Create logger at module level
**Location**: Line 18 (after imports)
```python
# BEFORE:
from receipts.exceptions import BlobUploadError, DocumentExtractionError, CompressionError


class ReceiptService:

# AFTER:
from receipts.exceptions import BlobUploadError, DocumentExtractionError, CompressionError

logger = logging.getLogger(__name__)


class ReceiptService:
```

### Change 3: Add diagnostic logging around classifier
**Location**: Lines 128-144 (in process_receipt method)
```python
# BEFORE:
category_result = self.determine_category(extracted)
receipt.category = category_result.get('category', 'Other')
receipt.category_confidence = category_result.get('confidence', 0.0)
receipt.category_reason = category_result.get('reason', '')

# AFTER:
# Log what gets passed to classifier
merchant_for_classifier = extracted.get('merchant', {}).get('name')
logger.info(f"[CATEGORY_CLASSIFIER_INPUT] Receipt {receipt_id}: "
           f"merchant={merchant_for_classifier}, "
           f"has_amount={extracted.get('amounts', {}).get('total') is not None}, "
           f"has_date={extracted.get('invoice', {}).get('transaction_date') is not None}, "
           f"has_line_items={len(extracted.get('line_items', [])) > 0}")

category_result = self.determine_category(extracted)
receipt.category = category_result.get('category', 'Other')
receipt.category_confidence = category_result.get('confidence', 0.0)
receipt.category_reason = category_result.get('reason', '')

# Log classification result
logger.info(f"[CATEGORY_CLASSIFICATION] Receipt {receipt_id}: "
           f"category={receipt.category}, "
           f"confidence={receipt.category_confidence}, "
           f"reason={receipt.category_reason}, "
           f"will_ask_manual_selection={receipt.category_confidence < 0.75}")
```

### Change 4: Remove redundant logger from exception handler
**Location**: Lines 87-90 (in process_receipt method)
```python
# BEFORE:
except DocumentExtractionError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"OCR extraction failed for receipt {receipt_id}: {str(e)}")

# AFTER:
except DocumentExtractionError as e:
    logger.error(f"OCR extraction failed for receipt {receipt_id}: {str(e)}")
```

### Change 5: Remove redundant logger from another exception handler
**Location**: Lines 319-321 (in _get_processing_copy method)
```python
# BEFORE:
except CompressionError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"File compression failed: {str(e)}. Falling back to original bytes.")

# AFTER:
except CompressionError as e:
    logger.warning(f"File compression failed: {str(e)}. Falling back to original bytes.")
```

---

## File 2: receipts/tests.py

### Addition: New Test Class for Ola/Rapido Scenarios
**Location**: End of file (after line 2775)

Added complete new test class with 3 tests:

```python
class OlaScreenshotClassificationTests(TestCase):
    """
    Tests for real Ola receipt screenshot classification scenario.
    Simulates the exact flow when a user uploads an Ola email receipt screenshot.
    """

    def test_ola_receipt_with_ocr_fallback_classifies_as_transport(self):
        """
        Test that an Ola receipt extracted via OCR fallback classifies as Transport.
        
        Simulates: User uploads Ola email receipt screenshot -> OCR fails on structured field ->
        OCR fallback finds 'Ola' in text -> Classifier recognizes Ola as Transport ->
        Confidence >= 0.75 -> Auto-classify (no manual selection prompt).
        """
        extracted_from_ocr = {
            'merchant': {'name': 'Ola', ...},
            'invoice': {'invoice_number': 'OLA123456', ...},
            'amounts': {'subtotal': 180.00, 'total': 180.00, 'currency': 'INR'},
            'payment': {'method': 'GPAY'},
            'line_items': [{'description': 'Ride Fare', ...}],
            'extraction': {'provider': 'azure_ai_document_intelligence', ...},
        }
        
        result = ReceiptService.determine_category(extracted_from_ocr)
        
        self.assertEqual(result['category'], 'Transport: Taxis/Cab/Uber')
        self.assertGreaterEqual(result['confidence'], 0.75)
        self.assertIn('ola', result['reason'].lower())

    def test_rapido_receipt_with_ocr_fallback_classifies_as_transport(self):
        """Test that a Rapido receipt classifies as Transport: Taxis/Cab/Uber."""
        extracted_from_ocr = {
            'merchant': {'name': 'Rapido', ...},
            'invoice': {'invoice_number': None, ...},
            'amounts': {'subtotal': 120.00, 'total': 120.00, 'currency': 'INR'},
            'payment': {'method': 'Card'},
            'line_items': [],
            'extraction': {'provider': 'azure_ai_document_intelligence', ...},
        }
        
        result = ReceiptService.determine_category(extracted_from_ocr)
        
        self.assertEqual(result['category'], 'Transport: Taxis/Cab/Uber')
        self.assertGreaterEqual(result['confidence'], 0.75)

    def test_ola_receipt_without_merchant_name_asks_for_manual_selection(self):
        """
        Test that when Ola merchant name is NOT extracted (OCR failure),
        receipt gets 'Other' category and prompts manual selection.
        """
        extracted_no_merchant = {
            'merchant': {'name': None, ...},
            'invoice': {'invoice_number': None, ...},
            'amounts': {'subtotal': 150.00, 'total': 150.00, 'currency': 'INR'},
            'payment': {'method': None},
            'line_items': [],
            'extraction': {'provider': 'azure_ai_document_intelligence', ...},
        }
        
        result = ReceiptService.determine_category(extracted_no_merchant)
        
        self.assertEqual(result['category'], 'Other')
        self.assertLess(result['confidence'], 0.75)
```

**Result**: Adds 3 new passing tests → 141 total tests (was 138)

---

## File 3: receipts/services/category_classifier.py

### Change: Diagnostic logging in keyword matching
**Location**: Lines 192 & 236 (already present in _calculate_keyword_score method)

```python
# Line 192:
logger.debug(f"[KEYWORD_CLASSIFIER] Raw merchant: '{raw_merchant}' -> Normalized: '{merchant_name}'")

# Line 236:
logger.debug(f"[KEYWORD_CLASSIFIER] Result: category={best_category}, score={best_score}, reason={best_reason}")
```

**Status**: No changes made (diagnostic logging already in place from previous work)

---

## File 4: receipts/services/document_intelligence_service.py

### Status: No changes needed
The OCR extraction and merchant fallback logic was already correct:
- Lines 386-391: Diagnostic logging already present for merchant extraction
- Lines 173-180: Known merchant patterns for Ola, Rapido, etc. already in place
- Fallback extraction logic working correctly

**Note**: No code changes made to this file in this session. Diagnostic logging was already added in previous work.

---

## Summary of Changes

| File | Lines | Change Type | Impact |
|------|-------|------------|--------|
| receipt_service.py | 4 | Add import | Fix scope |
| receipt_service.py | 18 | Add logger | Enable logging everywhere |
| receipt_service.py | 87-90 | Remove logger def | Clean up redundancy |
| receipt_service.py | 128-144 | Add logging | Diagnostic trace points |
| receipt_service.py | 319-321 | Remove logger def | Clean up redundancy |
| tests.py | +2800 | Add test class | +3 tests for Ola/Rapido |
| **Total** | | | **141 tests passing** |

## What Was NOT Changed

- No model migrations (no database changes)
- No configuration changes (existing settings used)
- No API endpoint changes (existing endpoints work)
- No Teams integration changes (frontend logic separate)
- No business logic changes (only diagnostics added)

## Verification Commands

```bash
# Run all tests
python manage.py test receipts.tests -v 0

# Run only Ola/Rapido tests
python manage.py test receipts.tests.OlaScreenshotClassificationTests -v 2

# Run classifier tests
python manage.py test receipts.tests.HybridCategoryClassifierTests -v 2

# Check for any syntax errors
python manage.py check

# Verify migrations (should be none)
python manage.py showmigrations
```

## Expected Test Results

```
Ran 141 tests in ~55-65 seconds

OK
```

All tests should pass, including:
- 2 failing tests now fixed ✓
- 3 new tests passing ✓
- All 136 original tests still passing ✓
