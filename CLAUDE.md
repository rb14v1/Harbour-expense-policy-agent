# CLAUDE.md — Expense Policy Agent

## 1. Project Mission

Build a production-structured **Expense Policy Agent** that runs inside **Microsoft Teams** and allows users to upload expense receipts for automated processing.

The system must:

1. Accept receipt uploads from Microsoft Teams.
2. Store the original uploaded file in Azure Blob Storage.
3. Generate a SHA-256 hash from the uploaded file content.
4. Detect exact duplicate files using the SHA-256 hash before OCR.
5. Use **Azure AI Document Intelligence** for OCR and structured receipt extraction.
6. Normalize extracted receipt data into a stable internal JSON schema.
7. Compare the normalized receipt with existing receipts in PostgreSQL.
8. Detect semantic/business duplicates using invoice number, vendor, date, amount, tax, currency, and related fields.
9. Reject duplicates with a clear reason.
10. Store unique receipt JSON in PostgreSQL.
11. Continue unique receipts to policy validation and later approval workflows.
12. Return processing status and results back to the user in Microsoft Teams.

The current priority is the **receipt ingestion + extraction + duplicate-detection pipeline**. Policy rules and approval workflows should be modular and added after the core receipt pipeline works reliably.

---

## 2. Finalized Architecture

```text
Microsoft Teams
    |
    | Teams SDK
    v
Teams App / Bot
    |
    | HTTPS
    v
Django Backend API
    |
    +--> Azure Blob Storage
    |       Store original receipt
    |
    +--> SHA-256 Hashing
    |       Exact-file duplicate check
    |
    +--> Background Worker
            |
            +--> Azure AI Document Intelligence
            |       OCR + receipt field extraction
            |
            +--> Normalize receipt JSON
            |
            +--> PostgreSQL
            |       Existing receipt lookup
            |       Duplicate comparison
            |       Store unique receipt
            |
            +--> Policy Engine
                    Future / next-stage processing
```

Finalized decisions:

- Frontend: Microsoft Teams using Teams SDK.
- Backend: Django + Django REST Framework.
- Database: PostgreSQL.
- Original file storage: Azure Blob Storage.
- OCR and receipt field extraction: Azure AI Document Intelligence.
- Exact duplicate detection: SHA-256 of file bytes.
- Business duplicate detection: normalized extracted receipt data.
- Policy processing begins only after duplicate checks pass.

Do not replace these technologies unless explicitly requested.

---

## 3. Core User Flow

```text
1. User logs in to Microsoft Teams
        |
        v
2. User opens Expense Policy Agent
        |
        v
3. User views dashboard / previous claims / upload action
        |
        v
4. User uploads receipt (PDF / JPG / JPEG / PNG)
        |
        v
5. Teams shows upload accepted / processing
        |
        v
6. Django backend receives file
        |
        v
7. Store original file in Azure Blob Storage
        |
        v
8. Generate SHA-256 hash from FILE CONTENT
        |
        v
9. Exact duplicate check by hash
        |
        +----------------------------+
        |                            |
        | Hash exists                | No hash match
        v                            v
   Reject exact duplicate       Azure AI Document Intelligence
                                     |
                                     v
                              OCR + field extraction
                                     |
                                     v
                               Normalize JSON
                                     |
                                     v
                         Compare against PostgreSQL
                                     |
                          +----------+----------+
                          |                     |
                          | Duplicate           | Unique
                          v                     v
                     Reject receipt        Save normalized JSON
                                                |
                                                v
                                         Policy validation
                                                |
                                                v
                                         Approval workflow
```

This processing order is intentional. Exact-file duplicates must be stopped before OCR so Azure Document Intelligence is not called unnecessarily.

---

## 4. Technology Stack

### Microsoft Teams layer

Use Microsoft Teams SDK and Teams-native app capabilities. Use Adaptive Cards where useful for status and result presentation. The Teams layer is a thin UI/integration layer and must not contain OCR, database, duplicate, storage, or policy logic.

### Backend

Use:

```text
Python 3.11+
Django
Django REST Framework
PostgreSQL
psycopg / psycopg2
Azure SDKs
```

Recommended asynchronous processing:

```text
Celery
Redis
```

