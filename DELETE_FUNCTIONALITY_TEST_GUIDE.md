# Delete Receipt Functionality - Test Guide

## Overview
This guide describes the 11 test scenarios for the new receipt deletion functionality implemented for Version1 Finance Department users.

## Test Environment Setup
- Finance Dashboard URL: `http://localhost:3000/finance` (or equivalent)
- API base: `http://localhost:8000/api/v1`
- Finance user: `owner=finance-department`
- Non-Finance user: `owner=default-user` (or any non-finance owner)

## Test Scenarios

### TEST 1: Authorized Finance User Can See Delete Button
**Objective:** Verify that Finance Department users see the Delete button in the receipt details modal.

**Steps:**
1. Login as Finance Department user (owner=finance-department)
2. Navigate to Finance Dashboard
3. Click "View" on any NEEDS_REVIEW or UNIQUE status receipt
4. Open the receipt details modal

**Expected Result:** 
- Modal displays with receipt information
- "Delete" button visible alongside "Approve", "Reject", and "Preview" buttons
- Delete button is enabled (not grayed out)

**Pass/Fail:** ___________

---

### TEST 2: Unauthorized User Cannot See Delete Button
**Objective:** Verify that non-Finance users do not see the Delete button.

**Steps:**
1. Login as non-Finance user (owner=default-user or employee)
2. If employee dashboard exists, navigate and try to view receipt details
3. Observe button availability

**Expected Result:**
- Delete button is NOT visible to non-Finance users
- Only actions appropriate to user role are available

**Pass/Fail:** ___________

---

### TEST 3: Confirmation Dialog Shows Correct Receipt Details
**Objective:** Verify the confirmation dialog displays accurate receipt information.

**Steps:**
1. Login as Finance Department user
2. Open Finance Dashboard
3. Select a receipt (note vendor name, amount, date)
4. Click "Delete" button
5. Review confirmation dialog

**Expected Result:**
- Dialog title: "Confirm Delete Receipt"
- Receipt details displayed:
  - Vendor name matches selected receipt
  - Amount matches (with currency)
  - Transaction date displayed correctly
- Warning message displayed: "This action is permanent and cannot be undone..."
- Two buttons visible: "Cancel" and "Confirm Delete"

**Pass/Fail:** ___________

**Example Receipt Details in Dialog:**
- Vendor: Starbucks
- Amount: USD 5.50
- Date: October 15, 2026

---

### TEST 4: Cancelling Dialog Leaves Receipt Unchanged
**Objective:** Verify that closing the confirmation dialog doesn't delete anything.

**Steps:**
1. Open Finance Dashboard as Finance user
2. Select a receipt and click "Delete"
3. Confirmation dialog appears
4. Click "Cancel" button
5. Return to Finance Dashboard and search for the receipt

**Expected Result:**
- Confirmation dialog closes
- Modal returns to main receipt details view (or closes)
- Receipt still exists in database
- Receipt still visible in Finance Dashboard list
- Can still view, approve, reject, or delete the receipt

**Pass/Fail:** ___________

---

### TEST 5: Confirming Deletes Receipt from Database
**Objective:** Verify that clicking "Confirm Delete" removes the receipt from the database.

**Steps:**
1. Open Finance Dashboard as Finance user
2. Note the total count of receipts
3. Select a specific receipt (record ID for later verification)
4. Click "Delete" → "Confirm Delete"
5. Wait for deletion to complete
6. Check Finance Dashboard receipt count

**Expected Result:**
- "Confirm Delete" button shows loading state (e.g., "Deleting...")
- Deletion completes (buttons re-enable)
- Confirmation dialog closes
- Receipt no longer appears in Finance Dashboard list
- Total receipt count decreases by 1
- Receipt cannot be accessed via API (returns 404)

**Pass/Fail:** ___________

**Verification via API:**
```bash
curl "http://localhost:8000/api/v1/receipts/{deleted_receipt_id}/?owner=finance-department" \
  -H "Authorization: Bearer <token>"
# Expected: 404 Not Found
```

---

### TEST 6: Confirming Deletes Blob from Azure Storage
**Objective:** Verify that the receipt file is deleted from Azure Blob Storage.

**Steps:**
1. Select a receipt with blob_name (has file uploaded)
2. Note the blob_name from receipt details (or check logs)
3. Delete the receipt (confirm deletion)
4. Attempt to download/preview the receipt
5. Check server logs for deletion confirmation

**Expected Result:**
- Blob file deleted from Azure Storage
- Attempting to preview deleted receipt returns 404 error
- Server logs show: "[DELETE_BLOB_SUCCESS] blob_name=... receipt_id=..."
- If preview attempted: "Unable to preview this receipt because the original file is no longer available"

**Pass/Fail:** ___________

**Server Log Verification:**
Look for log entries:
- `[DELETE_START] receipt_id=..., blob_name=...`
- `[DELETE_DB_SUCCESS] receipt_id=...`
- `[DELETE_BLOB_SUCCESS] blob_name=..., receipt_id=...`
- `[DELETE_SUCCESS] receipt_id=..., blob_name=...`

---

### TEST 7: Receipt Disappears from Finance Dashboard After Deletion
**Objective:** Verify the UI updates immediately to reflect deletion.

**Steps:**
1. Open Finance Dashboard
2. Note a specific receipt visible in the list
3. Delete the receipt (via confirmation dialog)
4. Observe the receipts table

**Expected Result:**
- Confirmation dialog closes after deletion
- Finance Dashboard automatically refreshes receipt list
- Deleted receipt no longer appears in table
- Other receipts remain unchanged
- "Pending Review" count decreases if receipt was NEEDS_REVIEW status

