# Real-World Test Action Plan for Ola/Rapido Classification

## Status Summary
✅ **Code changes complete**
- Fixed critical logger scope bug
- Added 3 comprehensive Ola/Rapido tests (all passing)
- All 141 tests pass
- Diagnostic logging points added throughout pipeline

❌ **Real-world issue persists**
- Ola/Rapido screenshots still prompt for manual category selection
- Tests pass but real website behavior incorrect
- Root cause unknown—needs diagnostic logging to identify

## Step-by-Step Real-World Test Plan

### Phase 1: Deploy Diagnostic Logging (Today)

1. **Apply current code changes to staging/production**
   ```bash
   # In the expense-policy-agent directory
   git status  # Verify clean state
   python manage.py test receipts.tests -v 0  # Verify all 141 tests pass
   ```

2. **Verify changes are in place**
   - `receipts/services/receipt_service.py` has module-level logger
   - Diagnostic logging includes `[OCR_EXTRACTION]`, `[CATEGORY_CLASSIFIER_INPUT]`, `[CATEGORY_CLASSIFICATION]`
   - `receipts/tests.py` includes new `OlaScreenshotClassificationTests` class

3. **Enable DEBUG logging for receipt services**
   
   In your Django settings (e.g., `config/settings.py` or via environment):
   ```python
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'handlers': {
           'console': {
               'class': 'logging.StreamHandler',
           },
           'file': {
               'class': 'logging.FileHandler',
               'filename': '/var/log/receipt_debug.log',
               'level': 'DEBUG',
           },
       },
       'loggers': {
           'receipts.services.document_intelligence_service': {
               'level': 'DEBUG',
               'handlers': ['console', 'file'],
           },
           'receipts.services.receipt_service': {
               'level': 'INFO',
               'handlers': ['console', 'file'],
           },
           'receipts.services.category_classifier': {
               'level': 'DEBUG',
               'handlers': ['console', 'file'],
           },
       },
   }
   ```

### Phase 2: Reproduce the Issue (Today/Tomorrow)

1. **Log into the website as a test user**

2. **Upload an Ola receipt screenshot**
   - Use a real Ola email receipt or app screenshot
   - Or use one of these test cases:
     - Ola ride confirmation email screenshot
     - Rapido bike taxi receipt screenshot
     - Any ride-sharing app screenshot

3. **Watch processing flow**
   - Frontend should show "Processing..." 
   - Backend processes receipt
   - API returns classification result
   - Frontend receives and displays result

4. **Document observed behavior**
   - Does it auto-classify as Transport?
   - Does it prompt for manual selection?
   - What category does it show?

### Phase 3: Trace the Logs (Critical)

**IMPORTANT**: This is where we identify the root cause.

1. **After uploading screenshot, check logs immediately**
   
   Look for **4 specific log messages** (in order):

   **Message 1 - OCR Extraction**
   ```
   [OCR_EXTRACTION] Merchant from OCR fallback: Ola
   ```
   OR
   ```
   [OCR_EXTRACTION] Merchant from structured field: Ola
   ```
   OR (Bad)
   ```
   [OCR_EXTRACTION] No merchant found - structured=None, fallback=None
   ```

   **Message 2 - Classifier Input**
   ```
   [CATEGORY_CLASSIFIER_INPUT] Receipt {id}: merchant=Ola, has_amount=True, has_date=True, has_line_items=False
   ```
   Look for: Does `merchant=Ola` or `merchant=None`?

   **Message 3 - Keyword Matching (debug level)**
   ```
   [KEYWORD_CLASSIFIER] Raw merchant: 'Ola' -> Normalized: 'ola'
   ```

   **Message 4 - Final Classification**
   ```
   [CATEGORY_CLASSIFICATION] Receipt {id}: category=Transport: Taxis/Cab/Uber, confidence=0.95, reason=Matched 'ola' keyword in merchant name, will_ask_manual_selection=False
   ```
   Look for: `confidence=X.XX` and `will_ask_manual_selection=True/False`

2. **Report findings**
   
   Create a report showing:
   - Which messages appeared
   - Which messages were missing
   - What values were shown (especially merchant name and confidence)
   - What the website displayed to user

### Phase 4: Root Cause Diagnosis

Based on logs, identify root cause:

