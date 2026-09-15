# Quick Start - 5 Minutes to Running

## Step 1: Copy Environment Config

```bash
cd C:\Users\admin\Documents\expense-policy-agent\expense-policy-agent
copy .env.example .env
```

Edit `.env` and set (minimum required):
```
DJANGO_SECRET_KEY=any-random-string-here
DJANGO_DEBUG=True
USE_SQLITE=True
```

That's it. Other values have defaults.

## Step 2: Install & Migrate

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

## Step 3: Start Server

```bash
python manage.py runserver
```

Visit: `http://localhost:8000`

## Step 4: Verify (Optional)

In another terminal:
```bash
python test_api.py
```

You should see all tests pass ✓

---

## That's It! 🎉

Your API is now running at: **http://localhost:8000/api/v1/receipts/**

### Try uploading a receipt:

```bash
# On Windows (PowerShell)
$file = Get-Item "C:\path\to\receipt.pdf"
$fileBytes = [System.IO.File]::ReadAllBytes($file.FullName)
$boundary = [System.Guid]::NewGuid().ToString()
$body = @"
--$boundary
Content-Disposition: form-data; name="file"; filename="receipt.pdf"
Content-Type: application/pdf

"@
# For simplicity, use curl instead:

# On Mac/Linux (or Windows with curl installed):
curl -X POST http://localhost:8000/api/v1/receipts/upload \
  -F "file=@receipt.pdf" \
  -F "owner=myuser"
```

Response:
```json
{
  "receipt_id": "12345678-1234-5678-1234-567812345678",
  "status": "UNIQUE",
  "message": "Receipt processed successfully.",
  "is_final": true
}
```

### Check status:

```bash
curl http://localhost:8000/api/v1/receipts/12345678-1234-5678-1234-567812345678/
```

---

## With Azure (Optional)

When ready to use real OCR and file storage:

1. Get Azure credentials:
   - Blob Storage connection string
   - Document Intelligence endpoint + key

2. Update `.env`:
```
USE_SQLITE=False
POSTGRES_DB=expense_policy
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://xxx.api.cognitive.microsoft.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key
```

3. Set up PostgreSQL locally (or use Azure Database for PostgreSQL)

4. Migrate database:
```bash
python manage.py migrate
```

5. Restart server

Now uploads will:
- Store original files in Azure Blob
- Call Azure AI Document Intelligence for OCR
- Extract vendor, invoice number, date, amounts
- Check for duplicates
- Validate policy rules

---

## Troubleshooting

### "Module not found" errors
- Make sure you're in the correct directory
- Make sure venv is activated
- Run `pip install -r requirements.txt` again

### "Port 8000 already in use"
```bash
python manage.py runserver 8001
```

### "Database locked" (SQLite)
- Close all other Python processes
- Delete `db.sqlite3` and re-migrate if stuck

### Need to reset database?
```bash
# SQLite
rm db.sqlite3
python manage.py migrate

# PostgreSQL
dropdb expense_policy
createdb expense_policy
python manage.py migrate
```

---

## Admin Interface

After creating a superuser (optional):
```bash
python manage.py createsuperuser
```

Visit: `http://localhost:8000/admin`

Browse and manage receipts manually.

---

## API Documentation

Full docs in `README.md`

Key endpoints:
- `POST /api/v1/receipts/upload` — Upload receipt
- `GET /api/v1/receipts/` — List receipts
- `GET /api/v1/receipts/{id}/` — Get status
- `GET /api/v1/receipts/{id}/details` — Get full details

---

**Want more details?** See:
- `README.md` — Full API reference
- `SETUP.md` — Installation options
- `CLAUDE.md` — Architecture specification
- `PROJECT_STATUS.md` — What's implemented
