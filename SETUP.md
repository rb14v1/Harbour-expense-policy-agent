# Quick Start Setup

## Option 1: Local Development (SQLite + No External Services)

Fastest way to get running without Azure credentials initially.

### 1. Create .env file

```bash
cp .env.example .env
```

Edit `.env` and set:
```
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
USE_SQLITE=True
DJANGO_SECRET_KEY=your-dev-secret-key-change-in-production

# Skip Azure for now - will error if you try to upload
# Add these when you have Azure credentials:
# AZURE_STORAGE_CONNECTION_STRING=...
# AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=...
# AZURE_DOCUMENT_INTELLIGENCE_KEY=...
```

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Create superuser (optional, for Django admin)

```bash
python manage.py createsuperuser
```

### 5. Start server

```bash
python manage.py runserver
```

Server at: `http://localhost:8000`

Admin at: `http://localhost:8000/admin`

## Option 2: PostgreSQL Local (Production-like)

### Prerequisites
- PostgreSQL installed locally

### 1. Create .env file

```bash
cp .env.example .env
```

Edit `.env`:
```
DJANGO_DEBUG=True
POSTGRES_DB=expense_policy
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Azure credentials
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your-endpoint
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key
```

### 2. Create PostgreSQL database

```bash
psql -U postgres -c "CREATE DATABASE expense_policy;"
```

### 3. Install & run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Option 3: With Celery + Redis (Full Setup)

For async processing when you need it later.

### 1. Install Redis

- **Mac**: `brew install redis`
- **Windows**: Use Windows Subsystem for Linux or Docker
- **Linux**: `apt-get install redis-server`

### 2. Update .env

```
REDIS_URL=redis://localhost:6379/0
```

### 3. Start Redis

```bash
redis-server
```

### 4. Install Celery (already in requirements.txt)

### 5. Start Celery worker (separate terminal)

```bash
celery -A celery_app worker --loglevel=info
```

### 6. Django will automatically use Celery for async tasks

## Testing the API

### Upload Receipt

```bash
curl -X POST http://localhost:8000/api/v1/receipts/upload \
  -F "file=@receipt.pdf" \
  -F "owner=user1"
```

### Check Status

```bash
curl http://localhost:8000/api/v1/receipts/<receipt-id>/
```

### List Receipts

```bash
curl "http://localhost:8000/api/v1/receipts/?owner=user1"
```

## Troubleshooting

### "django.core.exceptions.ImproperlyConfigured"

Make sure:
- You're in the project root directory
- `.env` file exists
- DJANGO_SETTINGS_MODULE is set (should be automatic)

### "psycopg connection refused"

PostgreSQL not running. Either:
- Start PostgreSQL service
- Switch to SQLite: set `USE_SQLITE=True` in .env

### "ModuleNotFoundError: No module named 'receipts'"

Make sure you're in the correct directory and have run migrations.

### Azure errors on upload

You need Azure credentials in `.env`. Get them from:
- Azure Storage Account connection string
- Azure AI Document Intelligence endpoint + key

For testing without Azure, file validation happens first, so invalid files fail before Azure calls.

## Database Reset

To start fresh:

**SQLite:**
```bash
rm db.sqlite3
python manage.py migrate
```

**PostgreSQL:**
```bash
dropdb expense_policy
createdb expense_policy
python manage.py migrate
```

## Admin Interface

Navigate to `http://localhost:8000/admin` (after creating superuser).

Browse and manage receipts with filtering by status, vendor, date.

## Next Steps

1. Add Azure credentials to `.env`
2. Test full receipt upload flow
3. Deploy to Azure App Service
4. Set up Teams integration layer
5. Add authentication with Azure AD
