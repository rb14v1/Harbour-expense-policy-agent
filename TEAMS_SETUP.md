# Teams Integration Setup Guide

## Overview

The Expense Policy Agent is integrated with Microsoft Teams to provide:

1. **Employee Experience**: Upload expense receipts directly from Teams with automatic duplicate detection
2. **Finance Review Tab**: Finance Department reviews, approves, or rejects receipts in Teams
3. **Django Backend**: All business logic (OCR, duplicate detection, policy validation) remains in Django

The Teams layer is thin and stateless, calling Django REST APIs for all business operations.

---

## Architecture

```
Teams Client
    |
    +-- Employee: Upload Receipt
    |       |
    |       v
    |   Teams Bot (messages webhook)
    |       |
    |       v
    |   Django: POST /api/v1/teams/upload/
    |
    +-- Finance: Review Tab (static tab)
            |
            v
        Finance Dashboard (HTML/JS)
            |
            v
        Django: GET /finance/api/receipts/
                POST /finance/api/receipts/{id}/decision/
                GET /api/v1/receipts/{id}/preview/

All receipt processing (OCR, hashing, duplicate detection) happens in Django.
Teams is purely a UI/integration layer.
```

---

## Prerequisites

1. **Azure Account** with:
   - Azure App Registration created (for Teams app identity)
   - CLIENT_ID, CLIENT_SECRET, TENANT_ID available
   - Resource Group for Azure services

2. **Local Environment**:
   - Python 3.11+
   - PostgreSQL (or SQLite for development)
   - Django 5.1.3+

3. **Microsoft Teams**:
   - Teams client (desktop or web)
   - Access to sideload apps (non-production Teams environment recommended)

4. **Network**:
   - HTTPS tunnel for local development (ngrok, localtunnel, or dev tunnel)

---

## Step 1: Create Azure App Registration

### In Azure Portal:

1. Go to **Azure Entra ID** → **App Registrations**
2. Click **New registration**
3. Fill in:
   - **Name**: `V1-BusinessApplication-ExpensePolicyAgent-Dev`
   - **Supported account types**: Single tenant
   - **Redirect URI** (leave empty for now)
4. Click **Register**
5. On the **Overview** page, copy:
   - **Application (client) ID** → `CLIENT_ID`
   - **Directory (tenant) ID** → `TENANT_ID`

6. Go to **Certificates & secrets** → **Client secrets** → **New client secret**
   - Add description: "Teams Bot Secret"
   - Set expiration: 24 months (or per your policy)
   - Copy the **Value** → `CLIENT_SECRET`
   - **Never commit this secret to Git**

7. Go to **API permissions** → **Add a permission**
   - Select **Microsoft Graph** → **Delegated permissions**
   - Add: `TeamsAppInstallation.ReadWriteForTeam`, `TeamsAppInstallation.ReadWrite.All`
   - Click **Grant admin consent**

---

## Step 2: Configure Environment Variables

### Create `.env` file (never commit):

```env
# Django Configuration
DJANGO_SECRET_KEY=generate-a-secure-random-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,*.ngrok.io

# PostgreSQL Configuration (or use SQLite for dev)
POSTGRES_DB=expense_policy
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-postgres-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Azure Storage (Blob Storage)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER_NAME=receipts

# Azure AI Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://<region>.api.cognitive.microsoft.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key-here

# Teams / Azure Entra ID (from App Registration)
CLIENT_ID=your-client-id-here
CLIENT_SECRET=your-client-secret-here
TENANT_ID=your-tenant-id-here

# Teams Service Configuration
TEAMS_SERVICE_URL=https://smba.trafficmanager.net/apis/

# Local Development
DJANGO_API_URL=http://localhost:8000/api/v1
USE_SQLITE=False

# Receipt Processing
MAX_RECEIPT_UPLOAD_MB=10
RECEIPT_MAX_AGE_DAYS=35

# Duplicate Detection
DUPLICATE_SCORE_THRESHOLD=90
REVIEW_SCORE_THRESHOLD=75

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,https://*.ngrok.io
```

**⚠️ SECURITY**: Never commit `.env`. Use `.env.example` for template values.

---

## Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or create a virtual environment first
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Step 4: Start Django Backend

```bash
# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver 0.0.0.0:8000
```

**Output should show:**
```
Starting development server at http://0.0.0.0:8000/
```

---

## Step 5: Set Up HTTPS Tunnel for Local Development

Teams requires HTTPS and valid domain. Use a tunnel:

### Option A: ngrok (recommended)

```bash
# Download from https://ngrok.com/download

# Start ngrok tunnel (in a new terminal)
ngrok http 8000

# You'll see output like:
# https://abc123.ngrok.io -> http://localhost:8000
```

Copy the HTTPS URL: `https://abc123.ngrok.io`

### Option B: localtunnel

