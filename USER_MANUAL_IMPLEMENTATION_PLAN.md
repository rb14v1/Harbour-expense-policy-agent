# User Manual Feature - Implementation Plan

## Project Analysis Summary

### Current Architecture
- **Frontend**: Django with HTML template (`receipts/templates/receipts/upload.html`)
- **Backend**: Django REST Framework with ViewSets (`receipts/views.py`)
- **Storage**: Azure Blob Storage (via `BlobService` with connection string auth)
- **Teams Integration**: Bot handler (`teams_app/bot_handler.py`) + Finance Tab (`teams_app/finance_tab.py`)
- **Data Model**: Receipt model with statuses and categories defined

### Actual Implemented Workflows

**Employee Workflow** (from code inspection):
1. Upload receipt via HTML form (upload.html)
2. POST to `/api/v1/receipts/` endpoint
3. File validation + Blob Storage upload
4. SHA-256 hash calculation
5. Exact duplicate check
6. If unique: Queue for OCR processing
7. Azure Document Intelligence OCR + extraction
8. Receipt data normalization
9. Semantic duplicate checking
10. Policy validation (35-day rule + category)
11. Status updates returned via API
12. Frontend polls `/api/v1/receipts/{id}/` for status
13. Final status shown (APPROVED/REJECTED/NEEDS_REVIEW/etc.)

**Finance Workflow** (from code inspection):
1. Access Finance Tab in Teams (via manifest)
2. Finance dashboard displays pending receipts
3. Finance user selects receipt for review
4. Adaptive Card shows receipt details
5. Finance user approves or rejects via card buttons
6. Decision posted to backend
7. Receipt status updated
8. Employee sees updated status

### Actual Receipt Statuses (from models.py)
- UPLOADED, HASHING, EXACT_DUPLICATE, QUEUED_FOR_OCR
- OCR_PROCESSING, OCR_FAILED, EXTRACTED, NORMALIZED
- DUPLICATE_CHECKING, SEMANTIC_DUPLICATE, UNIQUE
- POLICY_PROCESSING, APPROVED, REJECTED, NEEDS_REVIEW
- FAILED

### Actual Category Choices
44 categories including Transport, Food, Accommodation, various mileage rates per region, etc.

---

## Implementation Plan

### Phase 1: Create User Manual HTML Document

**File**: `expense_policy_agent_user_manual.html`

**Content Sections**:
1. **Introduction** - What it does, who uses it
2. **Employee Workflow** - Complete upload to final status (with diagram)
3. **Expense Statuses** - Table mapping status → meaning → employee action → finance action
4. **Finance Workflow in Teams** - How finance approves/rejects (with diagram)
5. **Common Scenarios** - 8-10 realistic situations with solutions
6. **FAQ** - 10-15 practical Q&A
7. **Quick Reference** - 1-page employee summary, 1-page finance summary, glossary

**Features**:
- Responsive HTML5
- Table of contents with anchor links
- Embedded SVG diagrams
- Professional styling
- Mobile-friendly
- No embedded images (avoids maintenance)
- No secrets/credentials

**Verification**: All workflows match actual code behavior

---

### Phase 2: Azure Blob Storage Integration

**Upload Process**:
1. Create utility function in `receipts/services/blob_service.py` to upload manual
2. Upload manual to: `documentation/expense_policy_agent_user_manual.html`
3. Set content-type: `text/html; charset=utf-8`
4. Make idempotent (overwrite on each update)
5. No changes to receipt container/security

**Configuration**:
- Reuse existing `AZURE_STORAGE_CONNECTION_STRING` and `AZURE_STORAGE_CONTAINER_NAME`
- Store path in settings: `MANUAL_BLOB_PATH = "documentation/expense_policy_agent_user_manual.html"`

**Deployment Script**:
- Create management command: `python manage.py upload_user_manual`
- Idempotent (safe to run multiple times)
- Verify upload succeeded before completing

---

### Phase 3: Backend Endpoints

**New Endpoint 1**: Retrieve Manual
```
GET /api/v1/user-manual/
Response: Streaming HTML file or 200 with content-type text/html
```

**Implementation**:
- New view in `receipts/views.py` or dedicated `user_manual/views.py`
- Download from Blob Storage
- Set correct content-type header
- Handle missing manual gracefully (404)
- Cache-friendly headers

**New Endpoint 2** (Optional): Manual metadata
```
GET /api/v1/user-manual/info/
Response: {"available": true, "last_updated": "2026-10-14T..."}
```

---

### Phase 4: Frontend Integration

**Location**: Upload page (`receipts/templates/receipts/upload.html`)

**Add**:
- "User Manual" link/button near top of page (e.g., next to "Upload Receipt" heading)
- Click handler fetches manual from `/api/v1/user-manual/`
- Display in modal or new container
- Smooth transitions
- Close button returns to main view
- Responsive (works on mobile)

**Implementation**:
- Minimal JavaScript (fetch + modal toggle)
- Reuse existing styling if possible
- No new dependencies

---

