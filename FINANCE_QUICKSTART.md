# Finance Dashboard - Quick Start Guide

## Launch the Dashboard

1. Start your Django application (if not running):
   ```bash
   python manage.py runserver
   ```

2. Open browser and navigate to:
   ```
   http://localhost:8000/finance/
   ```

3. You should see:
   - Header: "📊 Finance Department - Receipt Review Dashboard"
   - Filter section with dropdowns and input fields
   - Empty state message (if no receipts exist)

---

## Test Data Setup (Development)

To test the dashboard with sample receipts:

```bash
# Run existing test fixture (creates test receipts)
python manage.py test finance.tests.FinanceDashboardViewTests.test_finance_receipts_list_all -v 2
```

Or manually insert test data:

```python
from receipts.models import Receipt
from datetime import date, timedelta
from decimal import Decimal

# Create sample receipt
Receipt.objects.create(
    owner='finance-department',
    original_filename='test_receipt.pdf',
    blob_name='receipts/finance-department/test/test.pdf',
    mime_type='application/pdf',
    file_size=5000,
    sha256_hash='test_hash_123',
    status='APPROVED',
    vendor_name='ABC Restaurant',
    transaction_date=date.today() - timedelta(days=5),
    total_amount=Decimal('150.00'),
    currency='USD',
    category='Food: Dinner - Max Claim: €/$/AUD 45 / INR700',
    category_confidence=0.92,
    category_reason='Matched restaurant keywords',
    policy_status='APPROVED',
    policy_result_json={
        'status': 'APPROVED',
        'rules': [{
            'code': 'RECEIPT_AGE_OK',
            'passed': True,
            'message': 'Receipt age is within policy (5 days old).'
        }]
    }
)
```

---

## Using Filters

### 1. Status Filter
- **All Statuses** — No filter
- **Approved** — Only approved receipts
- **Rejected** — Only rejected receipts
- **Exact Duplicate** — Exact file duplicates
- **Semantic Duplicate** — Similar expense detected
- **Unique** — No duplicates found
- **OCR Failed** — Processing failed

### 2. Category Filter
- Dropdown automatically populated from master list
- 45 expense categories available
- Multi-select not available (single selection per search)

### 3. Date Range
- **Date From** — Receipts on or after this date
- **Date To** — Receipts on or before this date
- **Example:** Date From: 2026-09-01, Date To: 2026-09-15

### 4. Amount Range (NEW)
- **Amount Min** — Receipts >= this amount
- **Amount Max** — Receipts <= this amount
- **Example:** Min: 50.00, Max: 200.00

### 5. Text Search
- **Vendor** — Case-insensitive vendor name search
- **Filename** — Case-insensitive filename search
- **Example:** Vendor: "ABC" finds "ABC Restaurant", "ABC Cafe", etc.

### Search & Clear Buttons
- **🔍 Search** — Apply all active filters, reset to page 1
- **✕ Clear Filters** — Reset all filters to empty, reload results

---

## Viewing Receipt Details

1. **In the receipts table, click "View" button**

2. **Details modal opens with sections:**

   **Receipt Information**
   - Filename, vendor, date, amount, currency, invoice number, payment method

   **Category**
   - Category, confidence score (%), reason for classification

   **Processing Information**
   - Status (colored badge), processing message

   **Duplicate Information** (if applicable)
   - Type (Exact/Semantic), score, reason for duplicate flag

   **Policy Information** (if policy processed)
   - Policy status (colored badge)
   - List of policy rules with:
     - Rule code
     - Pass/fail status (✓ or ✗)
     - Human-readable reason

   **Timestamps**
   - Created date/time, updated date/time

3. **Click "[Preview Receipt]" to see PDF/image**

4. **Close with ✕ button or press Escape**

---

## Understanding Receipt Status

| Status | Meaning | Next Action |
|--------|---------|-------------|
| APPROVED | Passed all checks | No action needed |
| REJECTED | Failed policy validation | Review reason, contact employee if needed |
| EXACT_DUPLICATE | Same file uploaded before | Request employee re-scan different receipt |
| SEMANTIC_DUPLICATE | Same expense submitted multiple ways | Investigate, may be duplicate claim |
| UNIQUE | No duplicates found | Good candidate for processing |
| OCR_FAILED | Text extraction failed | Manual review needed |

