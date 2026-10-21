# Frontend Testing Checklist

## Setup

```bash
# Terminal 1: Django
cd C:\Users\admin\Desktop\expense-policy-agent
python manage.py runserver

# Terminal 2: Check everything loads
curl http://localhost:8000/finance/ | grep -o "dashboard-header"
curl http://localhost:8000/upload/ | grep -o "chat-container"
```

---

## Finance Dashboard Testing

**URL:** `http://localhost:8000/finance/`

### Load & Layout
- [ ] Page loads without errors
- [ ] Purple/blue gradient header visible
- [ ] "Finance Department - Receipt Review Dashboard" title shows
- [ ] Filters section displays (Status, Category, Vendor, etc.)
- [ ] Receipts table/list visible
- [ ] Page is responsive (try resizing browser)

### Filtering
- [ ] Click Search button → receipts load
- [ ] Filter by Status (select UNIQUE) → only UNIQUE receipts show
- [ ] Filter by Category → only that category shows
- [ ] Filter by Vendor → vendor search works
- [ ] Filter by Date Range → date filter works
- [ ] Filter by Amount Range → amount filter works
- [ ] Clear Filters button → all filters reset
- [ ] Click Search again → original list returns

### Receipt Details Modal
- [ ] Click "View" button on any receipt → modal opens
- [ ] Modal shows Receipt Information section with details
- [ ] Modal shows Category section with confidence %
- [ ] Modal shows Processing Information (status, message)
- [ ] Modal shows Duplicate Information (if duplicate)
- [ ] Modal shows Policy Information (if policy applied)
- [ ] Modal shows Timestamps (created, updated)
- [ ] Press Escape key → modal closes
- [ ] Click X button → modal closes
- [ ] Preview button → file preview loads in iframe

### Approve/Reject (New Feature)
**IMPORTANT: Select a UNIQUE receipt (status = UNIQUE)**

- [ ] Scroll down in modal (UNIQUE receipt only)
- [ ] See "Finance Decision" section
- [ ] See two buttons: "✅ Approve" and "❌ Reject"
- [ ] Click "✅ Approve" → approval form appears
- [ ] Approval form has textarea for optional notes
- [ ] Type some notes → text appears
- [ ] Click "Submit Approval" → form disappears, receipt marked APPROVED
- [ ] Back on receipts list → status now shows APPROVED (green badge)

**Test Rejection:**
- [ ] Click "View" on another UNIQUE receipt
- [ ] Click "❌ Reject" → rejection form appears
- [ ] Rejection form has textarea for required reason
- [ ] Don't enter reason, click "Submit Rejection" → error message appears
- [ ] Enter a rejection reason → text appears
- [ ] Click "Submit Rejection" → form disappears, receipt marked REJECTED
- [ ] Back on receipts list → status now shows REJECTED (red badge)

### Pagination
- [ ] If more than 1 page: see pagination controls
- [ ] Click "Next →" → page 2 loads
- [ ] Click "← Previous" → page 1 loads
- [ ] Page indicator updates

---

## Upload Page Testing

**URL:** `http://localhost:8000/upload/`

### Layout
- [ ] Page loads with assistant-style card
- [ ] Purple/blue gradient background visible
- [ ] Header shows "💰 Expense Policy Assistant"
- [ ] Chat area visible
- [ ] File input area at bottom

### Single File Upload (Basic)
- [ ] Click "📎 Choose receipts" → file picker opens
- [ ] Select one PDF/JPG/PNG file → picker closes
- [ ] See selected file list with that file and Remove button
- [ ] Click "Send" → file processes
- [ ] See result card with filename, status, vendor, amount, category
- [ ] See "📄 Preview Receipt" button

### Multiple File Selection (New Feature)
- [ ] Click "📎 Choose receipts" → file picker opens
- [ ] Hold Ctrl (Windows) or Cmd (Mac) and select 3 files
- [ ] File picker closes
- [ ] See selected files list with all 3 files
- [ ] Each file has its own Remove button
- [ ] File sizes shown next to names