### Phase 5: Microsoft Teams Integration

**Where**: Finance Tab + Bot conversations

**Option A: Finance Tab** (Primary)
- Add "User Manual" link in Finance Dashboard card/toolbar
- Click opens browser to `/api/v1/user-manual/` (Teams will render in web view)

**Option B: Bot Conversation** (Secondary)
- If employee or finance messages bot: include "View User Manual" as card action
- Use OpenURL action to `https://{deployed-domain}/api/v1/user-manual/`

**Implementation**:
- No changes to existing Teams action handlers
- Add link in Finance Tab header or footer
- Test in Teams client

---

### Phase 6: Testing

**Manual Content Verification**:
- [ ] All documented statuses exist in models.py
- [ ] Employee workflow matches actual code flow
- [ ] Finance workflow matches actual bot/handler implementation
- [ ] Diagrams are accurate

**Azure Blob Storage**:
- [ ] Manual uploads successfully
- [ ] Repeated uploads replace the file
- [ ] Content-type is text/html
- [ ] File is not world-readable (respects container security)

**Backend Endpoint**:
- [ ] GET `/api/v1/user-manual/` returns 200 with HTML
- [ ] Content-Type header is correct
- [ ] Missing manual returns 404
- [ ] Unauthenticated access is allowed (or meets security requirements)

**Frontend**:
- [ ] Manual link is visible on upload page
- [ ] Click opens manual in modal
- [ ] Manual renders correctly
- [ ] Close button works
- [ ] Responsive on mobile

**Teams**:
- [ ] Finance Tab loads without errors
- [ ] Manual link/action is visible
- [ ] Click opens manual (browser view in Teams)
- [ ] Existing finance actions still work

**End-to-End**:
- [ ] Employee uploads receipt → sees "User Manual" link → opens manual → understands workflow
- [ ] Finance team accesses Teams → sees "User Manual" option → opens → understands approval process

---

## Files To Create/Modify

### Create:
1. `expense_policy_agent_user_manual.html` (Main manual document)
2. `receipts/management/commands/upload_user_manual.py` (Deployment helper)
3. `receipts/tests/test_user_manual.py` (Tests)

### Modify:
1. `receipts/services/blob_service.py` - Add utility method for manual upload
2. `receipts/views.py` - Add endpoint for manual retrieval
3. `receipts/templates/receipts/upload.html` - Add "User Manual" link + modal
4. `config/settings.py` - Add `MANUAL_BLOB_PATH` setting
5. `teams_app/finance_tab.py` - Add manual link/action (optional)

### No Changes:
- Database models (no manual table)
- Authentication/authorization (reuse existing)
- Receipt processing logic
- Azure configuration (reuse existing)

---

## Key Decisions

**1. Where to store manual**:
- Chosen: Azure Blob Storage (existing infrastructure)
- Rationale: Centralized, versioned, accessible to Teams

**2. Frontend access method**:
- Chosen: Backend endpoint that downloads from Blob
- Rationale: Avoids exposing storage URLs, enables caching, consistent with existing patterns

**3. HTML format**:
- Chosen: Pure HTML5 (no embedded media)
- Rationale: Lightweight, renders everywhere, easy to maintain

**4. Teams access**:
- Chosen: OpenURL action pointing to backend endpoint
- Rationale: Works reliably in Teams clients, no special SDK needed

**5. Authentication**:
- Chosen: Allow unauthenticated access (or match app's existing pattern)
- Rationale: User manual is help resource, not sensitive data

---

## Deployment Checklist

- [ ] Review implementation plan (THIS DOCUMENT)
- [ ] Create HTML manual document
- [ ] Add backend endpoint
- [ ] Add frontend modal
- [ ] Test locally
- [ ] Add Teams integration
- [ ] Run test suite
- [ ] Deploy management command: `python manage.py upload_user_manual`
- [ ] Verify manual in Blob Storage
- [ ] Test in Teams (if available)
- [ ] Document any deployment configuration needed
- [ ] Update project README with manual access info

---

## Estimated Effort

| Task | Effort | Duration |
|------|--------|----------|
| Create HTML manual | Medium | 3-4 hours |
| Backend endpoint | Low | 30-45 min |
| Frontend integration | Low | 1-2 hours |
| Teams integration | Low | 30-45 min |
| Testing | Medium | 1-2 hours |
| **Total** | | **7-10 hours** |

---

## Success Criteria

✅ User can access comprehensive manual from both web frontend and Teams
✅ Manual accurately documents actual workflows and statuses
✅ Manual uploads to Azure Blob Storage
✅ All tests pass
✅ No existing functionality broken
✅ Manual renders correctly on desktop and mobile
✅ Finance workflow documentation is accurate and helpful

---

## Dependencies & Prerequisites

- Azure Storage account configured (already exists)
- Teams deployment environment (for Teams testing)
- HTML/CSS knowledge for styling
- Django management command framework (already available)

---

## Next Step

User should review and approve this plan. Once approved, implementation will proceed in phases as outlined above.
