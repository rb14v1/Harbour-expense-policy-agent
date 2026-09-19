# Receipt Upload Error Handling - Complete Flow Analysis

## Files Involved in Upload Flow

### Frontend Layer
- **receipts/templates/receipts/upload.html** (Lines 409-676)
  - `uploadReceipt()` - Line 422
  - `pollReceiptStatus()` - Line 479
  - `displayReceiptResult()` - Line 577
  - Error display - Line 471: Generic "Upload failed" message

### Backend Layer
- **receipts/views.py** - `upload()` action (Lines 79-119)
  - Catches serializer exceptions
  - Returns 400 for validation errors
  
- **receipts/serializers.py** - `ReceiptUploadSerializer` (Lines 84-96)
  - Calls `ReceiptService.create_and_upload_receipt()`
  
- **receipts/services/receipt_service.py**
  - `create_and_upload_receipt()` (Lines 24-64)
  - `process_receipt()` (Lines 66-150+)
  
- **receipts/services/file_validation_service.py** (Lines 1-165)
  - `FileValidationService.validate()` (Lines 22-50)
  - `_validate_pdf()` (Lines 53-76)
  - `_validate_image()` (Lines 79-119)
  - `_check_blank_image()` (Lines 122-158)
  
- **receipts/services/blob_service.py** - Azure Blob upload/download

- **receipts/services/document_intelligence_service.py** - OCR service
  - `analyze_receipt()` (Lines 20-43)
  
- **receipts/exceptions.py** - Exception classes

- **config/settings.py** - Configuration values

---

## Current File-Size Limits

**Setting: `MAX_RECEIPT_UPLOAD_MB`** (config/settings.py, Line 89)
- Default: 20 MB
- Environment variable: `MAX_RECEIPT_UPLOAD_MB`

**Frontend check** (upload.html, Line 430):
```javascript
const maxSizeBytes = 20 * 1024 * 1024;
```

**Backend check** (file_validation_service.py, Lines 30-34):
```python
file_size_mb = file_obj.size / (1024 * 1024)
max_size_mb = settings.MAX_RECEIPT_UPLOAD_MB
if file_size_mb > max_size_mb:
    raise ReceiptTooLargeError(...)
```

### Where "5 MB Behavior" Comes From
❌ **NOT in project code** - No 5 MB limit exists in application
⚠️ **Django framework default**: `FILE_UPLOAD_MAX_MEMORY_SIZE` = 2.5 MB
⚠️ **Django framework default**: `DATA_UPLOAD_MAX_MEMORY_SIZE` = 2.5 MB
- Combined: ~5 MB before Django rejects upload with HTTP 413

### Where "10 MB Behavior" Comes From
❌ **NOT in project code** - No 10 MB limit exists in application
⚠️ **Likely source**: Files > 10 MB hit Django's memory limits
⚠️ **Result**: HTTP 413 Payload Too Large (not our error handling)
⚠️ **Frontend sees**: `!response.ok` → generic "Upload failed" message

---

## Allowed File Types

**Extensions** (file_validation_service.py, Line 14):
```python
{'.pdf', '.jpg', '.jpeg', '.png'}
```

**MIME types** (file_validation_service.py, Lines 8-12):
- `application/pdf` → `.pdf`
- `image/jpeg` → `.jpg`
- `image/png` → `.png`

**Validation order:**
1. Check extension
2. Check file MIME type
3. Check file header bytes
4. For PDF: Validate structure via PdfReader
5. For images: Validate via PIL.Image.open()
6. For images: Check if blank (>95% white)

---

## Blank Document Detection

### Current Behavior

**For Images** (file_validation_service.py, Lines 122-158):
✅ **Detects:**
- Image with 0x0 dimensions
- Image < 10x10 pixels  
- Image > 95% white pixels

✅ **Raises**: `UnsupportedFileTypeError` with specific reason

**For PDFs** (file_validation_service.py, Lines 64-67):
❌ **Only checks**: PDF has at least 1 page
❌ **Does NOT check**: PDF text is readable
⚠️ **Result**: Empty/unreadable PDFs pass upload validation
⚠️ **Detected later**: After Azure OCR processing (wastes API call)

**After OCR** (receipt_service.py, Lines 85-90):
```python
if self._is_ocr_result_blank(extracted):
    receipt.status = "FAILED"
    duplicate_reason = "Receipt appears to be blank..."
    processing_message = "The uploaded receipt appears to be blank..."
```

---

## OCR Failure Handling

**Current flow:**

