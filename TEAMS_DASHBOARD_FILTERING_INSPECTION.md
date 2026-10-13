# Teams Dashboard Filtering — Inspection Report

**Status:** INSPECTION ONLY — No code changes made

---

## 1. Current Dashboard Flow

### Architecture Overview

**TWO separate dashboards exist:**

#### A. Finance Tab (/finance/tab) — Browser-based embedded dashboard
- **Location**: `teams_service/main.py` lines 264-932
- **Type**: Embedded HTML/JavaScript in Teams
- **Behavior**: Single interactive page with client-side DOM updates
- **Filtering**: Client-side JavaScript, no Adaptive Card messages sent
- **Issue**: DOES NOT apply — this dashboard is client-side only

#### B. Teams Messaging Dashboard — Bot-generated Adaptive Cards
- **Location**: `teams_service/handlers/message_handlers.py`
- **Type**: Adaptive Card messages sent via Teams bot
- **Behavior**: Sends new card for every filter action
- **Filtering**: Server-side, triggers `handle_dashboard_request()`
- **Issue**: **THIS is the problematic dashboard**

---

## 2. Problem: Multiple Dashboard Messages

### Current Exact Flow

**Step 1: Initial dashboard request**
```
User: "dashboard" message
→ message_handlers.py:75-76
→ handle_dashboard_request(context)
→ line 295: await context.send(card)
→ [Adaptive Card appears in Teams]
```

**Step 2: User applies filters**
```
User: Clicks "Apply Filters" button
→ Adaptive Card action triggers
→ message_handlers.py:55-56
→ handle_apply_filters(context, value)
→ line 312: calls handle_dashboard_request(context, page=1, ...)
→ line 295: await context.send(card)  ← NEW message created!
→ [Second card appears in conversation]
```

**Step 3: User changes page**
```
User: Clicks "Next Page" button
→ message_handlers.py:59-62
→ handle_dashboard_request(context, page=page, ...)
→ line 295: await context.send(card)  ← NEW message created!
→ [Third card appears in conversation]
```

**Result**: Conversation fills with multiple dashboard Adaptive Cards

### Code Path

```
message_handlers.py:
  Line 55-56:    handle_apply_filters(context, value)
  Line 302-322:  (function definition)
  Line 312:      → handle_dashboard_request(context, page=1, status=..., ...)
  
  Line 240-300:  handle_dashboard_request(context, page=1, ...)
  Line 263-271:  Call django_client.get_receipts(filters)
  Line 279-292:  Call get_receipt_dashboard_card(receipts, filters)
  Line 293:      card = AdaptiveCard.model_validate(card_dict)
  Line 295:      await context.send(card)  ← SENDS NEW MESSAGE
```

---

## 3. Installed Teams SDK Version

**microsoft-teams-apps==2.0.16** (from requirements.txt:22)

This is a stable version that provides:
- `App` class for Teams bot initialization
- `ActivityContext` for message handling
- `AdaptiveCard` for card generation
- `context.send()` method for sending messages

---

## 4. ActivityContext Object Analysis

### Available Methods

**From SDK documentation and usage in codebase:**

✅ `context.send(card)` — Send a NEW message/activity
✅ `context.activity` — Access current activity information
✅ `context.activity.id` — Activity ID of current message
✅ `context.activity.conversation` — Conversation reference
✅ `context.activity.service_url` — Teams service URL
✅ `context.activity.from_` — Sender information

### Activity Object Properties

```python
activity.id               # UUID of current activity/message
activity.type            # "message" or "invoke"
activity.from_           # User/bot sending the message
activity.text            # Message text content
activity.value           # Adaptive Card action payload
activity.conversation    # Conversation info (thread ID, etc.)
activity.service_url     # Teams service URL for API calls
activity.channel_data    # Teams-specific metadata
```

### Update Activity Support

**Status**: ❌ **NOT EXPOSED in microsoft-teams-apps==2.0.16**

The `ActivityContext` object does NOT have:
- `update_activity()` method
- `reply(update=True)` parameter
- `update()` method

The SDK only provides `context.send()` which creates new messages.

---

## 5. Microsoft Teams SDK Limitations

### What We CAN Do
✅ Send new messages: `context.send(card)`
✅ Send text replies: `context.send("text")`
✅ Access activity ID: `context.activity.id`
✅ Access conversation reference: `context.activity.conversation`
✅ Generate Adaptive Cards with state preservation