If Redis/Celery are not yet available locally, keep processing logic behind services so development can temporarily run synchronously without changing core business code.

### Required Azure services

**Azure Blob Storage** — stores original receipt files.

**Azure AI Document Intelligence** — performs OCR and receipt field extraction. Keep all Azure-specific OCR code inside a dedicated service.

**Microsoft Entra ID / app registration** — Teams application identity and secure authentication/integration.

Never hard-code secrets, tokens, connection strings, client secrets, or storage keys.

---

## 5. Target Repository Structure

```text
expense-policy-agent/
|
├── CLAUDE.md
├── README.md
├── manage.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml              # optional local PostgreSQL/Redis
|
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
|
├── apps/
│   ├── accounts/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── services.py
│   |
│   ├── receipts/
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── selectors.py
│   │   ├── tasks.py
│   │   └── services/
│   │       ├── receipt_service.py
│   │       ├── blob_service.py
│   │       ├── hashing_service.py
│   │       ├── document_intelligence_service.py
│   │       ├── normalization_service.py
│   │       ├── duplicate_service.py
│   │       └── file_validation_service.py
│   |
│   ├── policies/
│   │   ├── models.py
│   │   ├── services/
│   │   │   └── policy_service.py
│   │   └── rules/
│   |
│   └── audit/
│       ├── models.py
│       └── services.py
|
├── teams-app/
│   ├── appPackage/
│   │   ├── manifest.json
│   │   ├── color.png
│   │   └── outline.png
│   ├── src/
│   │   ├── bot/
│   │   ├── cards/
│   │   ├── handlers/
│   │   ├── api/
│   │   └── config/
│   ├── package.json
│   └── tsconfig.json
|
├── tests/
│   ├── receipts/
│   ├── policies/
│   ├── api/
│   └── integration/
|
├── scripts/
│   ├── seed_receipts.py
│   └── create_test_data.py
|
└── docs/
    ├── architecture.md
    ├── api.md
    └── data-model.md
```

---

## 6. Architecture Rules

### Keep Teams thin

Teams handles user interaction, uploads, status display, history display, and result cards. Teams must not implement business logic.

### Keep Django views thin

Views should authenticate, validate requests, invoke service/application logic, and return responses. Do not place receipt-processing workflows in views.

### Isolate Azure integrations

Azure Blob SDK calls belong in `blob_service.py`.

Azure AI Document Intelligence SDK calls belong in `document_intelligence_service.py`.

Do not scatter Azure SDK calls through models, serializers, views, or tasks.

### Separate binary and structured data

Original receipt binary -> Azure Blob Storage.

Normalized receipt data -> PostgreSQL.

Do not store large receipt files directly in PostgreSQL.

### Hash file bytes, never filenames

The SHA-256 digest must be based on file content. Two files with different names but identical bytes must produce the same hash.

### Exact duplicate check before OCR

```text
upload -> store -> hash -> exact duplicate lookup -> OCR only if unique hash
```

### Business duplicate check after normalization

```text
OCR -> extraction -> normalization -> duplicate comparison
```

Never compare raw OCR text directly for business duplicate detection.

---

## 7. Receipt Data Model

The primary `Receipt` model should conceptually contain:

```text
id: UUID
owner/user reference
original_filename
blob_name
blob_reference
mime_type
file_size
sha256_hash
status
upload_timestamp

vendor_name
vendor_normalized
invoice_number
invoice_number_normalized
transaction_date
subtotal
tax_amount
total_amount
currency
payment_method

normalized_json JSONB
raw_document_intelligence_json JSONB

exact_duplicate_of
semantic_duplicate_of
duplicate_score
duplicate_reason

policy_status
policy_result_json JSONB

created_at
updated_at
```

Recommended status values:

```text
UPLOADED
HASHING
EXACT_DUPLICATE
QUEUED_FOR_OCR
OCR_PROCESSING
OCR_FAILED
EXTRACTED
NORMALIZED
DUPLICATE_CHECKING
SEMANTIC_DUPLICATE
UNIQUE
POLICY_PROCESSING
APPROVED
REJECTED
NEEDS_REVIEW
FAILED
```

The exact enum may be simplified initially, but processing state must remain explicit and auditable.

