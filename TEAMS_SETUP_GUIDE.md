# Teams Bot Setup Guide

Step-by-step guide to register and test your Expense Policy Agent bot in Microsoft Teams.

## Prerequisites

- Microsoft Azure account
- Django backend running
- ngrok for local testing (https://ngrok.com/download)

---

## Step 1: Create Azure Bot Service

### 1.1 Go to Azure Portal

```
https://portal.azure.com
→ Create a resource
→ Search "Bot Service"
→ Click "Bot Service"
→ Create
```

### 1.2 Configure Bot

```
Bot handle: expense-policy-agent-dev
Subscription: (your subscription)
Resource group: (create new or use existing)
Pricing tier: Free (or Standard)
App type: Multi Tenant
```

Click **Create** and wait ~2 minutes.

### 1.3 Get Bot Credentials

After creation:

```
Settings → Configuration
```

Copy these:
- **App ID** (Microsoft App ID)
- **App Password** (Generate new secret)

### 1.4 Enable Teams Channel

```
Channels → Add Teams Channel → Save
```

---

## Step 2: Update Environment

### 2.1 Edit `.env`

```
TEAMS_APP_ID=your-app-id-from-azure
TEAMS_APP_PASSWORD=your-app-password
MICROSOFT_TENANT_ID=common
DJANGO_API_URL=http://localhost:8000/api/v1
```

### 2.2 Update Teams Manifest

Edit `teams_app/manifest.json`:

```json
{
  "id": "YOUR-APP-ID-HERE",
  "botId": "YOUR-APP-ID-HERE",
  ...
}
```

---

## Step 3: Expose Local Server (For Testing)

### 3.1 Install ngrok

```bash
# Download from https://ngrok.com/download
# On Windows, extract to a folder
# Add to PATH or run from extracted folder
```

### 3.2 Start ngrok Tunnel

```bash
ngrok http 8000
```

You'll see:
```
Forwarding                    http://xxxx-xx-xxx-xxx.ngrok.io -> http://localhost:8000
```

**Copy the `https://` URL** — you'll need it next.

### 3.3 Keep ngrok Running

Leave this terminal open. The tunnel will stay active for 8 hours.

---

## Step 4: Configure Messaging Endpoint

### 4.1 Back to Azure Portal

```
Settings → Configuration
Messaging Endpoint: https://xxxx-xx-xxx-xxx.ngrok.io/api/v1/teams/messages/
```

Click **Apply**.

### 4.2 Test Health Check

```bash
curl https://xxxx-xx-xxx-xxx.ngrok.io/api/v1/teams/health/
```

Should return:
```json
{
  "status": "ok",
  "service": "Expense Policy Agent Teams Bot",
  "version": "1.0.0"
}
```

---

## Step 5: Test with Bot Emulator

### 5.1 Download Bot Emulator

```
https://github.com/Microsoft/BotFramework-Emulator/releases
```

Download and install the latest version.

### 5.2 Open Bot Emulator

Launch the app.

### 5.3 Connect to Your Bot

```
Open Bot or Web App Chat
URL: https://xxxx-xx-xxx-xxx.ngrok.io/api/v1/teams/messages/
Microsoft App ID: (your-app-id)
Microsoft App Password: (your-password)
```

Click **Connect**.

### 5.4 Send Test Message

In the emulator chat:

```
upload receipt
```

Bot should respond:
```
Please upload your receipt file. I'll process it and check for duplicates.
```

### 5.5 Test File Upload

In emulator, use "+" to attach a file (PDF/JPG).

Bot should respond with status card.

---

## Step 6: Test in Microsoft Teams

### 6.1 Add Bot to Teams

```
Teams App Store
→ Search "Expense Policy Agent"
→ (or search by bot name)
→ Add
```

Or manually:
```
Teams → More apps → Upload custom app
→ Select teams_app/manifest.json
→ Approve when prompted
```

### 6.2 Open Bot in Teams

In Teams, find the bot in your recent apps.

Click to open 1-on-1 chat.

### 6.3 Send Messages

```
@Expense Policy Agent upload receipt
```

Bot should respond with upload instructions.

### 6.4 Upload Receipt

Click the attachment button (paperclip).

Upload a PDF/JPG receipt.

Bot should show processing status.

### 6.5 Check Status

After upload completes, you should see:

```
Receipt Status: UNIQUE
No duplicate found. Checking expense policy.
```

---

## Step 7: Deploy to Production

### 7.1 Deploy Django Backend

```bash
# Option 1: Azure App Service
git push azure main

# Option 2: Docker
docker build -t expense-policy-agent .
docker push your-registry/expense-policy-agent

# Option 3: Any WSGI host
# Deploy with gunicorn
```

### 7.2 Update Azure Bot Configuration

```
Settings → Configuration
Messaging Endpoint: https://your-domain.azurewebsites.net/api/v1/teams/messages/
```

### 7.3 Update .env on Server

```
TEAMS_APP_ID=your-production-app-id
TEAMS_APP_PASSWORD=your-production-password
DJANGO_API_URL=https://your-domain.azurewebsites.net/api/v1
USE_SQLITE=False
POSTGRES_HOST=your-postgres-server
POSTGRES_USER=postgres
POSTGRES_PASSWORD=***
```

### 7.4 Publish to Teams App Store

```bash
# Create package
mkdir ExpensePolicyAgent
cp teams_app/manifest.json ExpensePolicyAgent/
cp teams_app/assets/* ExpensePolicyAgent/
zip -r ExpensePolicyAgent.zip ExpensePolicyAgent/
```

Upload to Teams Admin Center.

---

## Troubleshooting

### Bot doesn't respond in Emulator

**Check:**
1. Django backend running: `python manage.py runserver`
2. ngrok active: `ngrok http 8000`
3. Messaging endpoint configured in Azure
4. Check Django logs for errors
5. Test health endpoint: `curl https://xxxx.ngrok.io/api/v1/teams/health/`

### "Invalid credentials"

**Fix:**
1. Get fresh App ID & Password from Azure
2. Update `.env` with correct values
3. Restart Django server
4. Reconnect in Bot Emulator

### File upload fails

**Check:**
1. File is PDF/JPG/PNG (not .txt, .doc, etc.)
2. File is < 10MB
3. Azure Blob Storage credentials in `.env`
4. Check Django logs: `python manage.py runserver`

### Bot offline in Teams

**Check:**
1. Azure Bot Service status
2. Messaging endpoint still valid
3. Django backend healthy
4. No ngrok restart (if in development)

### Status card not showing

**Check:**
1. Receipt was created in Django: `curl http://localhost:8000/api/v1/receipts/`
2. Django backend processing:
   - File validation passed
   - No Azure errors (if using OCR)
3. Check Adaptive Card JSON valid

### "Manifest invalid"

**Fix:**
1. Validate JSON: `python -m json.tool teams_app/manifest.json`
2. Check all required fields present
3. Check image URLs accessible
4. Update IDs to match Azure Bot

---

## Health Monitoring

### Check Bot Health

```bash
curl https://your-domain/api/v1/teams/health/
```

### Monitor Django Backend

```bash
# Check logs
tail -f /var/log/app.log

# Check database
python manage.py shell
>>> from receipts.models import Receipt
>>> Receipt.objects.count()
```

### Monitor Teams Activity

In Bot Emulator:
- View message traffic
- See request/response JSON
- Debug card rendering

---

## Common Commands to Test

| Command | Expected Response |
|---------|-------------------|
| "upload receipt" | Upload card |
| "check status" | Status inquiry |
| "help" | List commands |
| (send image) | Process image |
| (send PDF) | Process PDF |

---

## Security Checklist

- ✅ HTTPS only (no HTTP in production)
- ✅ Bot credentials not in code
- ✅ Teams token validation enabled
- ✅ File validation before processing
- ✅ User isolation (each user's own receipts)
- ✅ No stack traces to users

---

## Performance Tips

1. **Use PostgreSQL** in production (not SQLite)
2. **Enable Celery** for async processing
3. **Use Redis** for Celery broker
4. **Add logging** to track issues
5. **Monitor costs** on Azure (OCR calls, storage)

---

## Support Resources

- Teams Developer Docs: https://docs.microsoft.com/teams
- Bot Framework Docs: https://docs.microsoft.com/azure/bot-service
- Adaptive Cards: https://adaptivecards.io

---

## Next Steps

1. ✅ Create Azure Bot Service
2. ✅ Get credentials (App ID, Password)
3. ✅ Update `.env` and manifest.json
4. ✅ Start ngrok tunnel
5. ✅ Configure messaging endpoint
6. ✅ Test with Bot Emulator
7. ✅ Test in Teams
8. ✅ Deploy to production
9. ✅ Publish to Teams App Store

---

**Status: Ready to Deploy**

Your Teams bot is built and ready. Follow these steps to get it running!