1. **document_intelligence_service.py** (Lines 20-43):
   - Catches all exceptions
   - Raises `DocumentExtractionError` with message
   
2. **receipt_service.py** `process_receipt()`:
   ❌ **NO explicit error handling** for OCR failures
   ❌ Exceptions bubble up to task worker
   
3. **Frontend** (upload.html, Line 492):
   - Polls for final status: `['APPROVED', 'REJECTED', 'EXACT_DUPLICATE', 'SEMANTIC_DUPLICATE', 'FAILED']`
   - ✅ Handles FAILED status
   - ✅ Displays with ❌ badge

**Problem**: User sees "FAILED" status but no specific OCR error message

---

## HTTP Status Codes & JSON Responses

### File Too Large (>20 MB)
- **Status**: HTTP 400 Bad Request
- **Error**: `ReceiptTooLargeError`
- **Response**: `{"errors": {"file": ["File too large: X.XXmb. Maximum: 20MB"]}}`
- **Frontend shows**: "Upload failed. Please try again."
- **User sees**: Generic message, loses context

### File Size > Django limit (~5-10 MB)
- **Status**: HTTP 413 Payload Too Large (Django framework error)
- **Response**: Django's default error page HTML
- **Frontend shows**: "Upload failed. Please try again."
- **User sees**: No indication it's a size issue

### Blank Image
- **Status**: HTTP 400 Bad Request
- **Error**: `UnsupportedFileTypeError("Image appears to be blank or mostly white (98.5% white pixels).")`
- **Response**: `{"errors": {"file": [message]}}`
- **Frontend shows**: "Upload failed. Please try again."
- **User sees**: No info about blank image

### Unsupported File Type
- **Status**: HTTP 400 Bad Request
- **Error**: `UnsupportedFileTypeError("Unsupported file extension: .txt. Allowed: {'.pdf', '.jpg', '.jpeg', '.png'}")`
- **Response**: `{"errors": {"file": [message]}}`
- **Frontend shows**: "Upload failed. Please try again."

### Empty File
- **Status**: HTTP 400 Bad Request
- **Error**: `UnsupportedFileTypeError("File is empty.")`
- **Response**: `{"errors": {"file": [message]}}`
- **Frontend shows**: "Upload failed. Please try again."

### OCR Failure (After upload)
- **Processing**: Asynchronous in background worker
- **Receipt status**: Set to `FAILED`
- **Message**: In `duplicate_reason` field
- **Response**: `GET /receipts/{id}/` returns `{"status": "FAILED", "duplicate_reason": "..."}`
- **Frontend shows**: Status card with ❌ FAILED
- **User sees**: No specific error about OCR

---

## Why Frontend Loses Specific Backend Error

**Location**: upload.html, Lines 459-472

**Code**:
```javascript
if (response.ok) {
    const data = await response.json();
    // ... process response
} else {
    removeLastMessage();
    appendMessage('assistant', 'Upload failed. Please try again.');
}
```

**Problems**:

1. **Generic fallback only**: Line 471 catches ALL non-2xx responses
2. **No error parsing**: `response.json()` not called on error
3. **Response body ignored**: Error details in `{"errors": {"file": [message]}}`
4. **No distinction** between different failure types:
   - File too large
   - Unsupported type
   - Empty/blank file
   - Blob upload failure
   - Azure credentials missing
   - Network error

5. **All become**: "Upload failed. Please try again."

**How it should work**:
1. Check `!response.ok`
2. Call `response.json()` to get error body
3. Extract message from `{"errors": {"file": [...]}}` structure
4. Display specific message to user
5. Fallback to generic only for truly unexpected errors

---

## Current Error Messages by Location

| Error | Location | Message |
|-------|----------|---------|
| File > 20 MB | file_validation_service.py:33 | "File too large: X.XXmb. Maximum: 20MB" |
| Empty file | file_validation_service.py:38 | "File is empty." |
| Bad extension | file_validation_service.py:26 | "Unsupported file extension: X. Allowed: {set}" |
| Invalid PDF header | file_validation_service.py:55 | "File does not appear to be a valid PDF. PDF files must start with %PDF header." |
| PDF zero pages | file_validation_service.py:65 | "PDF contains zero pages. Cannot process empty PDF." |
| Corrupted PDF | file_validation_service.py:74 | "PDF is corrupted or malformed: {error}" |
| Blank image | file_validation_service.py:149 | "Image appears to be blank or mostly white (X.X% white pixels)." |
| Image too small | file_validation_service.py:107 | "Image is too small (WxH). Minimum size is 10x10 pixels." |
| Invalid JPEG | file_validation_service.py:81 | "File does not appear to be a valid JPEG image..." |
| Invalid PNG | file_validation_service.py:86 | "File does not appear to be a valid PNG image..." |
| Corrupted image | file_validation_service.py:117 | "Image is corrupted or invalid: {error}" |
| Blank receipt after OCR | receipt_service.py:87 | "Receipt appears to be blank. No meaningful content was extracted." |
| Invalid receipt | receipt_service.py:94 | "Document does not appear to be a receipt. Required receipt information is missing." |
| Blob upload error | receipt_service.py:59 | "Blob upload failed: {error}" |
| OCR error | document_intelligence_service.py:43 | "Failed to analyze receipt: {error}" |