---

## 8. Normalized Receipt JSON Contract

All provider-specific OCR output must be converted into a stable internal structure similar to:

```json
{
  "receipt_id": "uuid",
  "source": {
    "original_filename": "receipt.pdf",
    "blob_reference": "receipts/user-id/uuid/receipt.pdf",
    "sha256": "..."
  },
  "merchant": {
    "name": "ABC Restaurant",
    "address": null,
    "phone": null
  },
  "invoice": {
    "invoice_number": "INV-10023",
    "transaction_date": "2026-09-01"
  },
  "amounts": {
    "subtotal": 1000.00,
    "tax": 180.00,
    "total": 1180.00,
    "currency": "INR"
  },
  "payment": {
    "method": null
  },
  "line_items": [
    {
      "description": "Lunch",
      "quantity": 1,
      "unit_price": 1000.00,
      "amount": 1000.00
    }
  ],
  "extraction": {
    "provider": "azure_ai_document_intelligence",
    "model": "prebuilt-receipt",
    "confidence": {}
  }
}
```

The rest of the project should consume this internal format rather than Azure SDK response objects.

---

## 9. Azure AI Document Intelligence Service

Create:

```text
apps/receipts/services/document_intelligence_service.py
```

Responsibilities:

1. Accept receipt bytes or content from Blob Storage.
2. Send the document to Azure AI Document Intelligence.
3. Perform OCR and structured receipt analysis.
4. Extract provider results safely.
5. Return a provider-neutral dictionary/DTO.
6. Preserve raw response JSON when required for debugging/audit.
7. Raise controlled application exceptions.
8. Never expose Azure SDK objects outside this service.

Conceptual interface:

```python
class DocumentIntelligenceService:
    def analyze_receipt(self, *, content: bytes, content_type: str) -> dict:
        ...
```

Attempt to extract, when present:

```text
merchant/vendor name
merchant address
transaction date
time
invoice/receipt number
subtotal
tax
tip
total
currency
payment method
line items
```

Missing fields are valid outcomes. Never fabricate missing OCR values.

Store confidence information where Azure provides it so low-confidence fields can later be reviewed.

---

## 10. Upload Requirements

Initially support:

```text
application/pdf
image/jpeg
image/png
```

Allowed extensions:

```text
.pdf
.jpg
.jpeg
.png
```

Validate both extension and MIME/content characteristics where feasible.

Use a configurable maximum upload size, e.g.:

```env
MAX_RECEIPT_UPLOAD_MB=10
```

Never trust the client filename as a storage key. Generate a safe path such as:

```text
receipts/{user_id}/{receipt_uuid}/{sanitized_filename}
```

---

## 11. Blob Storage Flow

`blob_service.py` should provide operations similar to:

```python
upload_receipt(...)
get_receipt(...)
delete_receipt(...)
generate_read_url_if_required(...)
```

Blob Storage is the source of truth for the original receipt binary. Containers should remain private.

---

## 12. SHA-256 Exact Duplicate Detection

Implement streaming hashing where possible:

```python
import hashlib

def calculate_sha256(file_obj) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()
```

Create a database index on `sha256_hash`.

Exact duplicate condition:

```text
same SHA-256 hash
```

When found:

```text
status = EXACT_DUPLICATE
exact_duplicate_of = existing_receipt.id
duplicate_reason = "Same file content was already uploaded."
```

Do not call Azure AI Document Intelligence for an exact duplicate.

---

## 13. Semantic / Business Duplicate Detection

A receipt may represent the same expense even when the binary differs, for example a screenshot, re-scan, compressed image, converted PDF, or renamed copy.

After OCR and normalization, perform layered duplicate checks.

### Level 1: strong invoice identity

Strong signal:

```text
invoice_number + vendor_name
```

Confirm with date and total where available.

### Level 2: same expense identity

If invoice number is missing, compare:

```text
vendor_name
transaction_date
total_amount
currency
```

A strong match should be treated as probable duplicate.

### Level 3: weighted duplicate score

Initial configurable scoring model:

```text
invoice number exact match       40
vendor normalized match          20
transaction date match           15
total amount match               15
tax amount match                  5
currency match                    5
-----------------------------------
maximum                          100
```

