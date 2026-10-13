# Teams Activity Update — SDK Support Inspection Report

**Status:** INSPECTION ONLY — No code changes made

---

## 1. Installed Package Versions

| Package | Version | Notes |
|---------|---------|-------|
| `microsoft-teams-apps` | 2.0.16 | Main Teams SDK (Activity handling, routing) |
| `microsoft-teams-api` | 2.1.0 | API client (Conversation, Activity operations) |
| `microsoft-teams-cards` | 2.1.0 | Card generation |
| `microsoft-teams-common` | 2.1.0 | Common utilities |

---

## 2. ActivityContext Attributes

**Available methods in ActivityContext:**
- ✅ `send(card)` — Send activity to Teams
- ✅ `reply(text)` — Reply to activity  
- ✅ `activity` — Current activity object
- ✅ `api` — **ApiClient instance** ⚠️ Key finding!
- ✅ `conversation_ref` — ConversationReference
- ✅ `app_graph`, `user_graph`, `sign_in`, `sign_out`

**Critical discovery**: `ActivityContext.api` contains the ApiClient!

---

## 3. ApiClient Methods

The `ActivityContext.api` provides:
- ✅ `api.bots` — Bot operations (deprecated)
- ✅ `api.conversations` — **ConversationClient** ⚠️ THIS IS KEY!
- ✅ `api.teams` — Team operations
- ✅ `api.users` — User operations
- ✅ `api.http` — HTTP client

---

## 4. ConversationClient Methods

**The cleanest supported SDK way:**

```python
context.api.conversations.update_activity(
    conversation_id: str,
    activity_id: str,
    activity: MessageActivityInput
) -> SentActivity
```

**Available operations:**
- ✅ `update_activity(conversation_id, activity_id, activity)` — **UPDATE EXISTING ACTIVITY**
- ✅ `create_activity(conversation_id, activity)` — Create new
- ✅ `delete_activity(conversation_id, activity_id)` — Delete
- ✅ `reply_to_activity(conversation_id, activity_id, activity)` — Reply
- ✅ `create_targeted_activity(...)` — Private messages
- ✅ `update_targeted_activity(...)` — Update private messages

---

## 5. Update Activity Method Signature

```python
ConversationClient.update_activity(
    self,
    conversation_id: str,
    activity_id: str,
    activity: MessageActivityInput | MessageReactionActivityInput | TypingActivityInput,
    *,
    service_url: str | None = None,
    agentic_identity: AgenticIdentity | None = None
) -> SentActivity
```

**Returns:** Updated `SentActivity` with `id` and server-populated fields

---

## 6. How to Obtain Required IDs

### Conversation ID

**Available from:**
- `context.activity.conversation.id` — Conversation ID where dashboard is displayed
- `context.conversation_ref.conversation.id` — Conversation reference

**Example:**
```python
conversation_id = context.activity.conversation.id
```

### Original Dashboard Activity ID

**Problem:** When user clicks "Apply Filters" action on Adaptive Card, Teams sends a NEW invocation activity. This activity is for the ACTION, not the original dashboard message.

**Available information:**
- ❌ `context.activity.id` — This is the action invocation ID, NOT the dashboard message ID
- ❌ `context.activity.reply_to_id` — May not identify dashboard message
- ⚠️ Must be included in Adaptive Card action payload

**Solution:** Include `activity_id` in the card's action payload:

```json
{
  "action": "apply_filters",
  "activity_id": "{original_dashboard_activity_id}",
  "filter_status": "APPROVED",
  ...
}
```

### Getting Activity ID from send() Response

**When initial dashboard is sent:**
```python
sent_activity = await context.send(card)
dashboard_activity_id = sent_activity.id
```

The `SentActivity` object returned contains:
- ✅ `id` — The activity ID assigned by Teams server
- ✅ `type` — Activity type ("message")
- ✅ `conversation` — Conversation information
- ✅ Other server-populated fields

---

## 7. Implementation Flow

### Step 1: Send Initial Dashboard & Store Activity ID

```python
# In handle_dashboard_request() when first called
sent_activity = await context.send(card)
dashboard_activity_id = sent_activity.id
# Store or include this ID in subsequent action payloads
```

### Step 2: Include Activity ID in Card Actions

**In `get_receipt_dashboard_card()` function:**

Update the filter action payloads to include `activity_id`:

```json
{
  "action": "apply_filters",
  "activity_id": "{dashboard_activity_id}",  // Add this
  "filter_status": "...",
  "filter_category": "...",
  ...
}
```

### Step 3: Update Activity on Filter Action

**In `handle_apply_filters()` and pagination handlers:**