**Pass/Fail:** ___________

---

### TEST 8: Receipt Stays Deleted After Page Refresh
**Objective:** Verify deletion is permanent in database, not just UI-level.

**Steps:**
1. Delete a receipt and confirm it's gone from dashboard
2. Note the receipt ID or take screenshot
3. Refresh the browser page (F5 or Cmd+R)
4. Search for the deleted receipt in Finance Dashboard

**Expected Result:**
- After page refresh, dashboard still doesn't show deleted receipt
- Receipt permanently removed from database
- If attempting to access via direct API call: returns 404

**Pass/Fail:** ___________

---

### TEST 9: Deleting One Receipt Doesn't Affect Others
**Objective:** Verify deletion is isolated and doesn't impact related receipts.

**Steps:**
1. Open Finance Dashboard
2. Note count of receipts (e.g., 10 receipts)
3. Record details of 2 different receipts (Receipt A and Receipt B)
4. Delete Receipt A (confirm deletion)
5. Search for Receipt B in dashboard

**Expected Result:**
- Receipt A successfully deleted
- Receipt B still visible and accessible
- Other receipts in dashboard remain unchanged
- Receipt B can still be viewed, approved, or rejected
- Total count: 9 receipts (10 - 1 deleted)

**Test with Related Duplicates:**
- If Receipt A had duplicate records (EXACT_DUPLICATE, SEMANTIC_DUPLICATE):
  - Deleting Receipt A should NOT cascade delete related records
  - Related duplicates should remain (they reference A but A is gone)
  - Related duplicates should show 404 when trying to preview (since original is deleted)

**Pass/Fail:** ___________

---

### TEST 10: API Returns 403 for Unauthorized Users
**Objective:** Verify the DELETE endpoint requires Finance Department authorization.

**Steps:**
1. Using API client (curl, Postman, etc.):
   ```bash
   curl -X DELETE "http://localhost:8000/api/v1/receipts/{receipt_id}/delete_receipt/?owner=default-user"
   ```
2. Attempt with non-Finance user

**Expected Result:**
- HTTP Status: 403 Forbidden
- Response body contains:
  ```json
  {
    "error": "Unauthorized. Finance Department access required."
  }
  ```
- Receipt remains in database (not deleted)

**Pass/Fail:** ___________

**Verification with Finance User:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/receipts/{receipt_id}/delete_receipt/?owner=finance-department"
# Expected: 204 No Content (success)
```

---

### TEST 11: API Returns 404 for Nonexistent Receipt
**Objective:** Verify proper error handling for invalid receipt IDs.

**Steps:**
1. Using API client:
   ```bash
   curl -X DELETE "http://localhost:8000/api/v1/receipts/invalid-or-nonexistent-id/delete_receipt/?owner=finance-department"
   ```
2. Use a UUID that never existed
3. Use a receipt ID that was already deleted

**Expected Result:**
- HTTP Status: 404 Not Found
- Response body contains:
  ```json
  {
    "error": "Receipt not found"
  }
  ```
- No side effects occur

**Pass/Fail:** ___________

---

## Test Summary

| # | Test Scenario | Status | Notes |
|---|---|---|---|
| 1 | Finance user sees Delete button | PASS/FAIL | |
| 2 | Non-Finance user cannot see Delete button | PASS/FAIL | |
| 3 | Confirmation dialog shows correct details | PASS/FAIL | |
| 4 | Cancelling leaves receipt unchanged | PASS/FAIL | |
| 5 | Confirming deletes from database | PASS/FAIL | |
| 6 | Confirming deletes blob from Azure | PASS/FAIL | |
| 7 | Receipt disappears from dashboard | PASS/FAIL | |
| 8 | Receipt stays deleted after refresh | PASS/FAIL | |
| 9 | Deleting one doesn't affect others | PASS/FAIL | |
| 10 | API returns 403 for unauthorized | PASS/FAIL | |
| 11 | API returns 404 for nonexistent | PASS/FAIL | |

**Overall Status:** ___________

**Tester Name:** ___________

**Date Tested:** ___________

**Issues Found:** 
- (List any failed tests or unexpected behavior)

---

## Rollback Procedure

If issues are discovered during testing:

1. **Revert HTML Manual:**
   - The user_manual changes are only display changes; employees won't see them unless the manual is accessed.

2. **Disable Delete Endpoint:**
   - Comment out `@require_finance_auth` and `delete_receipt` method in `receipts/views.py`
   - Delete button will still show in frontend but API will return errors

3. **Remove Delete Button:**
   - Remove the Delete button from `FinanceDashboard.tsx`
   - Recompile frontend and redeploy

4. **Full Rollback:**
   - Revert git commits
   - Redeploy both frontend and backend

---

## Appendix: Relevant Code Locations

### Backend
- **Auth Decorator:** `/teams_app/auth.py` - `require_finance_auth()`
- **Delete Endpoint:** `/receipts/views.py` - `ReceiptViewSet.delete_receipt()`
- **URL Route:** `/receipts/urls.py` - DRF router auto-generates route

### Frontend
- **Delete Button & Dialog:** `/frontend/src/pages/FinanceDashboard.tsx`
- **Handler Function:** `handleDeleteReceipt()` in FinanceDashboard

### Database
- Deletion uses Django ORM `receipt.delete()` with atomic transaction
- Azure Blob Storage deletion via `BlobService.delete(blob_name)`

### Logging
All deletion operations logged with:
- `[DELETE_START]`, `[DELETE_DB_SUCCESS]`, `[DELETE_BLOB_SUCCESS]`, `[DELETE_SUCCESS]`
- `[DELETE_ERROR]`, `[DELETE_BLOB_FAILED]` for errors