| Scenario | Evidence | Root Cause | Fix |
|----------|----------|-----------|-----|
| Message 1 missing/shows "No merchant" | `[OCR_EXTRACTION] No merchant found` | OCR extraction failing for screenshots | Improve OCR fallback patterns, add merchant aliases, handle screenshot preprocessing |
| Message 2 shows `merchant=None` despite Message 1 showing merchant | Messages 1→2 mismatch | Extracted merchant not propagated to classifier | Check receipt_service.py line 127-132 |
| Message 4 shows `confidence=0.50` | Classification output low confidence | Confidence calculation wrong for Ola | Adjust CLASSIFIER_KEYWORD_WEIGHT, check keyword score |
| All messages correct but frontend prompts manual | Logs show correct classification, website wrong | Frontend not reading API response correctly | Check JavaScript in upload.html, API response format |

### Phase 5: Apply Targeted Fix

Once root cause identified, apply minimal fix:

**Example: If OCR fallback not finding "ola"**
```python
# receipts/services/document_intelligence_service.py, line 173-180
# Add better patterns for ride-sharing apps

# Add regex patterns for Ola/Rapido that handle common OCR variations
ride_sharing_patterns = [
    r'\bola\b',           # Standard "ola"
    r'\brapido\b',        # Standard "rapido"
    r'(?:ola|rapido).*ride',  # "ola ride", "rapido ride"
    r'ride.*(?:ola|rapido)',   # "ride ola", "ride rapido"
]

for pattern in ride_sharing_patterns:
    if re.search(pattern, content, re.IGNORECASE):
        # Extract and use...
```

**Example: If confidence calculation wrong**
```python
# config/settings.py
# Adjust weights if needed
CLASSIFIER_KEYWORD_WEIGHT = 0.75  # Increase from 0.6
CLASSIFIER_SEMANTIC_WEIGHT = 0.25  # Decrease from 0.4
CLASSIFIER_CONFIDENCE_THRESHOLD = 0.70  # Lower threshold if justified
```

## Expected Success Criteria

When issue is fixed, real website should show:

1. **Upload Ola/Rapido screenshot** → Processing shows receipt being analyzed
2. **Processing complete** → Auto-classified as "Transport: Taxis/Cab/Uber"
3. **No manual category selection prompt** (confidence >= 0.75)
4. **Logs show complete chain**:
   ```
   [OCR_EXTRACTION] Merchant from OCR fallback: Ola
   [CATEGORY_CLASSIFIER_INPUT] ... merchant=Ola ...
   [CATEGORY_CLASSIFICATION] ... category=Transport: Taxis/Cab/Uber ... confidence=0.9+ ... will_ask_manual_selection=False
   ```

## Files to Monitor

During testing, watch these files for log output:
- Console output if running Django dev server: `python manage.py runserver`
- File log if configured: `/var/log/receipt_debug.log` (or your configured path)
- Django error logs: `logs/django.log` or similar

## Timeline

| Phase | Effort | Duration |
|-------|--------|----------|
| Phase 1: Deploy logging | Low | < 1 hour |
| Phase 2: Reproduce issue | Low | < 30 min |
| Phase 3: Trace logs | Medium | 1-2 hours |
| Phase 4: Diagnose | High | 1-3 hours |
| Phase 5: Fix & verify | Medium | 1-2 hours |
| **Total** | | **4-9 hours** |

## Key Files for Reference

- Diagnostic logging guide: `OLA_RAPIDO_TROUBLESHOOTING_GUIDE.md`
- Changes summary: `SESSION_CHANGES_SUMMARY.md`
- Classifier source: `receipts/services/category_classifier.py`
- OCR extraction: `receipts/services/document_intelligence_service.py`
- Receipt processing: `receipts/services/receipt_service.py`
- Tests (proof classifier works): `receipts/tests.py` → `OlaScreenshotClassificationTests`

## Next Steps

1. **Today**: Deploy code changes, enable DEBUG logging
2. **Tomorrow**: Upload Ola/Rapido screenshots, collect logs
3. **Follow logs**: Trace 4-point sequence to find breakage
4. **Fix & verify**: Apply targeted fix, test again
5. **Commit**: When issue confirmed fixed, commit changes with detailed message

The diagnostic logging is your key to finding the exact issue. Don't skip it—it will save hours of blind guessing.