```python
async def handle_apply_filters(self, context: ActivityContext, value: Dict[str, Any]) -> None:
    """Handle apply filters action - UPDATE instead of send new message."""
    
    # Extract the original dashboard activity ID from the action payload
    activity_id = value.get("activity_id")  # New field in payload
    
    if not activity_id:
        # Fallback to old behavior if ID missing (for safety)
        await self.handle_dashboard_request(context, page=1, ...)
        return
    
    # Extract filters
    status = value.get("filter_status")
    category = value.get("filter_category")
    ...
    
    try:
        # Get filtered data
        response = await django_client.get_receipts(
            status=status,
            category=category,
            ...
        )
        
        # Generate updated card
        card_dict = get_receipt_dashboard_card(
            response.get("results", []),
            categories=...,
            years=...,
            page=1,
            status=status,
            ...
        )
        
        # Create MessageActivityInput for update
        activity_input = MessageActivityInput(
            type="message",
            text="Finance Dashboard",
            attachments=[{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card_dict
            }]
        )
        
        # UPDATE the dashboard activity instead of sending new message
        conversation_id = context.activity.conversation.id
        updated_activity = await context.api.conversations.update_activity(
            conversation_id=conversation_id,
            activity_id=activity_id,
            activity=activity_input
        )
        
        # Success: dashboard is updated in-place, no new message sent
        
    except Exception as e:
        logger.error(f"Error updating dashboard: {e}")
        # Fallback: send error message
        card_dict = get_error_card("Could not update dashboard")
        card = AdaptiveCard.model_validate(card_dict)
        await context.send(card)
```

---

## 8. Activity Information Available

### From context.activity:
- ✅ `context.activity.id` — Current activity ID (invocation, not dashboard)
- ✅ `context.activity.type` — Activity type
- ✅ `context.activity.conversation` — Conversation info with `.id`
- ✅ `context.activity.from_` — Sender info
- ✅ `context.activity.value` — Action payload
- ✅ `context.activity.service_url` — Teams service URL

### From context.conversation_ref:
- ✅ `context.conversation_ref.conversation.id` — Conversation ID
- ✅ `context.conversation_ref.activity_id` — Activity ID field (may be set)
- ✅ `context.conversation_ref.service_url` — Service URL

---

## 9. Recommended Implementation Path

| Step | Location | Change | Complexity |
|------|----------|--------|-----------|
| 1 | `teams_service/cards/receipt_cards.py` | Include `activity_id` in action payloads | Low |
| 2 | `teams_service/handlers/message_handlers.py` | Store initial dashboard activity ID | Low |
| 3 | `teams_service/handlers/message_handlers.py` | Use `context.api.conversations.update_activity()` instead of `context.send()` for filter actions | Medium |
| 4 | `teams_service/handlers/message_handlers.py` | Update `handle_apply_filters()`, `handle_dashboard_request()` pagination to use update | Medium |
| 5 | Tests | Add tests for activity update flow | Medium |

---

## 10. Whether Direct Bot Connector REST API Needed

**Answer: ❌ NO**

The installed SDK (microsoft-teams-api==2.1.0) provides:
- ✅ `ConversationClient.update_activity()` method
- ✅ Proper authentication handling (JWT already managed by SDK)
- ✅ Typed response objects (SentActivity)
- ✅ Full parameter validation

**No need for:**
- ❌ Manual REST calls
- ❌ JWT generation
- ❌ Raw Bot Connector API
- ❌ Bypassing the SDK

---

## 11. Whether JWT Generation Necessary

**Answer: ❌ NO**

The SDK method `context.api.conversations.update_activity()` handles:
- ✅ Authentication automatically
- ✅ JWT token management internally
- ✅ Service URL routing
- ✅ All HTTP details

**You provide only:**
- `conversation_id`
- `activity_id`
- `activity` (MessageActivityInput)

The SDK handles the rest.

---

## 12. Files Requiring Modification

### 1. **teams_service/cards/receipt_cards.py**

**Modification needed:**
- Add `activity_id` parameter to `get_receipt_dashboard_card()` function
- Include `activity_id` in all Adaptive Card action payloads
- Update action payload structure

**Example:**
```python
def get_receipt_dashboard_card(
    receipts,
    categories,
    years,
    page=1,
    has_next=False,
    activity_id=None,  # Add this parameter
    status=None,
    ...
):
    # ... card generation ...
    
    # In apply_filters action:
    "actions": [{
        "type": "Action.Submit",
        "title": "Apply Filters",
        "data": {
            "action": "apply_filters",
            "activity_id": activity_id,  # Add this
            "filter_status": "input_filter_status",
            ...
        }
    }]
```

### 2. **teams_service/handlers/message_handlers.py**

**Modifications needed:**
- Modify `handle_dashboard_request()` to:
  - Capture the initial dashboard's activity ID
  - Pass it to card generation
  - Support update mode vs send mode

- Modify `handle_apply_filters()` to:
  - Extract `activity_id` from value
  - Use `context.api.conversations.update_activity()` instead of `context.send()`
  - Fallback to send if update fails

- Modify pagination handlers (`dashboard_next`, `dashboard_previous`) to use update

### 3. **No changes needed:**
- ✅ Django backend
- ✅ Filtering logic
- ✅ Receipt processing
- ✅ Finance Tab HTML
- ✅ React frontend
- ✅ Azure services