### What We CANNOT Do (Without SDK Changes)
❌ Update existing activity/card in-place
❌ Use `UpdateActivity` Bot Framework endpoint directly from SDK
❌ Modify card content of previous message
❌ Preserve message thread without new cards

---

## 6. Potential Solution Paths

### Option A: Direct Bot Connector API (Workaround)
**Bypass the SDK limitation by calling Microsoft Bot Connector API directly**

The SDK doesn't expose update_activity, BUT the underlying Bot Framework does:

```
POST https://{serviceUrl}/v3/conversations/{conversationId}/activities/{activityId}
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "type": "message",
  "id": "{activityId}",
  "from": {...},
  "conversation": {...},
  "attachments": [{
    "contentType": "application/vnd.microsoft.card.adaptive",
    "content": {...updated card...}
  }]
}
```

**Requirements**:
- `context.activity.id` (current activity ID) ✅ Available
- `context.activity.conversation.id` (conversation ID) ✅ Available
- `context.activity.service_url` (Teams API URL) ✅ Available
- JWT token for authorization ❓ Need to extract/generate

**Viability**: ⚠️ Possible but requires:
- Extracting JWT from context
- Making HTTP call to Bot Connector API
- Error handling for failed updates
- Not using official SDK method

### Option B: Preserve Activity ID in Card Actions
**Store the dashboard activity ID in card payload and update only when user triggers action**

Current Adaptive Card action payload:
```json
{
  "action": "apply_filters",
  "filter_status": "APPROVED",
  "filter_category": "..."
}
```

Enhanced payload with activity tracking:
```json
{
  "action": "apply_filters",
  "activity_id": "19:xxx@thread.skype",  ← Add this
  "filter_status": "APPROVED",
  "filter_category": "..."
}
```

Then use Option A to update that specific activity.

**Viability**: ✅ Feasible with Option A

### Option C: Accept New Messages (Current Behavior)
**Keep sending new messages but improve UX**

Possible improvements:
- Add "collapse previous dashboard" button
- Include filter summary in card to show what changed
- Use threading (reply in thread) instead of main channel
- Add visual "replaced by newer dashboard" indicator

**Viability**: ✅ Easy but doesn't solve stated problem

---

## 7. Current Backend Filtering

**Location**: `teams_service/services/django_client.py` lines 21-74

**Supported filters** (all already working):
- ✅ `status` — Receipt status
- ✅ `category` — Expense category
- ✅ `vendor` — Vendor name
- ✅ `date_from` — Start date (YYYY-MM-DD)
- ✅ `date_to` — End date (YYYY-MM-DD)
- ✅ `amount_min` — Minimum amount
- ✅ `amount_max` — Maximum amount
- ✅ `page` — Pagination

**No changes needed** — Filtering backend is complete.

---

## 8. Current Adaptive Card Structure

**Location**: `teams_service/cards/receipt_cards.py` lines 24-150+

**Card Features**:
- ✅ Filter input fields (dropdowns, text boxes, date inputs)
- ✅ "Apply Filters" action button
- ✅ "Clear Filters" action button
- ✅ "Previous Page" / "Next Page" pagination buttons
- ✅ Receipt table with results
- ✅ Status badges and formatting

**Card Includes**:
- Receipt list with vendors, dates, amounts, categories, status
- Clickable "View" buttons for receipt details
- Filter form with all parameters
- Pagination controls

**Card Actions** (generate new dashboard cards):
- `apply_filters` (line 302-322 in message_handlers.py)
- `clear_filters` (line 58 in message_handlers.py)
- `dashboard_next` (line 59-62 in message_handlers.py)
- `dashboard_previous` (line 63-66 in message_handlers.py)

---

## 9. Activity ID Availability

**First message activity ID**:
- ✅ Available in `context.activity.id` after initial dashboard send
- ❌ But subsequent handler calls receive NEW activity context (for the action invocation, not the dashboard)

**Problem**: When user clicks "Apply Filters", the new context is for the ACTION invocation, not the original dashboard message. The action payload doesn't contain the original dashboard activity ID.

**Solution**: 
1. Store dashboard activity ID when initially sent
2. Include it in card action payloads
3. Retrieve it from the payload to update the correct activity

---

## 10. Files That Would Need Modification

**For Option A + B implementation (Update activity approach):**

