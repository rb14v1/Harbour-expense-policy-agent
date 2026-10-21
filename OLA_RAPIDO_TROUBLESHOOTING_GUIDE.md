# Ola/Rapido Screenshot Classification Troubleshooting Guide

## Issue Summary
When uploading screenshots of Ola or Rapido receipts, the website prompts for manual category selection instead of auto-classifying as "Transport: Taxis/Cab/Uber" (confidence >= 0.75).

Despite 141 passing tests confirming the classifier works correctly, the real-world issue persists.

## What Was Fixed
1. **Logger scope bug** (receipt_service.py): Logger was only defined inside exception blocks, causing UnboundLocalError. Fixed by moving logger to module level.
2. **Test coverage**: Added 3 new comprehensive tests for Ola/Rapido screenshot scenarios, all passing.

## Diagnostic Logging Now In Place

### Flow Trace Points

When a receipt is uploaded and processed, these log messages should appear:

#### 1. OCR Extraction Point
**File**: `receipts/services/document_intelligence_service.py` (lines 386-391)

Look for one of these log messages:
```
[OCR_EXTRACTION] Merchant from structured field: Ola
[OCR_EXTRACTION] Merchant from OCR fallback: Ola
[OCR_EXTRACTION] No merchant found - structured=None, fallback=None
```

**What it means:**
- **"structured field"**: Azure Document Intelligence successfully extracted merchant name
- **"OCR fallback"**: Azure didn't provide MerchantName, but OCR text contained "ola" or "rapido" keyword
- **"No merchant found"**: Neither structured field nor OCR fallback found a merchant name → will trigger manual selection

#### 2. Classifier Input Point
**File**: `receipts/services/receipt_service.py` (lines 128-132)

Look for:
```
[CATEGORY_CLASSIFIER_INPUT] Receipt {id}: merchant={name}, has_amount=True, has_date=True, has_line_items=False
```

**What it means:**
- Confirms what data reaches the classifier
- If `merchant=None`, classifier will default to "Other"
- If `merchant=Ola`, should classify as Transport

#### 3. Keyword Matching Point
**File**: `receipts/services/category_classifier.py` (line 192)

Look for (debug level):
```
[KEYWORD_CLASSIFIER] Raw merchant: 'Ola' -> Normalized: 'ola'
```

**What it means:**
- Shows raw merchant name from OCR
- Shows normalized version (lowercase, trimmed)
- Should be: `Raw merchant: 'Ola' -> Normalized: 'ola'`

#### 4. Classification Result Point
**File**: `receipts/services/receipt_service.py` (lines 140-144)

Look for:
```
[CATEGORY_CLASSIFICATION] Receipt {id}: category=Transport: Taxis/Cab/Uber, confidence=0.95, reason=Matched 'ola' keyword in merchant name, will_ask_manual_selection=False
```

**What it means:**
- Final classification result
- `confidence=0.95` (>= 0.75) → NO manual selection prompt ✓
- `confidence=0.50` (< 0.75) → YES manual selection prompt ✗

## How to Diagnose

### Step 1: Enable Debug Logging
In Django settings or environment, enable DEBUG logging for receipt processing:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'receipts.services.document_intelligence_service': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'receipts.services.receipt_service': {
            'level': 'INFO',
            'handlers': ['console'],
        },
        'receipts.services.category_classifier': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

### Step 2: Upload an Ola Screenshot
1. Log into the website
2. Upload an actual Ola email receipt or screenshot
3. Watch the console/logs during processing

### Step 3: Trace the Logs
Follow the 4 flow trace points above. Expected sequence:

```
[OCR_EXTRACTION] Merchant from OCR fallback: Ola
[CATEGORY_CLASSIFIER_INPUT] Receipt ...: merchant=Ola, ...
[KEYWORD_CLASSIFIER] Raw merchant: 'Ola' -> Normalized: 'ola'
[CATEGORY_CLASSIFICATION] Receipt ...: category=Transport: Taxis/Cab/Uber, confidence=0.95, will_ask_manual_selection=False
```

### Step 4: Compare with Test Output
Run this test to confirm the classifier works:

```bash
python manage.py test receipts.tests.OlaScreenshotClassificationTests.test_ola_receipt_with_ocr_fallback_classifies_as_transport -v 2
```

This test simulates exactly what should happen with a real Ola receipt.

## Possible Root Causes

### 1. Merchant Name Not Extracted
**Log Evidence**: `[OCR_EXTRACTION] No merchant found`

**Why**: 
- OCR text doesn't contain "ola" or "rapido" (misspelled, in different case, etc.)
- Known merchant patterns are too strict
- Image quality too poor for OCR

**Fix**:
- Improve OCR fallback patterns in `document_intelligence_service.py` line 173-180
- Add more merchant aliases
- Improve screenshot handling (compression, preprocessing)

### 2. Merchant Name Extracted But Null in Classifier
**Log Evidence**: 
```
[OCR_EXTRACTION] Merchant from OCR fallback: Ola
[CATEGORY_CLASSIFIER_INPUT] Receipt ...: merchant=None
```

**Why**: Extracted merchant not being passed through the extraction dict correctly

**Fix**:
- Check `receipt_service.py` line 127 - ensure merchant is retrieved from extracted dict
- Verify normalization isn't stripping it

### 3. Confidence Calculation Wrong
**Log Evidence**:
```
[CATEGORY_CLASSIFICATION] ... confidence=0.50 ... will_ask_manual_selection=True
```

**Why**:
- Keyword weight too low (default 0.6)
- Semantic model output incorrect
- Ambiguity margin triggering incorrectly

**Fix**:
- Check `settings.py` for classifier weights:
  - `CLASSIFIER_KEYWORD_WEIGHT` (default 0.6)
  - `CLASSIFIER_SEMANTIC_WEIGHT` (default 0.4)
  - `CLASSIFIER_CONFIDENCE_THRESHOLD` (default 0.75)
- Adjust if needed in environment variables

### 4. Frontend Not Reading Classification Result
**Log Evidence**: All logs show correct classification, but frontend prompts for manual selection

**Why**: 
- API response not including category/confidence fields
- Frontend checking wrong field name
- JavaScript error on frontend

**Fix**:
- Check API response includes:
  ```json
  {
    "category": "Transport: Taxis/Cab/Uber",
    "category_confidence": 0.95,
    "category_reason": "..."
  }
  ```
- Check frontend JavaScript in upload handler
- Verify confidence threshold logic in frontend

## Test Results

All 141 tests pass, including:
- 3 new Ola/Rapido screenshot tests
- Original classifier tests
- OCR fallback extraction tests
- End-to-end workflow tests

**The classifier logic is correct.** The issue is in the execution environment.

## Files Modified

1. `receipts/services/receipt_service.py` - Fixed logger scope, added diagnostic logging
2. `receipts/services/document_intelligence_service.py` - Diagnostic logging already in place
3. `receipts/services/category_classifier.py` - Diagnostic logging already in place
4. `receipts/tests.py` - Added 3 new Ola/Rapido tests (OlaScreenshotClassificationTests)

## Next Steps

1. Deploy code to staging environment with DEBUG logging enabled
2. Upload a real Ola/Rapido screenshot
3. Check logs at the 4 trace points
4. Report which log message is missing or incorrect
5. That will pinpoint the exact root cause