Suggested thresholds:

```text
90-100  duplicate
75-89   probable duplicate / needs review
0-74    unique
```

Thresholds and weights must be centralized in configuration, not scattered through the codebase.

---

## 14. Normalization Rules

Create `normalization_service.py`.

Normalize comparison values for:

```text
vendor names
invoice numbers
dates
currency
decimal amounts
whitespace
safe punctuation
```

Example vendor variants:

```text
ABC RESTAURANT PVT LTD
ABC Restaurant Pvt. Ltd.
abc restaurant pvt ltd
```

should produce a comparison-friendly normalized value such as:

```text
abc restaurant pvt ltd
```

Do not destructively replace the original extracted value. Keep normalized comparison values separately when useful.

Normalize dates to `YYYY-MM-DD` and currency codes to uppercase where possible.

---

## 15. PostgreSQL Strategy

PostgreSQL stores:

```text
receipt metadata
extracted fields
normalized comparison fields
duplicate links
processing statuses
policy results
audit timestamps
```

Use JSONB for:

```text
normalized_json
raw_document_intelligence_json
policy_result_json
```

Use normal indexed columns for fields frequently queried during duplicate checks:

```text
sha256_hash
vendor_normalized
invoice_number_normalized
transaction_date
total_amount
currency
owner/user
```

Do not depend exclusively on JSONB lookups for high-frequency matching.

---

## 16. Background Worker

OCR should not block a long-lived Teams HTTP request.

Recommended upload flow:

```text
POST /receipts
   -> validate file
   -> create receipt record
   -> upload Blob
   -> generate SHA-256
   -> exact duplicate check
   -> enqueue process_receipt(receipt_id)
```

Worker flow:

```text
Azure Document Intelligence
 -> normalize
 -> semantic duplicate check
 -> persist result
 -> policy processing
```

Pass `receipt_id` to the worker, not receipt binary content through Redis.

Worker tasks must be idempotent and safe to retry.

---

## 17. Django API Design

Minimum endpoints:

### Upload

```text
POST /api/v1/receipts/
```

Input:

```text
multipart/form-data
file=<receipt>
```

Response example:

```json
{
  "id": "uuid",
  "status": "QUEUED_FOR_OCR",
  "message": "Receipt uploaded successfully and is being processed."
}
```

### Receipt status/details

```text
GET /api/v1/receipts/{id}/
```

Example:

```json
{
  "id": "uuid",
  "status": "UNIQUE",
  "duplicate": false,
  "receipt": {
    "vendor_name": "ABC Restaurant",
    "transaction_date": "2026-09-01",
    "total_amount": "1180.00",
    "currency": "INR"
  }
}
```

### User receipt history

```text
GET /api/v1/receipts/
```

Use pagination and return only receipts the authenticated user is allowed to see.

---

## 18. Teams Experience

The Teams app should support:

```text
Upload Receipt
View Recent Claims
View Receipt Status
View Duplicate Result
View Policy Result
```

Example user messages/cards:

Upload accepted:

```text
Receipt uploaded successfully. Processing...
```

Exact duplicate:

```text
Duplicate receipt detected. This exact file has already been uploaded.
```

Semantic duplicate:

```text
Possible duplicate expense detected. A matching expense already exists.
```

Unique:

```text
Receipt processed successfully. No duplicate detected. Continuing with policy checks.
```

Never expose stack traces, raw OCR JSON, Blob paths, secrets, or Azure implementation details to end users.

---

## 19. Policy Engine

Policy logic belongs under `apps/policies/` and must remain separate from duplicate logic.

Initial rule already agreed:

```text
receipt age must be <= 35 days
```

Future rules may include:

```text
allowed category
category amount limit
receipt-required threshold
currency handling
employee eligibility
approval rules
```

Example result:

```json
{
  "status": "FAILED",
  "rules": [
    {
      "code": "RECEIPT_TOO_OLD",
      "passed": false,
      "message": "Receipt is older than 35 days."
    }
  ]
}
```

Correct order:

```text
ingestion -> duplicate checks -> unique -> policy engine -> approval
```

---

## 20. No LLM/Agent in the Critical Path

