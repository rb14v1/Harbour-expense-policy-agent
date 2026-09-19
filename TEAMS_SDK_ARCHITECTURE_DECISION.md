# Microsoft Teams SDK Architecture Decision

**Date:** 2026-09-19  
**Status:** Architectural Analysis — Awaiting Decision  
**Django Tests:** ✅ 90/90 Passing  
**Cleanup Status:** ✅ Complete (legacy BotBuilder removed, current Teams SDK installed)

---

## Cleanup Summary (Completed)

✅ **Deleted dead legacy files:**
- `teams_app/teams_authentication.py` — Imported missing botbuilder, never used
- `teams_app/teams_sdk_integration.py` — Dead code, never imported

✅ **Removed from requirements.txt:**
- `botbuilder-core==4.21.1` — Legacy BotBuilder, not installed
- `botbuilder-schema==4.21.1` — Legacy BotBuilder, not installed

✅ **Added to requirements.txt:**
- `microsoft-teams-apps==2.1.0` — Current Microsoft Teams SDK for Python

✅ **Kept:**
- `PyJWT==2.8.1` — Used by existing teams_app/auth.py

✅ **Installed:**
- microsoft-teams-apps==2.1.0 ✅
- Dependencies: fastapi, dependency-injector, microsoft-teams-api, microsoft-teams-common
- python -c "from microsoft_teams.apps import App; print('✅ Import OK')"

---

## Critical Architectural Finding

### Current Situation

**Your Backend:** Django WSGI  
**Current Teams SDK:** microsoft-teams-apps (FastAPI/ASGI-based)

### The Problem

The current microsoft-teams-apps SDK (v2.1.0) is **fundamentally designed for FastAPI/ASGI applications**, not Django WSGI.

**Evidence:**

1. **HttpServerAdapter** — Runs its own HTTP server
   ```python
   adapter.start()      # Starts async server
   adapter.stop()       # Stops async server
   adapter.register_route(...)
   ```

2. **FastAPIAdapter** — Explicitly requires FastAPI
   ```python
   from microsoft_teams.apps.http import FastAPIAdapter
   # Only adapter available for HTTP server integration
   ```

3. **Dependencies** — Requires async frameworks
   ```
   fastapi>=0.115.13
   uvicorn>=0.34.3
   dependency-injector>=4.48.1
   ```

4. **Architecture** — Designed around async event-based message processing
   ```python
   @app.on_message()
   async def handle_message(activity: Activity):
       ...
   ```

### Current Working Implementation

Your current Teams webhook **already works perfectly without the Teams SDK**:

```python
# teams_app/views.py
POST /api/v1/teams/messages/
    ↓
teams_message_handler(request)  # Django view
    ↓
bot_handler.py → TeamsBot.handle_message()  # Plain Python
    ↓
Calls Django APIs
    ↓
Returns Adaptive Cards
```

**This approach is:**
- ✅ Simple and testable
- ✅ Integrated directly into Django WSGI
- ✅ No external HTTP servers needed
- ✅ Already passing all tests

---

## Architectural Options

### Option A: Keep Current Implementation (Recommended for Django)

**Architecture:**
```
Teams Webhook → Django WSGI (teams_app/views.py)
                    ↓
                bot_handler.py (plain Python)
                    ↓
                Django APIs / PostgreSQL
```

**Pros:**
- ✅ Works now, all tests pass
- ✅ Single WSGI process
- ✅ No separate HTTP servers
- ✅ Integrated with Django
- ✅ Simple deployment

**Cons:**
- ❌ Doesn't use microsoft-teams-apps SDK
- ❌ Manual Teams protocol handling
- ⚠️ May miss future Teams SDK features

**When to use:** If you want simplicity and tight Django integration.

---

### Option B: Use Teams SDK with Separate Microservice

**Architecture:**
```
Teams Webhook → Standalone Python Service (microsoft-teams-apps)
                    ↓
                Teams SDK (FastAPI/ASGI)
                    ↓
                Django REST APIs
                    ↓
                PostgreSQL
```

**Pros:**
- ✅ Uses current Microsoft Teams SDK
- ✅ Benefit from SDK features/updates
- ✅ SDK handles Teams protocol properly
- ✅ Loosely coupled from Django

**Cons:**
- ❌ Two separate processes to deploy
- ❌ More complex local development
- ❌ IPC/networking overhead
- ❌ Separate configuration management

**When to use:** If you want to use the current Teams SDK as intended.

---

### Option C: Hybrid — Use Teams SDK in Django View

**Architecture:**
```
Teams Webhook → Django WSGI view
                    ↓
                Teams SDK activity handler (non-HTTP)
                    ↓
                bot_handler.py
                    ↓
                Django APIs
```

**Status:** ⚠️ **POSSIBLE BUT NOT RECOMMENDED**

- The SDK's `_process_activity_event()` method could be called directly
- But this bypasses the SDK's HTTP server, authentication, middleware
- Defeats the purpose of using the SDK
- No documentation/support for this usage pattern

---

## Recommendation

### For this project, I recommend **Option A: Keep Current Implementation**

**Reasons:**

1. **Django is the backend** — You explicitly said "Do NOT replace Django with FastAPI"
2. **Current approach is solid** — All 90 tests pass, it works
3. **Lowest complexity** — Single process, single framework
4. **Teams SDK mismatch** — The current SDK isn't designed for WSGI
5. **Maintainability** — One code path to maintain

### If you must use the Teams SDK, then **Option B: Separate Microservice**

This would be the proper way to use microsoft-teams-apps without compromising Django.

---

## Current State

| Item | Status |
|------|--------|
| Django WSGI Backend | ✅ Working |
| Teams Webhook | ✅ Working |
| Finance APIs | ✅ Working |
| Django Tests | ✅ 90/90 Passing |
| Legacy BotBuilder | ✅ Removed |
| Current Teams SDK | ✅ Installed |
| Teams SDK Integration | ⏳ **Awaiting Decision** |

---

## Decision Required

**Choose:**

A. **Keep current Django WSGI-based Teams webhook**
   - Continue with bot_handler.py / auth.py / finance_tab.py approach
   - Remove microsoft-teams-apps from requirements.txt
   - Document why current approach is better for Django

B. **Migrate to Teams SDK microservice**
   - Create separate FastAPI/ASGI service for Teams
   - Keep Django as REST backend
   - Use Teams SDK properly in its intended environment

C. **Other**
   - Explain the desired architecture

---

## What I've Done So Far

✅ Deleted dead code (teams_authentication.py, teams_sdk_integration.py)  
✅ Removed legacy BotBuilder dependencies  
✅ Installed current microsoft-teams-apps SDK  
✅ Verified all Django tests still pass  
✅ Analyzed architectural options  
⏳ **Awaiting your decision on Teams SDK integration strategy**

---

## Next Steps (After Decision)

**If Option A (keep current):**
1. Remove microsoft-teams-apps from requirements.txt
2. Keep existing teams_app code
3. Complete Finance Teams experience using current approach
4. Document the architecture

**If Option B (separate microservice):**
1. Create separate /teams-service/ directory
2. Implement FastAPI app with microsoft-teams-apps
3. Configure it to call Django REST APIs
4. Document deployment architecture
5. Update this project's README