---

## Understanding Policy Rejection Reasons

When a receipt shows status **REJECTED**, check **Policy Information** section for reasons:

### Current Policy Rule

**Receipt Age Limit (35 days)**
```
RECEIPT_TOO_OLD ✗
Receipt is older than 35 days (40 days old).
```

The receipt was submitted after the 35-day deadline.

**Action:** Contact employee, request newer receipt or waiver.

### Future Policy Rules

When additional rules are added, they will appear here with:
- Rule code (e.g., AMOUNT_EXCEEDS_LIMIT)
- Status (Pass ✓ or Fail ✗)
- Specific reason message

---

## Pagination

- **Results per page:** 50 receipts
- **Navigation:** Previous/Next buttons at bottom
- **Page indicator:** Shows current page number
- **Disabled state:** Previous disabled on first page, Next disabled on last page

---

## Preview Receipts

1. **Click "View" on any receipt**
2. **Click "[Preview Receipt]" button in details modal**
3. **Preview modal opens with file (PDF or image)**
4. **Supported formats:**
   - PDF documents
   - JPG/JPEG images
   - PNG images
5. **Close preview:** Click ✕ or press Escape

### Preview Works For:
- ✅ Approved receipts (original file available)
- ✅ Rejected receipts (original file available)
- ✅ Exact duplicates (shows original receipt file)
- ✅ Semantic duplicates (shows original receipt file)

**Note:** Duplicate receipts automatically show the original file used for processing.

---

## Common Tasks

### Find All Approved Receipts from Last 30 Days
1. Status → "Approved"
2. Date From → 30 days ago
3. Click "🔍 Search"

### Find Rejected Receipts
1. Status → "Rejected"
2. Click "🔍 Search"
3. Click "View" on any result
4. Check "Policy Information" section for rejection reason

### Search by Vendor
1. Vendor → Type "ABC"
2. Click "🔍 Search"
3. Shows all receipts from vendors containing "ABC"

### Search by Amount Range
1. Amount Min → 100.00
2. Amount Max → 500.00
3. Click "🔍 Search"
4. Shows receipts between $100-$500

### Find Duplicates
1. Status → "Exact Duplicate" or "Semantic Duplicate"
2. Click "🔍 Search"
3. View → Check "Duplicate Information" section
4. See which receipt was matched

---

## API Endpoints (For Integration)

### Get Finance Receipts List
```
GET /finance/api/receipts/?status=APPROVED&date_from=2026-09-01&date_to=2026-09-30
```

### Get Finance Receipt Detail
```
GET /finance/api/receipts/{receipt_id}/
```

### Preview Receipt File
```
GET /api/v1/receipts/{receipt_id}/preview/?owner=finance-department
```

### Get Categories Master
```
GET /api/v1/receipts/categories/
```

---

## Keyboard Shortcuts

- **Escape** — Close any modal (details or preview)
- **Tab** — Navigate between form fields
- **Enter** — Submit filter search

---

## Troubleshooting

### Dashboard doesn't load (404 error)
- Ensure Django is running: `python manage.py runserver`
- Check URL: `http://localhost:8000/finance/`
- Verify finance app is in INSTALLED_APPS (config/settings.py)

### No receipts showing
- Check if receipts exist with owner='finance-department'
- Try clearing all filters and searching again
- Run tests to populate test data: `python manage.py test finance`

### Preview not loading
- Ensure blob file still exists in Azure Blob Storage
- Check browser console for errors (F12)
- Verify receipt has valid blob_name

### Filters not working
- Click "🔍 Search" button (doesn't auto-filter on change)
- Clear filters if stuck with "✕ Clear Filters"
- Check browser console for errors

### "Unauthorized" on preview
- Verify receipt owner is 'finance-department'
- Check if file was deleted from Blob Storage

---

## Support

For issues or questions:
1. Check FINANCE_DASHBOARD_IMPLEMENTATION.md for detailed documentation
2. Review FINANCE_VALIDATION_REPORT.md for test coverage
3. Check Django logs: `python manage.py runserver` output
4. Run tests: `python manage.py test receipts finance -v 2`