Do not add an autonomous agent or LLM to deterministic functions such as:

```text
file validation
SHA-256 hashing
exact duplicate detection
Azure OCR call
normalization
database lookup
policy rule checks
```

An LLM may be considered later for:

```text
natural-language policy Q&A
explaining rejection reasons
ambiguous category assistance
user-friendly summaries
```

It must not replace deterministic financial checks.

---

## 21. Environment Variables

Create and maintain `.env.example`.

```env
# Django
DJANGO_SECRET_KEY=
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
POSTGRES_DB=expense_policy
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=
AZURE_STORAGE_CONTAINER_NAME=receipts

# Azure AI Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=
AZURE_DOCUMENT_INTELLIGENCE_KEY=

# Teams / Entra
TEAMS_APP_ID=
TEAMS_APP_PASSWORD=
MICROSOFT_TENANT_ID=

# Worker
REDIS_URL=redis://localhost:6379/0

# Receipt rules
MAX_RECEIPT_UPLOAD_MB=10
RECEIPT_MAX_AGE_DAYS=35

# Duplicate detection
DUPLICATE_SCORE_THRESHOLD=90
REVIEW_SCORE_THRESHOLD=75
```

Never commit `.env`.

---

## 22. Error Handling

Create controlled application errors such as:

```text
UnsupportedFileTypeError
ReceiptTooLargeError
BlobUploadError
DocumentExtractionError
ReceiptNormalizationError
DuplicateReceiptError
```

User-facing responses must be simple and safe. Internal logs can contain technical context but must never contain credentials or secrets.

If Blob upload fails, mark the receipt failed cleanly.

If OCR fails, keep the original receipt in Blob Storage, mark `OCR_FAILED`, and allow controlled retry.

---

## 23. Security Requirements

Implement:

```text
authentication
authorization
user-level receipt isolation
private Blob Storage
safe filename handling
file-size limits
MIME validation
HTTPS in deployed environments
secure secret configuration
appropriate CSRF/CORS configuration
```

Never trust a user-submitted owner ID, arbitrary Blob path, or client-side authorization decision.

User A must never be able to retrieve User B's receipt unless explicitly authorized by business rules.

---

## 24. Audit and Logging

Track at minimum:

```text
who uploaded
when uploaded
file hash
blob storage completion
status transitions
OCR started/completed/failed
duplicate decision
duplicate source receipt
policy decision
```

Suggested structured event names:

```text
receipt.uploaded
receipt.hash_generated
receipt.exact_duplicate_detected
receipt.ocr_started
receipt.ocr_completed
receipt.ocr_failed
receipt.normalized
receipt.semantic_duplicate_detected
receipt.unique
receipt.policy_started
receipt.policy_completed
```

Do not log full receipt binaries or credentials.

---

## 25. Testing Requirements

### Upload validation

Test:

```text
valid PDF
valid JPG
valid PNG
unsupported extension
oversized file
empty file
```

### Hash duplicate logic

Test:

```text
same bytes + same filename -> exact duplicate
same bytes + different filename -> exact duplicate
different bytes + same filename -> not exact duplicate
```

Filename alone must never determine duplication.

### OCR normalization

Test:

```text
all major fields present
missing invoice number
missing tax
missing currency
multiple line items
low-confidence fields
```

### Semantic duplicates

Test:

```text
same invoice + vendor
same vendor/date/amount
same vendor but different amount
same amount but different date
different currency
vendor formatting differences
```

### Authorization

Test that one user cannot fetch another user's receipt.

---

## 26. Sample Development Data

Use about 20 fictional receipts during development, including:

```text
normal unique receipts
exact duplicates
same expense in a different image/PDF representation
different expenses from same vendor
missing invoice number
tax/no-tax receipts
different currencies
receipts older than 35 days
future-dated malformed example
PDF/JPG/PNG files
```

Do not use real employee financial information for test fixtures.

---

## 27. Implementation Order

### Phase 1 — Django foundation

```text
create Django project
configure settings
configure PostgreSQL
create Receipt model
create migrations
create serializers/views/URLs
```

### Phase 2 — Upload + Azure Blob

```text
file validation
create DB row
upload original binary
save Blob reference
```

