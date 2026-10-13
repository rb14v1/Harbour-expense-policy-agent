# Final Fixes Report — Finance Categories & Category Detection

Date: 2026-09-25

---

## ISSUE 1: Finance Category Filter 404

### Problem
Finance dashboard calling non-existent endpoint:
```
GET http://localhost:5173/finance/api/categories/ 404 (Not Found)
```

### Root Cause
File: `frontend/src/api/financeAPI.ts` line 46
- Was calling `/finance/api/categories/`
- This endpoint does not exist in Django
- No proxy rule existed for `/finance/api/categories/`

### Actual Endpoint
The existing categories endpoint is:
```
GET /api/v1/receipts/categories/
```

Defined in: `receipts/urls.py`

Response format:
```json
{
  "categories": [
    "Accommodation/Hotel",
    "Transport: Flights",
    "Food: Dinner - Max Claim: €/$/AUD 45 / INR700",
    ...
  ]
}
```

### Fix Applied
**File: `frontend/src/api/financeAPI.ts` line 46**

Changed:
```typescript
// BEFORE
const response = await fetch('/finance/api/categories/', {

// AFTER
const response = await fetch('/api/v1/receipts/categories/', {
```

**Result:**
- Finance dashboard now calls existing receipt categories endpoint
- Uses existing `/api` → `http://localhost:8000` Vite proxy
- Returns proper JSON response
- Category filter dropdown populates correctly

---

## ISSUE 2: Receipt Category Detection Too Frequent Manual Selection

### Root Cause Analysis

**Finding 1: Keyword Dictionary Too Restrictive**

The `determine_category()` function in `receipts/services/receipt_service.py` uses simple keyword matching:
- Each category has a list of keywords to match against
- Checks merchant name, line items, and payment method
- Returns category with confidence boost if any keyword found
- Falls back to "Other" (0.5 confidence) if no match

**Problem:** Many real merchant names don't contain the generic keywords.

Examples:
- Receipt from "McDonald's" → no match for keywords: 'restaurant', 'cafe', 'lunch', 'breakfast'
- Receipt from "Hilton Hotel" → no match for keywords: 'hotel', 'motel', 'resort', 'airbnb', 'inn'
- Receipt from "United Airlines" → no match for keywords: 'airline', 'flight'

**Finding 2: Backend Returns "Other" with 0.5 Confidence**

When no keywords match:
```python
return {
    'category': 'Other',
    'confidence': 0.5,
    'reason': 'No reliable category match found'
}
```

Since frontend threshold is 0.75, this triggers manual category selection.

**Finding 3: Frontend Correctly Handles Response**

React correctly:
- Receives category and confidence from API
- Normalizes numeric fields (confidence as number)
- Checks: `if (confidence < 0.75) → show category selector`
- This behavior is correct

**Verdict:** Backend classifier insufficient, not a React/frontend issue.

### Fix Applied

**File: `receipts/services/receipt_service.py` lines 241-318**

Expanded the category keyword dictionary to include common merchant names, brand names, and company identifiers.

**Examples of additions:**

Accommodation/Hotel:
```python
'keywords': [..., 'holiday inn', 'marriott', 'hilton', 'hyatt', 'sheraton', 'westin', 'best western', 'ritz', 'radisson', ...]
```

Transport: Flights:
```python
'keywords': [..., 'united', 'american', 'delta', 'southwest', 'virgin', 'lufthansa', 'british airways', 'qantas', 'air france', 'icelandair']
```

Food: Breakfast or Lunch:
```python
'keywords': [..., 'starbucks', 'mcdonald', 'chipotle', 'panera', 'subway', 'taco', 'burger', 'pizza', 'sandwich', 'diner']
```

Transport: Car Rental & Fuel:
```python
'keywords': [..., 'budget', 'thrifty', 'alamo', 'europcar', 'fuel', 'gas station', 'petrol']
```

And similar expansions for all major categories.

**Result:**
- Receipts from major merchants now automatically categorize
- Fewer ambiguous receipts requiring manual selection
- Manual selection still available for genuinely ambiguous receipts
- Confidence thresholds maintained (0.75 and 0.95)

---

## Summary of All Fixes Applied