```bash
npm install -g localtunnel

# Start tunnel
lt --port 8000 --subdomain expense-policy-dev

# You'll see:
# your url is: https://expense-policy-dev.loca.lt
```

### Option C: Dev Tunnel (if using Visual Studio)

```bash
devtunnel host run --allow-anonymous
```

---

## Step 6: Update Teams Manifest

Edit `teams_app/manifest.json` and replace placeholders:

```json
{
  "id": "YOUR_CLIENT_ID_HERE",
  "bots": [
    {
      "botId": "YOUR_CLIENT_ID_HERE"
    }
  ],
  "validDomains": [
    "abc123.ngrok.io",
    "localhost:8000",
    "localhost:3000"
  ],
  "webApplicationInfo": {
    "id": "YOUR_CLIENT_ID_HERE",
    "resource": "api://abc123.ngrok.io/YOUR_CLIENT_ID_HERE"
  }
}
```

---

## Step 7: Package Teams App

Create a ZIP file with:

```
manifest.json
assets/
  color.png       (192x192 px)
  outline.png     (32x32 px)
```

**Example folder structure:**
```
expense-policy-app.zip
├── manifest.json
└── assets/
    ├── color.png
    └── outline.png
```

Generate icons if needed:
- Create 192x192 PNG (color) and 32x32 PNG (outline) images
- Place them in `teams_app/assets/` directory

---

## Step 8: Sideload Teams App

### In Teams (development environment):

1. Open **Teams**
2. Click **Apps** → **Manage your apps**
3. Click **Upload a custom app** (if available)
4. Select your `expense-policy-app.zip`
5. Review and click **Add**

**Alternatively (if upload not available):**

1. Go to **Teams Admin Center** (requires admin access)
2. Navigate to **Teams apps** → **Manage apps**
3. Upload custom app
4. Approve for use

---

## Step 9: Verify Integration

### Test Teams Bot (Employee Upload)

1. Open Teams
2. Go to **Expense Policy Agent** app
3. Click **Chat** or send a message
4. Type: `upload receipt`
5. You should see: "Please upload your receipt file..."

### Test Finance Tab

1. Go to your Team channel
2. Click **+** to add a tab
3. Search for "Expense Policy Agent"
4. Select **Finance Review** tab
5. You should see the Finance dashboard with receipt list

### Test Receipt Upload (via Bot)

1. Use the upload action in Teams
2. Select a receipt file (PDF/JPG/PNG)
3. Receipt should appear in Finance tab

### Test Finance Decision

1. In Finance tab, click a receipt
2. Click **View Details**
3. Click **Approve** or **Reject**
4. Status should update immediately

---

## API Endpoints Reference

### Employee Flow

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/teams/messages/` | POST | Receive Teams bot messages |
| `/api/v1/teams/upload/` | POST | Employee receipt upload |
| `/api/v1/teams/receipts/{id}/status/` | GET | Receipt processing status |
| `/api/v1/receipts/{id}/preview/` | GET | View receipt file |

### Finance Flow

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/finance/api/receipts/` | GET | List all receipts (with filters) |
| `/finance/api/receipts/{id}/` | GET | Receipt details |
| `/finance/api/receipts/{id}/decision/` | POST | Approve/reject receipt |
| `/api/v1/teams/finance/tab/config/` | GET | Finance tab configuration |

### Filters for `/finance/api/receipts/`

Query parameters:
- `status`: UNIQUE, EXACT_DUPLICATE, SEMANTIC_DUPLICATE, APPROVED, REJECTED, etc.
- `category`: Expense category
- `vendor`: Vendor name (partial match)
- `filename`: Receipt filename (partial match)
- `date_from`: Transaction date range start (YYYY-MM-DD)
- `date_to`: Transaction date range end (YYYY-MM-DD)
- `amount_min`: Minimum amount
- `amount_max`: Maximum amount
- `page`: Page number (default: 1)

Example:
```
GET /finance/api/receipts/?status=UNIQUE&category=Food&date_from=2026-01-01&page=1
```

### Decision Endpoint

```
POST /finance/api/receipts/{receipt_id}/decision/

{
  "decision": "APPROVED" | "REJECTED",
  "notes": "optional notes"
}

Response:
{
  "id": "uuid",
  "status": "APPROVED" | "REJECTED",
  "vendor_name": "...",
  "total_amount": "...",
  ...
}
```

---

## Environment Variables (Complete Reference)