### Phase 3 — Exact duplicate check

```text
SHA-256 service
DB index
hash lookup
exact duplicate response
```

This must work before OCR integration.

### Phase 4 — Azure AI Document Intelligence

```text
DocumentIntelligenceService
analyze receipt
parse fields
controlled failures
persist raw result where needed
```

### Phase 5 — Normalization

```text
Azure output -> stable internal receipt JSON
```

### Phase 6 — Semantic duplicate detection

```text
invoice/vendor rules
vendor/date/amount rules
weighted score
clear duplicate explanation
```

### Phase 7 — Worker

Move OCR, normalization, semantic duplicate checks, and policy continuation into the worker while preserving service interfaces.

### Phase 8 — Teams integration

```text
upload
processing state
receipt history
duplicate result
policy result
```

Teams calls Django APIs rather than implementing the processing itself.

### Phase 9 — Policy engine

Start with the 35-day rule and add later rules as requirements are finalized.

---

## 28. Core MVP Definition of Done

The MVP is complete when all of the following work:

1. User uploads PDF/JPG/PNG from Teams.
2. Teams sends it to Django.
3. Django validates it and stores the original file in Azure Blob Storage.
4. SHA-256 is generated from file bytes.
5. Existing SHA-256 causes immediate duplicate rejection.
6. Unique hashes continue to Azure AI Document Intelligence.
7. OCR/extraction returns structured receipt data.
8. Data is normalized into the internal JSON contract.
9. Receipt is compared against existing PostgreSQL receipt data.
10. Semantic duplicates are rejected with a reason.
11. Unique receipts are persisted.
12. Unique receipts continue to policy validation.
13. Teams displays current/final status.
14. Infrastructure errors are handled safely.
15. Core flows are covered by automated tests.

---

## 29. Coding Standards

Use:

```text
type hints
small functions
service-layer separation
clear names
Django transactions where consistency matters
configuration instead of magic numbers
migrations for model changes
unit tests for business logic
```

Avoid:

```text
god classes
business logic in views
business logic in serializers
Azure calls spread across the project
hard-coded secrets
magic duplicate thresholds
unbounded file uploads
silent exception swallowing
```

---

## 30. Transaction and Retry Guidance

PostgreSQL and Azure Blob Storage do not share a single transaction. Design for recoverability.

Suggested upload lifecycle:

```text
create receipt row
 -> upload blob
 -> save blob reference
 -> calculate hash
 -> exact duplicate check
 -> enqueue worker
```

If Blob upload fails, mark the row failed rather than pretending the upload succeeded.

If OCR fails, retain the original blob and allow retry.

Worker tasks must be idempotent. Before processing, check current receipt state. Do not re-run successful OCR or overwrite final duplicate decisions accidentally.

---

## 31. Suggested Service Interfaces

```python
class BlobService:
    def upload(self, *, file_obj, blob_name: str, content_type: str) -> str:
        ...

    def download(self, *, blob_name: str) -> bytes:
        ...
```

```python
class HashingService:
    def sha256(self, file_obj) -> str:
        ...
```

```python
class DocumentIntelligenceService:
    def analyze_receipt(self, *, content: bytes, content_type: str) -> dict:
        ...
```

```python
class ReceiptNormalizationService:
    def normalize(self, extracted: dict) -> dict:
        ...
```

```python
class DuplicateService:
    def find_exact_duplicate(self, *, sha256_hash: str, user=None):
        ...

    def evaluate_semantic_duplicate(self, *, receipt):
        ...
```

```python
class PolicyService:
    def evaluate(self, *, receipt) -> dict:
        ...
```

---

## 32. Receipt Processing Orchestrator

The main OCR/normalization/semantic duplicate workflow belongs in an application service or worker task, not a Django view.

Conceptual flow:

```python
def process_uploaded_receipt(receipt_id):
    receipt = get_receipt(receipt_id)

    if receipt.is_final:
        return

    receipt.mark_ocr_processing()

    file_bytes = blob_service.download(blob_name=receipt.blob_name)

    extracted = document_intelligence_service.analyze_receipt(
        content=file_bytes,
        content_type=receipt.mime_type,
    )

    normalized = normalization_service.normalize(extracted)
    save_extraction(receipt, extracted, normalized)

    duplicate_result = duplicate_service.evaluate_semantic_duplicate(
        receipt=receipt
    )

    if duplicate_result.is_duplicate:
        mark_duplicate(receipt, duplicate_result)
        return

    mark_unique(receipt)

    policy_result = policy_service.evaluate(receipt=receipt)
    save_policy_result(receipt, policy_result)
```