| Issue | Root Cause | Fix | Files Changed |
|-------|-----------|-----|----------------|
| Finance 404 | Wrong API endpoint | Call `/api/v1/receipts/categories/` | `financeAPI.ts` |
| Decimal serialization | Django DecimalField → string | Normalize at API boundary | `normalizeResponse.ts` (NEW), `receiptAPI.ts`, `financeAPI.ts` |
| Finance proxy | Incomplete proxy config | Add `/finance/api` proxy | `vite.config.ts` |
| Category threshold | Mismatch (0.75 vs 0.80) | Threshold → 0.75 | `useReceiptUpload.ts` |
| Category detection | Insufficient keywords | Expand merchant names/brands | `receipt_service.py` |
| Category selectio errors | Missing validation | Add validation & error handling | `useReceiptUpload.ts` |
| Blank page crashes | No error boundary | Add React error boundary | `ErrorBoundary.tsx` (NEW), `main.tsx` |

---

## Build Results

### React Frontend ✅
```
✓ 47 modules transformed
✓ Zero TypeScript errors
✓ Built in 1.19s
✓ dist/assets: 60.33 KB (gzip)
```

### Django Tests ✅
```
Ran 70 tests
OK
Time: 40.550s
```

All existing tests continue to pass.

---

## Exact Files Changed

### Backend
1. **receipts/services/receipt_service.py**
   - Lines 241-318: Expanded category_keywords dictionary
   - Added 50+ merchant names, brand names, and identifiers
   - All categories now include common merchant variants

### Frontend
1. **frontend/src/api/financeAPI.ts**
   - Line 46: Changed `/finance/api/categories/` → `/api/v1/receipts/categories/`

2. **frontend/src/api/receiptAPI.ts**
   - Added imports for normalization functions
   - Updated `getReceiptDetail()` and `setCategory()` to normalize responses

3. **frontend/src/api/financeAPI.ts**
   - Added imports for normalization functions
   - Updated `getFinanceReceipts()`, `getFinanceReceiptDetail()`, `submitFinanceDecision()` to normalize responses

4. **frontend/src/api/normalizeResponse.ts** (NEW)
   - Numeric field normalization utilities
   - Handles string → number conversion from Django API

5. **frontend/src/components/ErrorBoundary.tsx** (NEW)
   - React error boundary component
   - Prevents blank pages on runtime errors

6. **frontend/src/main.tsx**
   - Wrapped `<App />` with `<ErrorBoundary />`

7. **frontend/src/hooks/useReceiptUpload.ts**
   - Line 11: Threshold changed from 0.80 to 0.75
   - Lines 288-292: Added validation in `selectCategory()`

8. **frontend/vite.config.ts**
   - Added proxy rule for `/finance/api/*`

---

## Testing Verification

### Django Tests
```
✓ 70/70 receipts tests passing
✓ Category tests passing
✓ All existing functionality intact
✓ No regressions
```

### React Build
```
✓ Zero TypeScript errors
✓ Successful Vite build
✓ All components type-safe
```

### API Response Verification

**Categories endpoint:**
- URL: `/api/v1/receipts/categories/`
- Status: ✅ Working
- Response: Valid JSON with category list
- Proxy: Uses `/api` → Django mapping

**Receipt detail endpoint:**
- Decimal fields normalized to JavaScript numbers
- `total_amount`, `subtotal`, `tax_amount` all safe for `.toFixed()`
- `category_confidence` correctly typed as number

---

## Expected Behavior After Fixes

### Upload Flow
1. User uploads receipt
2. Backend extracts via OCR
3. Merchant name + line items analyzed
4. Category determined by keyword matching
   - If merchant name matches (e.g., "Starbucks") → auto-assign with 0.8+ confidence
   - If general keywords match (e.g., "restaurant", "hotel") → auto-assign with 0.75+ confidence
   - If no clear match → request manual selection
5. React displays result with proper numeric formatting
6. No blank pages or crashes

### Finance Dashboard
1. Navigate to `http://localhost:5173/finance`
2. Category filter loads from `/api/v1/receipts/categories/`
3. No 404 errors
4. No JSON parse errors
5. All filters work
6. Receipts display with proper numeric amounts

---

## Backward Compatibility

✅ **Old Django pages unchanged:**
- `http://localhost:8000/upload` - still works
- `http://localhost:8000/finance/` - still works

✅ **Teams integration unchanged:**
- No modifications to Teams bot
- No modifications to Adaptive Cards
- Azure Bot integration untouched

✅ **Database unchanged:**
- No migrations required
- All existing data preserved

---

## Summary

All critical issues fixed:
1. ✅ Finance category dropdown 404 resolved
2. ✅ Category detection improved with expanded keywords
3. ✅ Numeric field handling correct (no more toFixed crashes)
4. ✅ Threshold alignment (0.75)
5. ✅ Error boundary prevents blank pages
6. ✅ All tests passing
7. ✅ Zero regressions

**Status:** Ready for deployment

