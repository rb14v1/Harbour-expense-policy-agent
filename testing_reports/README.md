# Receipt Testing Report Generator

## Overview

This utility generates comprehensive testing and presentation reports from existing receipt data in the Expense Policy Agent's PostgreSQL database.

**IMPORTANT:** This is a **READ-ONLY utility**. It does not modify the database or any application code.

## Purpose

Generate human-readable reports suitable for:
- Demonstrating the expense policy system to technical clients
- Testing receipt workflows and data processing
- Analyzing receipt processing results
- Documenting system behavior and decisions

## How It Works

The utility reads existing Receipt records from the Django database and generates:

1. **Markdown Report** (`receipt_report.md`) - Full technical report with all details
2. **PDF Report** (`receipt_report.pdf`) - Formatted report for presentation

Both reports are **read-only snapshots** of the current database state.

## What It Reads

The utility reads only the following from the database:

- Receipt model fields (id, status, processing_message, etc.)
- Extracted receipt data (vendor, date, amount, currency, etc.)
- Policy validation results (policy_status, policy_result_json)
- Duplicate detection results (duplicate_score, duplicate_reason)
- Category classification (category, category_confidence, category_reason)
- Timestamps (created_at, updated_at)

**It does NOT:**
- Call OCR or Document Intelligence services
- Execute Celery tasks
- Access Azure Blob Storage
- Modify any database records
- Change any application state

## Installation

### Prerequisites
- Python 3.11+
- Django setup from the parent project (already configured)
- (Optional) `reportlab` for PDF generation

### Install optional PDF support:

```bash
pip install reportlab
```

## Usage

### Generate Report

From the project root:

```bash
python testing_reports/generate_receipt_report.py
```

Or from within the testing_reports directory:

```bash
python generate_receipt_report.py
```

### Output

Reports are generated in `testing_reports/output/`:

```
testing_reports/
├── output/
│   ├── receipt_report.md      # Full Markdown report
│   └── receipt_report.pdf     # PDF report (if reportlab installed)
└── generate_receipt_report.py
```

## Report Contents

### Executive Summary
- Total receipts
- Approval/rejection counts
- Duplicate counts
- Processing failures

### Receipt-by-Receipt Details

For each receipt:
- **Basic Info:** ID, filename, owner, upload date
- **Processing:** Current status, processing message
- **Extracted Data:** Vendor, date, amount, currency, payment method, invoice number
- **Classification:** Category, confidence score, reasoning
- **Policy Validation:** Policy status, rules checked, results
- **Duplicate Check:** Exact/semantic duplicate status, matching receipt, score
- **Finance Review:** Approval/rejection status
- **Final Result:** Overall status and explanation

### Scoring Explanation

Documents the actual implementation:
- **Category Confidence:** 0.0-1.0 threshold 0.75
- **Duplicate Scoring:** 100-point scale with weights
  - Invoice number: 40 points
  - Vendor: 20 points
  - Date: 15 points
  - Total amount: 15 points
  - Tax: 5 points
  - Currency: 5 points
  - Thresholds: 90+ = duplicate, 75-89 = review
- **Policy Rules:** Receipt age ≤ 35 days

### Workflow Summary

Detailed explanation of the complete processing pipeline:
1. File validation
2. SHA-256 hashing
3. Exact duplicate check
4. Blob storage
5. OCR (Azure Document Intelligence)
6. Normalization
7. Category classification
8. Semantic duplicate detection
9. Policy validation
10. Finance review

### Technical Implementation Map

Table showing where each feature is implemented:
- File validation
- Hashing
- Blob operations
- OCR
- Normalization
- Category classification
- Duplicate detection
- Policy validation
- Finance decisions
- Receipt filtering

## Database Changes

**Zero database modifications:**
- No records are created, updated, or deleted
- No migrations are executed
- No tables are altered
- The database remains in its original state

## Environment Setup

The utility automatically:
- Loads Django settings from `config.settings`
- Initializes Django ORM
- Connects to the configured database

No additional setup needed beyond the existing Django configuration.

## Data Safety

- **Read-only:** All operations use Django ORM `.filter()` and `.get()`
- **No mutations:** No `.save()`, `.update()`, `.create()`, or `.delete()` calls
- **No side effects:** Does not trigger any business logic
- **Safe to run repeatedly:** Can generate reports multiple times without impact

## Troubleshooting

### "No receipts found"
- The database may be empty
- The utility will still generate a valid report with summary data

### PDF not generated
- Install `reportlab`: `pip install reportlab`
- Markdown report will still be generated

### Django settings error
- Ensure you're running from the project root
- Check that `config/settings.py` exists
- Verify Django is properly installed

### Database connection error
- Check `.env` file has correct database credentials
- Verify PostgreSQL is running
- Confirm Django settings are correct

## Regenerating Reports

Simply run the command again. Previous reports are overwritten.

```bash
python testing_reports/generate_receipt_report.py
```

## Files

```
testing_reports/
├── README.md                          # This file
├── generate_receipt_report.py         # Main utility (executable)
└── output/                            # Generated reports
    ├── receipt_report.md              # Markdown format
    └── receipt_report.pdf             # PDF format (if reportlab installed)
```

## Isolation

This utility is **completely isolated** from production code:

- Separate directory (`testing_reports/`)
- No modifications to existing files
- No migrations applied
- No changes to models, views, serializers, or services
- Can be safely deleted without affecting the application

The main application continues working exactly as before.

## When to Run

- Before demos to clients (generates current snapshot)
- After testing to document results
- To analyze processing behavior
- To verify policy decisions
- To inspect duplicate detection

## Notes

- Reports reflect the database state at generation time
- Timestamps show when data was created/updated
- Policy and scoring rules are documented from actual code
- Configuration values (thresholds, age limits) are read from Django settings
