# ROOT CAUSE ANALYSIS

## ISSUE 1: Generic Rejection Reasons

### Root Cause
**File**: `receipts/serializers.py` lines 54-73 (ReceiptStatusSerializer.get_message())

The ReceiptStatusSerializer has a hardcoded message dictionary that returns generic messages regardless of the actual rejection reason:

```python
'REJECTED': 'Receipt rejected by policy.',  # ← Generic, ignores actual reason
```

Even though the actual rejection reason is properly stored in the receipt's `processing_message` field (set in receipt_service.py lines 199-200), the serializer ignores it and returns a generic string.

**Other affected statuses**:
- `OCR_FAILED` uses `obj.duplicate_reason` (line 61) which is wrong - it should use processing_message

### Current Flow
1. ✅ Receipt validation/policy checks set detailed `processing_message` (receipt_service.py:199-200)
2. ✅ Example: "Receipt is older than 35 days (45 days old)."
3. ❌ Serializer overrides with generic: "Receipt rejected by policy."
4. ❌ User sees generic message instead of real reason

### Impact
- Users don't know why their receipt was rejected
- Finance team reviewing receipts sees generic messages
- No guidance for users to fix/resubmit

---

## ISSUE 2: Incorrect Category Detection

### Root Cause
**File**: `receipts/services/receipt_service.py` lines 214-349 (determine_category())

The category classification algorithm has three problems:

**Problem 1: No Priority Order**
- Keywords are checked in iteration order, not by specificity
- Generic keywords like "booking" match before more specific ones like "uber"
- If OCR text contains "booking" anywhere, it might match "Prepaid Flights" first
- Then the loop breaks (line 341), never reaching "Transport: Taxis/Cab/Uber"

**Problem 2: Blended Evidence**
- All OCR text is concatenated: `merchant_name + line_items_desc + payment_method` (line 239)
- Treated equally - merchant_name has no priority
- An Uber receipt could have "booking" in a field that's not the merchant name and get misclassified

**Problem 3: Generic Keywords
- Keywords like "booking" (in Prepaid Flights) are too broad
- "flight booking" split as two words won't match; "booking" alone matches anything
- No distinction between specific keywords ("united airlines") and generic ones ("booking")

### Current Flow
1. Concatenate all text: "uber booking payment method details"
2. Loop through categories in order
3. For each category, loop through keywords
4. First keyword match wins → **break**
5. Never checks more specific categories if generic keyword matches first

### Impact
- Taxi/Uber receipts classified as "Prepaid Flights" (contains "booking")
- Flight receipts misclassified as "Transport: Flights" vs "Prepaid Flights" randomly
- Inconsistent classification for same vendor across multiple receipts

---

## Fixes Required

### Fix 1: Expose Actual Rejection Reason
- Change ReceiptStatusSerializer.get_message() to return processing_message for REJECTED
- Keep all other status messages (they're operational not policy-based)
- Include actual rejection reason in response

### Fix 2: Improve Category Classification
- Prioritize merchant_name over other text fields
- Order keywords by specificity (longer/more specific first)
- Check merchant-specific keywords with higher confidence
- Avoid letting generic keywords in one category prevent checking another category
- Separate merchant matching from item/payment method matching