| Variable | Required | Purpose | Example |
|----------|----------|---------|---------|
| `CLIENT_ID` | Yes | Teams app client ID | `08923630-1eab-4fed-...` |
| `CLIENT_SECRET` | Yes | Teams app client secret (DO NOT COMMIT) | `7Ge8Q~Tq8G~...` |
| `TENANT_ID` | Yes | Azure tenant ID | `3e0088dc-0629-4ae6-...` |
| `DJANGO_SECRET_KEY` | Yes | Django secret key | Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DJANGO_DEBUG` | No | Debug mode (False for production) | `True` |
| `DJANGO_ALLOWED_HOSTS` | No | Allowed domains | `localhost,127.0.0.1,*.ngrok.io` |
| `AZURE_STORAGE_CONNECTION_STRING` | Yes | Azure Blob connection | `DefaultEndpointsProtocol=https;...` |
| `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | Yes | Document Intelligence endpoint | `https://prompt.cognitiveservices.azure.com/` |
| `AZURE_DOCUMENT_INTELLIGENCE_KEY` | Yes | Document Intelligence key | `E9QflhaM5Uuf...` |
| `POSTGRES_HOST` | Yes | PostgreSQL host | `localhost` or `db.example.com` |
| `POSTGRES_USER` | Yes | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Yes | Database password | (never hardcode) |
| `POSTGRES_DB` | Yes | Database name | `expense_policy` |
| `CORS_ALLOWED_ORIGINS` | No | CORS origins | `http://localhost:3000,https://teams.microsoft.com` |

---

## Troubleshooting

### Teams Bot Not Responding

**Check:**
1. HTTPS tunnel is running: `ngrok http 8000`
2. Django is running: `python manage.py runserver`
3. Manifest has correct domain (no trailing slash)
4. Environment variables loaded: `echo $CLIENT_ID` (should show your ID)

**Debug:**
```bash
# Check Teams endpoint health
curl -X GET http://localhost:8000/api/v1/teams/health/
# Should return: {"status": "ok", "service": "Expense Policy Agent Teams Bot"}
```

### Finance Tab Not Loading

**Check:**
1. Teams manifest has Finance tab in `staticTabs` section
2. Content URL is accessible: `https://your-domain/finance/tab`
3. Django app sideloaded with correct manifest
4. Browser console shows no CORS errors

**Debug:**
```bash
# Test Finance API endpoint
curl -X GET http://localhost:8000/finance/api/receipts/
# Should return JSON array of receipts
```

### Receipt Upload Fails

**Check:**
1. File size under 10MB (default limit)
2. File type is PDF, JPG, JPEG, or PNG
3. Azure Blob Storage connection string is valid
4. Django logs show no errors

**Debug:**
```bash
# Check file validation
curl -X POST http://localhost:8000/api/v1/teams/upload/ \
  -F "file=@receipt.pdf" \
  -F "user_id=test-user"
```

### CORS Errors

**Check:**
1. `CORS_ALLOWED_ORIGINS` in `.env` includes Teams domain
2. Django CORS middleware is configured
3. Check browser console for exact origin

**Fix:**
```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,https://teams.microsoft.com,https://*.ngrok.io
```

---

## Production Deployment

### Before Going Live

1. **Security**:
   - Set `DJANGO_DEBUG=False`
   - Generate strong `DJANGO_SECRET_KEY`
   - Use Azure Key Vault for secrets (never in code)
   - Enable HTTPS only

2. **Configuration**:
   - Update `DJANGO_ALLOWED_HOSTS` with production domain
   - Configure `CORS_ALLOWED_ORIGINS` for Teams production
   - Update Teams manifest with production domain
   - Set `TEAMS_SERVICE_URL` to production endpoint

3. **Database**:
   - Use managed PostgreSQL (Azure Database for PostgreSQL)
   - Configure backups
   - Enable encryption at rest

4. **Deployment**:
   - Use gunicorn or similar WSGI server
   - Configure reverse proxy (nginx/Apache)
   - Enable logging and monitoring
   - Set up health checks

5. **Teams Registration**:
   - Register app in Microsoft Teams Admin Center
   - Obtain production app ID and credentials
   - Update manifest with production values

### Example Production Deployment (Azure App Service)

```bash
# Build container
docker build -t expense-policy-agent:latest .

# Deploy to Azure App Service
az appservice up --name expense-policy-prod --resource-group my-rg
```

---

## Testing

### Unit Tests

```bash
# Run existing receipt tests
python manage.py test receipts

# Run finance tests
python manage.py test finance

# Run Teams app tests
python manage.py test teams_app
```

### Integration Tests

```bash
# Test end-to-end flow
python test_end_to_end_upload.py

# Test Teams bot messages
python test_teams_bot.py

# Test Finance decision
curl -X POST http://localhost:8000/finance/api/receipts/{receipt_id}/decision/ \
  -H "Content-Type: application/json" \
  -d '{"decision": "APPROVED", "notes": "looks good"}'
```

---

## Support & Documentation

- **Teams Development**: https://learn.microsoft.com/en-us/microsoftteams/platform/
- **Bot Framework**: https://learn.microsoft.com/en-us/azure/bot-service/
- **Django Documentation**: https://docs.djangoproject.com/
- **Azure Services**: https://learn.microsoft.com/en-us/azure/
