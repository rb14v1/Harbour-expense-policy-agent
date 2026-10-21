# Exact Duplicate Detection Bug Analysis

## The Problem

Every receipt is being marked as an EXACT_DUPLICATE of itself.

## Root Cause

**File:** `receipts/services/duplicate_service.py`  
**Method:** `find_exact_duplicate()` (lines 17-22)  
**Issue:** The query finds the receipt being checked and compares it to itself

### Current Query Logic

```python
@staticmethod
def find_exact_duplicate(sha256_hash: str, user: str = None):
    query = Receipt.objects.filter(sha256_hash=sha256_hash)
    if user:
        query = query.filter(owner=user)
    query = query.exclude(status='FAILED')  # ← Only excludes FAILED
    return query.first()
```

**Database Table:** `receipts_receipt`  
**Columns Queried:** `sha256_hash`, `owner`, `status`

### Execution Flow (Track A Upload)

1. **ReceiptService.create_and_upload_receipt()** (line 47 calls find_exact_duplicate)
   - Line 30-39: Create Receipt with `sha256_hash=""` and `status="UPLOADED"`
   - Line 42: Compute SHA-256
   - Line 43: Set `receipt.sha256_hash = computed_hash`
   - Line 44-45: Set `status="HASHING"` and save to database

2. **find_exact_duplicate(sha256_hash, owner)** is called
   - Query searches for: `sha256_hash = computed_hash AND owner = owner AND status != FAILED`
   - **FINDS:** The receipt that was just created (with status='HASHING')
   - **RESULT:** Marks receipt as duplicate of itself

## Debug Evidence

### Test 1: First Upload of test_receipt.pdf

```
New SHA-256: 213679f09e34424254a6e7b28e74d2c656dfbe4076f23c7c01c9e5ee6ba90d4a
Owner: test-user

Existing receipts being checked: (1 found)
- Receipt ID: 458fefaa-7e90-4ffe-b954-8479d3b55299  ← SAME RECEIPT BEING UPLOADED
  SHA-256: 213679f09e34424254a6e7b28e74d2c656dfbe4076f23c7c01c9e5ee6ba90d4a  ← SAME HASH
  Owner: test-user
  Status: HASHING  ← CURRENT STATUS (SET 5 LINES EARLIER)
  Comparison: MATCH

Final result:
EXACT DUPLICATE: YES
Duplicate receipt ID: 458fefaa-7e90-4ffe-b954-8479d3b55299
```

**Result:** First upload marked as EXACT_DUPLICATE ❌ (Should be QUEUED_FOR_OCR)

### Test 2: Different File (test_receipt_unique.pdf)

```
New SHA-256: c81220fb9ef2d5f6b5621a9c2e788d66fa9feba458b1761a7cc143c1b8c11cb2
Owner: test-user

Existing receipts being checked: (1 found)
- Receipt ID: dc3608a6-61b0-4582-bbb1-7bd422d80ecd  ← NEW RECEIPT
  SHA-256: c81220fb9ef2d5f6b5621a9c2e788d66fa9feba458b1761a7cc143c1b8c11cb2  ← DIFFERENT HASH, SAME RECEIPT
  Owner: test-user
  Status: HASHING
  Comparison: MATCH

Final result:
EXACT DUPLICATE: YES
```

**Result:** Different file marked as EXACT_DUPLICATE ❌ (Should be QUEUED_FOR_OCR)

### Test 3: Same File Again

```
New SHA-256: 213679f09e34424254a6e7b28e74d2c656dfbe4076f23c7c01c9e5ee6ba90d4a
Owner: test-user

Existing receipts being checked: (2 found)
- Receipt ID: 94c4ccdc-f9fd-45ac-8a24-eb8207e6ebc7  ← CURRENT RECEIPT BEING CHECKED
  SHA-256: 213679f09e34424254a6e7b28e74d2c656dfbe4076f23c7c01c9e5ee6ba90d4a
  Owner: test-user
  Status: HASHING
  Comparison: MATCH
- Receipt ID: 458fefaa-7e90-4ffe-b954-8479d3b55299  ← FIRST UPLOAD FROM TEST 1
  SHA-256: 213679f09e34424254a6e7b28e74d2c656dfbe4076f23c7c01c9e5ee6ba90d4a
  Owner: test-user
  Status: EXACT_DUPLICATE
  Comparison: MATCH

Final result:
EXACT DUPLICATE: YES
Duplicate receipt ID: 94c4ccdc-f9fd-45ac-8a24-eb8207e6ebc7  ← POINTS TO ITSELF
```

**Result:** Second upload of same file marked as EXACT_DUPLICATE ✅ (Correct by accident - it's matching itself)

---

## The Fix

### Option 1: Exclude HASHING Status (Simplest)

Add `status='HASHING'` to the exclusion list:

```python
@staticmethod
def find_exact_duplicate(sha256_hash: str, user: str = None):
    query = Receipt.objects.filter(sha256_hash=sha256_hash)
    if user:
        query = query.filter(owner=user)
    query = query.exclude(status__in=['FAILED', 'HASHING'])  # ← Exclude HASHING
    return query.first()
```

**Why this works:**
- HASHING is only set for the receipt being checked (lines 44-45 of receipt_service.py)
- Existing receipts that completed processing will have status UNIQUE, APPROVED, EXACT_DUPLICATE, SEMANTIC_DUPLICATE, etc.
- By excluding HASHING, we skip the receipt being checked and only look at truly existing receipts

### Option 2: Only Check Finalized Receipts

```python
query = query.filter(status__in=['UNIQUE', 'APPROVED', 'EXACT_DUPLICATE', 'SEMANTIC_DUPLICATE', 'REJECTED'])
```

### Option 3: Exclude Current Receipt by ID (requires passing receipt ID)

Would need to modify the method signature to accept the current receipt ID and exclude it:

```python
query = query.exclude(id=current_receipt_id)
```

---

## Recommendation

**Use Option 1** (Exclude HASHING status) because:
- Minimal change
- No signature changes needed
- Clear intent: don't compare a receipt to itself while it's being processed
- Consistent with the receipt lifecycle (HASHING → QUEUED_FOR_OCR → ... → UNIQUE/APPROVED/REJECTED)

## Impact Assessment

- **Frontend:** No changes needed - frontend correctly calls the API
- **Backend API:** Will now return correct status (QUEUED_FOR_OCR instead of EXACT_DUPLICATE for new files)
- **Tests:** Will need to verify duplicate detection works correctly
- **Database:** No schema changes needed
