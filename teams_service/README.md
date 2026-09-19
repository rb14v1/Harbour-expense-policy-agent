# Teams Service — Expense Policy Agent

**FastAPI-based Teams SDK service for expense receipt review**

This service handles Teams protocol using the Microsoft Teams SDK (`microsoft-teams-apps`).

## Architecture

```
Microsoft Teams
        ↓
FastAPI + Teams SDK Service (this service)
        ↓
Existing Django REST APIs
        ↓
Receipt Processing / Business Logic
```

## Quick Start

### Prerequisites

- Python 3.12+
- Django backend running on http://localhost:8000/api/v1
- Environment variables configured (.env file)

### Setup

```bash
# Install dependencies (from project root)
pip install -r requirements.txt

# Ensure .env has Teams credentials
# Required:
#   CLIENT_ID=your-client-id
#   CLIENT_SECRET=your-client-secret
#   TENANT_ID=your-tenant-id
```

### Run Teams Service

```bash
# From project root
python -m uvicorn teams_service.main:app --host 0.0.0.0 --port 8001 --reload
```

Or:

```bash
cd teams_service
python main.py
```

### Run Django Backend (Separate Terminal)

```bash
python manage.py runserver
```

### Verify Both Services Running

```bash
# Health check Teams service
curl http://localhost:8001/health

# Django
curl http://localhost:8000/api/v1/receipts/
```

## Directory Structure

```
teams_service/
├── main.py                      # FastAPI app + Teams SDK setup
├── config.py                    # Configuration from environment
├── handlers/
│   ├── __init__.py
│   └── message_handlers.py      # Teams message handling
├── cards/
│   ├── __init__.py
│   └── receipt_cards.py         # Adaptive Card generation
├── services/
│   ├── __init__.py
│   └── django_client.py         # Django REST API client
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_message_handlers.py
│   ├── test_django_client.py
│   └── test_cards.py
└── README.md
```

## Key Components

### main.py

- FastAPI application
- Teams SDK initialization using `App` from `microsoft_teams.apps`
- Configures FastAPI adapter for Teams
- Registers message handlers
- Exposes `/api/messages` endpoint (Teams webhook)

### config.py

- Loads environment variables (CLIENT_ID, CLIENT_SECRET, TENANT_ID)
- Configures Teams service host/port
- Configures Django backend URLs
- Validates required configuration

### handlers/message_handlers.py

- `FinanceMessageHandler` — handles Teams messages
- Routes based on message content
- Calls Django APIs through `django_client`
- Returns Adaptive Cards with receipt information

### services/django_client.py

- `DjangoReceiptClient` — HTTP client for Django APIs
- Async HTTP calls using `httpx`
- Methods:
  - `get_receipts()` — list receipts
  - `get_receipt_detail()` — receipt details
  - `make_receipt_decision()` — approve/reject receipt
  - `get_receipt_preview_url()` — preview endpoint

### cards/receipt_cards.py

- Adaptive Card generation
- `get_receipt_list_card()` — card for receipt list
- `get_receipt_detail_card()` — card for single receipt
- `get_decision_confirmation_card()` — confirmation after decision
- `get_error_card()` — error message card

## Teams Messaging Endpoint

**URL:** `/api/messages`

This endpoint receives all Teams activities:
- Messages
- Adaptive Card actions
- Team membership changes

The FastAPI adapter routes activities to registered handlers.

## Teams SDK Integration

### App Initialization

```python
from microsoft_teams.apps import App
from teams_service.config import config

teams_app = App(
    client_id=config.TEAMS_APP_ID,
    client_secret=config.TEAMS_APP_PASSWORD,
    tenant_id=config.TEAMS_TENANT_ID,
)
```

### Message Handler Registration

```python
@teams_app.on_message()
async def on_message(activity):
    # Handle Teams message
    return response
```

### FastAPI Adapter

```python
from microsoft_teams.apps.http import FastAPIAdapter

adapter = FastAPIAdapter(teams_app, app)
```

## Django API Integration

The Teams service calls existing Django Finance APIs:

```
GET /finance/api/receipts/              — list receipts
GET /finance/api/receipts/{receipt_id}/ — receipt details
POST /finance/api/receipts/{receipt_id}/decision/ — approve/reject
GET /api/v1/receipts/{receipt_id}/preview/ — preview file
```