All these messages are **lost** at the frontend because of generic error handling.

---

## Unreadable Document Detection

**Current status**: ❌ NO detection

**What exists**:
- Blank image detection (>95% white)
- Blank PDF detection (0 pages)
- Blank receipt after OCR (no extracted fields)

**What's missing**:
- Blurry image detection
- Unreadable text detection
- Low-confidence OCR detection

**How to detect** (for future implementation):
- Extract average confidence from OCR results
- If `avg_confidence < 30%`: Document likely unreadable
- Need to set confidence threshold in configuration

---

## Safest Minimal Implementation Plan

### PHASE 1: Error Message Propagation (SAFE - NO BREAKING CHANGES)

**Frontend change only** (upload.html, Line 469):
- ✅ Parse error response JSON
- ✅ Extract message from `{"errors": {"file": [...]}}` structure
- ✅ Display specific error to user
- ✅ Fallback to generic if structure unexpected
- ❌ NO backend changes
- ❌ NO model changes

**Impact**: User sees "File too large: 15.2MB" instead of "Upload failed"
**Risk**: Zero - only affects error display
**Cost**: ~10 lines of JavaScript

### PHASE 2: Django Memory Limit Configuration (SAFE - CONFIG ONLY)

**config/settings.py changes**:
- ✅ ADD: `FILE_UPLOAD_MAX_MEMORY_SIZE` setting
- ✅ ADD: `DATA_UPLOAD_MAX_MEMORY_SIZE` setting
- ✅ Make configurable via environment variables
- ❌ NO code changes
- ❌ NO model changes

**Impact**: Larger files accepted without 413 error
**Risk**: Zero - just exposes framework settings
**Cost**: ~5 lines of configuration

### PHASE 3: Early Blank PDF Detection (SAFE - NON-BLOCKING)

**receipt_service.py changes**:
- ✅ ADD: Quick PDF text extraction before Blob upload
- ✅ If PDF has <10 chars: raise `UnsupportedFileTypeError`
- ✅ Catches blank PDFs before Azure API call
- ❌ Existing PDFs unaffected
- ❌ Only new validations fail at upload
- ✅ Users can retry with better file

**Impact**: Saves Azure API call for obviously blank PDFs
**Risk**: Very low - only rejects PDF with zero readable text
**Cost**: ~15 lines (use pypdf text extraction)

### PHASE 4: OCR Failure Handling (CAREFUL - NEEDS TESTING)

**receipt_service.py changes**:
- ✅ WRAP: `process_receipt()` with try/catch
- ✅ CATCH: `DocumentExtractionError`
- ✅ SET: `receipt.status = "FAILED"`
- ✅ SET: `receipt.duplicate_reason = specific error`
- ✅ SET: `receipt.processing_message = user-friendly message`
- ✅ LOG: full error for debugging
- ✅ RETURN: receipt (don't re-raise)

**Impact**: User sees "OCR failed: low confidence" instead of generic
**Risk**: Low - just handles exception already possible
**Cost**: ~20 lines (try/catch wrapper)

### PHASE 5: Unreadable Document Detection (FUTURE - OPTIONAL)

- Requires setting confidence thresholds
- Future enhancement only
- Can be added after Phases 1-4 proven stable

---

## Implementation Safety Matrix

| Change | Risk | Breaking? | Tests needed? |
|--------|------|-----------|---------------|
| Error message propagation (FE) | None | No | No |
| Django memory limit config | None | No | No |
| PDF blank detection (early) | Low | No | Yes (3 cases) |
| OCR failure handling | Low | No | Yes (3 cases) |
| Unreadable doc detection | Medium | Maybe | Yes (5 cases) |

Each phase can be implemented independently in order without breaking existing flow.