1. **teams_service/handlers/message_handlers.py**
   - Lines 55-56: Modify `handle_apply_filters()` to extract activity_id from payload
   - Lines 240-300: Modify `handle_dashboard_request()` to support update mode
   - Lines 302-322: Add activity_id parameter passing
   - Add new method: `update_activity()` for Bot Connector API calls
   - Add JWT token handling

2. **teams_service/cards/receipt_cards.py**
   - Lines 24-150+: Modify `get_receipt_dashboard_card()` to include activity_id in action payloads
   - Line 279+: Add `activity_id` parameter to function

3. **teams_service/main.py**
   - Ensure JWT token is available for activity updates (from Teams context)
   - May need to add httpx client for Bot Connector API calls

4. **No changes needed**:
   - ✅ `teams_service/services/django_client.py` — Filtering already works
   - ✅ Django backend APIs — Already support all filters
   - ✅ Receipt models/serializers — No changes needed
   - ✅ Teams tab UI — Different system (not Adaptive Cards)

---

## 11. Testing Requirements

**New tests needed for:**

1. **Activity Update Flow**
   - Dashboard sent successfully
   - Activity ID captured and included in action payload
   - Filter action triggers update (not new send)
   - Updated card has same activity ID (not new message)

2. **Filter Preservation**
   - Filters passed correctly to updated card
   - Results correctly filtered and displayed
   - Pagination state maintained

3. **Backward Compatibility**
   - Existing receipt detail messages unaffected
   - Decision actions (approve/reject) unaffected
   - List receipts command unaffected
   - Help/error messages unaffected

4. **Error Handling**
   - Update fails gracefully (fall back to new message)
   - Invalid activity ID handled
   - Network errors handled
   - Expired activities handled

---

## 12. Teams SDK Constraints

| Constraint | Impact | Workaround |
|-----------|--------|-----------|
| No `update_activity()` in SDK | Must use Bot Connector API directly | Direct HTTP call to Activity endpoint |
| No JWT in context | Can't auth Bot Connector calls | Extract from Teams validation headers or generate |
| Activity ID in action payload not automatic | Must manually pass through card | Include `activity_id` in all action payloads |
| Session/state not persisted in SDK | Dashboard state lost between messages | Regenerate from scratch each time (current behavior) |
| No reply-in-thread support | All messages go to main channel | Accept this limitation or add clearing logic |

---

## 13. Summary Table

| Aspect | Current | Needed | Feasibility |
|--------|---------|--------|-------------|
| Dashboard display | ✅ Works | ✅ Works | ✅ Complete |
| Filter parameters | ✅ All supported | ✅ All supported | ✅ Complete |
| Backend filtering | ✅ Working | ✅ Working | ✅ Complete |
| Single message update | ❌ New message | ✅ Update existing | ⚠️ Possible with Bot Connector API |
| Activity ID preservation | ❌ Not tracked | ✅ Track & include | ✅ Easy (add to payload) |
| JWT auth for updates | ❌ Not needed | ✅ Needed | ⚠️ May require extraction/generation |
| Filter state retention | ❌ Regenerated | ✅ Persisted | ✅ Works automatically |

---

## Conclusion

**The problem is real**: Every filter action sends a new Adaptive Card message, filling the conversation.

**The solution is possible**: Use Microsoft Bot Connector API directly to update activities, bypassing SDK limitations.

**The effort level**: Medium - requires:
1. Extracting/obtaining JWT token for Bot Connector auth
2. Making direct HTTP calls to Bot Connector API  
3. Passing activity ID through card payloads
4. Proper error handling and fallback logic

**The SDK limitation**: `microsoft-teams-apps==2.0.16` doesn't expose activity update methods, but the underlying Bot Framework does.

---

## Appendix: Bot Connector Activity Update Endpoint

```
POST https://{serviceUrl}/v3/conversations/{conversationId}/activities/{activityId}

Headers:
  Authorization: Bearer {jwt_token}
  Content-Type: application/json

Body:
{
  "type": "message",
  "id": "{activityId}",
  "from": {
    "id": "{botId}",
    "name": "Expense Policy Agent"
  },
  "conversation": {
    "id": "{conversationId}"
  },
  "attachments": [{
    "contentType": "application/vnd.microsoft.card.adaptive",
    "content": {
      "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
      "type": "AdaptiveCard",
      "version": "1.4",
      ...updated dashboard card...
    }
  }]
}

Response:
  200 OK: { "id": "{activityId}" }
  404 Not Found: Activity ID doesn't exist
  401 Unauthorized: Invalid JWT token
```