### Per-File Removal (Critical Test)
**This is the most important new feature**

- [ ] With 3 files selected:
  - [ ] File A (selected.pdf)
  - [ ] File B (another.pdf)
  - [ ] File C (third.pdf)
- [ ] Click Remove button on File B
- [ ] File B disappears from list
- [ ] File A and File C remain in list
- [ ] Click Remove on File A
- [ ] Only File C remains
- [ ] File picker still shows File C as selected (you can verify)

**This proves individual removal works without clearing others**

### Multiple File Processing (New Feature)
- [ ] Select 2 valid PDF/JPG files
- [ ] Click "Send"
- [ ] See message: "Processing 2 receipts..."
- [ ] Each file processes (may take 10-30 seconds)
- [ ] See TWO separate result cards (one per file)
- [ ] Each result card shows:
  - [ ] Filename at top
  - [ ] Status (APPROVED/REJECTED/DUPLICATE)
  - [ ] Vendor, Date, Amount, Category
  - [ ] Preview button

### Error Handling
- [ ] Select one valid file and one invalid file (e.g., .txt)
- [ ] Click Send
- [ ] Valid file processes normally
- [ ] Invalid file shows error message (unsupported type)
- [ ] Both results appear independently

### File Size Validation
- [ ] Select a file larger than 5 MB (or mock one)
- [ ] Click Send
- [ ] See error: "File is too large. Maximum allowed is 5 MB"
- [ ] Other files (if any) still process

### Category Confidence
- [ ] Some receipts auto-detect category with high confidence
- [ ] Some receipts don't (confidence < 80%)
- [ ] For low-confidence receipts, see category selector
- [ ] Category dropdown shows all 45+ categories
- [ ] Select category, click "Confirm Category"
- [ ] Receipt result updates with selected category

### New Button
- [ ] After processing files, see result cards
- [ ] Click "New" button
- [ ] Chat clears
- [ ] See welcome message: "👋 Chat cleared..."
- [ ] Selected files list hidden
- [ ] File input cleared
- [ ] Ready for new upload

### Preview Button
- [ ] After processing, click "📄 Preview Receipt" on result
- [ ] If PDF: embedded viewer shows (in new window or browser viewer)
- [ ] If JPG/PNG: image displays
- [ ] Click back to chat or close window

---

## API Testing (Advanced)

### Finance Decision API

```bash
# Get a UNIQUE receipt first (check ID in browser developer tools)
RECEIPT_ID="some-uuid-here"

# Approve it
curl -X POST http://localhost:8000/finance/api/receipts/$RECEIPT_ID/decision/ \
  -H "Content-Type: application/json" \
  -d '{"decision": "APPROVED", "notes": "Approved for reimbursement"}'

# Should return receipt with status=APPROVED

# Reject it (create a new one if needed)
curl -X POST http://localhost:8000/finance/api/receipts/$RECEIPT_ID/decision/ \
  -H "Content-Type: application/json" \
  -d '{"decision": "REJECTED", "notes": "Missing vendor info"}'

# Should return receipt with status=REJECTED
```

### Categories API

```bash
curl http://localhost:8000/api/v1/receipts/categories/

# Should return JSON with 45+ categories
```

---

## Browser Developer Tools Testing

### Finance Dashboard
- [ ] Open F12 → Network tab
- [ ] Click Search button
- [ ] See `/finance/api/receipts/?...` request
- [ ] Response shows count, results, pagination
- [ ] Click View receipt → `/finance/api/receipts/{id}/` request
- [ ] Click Approve → `POST /finance/api/receipts/{id}/decision/` request
- [ ] Response includes updated status

### Upload Page
- [ ] Open F12 → Network tab
- [ ] Select files → no requests yet
- [ ] Click Send → see `/api/v1/receipts/upload/` POST request
- [ ] As processing, see `/api/v1/receipts/{id}/` polling requests
- [ ] Polling stops when receipt is APPROVED/REJECTED/DUPLICATE/FAILED