All calls are async using `httpx.AsyncClient`.

## Environment Variables

```env
# Teams / Azure Entra ID
CLIENT_ID=your-app-registration-client-id
CLIENT_SECRET=your-app-registration-client-secret
TENANT_ID=your-azure-tenant-id

# Teams Service
TEAMS_SERVICE_HOST=0.0.0.0
TEAMS_SERVICE_PORT=8001

# Django Backend
DJANGO_API_URL=http://localhost:8000/api/v1
DJANGO_FINANCE_API_URL=http://localhost:8000/finance/api

# Debug
DEBUG=False
SKIP_TEAMS_AUTH=False
```

## Local Development with HTTPS Tunnel

Teams requires HTTPS and a valid domain. Use ngrok or similar:

### Terminal 1: Django Backend

```bash
python manage.py runserver
```

### Terminal 2: Teams Service

```bash
python -m uvicorn teams_service.main:app --port 8001
```

### Terminal 3: HTTPS Tunnel

```bash
ngrok http 8001
# Output: https://abc123.ngrok.io

# Configure Teams manifest:
# "messaging_endpoint": "https://abc123.ngrok.io/api/messages"
```

### Terminal 4: Expose Teams Endpoint to Teams

Register the messaging endpoint in Teams App Registration:
- Go to Azure App Registration → API permissions
- Add: Application permissions for Teams Bot Framework

## Testing

Run Teams service tests:

```bash
# Unit tests
pytest teams_service/tests/ -v

# Or with coverage
pytest teams_service/tests/ --cov=teams_service

# Or from project root
python -m pytest teams_service/tests/ -v
```

### Test Categories

- `test_config.py` — Configuration loading
- `test_message_handlers.py` — Message handling logic
- `test_django_client.py` — Django API communication
- `test_cards.py` — Adaptive Card generation

## Security

### Secrets Management

- Never commit CLIENT_SECRET
- Never print secrets in logs
- Always use environment variables
- Config displays first 8 chars only: `CLIENT_ID[:8]...`

### Authentication

- Teams SDK handles Teams authentication
- Django protects its APIs (existing mechanism)
- No raw tokens exposed to users

## Deployment

### Local Development

Run both services locally:

```bash
Terminal 1: python manage.py runserver
Terminal 2: python -m uvicorn teams_service.main:app --port 8001
```

### Docker (Optional)

```bash
# Dockerfile for Teams service would go here
# Images: python:3.12-slim, pip install -r requirements.txt
```

### Production

- Deploy Teams service separately from Django
- Use Azure Container Instances / App Service for Teams service
- Configure messaging endpoint to production domain
- Use production App Registration credentials
- Enable comprehensive logging and monitoring

## Finance Feature: Receipt Review

Teams users in Finance can:

1. **View Receipts** — See list of receipts in Teams tab
2. **Filter** — By status, category, vendor, date, amount
3. **Details** — Open receipt for full information
4. **See Duplicates** — Duplicate status and score
5. **See Policy** — Policy validation results
6. **Preview** — Download/preview receipt file
7. **Approve** — Mark receipt as APPROVED
8. **Reject** — Mark receipt as REJECTED

All actions call existing Django APIs.

## Troubleshooting

### Import Error: microsoft_teams.apps not found

```bash
pip install microsoft-teams-apps
```

### Config Error: CLIENT_ID not set

Ensure `.env` file has:
```env
CLIENT_ID=your-id
CLIENT_SECRET=your-secret
TENANT_ID=your-tenant
```

### Django API Connection Error

Check:
```bash
curl http://localhost:8000/health  # Django health
curl http://localhost:8000/finance/api/receipts/  # Finance API
```

### Teams Webhook Not Responding

- Verify `messaging_endpoint` in Teams manifest
- Check HTTPS tunnel is running
- Verify CORS/HTTPS requirements

## References

- [Microsoft Teams Apps SDK](https://microsoft.github.io/teams-ai-docs/)
- [Teams Adaptive Cards](https://adaptivecards.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure App Registration](https://learn.microsoft.com/en-us/entra/identity-platform/)

## Contact

For issues with Teams service integration, check:
1. Configuration (CLIENT_ID, CLIENT_SECRET, TENANT_ID)
2. Django backend is running and accessible
3. HTTPS tunnel is active and configured correctly
4. Teams manifest has correct messaging endpoint