Exact hash duplicate checking must already have occurred before this worker is queued.

---

## 33. Stable API Status Contract

Teams must consume a stable backend status object rather than infer workflow state.

Processing example:

```json
{
  "receipt_id": "uuid",
  "status": "OCR_PROCESSING",
  "stage": "ocr",
  "is_final": false,
  "message": "Reading receipt details."
}
```

Duplicate example:

```json
{
  "receipt_id": "uuid",
  "status": "SEMANTIC_DUPLICATE",
  "stage": "duplicate_check",
  "is_final": true,
  "message": "A matching expense already exists.",
  "duplicate": {
    "type": "semantic",
    "matched_receipt_id": "uuid",
    "score": 95
  }
}
```

Unique example:

```json
{
  "receipt_id": "uuid",
  "status": "UNIQUE",
  "stage": "policy",
  "is_final": false,
  "message": "No duplicate found. Checking expense policy."
}
```

---

## 34. Decisions That Must Not Be Changed Without Approval

Do not change these unless the user explicitly asks:

```text
Frontend = Microsoft Teams + Teams SDK
Backend = Django
Database = PostgreSQL
Original receipt storage = Azure Blob Storage
OCR/extraction = Azure AI Document Intelligence
Exact duplicate = SHA-256 file-content hash
Semantic duplicate = normalized receipt data comparison
Exact duplicate check occurs before OCR
Semantic duplicate check occurs after OCR + normalization
Policy checks occur after duplicate checks
Initial supported formats = PDF/JPG/JPEG/PNG
Receipt age policy = 35 days
```

Specifically, do not silently replace Django with FastAPI, PostgreSQL with MongoDB, Azure Document Intelligence with local OCR, Teams with a standalone web UI, or SHA-256 matching with filename matching.

---

## 35. Requirements Still Open

Do not invent these. Isolate them behind configuration or ask when implementation reaches them:

```text
full expense category list
category-specific limits
manager approval hierarchy
finance approval hierarchy
ERP/reimbursement integration
retention period
multi-currency conversion rules
cost centers
production hosting topology
notification strategy
```

---

## 36. Claude Working Instructions

When working on this repository:

1. Read this file first.
2. Preserve the finalized architecture.
3. Inspect existing files before generating new ones.
4. Implement one vertical slice at a time.
5. Keep Teams and Django responsibilities separated.
6. Keep Azure integrations behind service classes.
7. Do not add agents/LLMs to deterministic processing.
8. Add migrations whenever Django models change.
9. Add tests with each new business service.
10. Update `.env.example` when configuration changes.
11. Update README setup instructions when dependencies or startup commands change.
12. Never put secrets in code or example values.
13. Avoid destructive database changes without warning.
14. Prefer incremental, testable changes over huge rewrites.
15. Do not duplicate modules that already exist.
16. If a requirement conflicts with this document, stop and surface the conflict before changing architecture.

---

## 37. First Build Target

The first complete backend milestone is:

```text
Local Django API
    |
    v
POST receipt
    |
    v
Validate file
    |
    v
Store metadata
    |
    v
Upload to Azure Blob
    |
    v
Generate SHA-256
    |
    v
Check exact duplicate
    |
    +--> duplicate -> final response
    |
    v
Azure AI Document Intelligence
    |
    v
Normalize extracted fields
    |
    v
PostgreSQL semantic duplicate comparison
    |
    +--> duplicate -> final response
    |
    v
Unique receipt
    |
    v
35-day policy check
```

Only after this backend flow is stable should the full Microsoft Teams UI integration be completed.

---

## 38. Product Principle

This is a financial workflow system, not an experimental AI demo.

Prioritize:

```text
correctness
security
auditability
clear duplicate decisions
recoverability
maintainability
user experience
```

Every implementation choice should support those priorities.