### Console Errors
- [ ] No red error messages in console
- [ ] No warnings about undefined functions
- [ ] No CORS errors

---

## Regression Testing (Ensure Nothing Broke)

### Django Tests
```bash
python manage.py test receipts finance
# Should show: Ran 90 tests ... OK
```

### Receipt Upload (Original Flow)
- [ ] Upload page still works
- [ ] Receipt processes normally
- [ ] Status updates in chat
- [ ] Category selector works for low-confidence
- [ ] Preview button works

### Finance Dashboard (Original Flow)
- [ ] Dashboard filters work
- [ ] Pagination works
- [ ] Details modal shows all info
- [ ] Receipt details display correctly

### Teams Integration (If Available)
- [ ] Finance tab URL still works: `https://<ngrok>/finance/tab`
- [ ] Dashboard loads in Teams tab
- [ ] Approve/Reject works in Teams
- [ ] All buttons clickable in Teams

---

## Performance Testing

### Load Time
- [ ] `/finance/` loads in < 2 seconds
- [ ] `/upload/` loads in < 1 second
- [ ] First receipt list loads in < 1 second

### Responsiveness
- [ ] Click buttons → immediate visual feedback
- [ ] Type in filters → no lag
- [ ] Scroll modals → smooth (no jank)
- [ ] File selection → instant

### Memory
- [ ] Upload 10 files → no crashes
- [ ] Keep browser open → no memory growth over 5 minutes

---

## Checklist Summary

- [ ] Finance Dashboard loads and renders
- [ ] All filters work
- [ ] Details modal works
- [ ] **NEW: Approve button works (UNIQUE receipts)**
- [ ] **NEW: Reject button works (UNIQUE receipts)**
- [ ] **NEW: Decision forms work correctly**
- [ ] Upload page loads
- [ ] **NEW: Multiple file selection works**
- [ ] **NEW: Individual file removal works (critical)**
- [ ] **NEW: Each file processes independently**
- [ ] **NEW: Each file gets own result card**
- [ ] Category selector works
- [ ] Preview buttons work
- [ ] New button clears UI
- [ ] No console errors
- [ ] 90/90 Django tests pass
- [ ] No regressions detected

---

## Troubleshooting

### Finance Dashboard showing old layout
- [ ] Hard refresh browser (Ctrl+F5 or Cmd+Shift+R)
- [ ] Clear browser cache
- [ ] Check `/finance/templates/finance/dashboard.html` has decision section

### Approve/Reject buttons not appearing
- [ ] Make sure receipt status is UNIQUE (not APPROVED/REJECTED/DUPLICATE)
- [ ] Open browser console (F12) → check for JavaScript errors
- [ ] Verify `/finance/static/finance/dashboard.js` exists and loads
- [ ] Check Network tab for 404s on CSS/JS files

### Upload page not showing file list
- [ ] Check `/receipts/templates/receipts/upload.html` has selectedFilesList div
- [ ] Verify JavaScript console has no errors
- [ ] Try selecting files again
- [ ] Hard refresh page

### Per-file removal not working
- [ ] Check that `removeFile(index)` function exists in HTML script
- [ ] Verify `selectedFiles` array is being populated
- [ ] Check Network tab that file input still has multiple=true

### Django tests failing
- [ ] Ensure database is migrated: `python manage.py migrate`
- [ ] Check no other Django instance is running on port 8000
- [ ] Run: `python manage.py test receipts finance -v 2`

---

## Test Completion

Once all checks pass:
1. ✅ Frontend redesign is complete and working
2. ✅ Multiple file upload with individual removal verified
3. ✅ Approve/Reject functionality working
4. ✅ No regressions in existing features
5. ✅ Ready for production use

**Estimated Test Time:** 30-45 minutes
