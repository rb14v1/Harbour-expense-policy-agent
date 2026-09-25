# Expense Policy Agent

Production-ready Django backend for processing expense receipts with Microsoft Teams integration, Azure Blob Storage, and Azure AI Document Intelligence.

## Architecture Overview

- **Frontend**: Microsoft Teams + Teams SDK
- **Backend**: Django REST Framework
- **Database**: PostgreSQL
- **Storage**: Azure Blob Storage
- **OCR**: Azure AI Document Intelligence
- **Background Processing**: Celery + Redis

## Core Flow

```
Upload Receipt
    ↓
Calculate SHA-256 hash
    ↓
Exact duplicate check (PostgreSQL)
    ├─ Duplicate found? → Reject
    └─ Unique? → Continue
    ↓
Azure AI Document Intelligence (OCR)
    ↓
Normalize extracted fields
    ↓
Semantic duplicate check
    ├─ Duplicate found? → Reject
    └─ Unique? → Continue
    ↓
Policy validation (35-day age rule)
    ├─ Pass? → Approve
    └─ Fail? → Reject
```

## Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis (for Celery)
- Azure Storage Account
- Azure AI Document Intelligence
- Microsoft Teams / Entra setup

## Setup

### 1. Environment Setup

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Update `.env` with your Azure credentials and database details.

### 3. Database Setup

```bash
python manage.py migrate
```

Create superuser for admin:

```bash
python manage.py createsuperuser
```

### 4. Run Django Development Server

```bash
python manage.py runserver
```

Server runs on `http://localhost:8000`

### 5. Run Celery Worker (in separate terminal)

```bash
celery -A celery_app worker --loglevel=info
```

### 6. Frontend Development (React + Vite)

The web frontend is being migrated from Django templates to React. During development, both can run side-by-side.

#### Start React Development Server

```bash
cd frontend
npm install
npm run dev
```

React development server runs on `http://localhost:5173`

#### Build React for Production

```bash
cd frontend
npm run build
```

Output goes to `frontend/dist/`

#### Environment Configuration

Copy `frontend/.env.example` to `frontend/.env`:

```bash
cp frontend/.env.example frontend/.env
```

During local development, React proxies API calls to Django on `http://localhost:8000`.

#### Current Status

- **Phase 1**: React + Vite foundation complete
- **Existing Django templates**: Still active at `http://localhost:8000`
- **React pages**: Available at `http://localhost:5173/upload` and `http://localhost:5173/finance` (placeholder UI only)
- **Teams bot**: Unchanged; still uses Adaptive Cards
- **Backend APIs**: Unchanged; serve both Django and React frontends

## API Endpoints

### Upload Receipt

```
POST /api/v1/receipts/upload
Content-Type: multipart/form-data

file: <binary file>
owner: user-id (optional, defaults to "default-user")
```

Response:
```json
{
  "receipt_id": "uuid",
  "status": "QUEUED_FOR_OCR",
  "message": "Receipt uploaded successfully and is being processed.",
  "is_final": false
}
```

### Check Receipt Status

```
GET /api/v1/receipts/{receipt_id}
```

Response:
```json
{
  "id": "uuid",
  "status": "UNIQUE",
  "stage": "policy",
  "is_final": false,
  "message": "No duplicate found. Checking expense policy.",
  "duplicate_score": null,
  "policy_status": null
}
```

### List User Receipts

```
GET /api/v1/receipts/?owner=user-id
```

### Get Full Receipt Details

```
GET /api/v1/receipts/{receipt_id}/details
```

## Statuses

- `UPLOADED` — File uploaded
- `HASHING` — Calculating SHA-256
- `EXACT_DUPLICATE` — Same file already exists
- `QUEUED_FOR_OCR` — Waiting for processing
- `OCR_PROCESSING` — Extracting fields
- `EXTRACTED` — Fields extracted
- `NORMALIZED` — Data normalized
- `DUPLICATE_CHECKING` — Comparing with existing receipts
- `SEMANTIC_DUPLICATE` — Business duplicate found
- `UNIQUE` — No duplicate
- `POLICY_PROCESSING` — Validating policies
- `APPROVED` — Receipt approved
- `REJECTED` — Receipt rejected by policy
- `FAILED` — Processing failed

## Testing

Run test suite:

```bash
python manage.py test receipts
```

## Services

### FileValidationService
Validates file type and size.

### HashingService
Calculates SHA-256 hash of file content for exact duplicate detection.

### BlobService
Uploads/downloads receipts from Azure Blob Storage.

### DocumentIntelligenceService
Calls Azure AI Document Intelligence for OCR and field extraction.

### NormalizationService
Converts Azure output to stable internal JSON contract.

### DuplicateService
Performs semantic duplicate detection using:
- Invoice + Vendor (strong signal)
- Vendor + Date + Amount (fallback)
- Weighted scoring (0-100)

### PolicyService
Validates receipt against policy rules (currently: 35-day age limit).

### ReceiptService
Orchestrates upload and processing workflows.

## Configuration

Key environment variables:

- `DJANGO_SECRET_KEY` — Secret for Django
- `POSTGRES_*` — PostgreSQL connection
- `AZURE_STORAGE_CONNECTION_STRING` — Blob Storage
- `AZURE_DOCUMENT_INTELLIGENCE_*` — OCR credentials
- `MAX_RECEIPT_UPLOAD_MB` — Max file size (default: 10)
- `RECEIPT_MAX_AGE_DAYS` — Policy age limit (default: 35)
- `DUPLICATE_SCORE_THRESHOLD` — Duplicate threshold (default: 90)
- `REVIEW_SCORE_THRESHOLD` — Review threshold (default: 75)

## Database Models

### Receipt

Complete receipt record including:
- File metadata (hash, blob reference)
- Extracted OCR fields
- Normalized data (JSONB)
- Duplicate tracking (exact + semantic)
- Policy validation results

See `receipts/models.py` for full schema.

## Admin Interface

Access Django admin at `/admin` with superuser credentials.

Browse/manage receipts with filtering by status, date, vendor.

## Error Handling

System raises controlled exceptions:

- `UnsupportedFileTypeError` — Invalid file type
- `ReceiptTooLargeError` — File exceeds size limit
- `BlobUploadError` — Azure Blob upload failed
- `DocumentExtractionError` — OCR failed
- `ReceiptNormalizationError` — Normalization failed
- `DuplicateReceiptError` — Duplicate detected
- `PolicyValidationError` — Policy check failed

## Security

- Secrets in environment variables only
- PostgreSQL parameterized queries
- File validation before upload
- Private Blob Storage containers
- Safe filename handling
- HTTPS in production

## Next Steps

1. Teams app integration layer
2. User authentication (Azure AD)
3. Additional policy rules
4. Approval workflows
5. Notification system
6. Analytics dashboard