---

## 13. Tests to Add

### 1. **Activity Update Flow**
- Test: Initial dashboard sends new message
- Test: Dashboard activity ID is captured
- Test: Activity ID is included in action payloads
- Test: Filter action updates existing activity (not new send)

### 2. **Filter Preservation**
- Test: Filters applied correctly to updated card
- Test: Results filtered properly
- Test: Pagination state maintained across updates

### 3. **Backward Compatibility**
- Test: Receipt detail messages unaffected
- Test: Decision actions (approve/reject) unaffected
- Test: List receipts command unaffected
- Test: Error messages unaffected

### 4. **Error Handling**
- Test: Update fails gracefully
- Test: Falls back to new message on missing activity_id
- Test: Falls back on permission errors
- Test: Activity not found handled

### 5. **Conversation/Activity Data**
- Test: conversation_id correctly extracted
- Test: activity_id correctly passed through payload
- Test: Service URL available for update call

---

## 14. Code Example: Updated Filter Handler

```python
async def handle_apply_filters(self, context: ActivityContext, value: Dict[str, Any]) -> None:
    """Handle apply filters action - UPDATE dashboard instead of sending new message."""
    
    # Extract dashboard activity ID from action payload
    activity_id = value.get("activity_id")
    conversation_id = context.activity.conversation.id
    
    # Extract filters from action
    status = (value.get("filter_status") or "").strip() or None
    category = (value.get("filter_category") or "").strip() or None
    year = (value.get("filter_year") or "").strip() or None
    date_from = (value.get("filter_date_from") or "").strip() or None
    date_to = (value.get("filter_date_to") or "").strip() or None
    amount_min = (value.get("filter_amount_min") or "").strip() or None
    amount_max = (value.get("filter_amount_max") or "").strip() or None
    
    try:
        # Fetch filtered data
        response = await django_client.get_receipts(
            status=status,
            category=category,
            date_from=date_from,
            date_to=date_to,
            amount_min=amount_min,
            amount_max=amount_max,
            page=1
        )
        
        # Get categories and years for filter dropdowns
        categories = await django_client.get_categories()
        years = await django_client.get_available_years()
        
        # Generate updated card
        card_dict = get_receipt_dashboard_card(
            response.get("results", []),
            categories=categories,
            years=years,
            page=1,
            has_next=response.get("next") is not None,
            activity_id=activity_id,  # Pass activity ID to card generation
            status=status,
            category=category,
            year=year,
            date_from=date_from,
            date_to=date_to,
            amount_min=amount_min,
            amount_max=amount_max,
        )
        
        # Create activity input for update
        from microsoft_teams.api import MessageActivityInput
        activity_input = MessageActivityInput(
            type="message",
            text="Finance Dashboard - Filtered Results",
            attachments=[{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card_dict
            }]
        )
        
        # If we have activity_id, UPDATE the dashboard
        # Otherwise, fall back to sending new message
        if activity_id:
            try:
                await context.api.conversations.update_activity(
                    conversation_id=conversation_id,
                    activity_id=activity_id,
                    activity=activity_input
                )
                # Success: same message updated, no new card sent
                return
            except Exception as e:
                logger.warning(f"Could not update dashboard activity {activity_id}: {e}")
                # Fall through to fallback behavior
        
        # Fallback: send new message (original behavior)
        card = AdaptiveCard.model_validate(card_dict)
        await context.send(card)
        
    except Exception as e:
        logger.error(f"Error applying filters: {e}")
        card_dict = get_error_card("Could not apply filters. Please try again.")
        card = AdaptiveCard.model_validate(card_dict)
        await context.send(card)
```

---

## Summary

| Question | Answer |
|----------|--------|
| Is update_activity supported in installed SDK? | ✅ **YES** — `ConversationClient.update_activity()` |
| Where is it available? | `context.api.conversations.update_activity()` |
| How to get conversation_id? | `context.activity.conversation.id` |
| How to get dashboard activity_id? | Store from `context.send()` response; pass in action payload |
| Is JWT needed? | ❌ **NO** — SDK handles it internally |
| Is REST API needed? | ❌ **NO** — Use SDK method |
| Complexity? | **Medium** — Straightforward but requires careful ID tracking |
| Files to modify? | 2 files: `cards/receipt_cards.py`, `handlers/message_handlers.py` |

---

## Conclusion

**The installed SDK (microsoft-teams-api==2.1.0) provides full support for updating existing Teams activities.**

The cleanest, most supported approach:

1. ✅ Store dashboard activity ID when initially sent
2. ✅ Include it in Adaptive Card action payloads
3. ✅ Use `context.api.conversations.update_activity()` to update existing message
4. ✅ No JWT generation needed
5. ✅ No Bot Connector REST API needed
6. ✅ No bypassing the SDK

**Result:** Single dashboard card that updates in-place for filter actions, pagination, etc. No conversation clutter from multiple dashboard messages.

