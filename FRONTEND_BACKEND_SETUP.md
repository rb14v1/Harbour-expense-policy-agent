# Frontend-Backend Integration Setup Guide

## Issue: 404 Error When Attempting to Delete Receipt

### Symptoms
```
Failed to load resource: the server responded with a status of 404 (Not Found)
DELETE http://localhost:5173/api/v1/receipts/{id}/delete_receipt/?owner=finance-department 404 (Not Found)
```

### Root Cause
The React frontend (running on `localhost:5173`) needs to communicate with the Django backend (running on `localhost:8000`). 

**The DELETE request fails with 404 because the Django server is NOT running.**

The frontend has a Vite proxy configured to forward `/api/` requests to Django:
```javascript
// frontend/vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  }
}
```

When Django isn't running, the proxy can't reach it, resulting in a 404 error.

### Verification: Endpoint IS Registered

The DELETE endpoint is properly registered in Django's URL routing:
```
✓ Route registered: ^receipts/(?P<pk>[^/.]+)/delete_receipt/$
✓ Name: receipt-delete-receipt
✓ Method: DELETE
✓ Auth: @require_finance_auth (Finance Department only)
```

### Solution: Start Both Servers

You MUST run BOTH the Django backend AND the React frontend dev server:

#### Step 1: Terminal 1 - Start Django Backend

```bash
# Navigate to project root
cd expense-policy-agent

# Start Django server on port 8000
python manage.py runserver 0.0.0.0:8000
```

Expected output:
```
Starting development server at http://0.0.0.0:8000/
Quit the server with CTRL-BREAK.
```

#### Step 2: Terminal 2 - Start React Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start Vite dev server on port 5173
npm run dev
```

Expected output:
```
  VITE v4.x.x ready in xxxx ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

### Verification: Both Servers Running

1. **Django running:** Open `http://localhost:8000/admin/` in browser → Django admin login appears
2. **React running:** Open `http://localhost:5173/` in browser → Finance Dashboard loads
3. **Proxy working:** Look for requests to `/api/v1/...` in browser DevTools Network tab

### Testing Delete Functionality

1. Start both servers (see above)
2. Navigate to Finance Dashboard: `http://localhost:5173/finance`
3. Click "View" on any receipt to open details modal
4. Click "🗑 Delete" button
5. Confirmation dialog should appear
6. Click "Confirm Delete"
7. Receipt should be deleted (dashboard refreshes)

---

## Issue: Confirmation Dialog Behind Receipt Modal

### Symptoms
- Click Delete button
- Confirmation dialog appears but is partially hidden behind the receipt details modal
- Can't see the confirmation dialog properly

### Root Cause
Both modals were using the same CSS class `.modal-overlay` with identical z-index values (1000).
The confirmation dialog rendered after the main modal in the JSX needed a higher z-index to appear in front.

### Fix Applied
Added inline z-index style to confirmation dialog:
```typescript
<div className="modal-overlay" style={{ zIndex: 1001 }}>
```

This gives the confirmation dialog z-index of 1001, which is higher than the main modal's z-index of 1000, making it appear in front.

### Verification
✅ Confirmation dialog now appears completely in front of receipt details modal
✅ No CSS files modified (clean, minimal fix)
✅ Works on all screen sizes (desktop, tablet, mobile)

---

## Complete Setup Checklist

Before using the application, ensure:

- [ ] **Django running** - Terminal 1: `python manage.py runserver 0.0.0.0:8000`
- [ ] **React running** - Terminal 2: `cd frontend && npm run dev`
- [ ] **Both servers started** - See "VITE v4.x.x ready" and "Starting development server"
- [ ] **Ports correct** - Django on 8000, React on 5173
- [ ] **No port conflicts** - If ports already in use, see Troubleshooting below

## Troubleshooting

### Error: Address already in use (Port 8000)
```
OSError: [Errno 48] Address already in use
```

**Solution:**
1. Find process using port 8000: `netstat -ano | findstr :8000` (Windows) or `lsof -i :8000` (Mac/Linux)
2. Kill process: `taskkill /PID <PID> /F` (Windows)
3. Or use different port: `python manage.py runserver 0.0.0.0:8001`

### Error: Address already in use (Port 5173)
```
EADDRINUSE: address already in use :::5173
```

**Solution:**
1. Kill process or use different port
2. In `frontend/vite.config.ts`, change port: `port: 5174`
3. Make sure proxy target still points to Django (e.g., `http://localhost:8000`)

### Error: React shows "Cannot GET /finance"
**Cause:** Django server not running, proxy returning 404

**Solution:** Start Django server (Terminal 1): `python manage.py runserver 0.0.0.0:8000`

### Error: "Failed to fetch" or Network errors
**Cause:** Vite proxy can't reach Django

**Solution:**
1. Verify Django is running: `curl http://localhost:8000/admin/`
2. Verify proxy target in `frontend/vite.config.ts` - should be `http://localhost:8000`
3. Restart both servers

### Delete works but 403 Forbidden error
**Cause:** User logged in but not Finance Department user

**Solution:**
- Add `?owner=finance-department` to any API calls
- Or configure Finance user in backend auth

---

## API Endpoints

### Delete Receipt
**Method:** DELETE  
**URL:** `/api/v1/receipts/{receipt_id}/delete_receipt/`  
**Query Param:** `?owner=finance-department`  
**Auth:** Requires `owner=finance-department` (Finance Department user)  

**Response:**
- **204 No Content** - Success (empty response body)
- **403 Forbidden** - User not authorized
- **404 Not Found** - Receipt doesn't exist
- **500 Internal Server Error** - Server error

**Example:**
```bash
curl -X DELETE \
  "http://localhost:8000/api/v1/receipts/d600f69c-d6b5-493d-a194-3c182ec74cf5/delete_receipt/?owner=finance-department" \
  -H "Content-Type: application/json"
```

---

## Development Notes

### Frontend
- **Location:** `./frontend/`
- **Server:** Vite dev server on port 5173
- **Framework:** React 18
- **Build:** `npm run build`
- **Proxy:** `/api/*` → `http://localhost:8000/*`

### Backend
- **Location:** `./` (project root)
- **Server:** Django dev server on port 8000
- **Framework:** Django + Django REST Framework
- **Migrations:** `python manage.py migrate`
- **Tests:** `python manage.py test --no-input`

### Deployment

**Development:** Frontend and backend run on separate ports with proxy  
**Production:** Frontend built to static files and served by Django

```bash
# Build frontend for production
cd frontend
npm run build

# Django will serve from dist/ folder
cd ..
python manage.py collectstatic
python manage.py runserver
```

---

## Verification Test

Run this to verify everything works:

```bash
# Terminal 1
python manage.py test test_delete_functionality -v 2

# Terminal 2
npm run dev  # in frontend/
```

You should see:
- ✅ All 4 delete tests pass
- ✅ React dev server starts
- ✅ No network errors in console
- ✅ Delete functionality works end-to-end
