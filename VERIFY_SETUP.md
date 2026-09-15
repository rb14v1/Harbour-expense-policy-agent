# Verify Setup Checklist

Follow these steps to confirm everything is working correctly.

## ✅ Step 1: Environment

```bash
cd C:\Users\admin\Documents\expense-policy-agent\expense-policy-agent
```

Verify you see these files:
- ✓ manage.py
- ✓ celery_app.py
- ✓ requirements.txt
- ✓ .env.example
- ✓ config/ (directory)
- ✓ receipts/ (directory)

## ✅ Step 2: Create .env

```bash
copy .env.example .env
```

Open `.env` and ensure it has:
```
DJANGO_SECRET_KEY=any-string
DJANGO_DEBUG=True
USE_SQLITE=True
```

## ✅ Step 3: Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal.

## ✅ Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

Wait for installation to complete. You should see:
```
Successfully installed Django, djangorestframework, azure-storage-blob, ...
```

## ✅ Step 5: Run Migrations

```bash
python manage.py migrate
```

You should see:
```
Operations to perform:
  Apply all migrations: contenttypes, auth, receipts
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying receipts.0001_initial... OK
```

A `db.sqlite3` file should appear in the project root.

## ✅ Step 6: Start Server

```bash
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

## ✅ Step 7: Test API (New Terminal)

Keep the server running, open a new terminal.

```bash
curl http://localhost:8000/api/v1/receipts/
```

You should get:
```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

If you get a connection error, the server isn't running.

## ✅ Step 8: Run Tests (New Terminal)

```bash
python test_api.py
```

You should see:
```
✓ Testing File Validation Service...
✓ Testing Hashing Service...
✓ Testing Normalization Service...
✓ Testing Duplicate Detection...
✓ Testing Policy Validation...

Total: 5/5 passed
```

All tests should PASS. ✓

## 🟢 All Green?

If all steps above worked, your setup is **COMPLETE** and **WORKING**.

---

## 🔴 Troubleshooting

### "ModuleNotFoundError: No module named 'django'"

```bash
# Make sure venv is activated
venv\Scripts\activate

# Reinstall requirements
pip install -r requirements.txt
```

### "django.core.exceptions.ImproperlyConfigured"

```bash
# Make sure .env file exists
ls .env

# Make sure you're in correct directory
cd C:\Users\admin\Documents\expense-policy-agent\expense-policy-agent
```

### "sqlite3.OperationalError: unable to open database file"

```bash
# Check db.sqlite3 exists
ls db.sqlite3

# If not, run migrations again
python manage.py migrate

# If permissions issue, run as admin
```

### "Address already in use" port 8000

```bash
# Use different port
python manage.py runserver 8001
```

### "No module named 'receipts'"

```bash
# Make sure you're in project root
pwd  # should show: .../expense-policy-agent

# Check receipts directory exists
ls receipts/

# Check __init__.py exists
ls receipts/__init__.py
```

### "Test failed" errors

If any tests fail:

1. Check database exists
2. Check migrations ran: `python manage.py migrate`
3. Check .env has correct settings
4. Check no other Python processes using database

---

## 📊 What Each Test Verifies

| Test | Verifies |
|------|----------|
| File Validation | PDF/JPG validation works |
| Hashing | SHA-256 calculation consistent |
| Normalization | Data transformation correct |
| Duplicate Detection | Exact + semantic matching |
| Policy | 35-day age rule enforced |

---

## 🎉 Success Indicators

After running all checks above, you should have:

1. ✓ Virtual environment working
2. ✓ Django installed
3. ✓ Database created (db.sqlite3)
4. ✓ Migrations applied
5. ✓ Server running
6. ✓ API responding
7. ✓ All tests passing

---

## 🚀 Next: Try Uploading

Once verified, try uploading a test receipt:

```bash
# Make sure server is still running

# On PowerShell/Windows, create a test file first:
echo "test" > receipt.txt

# Use curl (install if needed: choco install curl)
curl -X POST http://localhost:8000/api/v1/receipts/upload `
  -F "file=@receipt.txt" `
  -F "owner=testuser"
```

Note: .txt files will be rejected (expected behavior).

Try with a PDF if you have one:
```bash
curl -X POST http://localhost:8000/api/v1/receipts/upload `
  -F "file=@receipt.pdf" `
  -F "owner=testuser"
```

Without Azure credentials, OCR will fail. But you'll see the file upload works and exact duplicate detection is ready.

---

## 📝 When Everything Works

You're ready to:

1. ✅ Upload receipts via API
2. ✅ Check duplicate status
3. ✅ View extracted fields
4. ✅ Validate against policies
5. ✅ Integrate with Teams (next step)

---

**Questions?** See README.md or PROJECT_STATUS.md for full documentation.
