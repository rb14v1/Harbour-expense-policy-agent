"""
Tests for Teams Message Handlers

Tests for Part 1: Finance-pending receipt list functionality.
Tests for Part 2: Complete Finance review workflow with Adaptive Cards.
"""
import asyncio
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock, MagicMock
from teams_service.handlers.message_handlers import FinanceMessageHandler


class FinanceMessageHandlerTests(IsolatedAsyncioTestCase):
    """Tests for FinanceMessageHandler with Finance-pending receipts."""

    async def test_handle_message_hi_returns_pending_receipts(self):
        """Test that 'hi' message triggers pending Finance receipt list."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = "hi"
        context.activity.from_property.id = "user123"
        context.send = AsyncMock()

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 1,
                "results": [{
                    "id": "receipt-1",
                    "original_filename": "receipt.pdf",
                    "vendor_name": "Test Vendor",
                    "transaction_date": "2026-09-01",
                    "total_amount": "100.00",
                    "currency": "USD",
                    "status": "NEEDS_REVIEW",
                }],
                "next": None,
                "previous": None,
            })

            await handler.handle_message(context)

            # Verify get_receipts was called with NEEDS_REVIEW filter
            mock_client.get_receipts.assert_called_once_with(status="NEEDS_REVIEW", page=1)

            # Verify context.send was called
            context.send.assert_called_once()

    async def test_handle_message_hello_returns_pending_receipts(self):
        """Test that 'hello' message triggers pending Finance receipt list."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = "hello"
        context.activity.from_property.id = "user123"
        context.send = AsyncMock()

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 0,
                "results": [],
                "next": None,
                "previous": None,
            })

            await handler.handle_message(context)

            # Verify get_receipts was called with NEEDS_REVIEW filter
            mock_client.get_receipts.assert_called_once_with(status="NEEDS_REVIEW", page=1)
            context.send.assert_called_once()

    async def test_handle_message_list_returns_pending_receipts(self):
        """Test that 'list' message triggers pending Finance receipt list."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = "list"
        context.activity.from_property.id = "user123"
        context.send = AsyncMock()

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 2,
                "results": [{
                    "id": "receipt-1",
                    "original_filename": "receipt1.pdf",
                    "vendor_name": "Vendor 1",
                    "transaction_date": "2026-09-01",
                    "total_amount": "100.00",
                    "currency": "USD",
                    "status": "NEEDS_REVIEW",
                }, {
                    "id": "receipt-2",
                    "original_filename": "receipt2.pdf",
                    "vendor_name": "Vendor 2",
                    "transaction_date": "2026-09-02",
                    "total_amount": "200.00",
                    "currency": "USD",
                    "status": "NEEDS_REVIEW",
                }],
                "next": None,
                "previous": None,
            })

            await handler.handle_message(context)

            # Verify get_receipts was called with NEEDS_REVIEW filter
            mock_client.get_receipts.assert_called_once_with(status="NEEDS_REVIEW", page=1)
            context.send.assert_called_once()

    async def test_handle_message_empty_returns_pending_receipts(self):
        """Test that empty message triggers pending Finance receipt list."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = ""
        context.activity.from_property.id = "user123"
        context.send = AsyncMock()

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 0,
                "results": [],
                "next": None,
                "previous": None,
            })

            await handler.handle_message(context)

            # Verify get_receipts was called with NEEDS_REVIEW filter
            mock_client.get_receipts.assert_called_once_with(status="NEEDS_REVIEW", page=1)
            context.send.assert_called_once()

    async def test_handle_message_no_pending_receipts(self):
        """Test handling when there are no pending Finance receipts."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = "list"
        context.activity.from_property.id = "user123"
        context.send = AsyncMock()

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 0,
                "results": [],
                "next": None,
                "previous": None,
            })

            await handler.handle_message(context)

            # Should still call send with a card (empty state)
            context.send.assert_called_once()

    async def test_handle_message_api_error(self):
        """Test error handling when API call fails."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = "list"
        context.activity.from_property.id = "user123"
        context.send = AsyncMock()

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(side_effect=Exception("API Error"))

            await handler.handle_message(context)

            # Should call send with error card
            context.send.assert_called_once()

    async def test_handle_message_help_not_pending_list(self):
        """Test that 'help' does NOT return pending receipts list."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = "help"
        context.activity.from_property.id = "user123"
        context.send = AsyncMock()

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            await handler.handle_message(context)

            # Verify get_receipts was NOT called
            mock_client.get_receipts.assert_not_called()

            # Should call send with help message
            context.send.assert_called_once()

    async def test_status_filter_is_needs_review(self):
        """Test that the handler specifically requests NEEDS_REVIEW status."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = "receipts"
        context.activity.from_property.id = "user123"
        context.send = AsyncMock()

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 0,
                "results": [],
                "next": None,
                "previous": None,
            })

            await handler.handle_message(context)

            # Verify status filter is exactly NEEDS_REVIEW
            call_args = mock_client.get_receipts.call_args
            self.assertEqual(call_args.kwargs.get('status'), 'NEEDS_REVIEW')

    async def test_preview_action_returns_preview_card(self):
        """Test that preview action returns a card with preview URL."""
        handler = FinanceMessageHandler()
        receipt_id = "receipt-123"

        context = MagicMock()
        context.activity.value = {
            "action": "preview_receipt",
            "receipt_id": receipt_id,
        }
        context.activity.text = None
        context.send = AsyncMock()

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            preview_url = f"http://localhost:8000/api/v1/receipts/{receipt_id}/preview/"
            mock_client.get_receipt_preview_url = AsyncMock(return_value=preview_url)

            await handler.handle_message(context)

            # Verify preview URL was requested
            mock_client.get_receipt_preview_url.assert_called_once_with(receipt_id)

            # Verify context.send was called
            context.send.assert_called_once()

            # Verify the card has an action with the preview URL
            call_args = context.send.call_args
            card_arg = call_args[0][0]
            self.assertIsNotNone(card_arg)


# Part 2: Adaptive Card Actions and Receipt Review Workflow Tests
class FinanceMessageHandlerPart2Tests(IsolatedAsyncioTestCase):
    """Tests for Part 2: Complete Finance review workflow."""

    async def test_open_receipt_action_returns_detail_card(self):
        """Test that open_receipt action returns receipt detail card."""
        handler = FinanceMessageHandler()
        receipt_id = "receipt-123"

        context = MagicMock()
        context.activity.value = {
            "action": "open_receipt",
            "receipt_id": receipt_id,
        }
        context.activity.text = None
        context.send = AsyncMock()

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipt_detail = AsyncMock(return_value={
                "id": receipt_id,
                "original_filename": "receipt.pdf",
                "vendor_name": "Test Vendor",
                "transaction_date": "2026-09-01",
                "total_amount": "100.00",
                "currency": "USD",
                "category": "Travel",
                "status": "NEEDS_REVIEW",
            })

            await handler.handle_message(context)

            # Verify detail was fetched
            mock_client.get_receipt_detail.assert_called_once_with(receipt_id)

            # Verify context.send was called
            context.send.assert_called_once()

    async def test_approve_action_routes_correctly(self):
        """Test that approve action is routed to handle_receipt_action."""
        handler = FinanceMessageHandler()
        receipt_id = "receipt-123"

        context = MagicMock()
        context.activity.value = {
            "action": "approve",
            "receipt_id": receipt_id,
        }
        context.activity.text = None
        context.send = AsyncMock()

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.make_receipt_decision = AsyncMock(return_value={
                "id": receipt_id,
                "status": "APPROVED",
            })

            await handler.handle_message(context)

            # Verify decision was made with APPROVED status
            mock_client.make_receipt_decision.assert_called_once()
            call_args = mock_client.make_receipt_decision.call_args
            self.assertEqual(call_args[0][0], receipt_id)
            self.assertEqual(call_args[0][1], "APPROVED")

            # Verify confirmation card is sent
            context.send.assert_called_once()

    async def test_reject_action_with_reason(self):
        """Test that reject action passes rejection reason to backend."""
        handler = FinanceMessageHandler()
        receipt_id = "receipt-123"
        rejection_reason = "Missing invoice details"

        context = MagicMock()
        context.activity.value = {
            "action": "reject",
            "receipt_id": receipt_id,
            "rejection_reason": rejection_reason,
        }
        context.activity.text = None
        context.send = AsyncMock()

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.make_receipt_decision = AsyncMock(return_value={
                "id": receipt_id,
                "status": "REJECTED",
            })

            await handler.handle_message(context)

            # Verify decision was made with rejection notes
            mock_client.make_receipt_decision.assert_called_once()
            call_args = mock_client.make_receipt_decision.call_args
            self.assertEqual(call_args[0][0], receipt_id)
            self.assertEqual(call_args[0][1], "REJECTED")
            self.assertEqual(call_args.kwargs.get('notes'), rejection_reason)

            # Verify confirmation card is sent
            context.send.assert_called_once()


# Part 3: Mobile Card Layout and Structure Tests
class MobileCardStructureTests(IsolatedAsyncioTestCase):
    """Tests for mobile-friendly Adaptive Card structure."""

    async def test_receipt_detail_card_structure_is_compact(self):
        """Test that receipt detail card has mobile-friendly structure."""
        from teams_service.cards.receipt_cards import get_receipt_detail_card

        receipt = {
            "id": "receipt-123",
            "original_filename": "invoice.pdf",
            "vendor_name": "Test Vendor",
            "transaction_date": "2026-09-01",
            "total_amount": "100.00",
            "currency": "USD",
            "category": "Travel",
            "category_confidence": 0.95,
            "status": "NEEDS_REVIEW",
        }

        card = get_receipt_detail_card(receipt)

        # Verify structure
        self.assertEqual(card["type"], "AdaptiveCard")
        self.assertIn("body", card)
        self.assertIn("actions", card)

        # Verify body has text blocks (not excessive)
        body = card["body"]
        self.assertGreater(len(body), 0)
        self.assertLess(len(body), 15)  # Should be compact for mobile

        # Verify actions are present
        actions = card["actions"]
        self.assertGreater(len(actions), 0)
        self.assertLessEqual(len(actions), 3)  # Preview, Approve, Reject max

        # Verify preview action is first
        self.assertEqual(actions[0]["data"]["action"], "preview_receipt")

    async def test_receipt_detail_card_has_correct_pdf_action(self):
        """Test that receipt detail card preview action has correct data structure."""
        from teams_service.cards.receipt_cards import get_receipt_detail_card

        receipt = {
            "id": "test-receipt-id",
            "original_filename": "receipt.pdf",
            "vendor_name": "Vendor",
            "status": "UNIQUE",
        }

        card = get_receipt_detail_card(receipt)
        actions = card["actions"]

        # Find preview action
        preview_action = next((a for a in actions if a["data"]["action"] == "preview_receipt"), None)
        self.assertIsNotNone(preview_action)
        self.assertEqual(preview_action["data"]["receipt_id"], "test-receipt-id")

    async def test_receipt_list_card_has_proper_actions(self):
        """Test that receipt list card has proper action structure for mobile."""
        from teams_service.cards.receipt_cards import get_receipt_list_card

        receipts = [{
            "id": "receipt-1",
            "original_filename": "receipt.pdf",
            "vendor_name": "Vendor",
            "transaction_date": "2026-09-01",
            "total_amount": "100.00",
            "currency": "USD",
        }]

        card = get_receipt_list_card(receipts)

        # Verify structure
        self.assertEqual(card["type"], "AdaptiveCard")
        self.assertIn("body", card)

        # Find ActionSet for the receipt
        action_sets = [elem for elem in card["body"] if elem.get("type") == "ActionSet"]
        self.assertEqual(len(action_sets), 1)

        # Verify action exists
        action_set = action_sets[0]
        self.assertIn("actions", action_set)
        self.assertEqual(len(action_set["actions"]), 1)

        # Verify action is open_receipt
        action = action_set["actions"][0]
        self.assertEqual(action["data"]["action"], "open_receipt")
        self.assertEqual(action["data"]["receipt_id"], "receipt-1")

    async def test_decision_confirmation_card_readable_on_mobile(self):
        """Test that decision confirmation card is compact and readable on mobile."""
        from teams_service.cards.receipt_cards import get_decision_confirmation_card

        card = get_decision_confirmation_card("receipt-123", "APPROVED", notes=None)

        # Verify structure
        self.assertEqual(card["type"], "AdaptiveCard")
        self.assertIn("body", card)

        # Verify body is compact (3-4 items for APPROVED)
        body = card["body"]
        self.assertGreater(len(body), 0)
        self.assertLess(len(body), 5)

    async def test_decision_confirmation_with_rejection_reason(self):
        """Test that rejection confirmation includes the reason."""
        from teams_service.cards.receipt_cards import get_decision_confirmation_card

        rejection_reason = "Missing invoice number"
        card = get_decision_confirmation_card("receipt-123", "REJECTED", notes=rejection_reason)

        # Verify the reason is in the card
        body_text = "\n".join([elem.get("text", "") for elem in card["body"]])
        self.assertIn(rejection_reason, body_text)

    async def test_receipt_card_text_uses_wrap_for_mobile(self):
        """Test that receipt cards use wrap: True for mobile readability."""
        from teams_service.cards.receipt_cards import get_receipt_detail_card

        receipt = {
            "id": "receipt-123",
            "original_filename": "very_long_filename_that_exceeds_normal_display_width.pdf",
            "vendor_name": "Test Vendor With Long Name",
            "status": "UNIQUE",
        }

        card = get_receipt_detail_card(receipt)
        body = card["body"]

        # Check that critical text blocks have wrap enabled
        has_wrap = False
        for elem in body:
            if elem.get("type") == "TextBlock" and "filename" in elem.get("text", "").lower():
                self.assertTrue(elem.get("wrap", False), "Filename should wrap on mobile")
                has_wrap = True
        self.assertTrue(has_wrap, "Should have at least one wrapped filename element")


# Task 2: Decision Locking and Enforcement Tests
class DecisionLockingTests(IsolatedAsyncioTestCase):
    """Tests for decision locking and backend validation."""

    async def test_approved_card_has_no_reject_action(self):
        """Test that APPROVED receipt card has no Reject action."""
        from teams_service.cards.receipt_cards import get_receipt_detail_card

        receipt = {
            "id": "receipt-123",
            "original_filename": "receipt.pdf",
            "status": "APPROVED",
            "vendor_name": "Test Vendor",
        }

        card = get_receipt_detail_card(receipt)
        actions = card.get("actions", [])

        # Should only have Preview action, no Approve or Reject
        action_titles = [a.get("title") for a in actions]
        self.assertIn("Preview", action_titles)
        self.assertNotIn("Approve", action_titles)
        self.assertNotIn("Reject", action_titles)

    async def test_rejected_card_has_no_approve_action(self):
        """Test that REJECTED receipt card has no Approve action."""
        from teams_service.cards.receipt_cards import get_receipt_detail_card

        receipt = {
            "id": "receipt-123",
            "original_filename": "receipt.pdf",
            "status": "REJECTED",
            "vendor_name": "Test Vendor",
            "processing_message": "Missing invoice",
        }

        card = get_receipt_detail_card(receipt)
        actions = card.get("actions", [])

        # Should only have Preview action, no Approve or Reject
        action_titles = [a.get("title") for a in actions]
        self.assertIn("Preview", action_titles)
        self.assertNotIn("Approve", action_titles)
        self.assertNotIn("Reject", action_titles)

    async def test_needs_review_card_has_both_approve_reject(self):
        """Test that NEEDS_REVIEW receipt card has both Approve and Reject actions."""
        from teams_service.cards.receipt_cards import get_receipt_detail_card

        receipt = {
            "id": "receipt-123",
            "original_filename": "receipt.pdf",
            "status": "NEEDS_REVIEW",
            "vendor_name": "Test Vendor",
        }

        card = get_receipt_detail_card(receipt)
        actions = card.get("actions", [])

        action_titles = [a.get("title") for a in actions]
        self.assertIn("Preview", action_titles)
        self.assertIn("Approve", action_titles)
        self.assertIn("Reject", action_titles)

    async def test_unique_card_has_approve_reject(self):
        """Test that UNIQUE receipt card has both Approve and Reject actions."""
        from teams_service.cards.receipt_cards import get_receipt_detail_card

        receipt = {
            "id": "receipt-123",
            "original_filename": "receipt.pdf",
            "status": "UNIQUE",
            "vendor_name": "Test Vendor",
        }

        card = get_receipt_detail_card(receipt)
        actions = card.get("actions", [])

        action_titles = [a.get("title") for a in actions]
        self.assertIn("Approve", action_titles)
        self.assertIn("Reject", action_titles)

    async def test_duplicate_card_has_no_actions(self):
        """Test that DUPLICATE receipt card has no decision actions."""
        from teams_service.cards.receipt_cards import get_receipt_detail_card

        receipt = {
            "id": "receipt-123",
            "original_filename": "receipt.pdf",
            "status": "EXACT_DUPLICATE",
            "vendor_name": "Test Vendor",
        }

        card = get_receipt_detail_card(receipt)
        actions = card.get("actions", [])

        # Should only have Preview, no Approve or Reject
        action_titles = [a.get("title") for a in actions]
        self.assertNotIn("Approve", action_titles)
        self.assertNotIn("Reject", action_titles)

    async def test_handle_decision_validation_error(self):
        """Test that decision validation errors from backend are properly handled."""
        handler = FinanceMessageHandler()
        receipt_id = "receipt-123"

        context = MagicMock()
        context.activity.value = {
            "action": "reject",
            "receipt_id": receipt_id,
            "rejection_reason": "Try to reject approved",
        }
        context.activity.text = None
        context.send = AsyncMock()

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            # Simulate backend returning validation error
            mock_client.make_receipt_decision = AsyncMock(return_value={
                "error": "Cannot change decision for receipt with status APPROVED",
                "current_status": "APPROVED",
                "code": "INVALID_STATUS_FOR_DECISION"
            })

            await handler.handle_message(context)

            # Verify error card was sent
            context.send.assert_called_once()
            call_args = context.send.call_args
            card = call_args[0][0]
            self.assertIsNotNone(card)


# Test for DjangoReceiptClient preview URL configuration
class DjangoClientConfigTests(IsolatedAsyncioTestCase):
    """Tests for DjangoReceiptClient configuration and URL generation."""

    async def test_get_receipt_preview_url_uses_public_api_url(self):
        """Test that get_receipt_preview_url() uses DJANGO_PUBLIC_API_URL, not DJANGO_API_URL."""
        from teams_service.services.django_client import DjangoReceiptClient
        from teams_service.config import config

        client = DjangoReceiptClient()
        receipt_id = "test-receipt-123"

        # Call the method
        preview_url = await client.get_receipt_preview_url(receipt_id)

        # Verify it uses DJANGO_PUBLIC_API_URL
        expected_url = f"{config.DJANGO_PUBLIC_API_URL}/receipts/{receipt_id}/preview/"
        self.assertEqual(preview_url, expected_url)

        # Verify it does NOT contain DJANGO_API_URL (localhost) when DJANGO_PUBLIC_API_URL is set
        self.assertNotIn("localhost", preview_url) if "localhost" not in config.DJANGO_PUBLIC_API_URL else None

    async def test_get_receipt_preview_url_includes_receipt_id(self):
        """Test that get_receipt_preview_url() correctly includes receipt ID."""
        from teams_service.services.django_client import DjangoReceiptClient

        client = DjangoReceiptClient()
        receipt_id = "abc-123-def-456"

        preview_url = await client.get_receipt_preview_url(receipt_id)

        # Verify receipt ID is in the URL
        self.assertIn(receipt_id, preview_url)
        self.assertIn("/preview/", preview_url)

    async def test_get_receipt_preview_url_is_https_for_ngrok(self):
        """Test that preview URL uses HTTPS when DJANGO_PUBLIC_API_URL is a public domain."""
        from teams_service.services.django_client import DjangoReceiptClient
        from teams_service.config import config
        import os

        # Verify the configured public URL starts with https for production
        if "ngrok" in config.DJANGO_PUBLIC_API_URL:
            self.assertTrue(config.DJANGO_PUBLIC_API_URL.startswith("https://"),
                          "Production DJANGO_PUBLIC_API_URL should use HTTPS for ngrok")

        client = DjangoReceiptClient()
        preview_url = await client.get_receipt_preview_url("test-id")

        # If it's an ngrok URL, it must be HTTPS
        if "ngrok" in preview_url:
            self.assertTrue(preview_url.startswith("https://"),
                          "Preview URL for ngrok should be HTTPS")


# Task 3: Dashboard Activity Update Tests
class DashboardActivityUpdateTests(IsolatedAsyncioTestCase):
    """Tests for in-place dashboard activity updates."""

    async def test_initial_dashboard_sends_new_message(self):
        """Test that initial dashboard is sent, then updated with activity_id via bootstrap."""
        handler = FinanceMessageHandler()
        context = MagicMock()
        context.activity.text = "dashboard"
        context.activity.conversation.id = "conv-123"
        context.send = AsyncMock()
        context.api = MagicMock()
        context.api.conversations.update_activity = AsyncMock()

        # Mock send to return activity with id
        sent_activity = MagicMock()
        sent_activity.id = "bootstrap-activity-id"
        context.send.return_value = sent_activity

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 0,
                "results": [],
                "next": None,
                "previous": None,
            })
            mock_client.get_categories = AsyncMock(return_value=[])
            mock_client.get_available_years = AsyncMock(return_value=[])

            await handler.handle_dashboard_request(context)

            # Initial dashboard should:
            # 1. Call context.send() once
            context.send.assert_called_once()
            # 2. Call update_activity() once for bootstrap
            context.api.conversations.update_activity.assert_called_once()
            # Verify bootstrap updated with captured activity ID
            update_call = context.api.conversations.update_activity.call_args
            self.assertEqual(update_call.kwargs["activity_id"], "bootstrap-activity-id")

    async def test_apply_filters_uses_activity_id_for_update(self):
        """Test that apply filters action uses activity_id from payload to update dashboard."""
        handler = FinanceMessageHandler()
        context = MagicMock()
        context.activity.conversation.id = "conv-123"
        context.send = AsyncMock()
        context.api = MagicMock()
        context.api.conversations.update_activity = AsyncMock()

        value = {
            "activity_id": "activity-456",  # Activity ID from bootstrap card
            "filter_status": "NEEDS_REVIEW",
            "filter_category": "",
            "filter_year": "",
            "filter_date_from": "",
            "filter_date_to": "",
            "filter_amount_min": "",
            "filter_amount_max": "",
        }

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 0,
                "results": [],
                "next": None,
                "previous": None,
            })
            mock_client.get_categories = AsyncMock(return_value=[])
            mock_client.get_available_years = AsyncMock(return_value=[])

            await handler.handle_apply_filters(context, value)

            # Should use update_activity with the activity_id from payload
            context.api.conversations.update_activity.assert_called_once()
            call_args = context.api.conversations.update_activity.call_args
            self.assertEqual(call_args.kwargs["conversation_id"], "conv-123")
            self.assertEqual(call_args.kwargs["activity_id"], "activity-456")

    async def test_clear_filters_updates_existing_activity(self):
        """Test that clear filters action with activity_id updates the dashboard."""
        handler = FinanceMessageHandler()
        context = MagicMock()
        context.activity.conversation.id = "conv-123"
        context.send = AsyncMock()
        context.api = MagicMock()
        context.api.conversations.update_activity = AsyncMock()

        value = {
            "action": "clear_filters",
            "activity_id": "activity-789",  # Activity ID from bootstrap
        }

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 0,
                "results": [],
                "next": None,
                "previous": None,
            })
            mock_client.get_categories = AsyncMock(return_value=[])
            mock_client.get_available_years = AsyncMock(return_value=[])

            # Simulate the action by calling handle_dashboard_request directly with activity_id
            await handler.handle_dashboard_request(context, dashboard_activity_id="activity-789")

            # Should use update_activity to update the dashboard
            context.api.conversations.update_activity.assert_called_once()
            call_args = context.api.conversations.update_activity.call_args
            self.assertEqual(call_args.kwargs["activity_id"], "activity-789")

    async def test_pagination_action_passes_activity_id(self):
        """Test that pagination actions with activity_id update the dashboard."""
        handler = FinanceMessageHandler()
        context = MagicMock()
        context.activity.conversation.id = "conv-123"
        context.send = AsyncMock()
        context.api = MagicMock()
        context.api.conversations.update_activity = AsyncMock()

        # Simulate a dashboard_next action
        value = {
            "page": 2,
            "filter_status": "",
            "filter_category": "",
            "filter_year": "",
            "filter_date_from": "",
            "filter_date_to": "",
            "filter_amount_min": "",
            "filter_amount_max": "",
        }

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 10,
                "results": [],
                "next": None,
                "previous": 1,
            })
            mock_client.get_categories = AsyncMock(return_value=[])
            mock_client.get_available_years = AsyncMock(return_value=[])

            # Call the pagination handler (simulated through handle_dashboard_request)
            await handler.handle_dashboard_request(
                context,
                page=2,
                dashboard_activity_id="activity-999"
            )

            # Should use update_activity instead of send
            context.api.conversations.update_activity.assert_called_once()
            context.send.assert_not_called()




class DashboardBootstrapTests(IsolatedAsyncioTestCase):
    """Tests for dashboard activity ID bootstrap mechanism."""

    async def test_initial_dashboard_sends_then_updates_with_activity_id(self):
        """Test that initial dashboard is sent, then updated with activity_id embedded."""
        handler = FinanceMessageHandler()
        context = MagicMock()
        context.activity.conversation.id = "conv-123"
        context.send = AsyncMock()
        context.api = MagicMock()
        context.api.conversations.update_activity = AsyncMock()

        # Mock the send response to return a SentActivity-like object with an id
        sent_activity = MagicMock()
        sent_activity.id = "dash-activity-456"
        context.send.return_value = sent_activity

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 2,
                "results": [
                    {"id": "r1", "vendor_name": "V1", "total_amount": "100.00", "status": "APPROVED"},
                    {"id": "r2", "vendor_name": "V2", "total_amount": "200.00", "status": "APPROVED"},
                ],
                "next": None,
            })
            mock_client.get_categories = AsyncMock(return_value=["Travel"])
            mock_client.get_available_years = AsyncMock(return_value=[2026])

            # Call with no activity_id (initial dashboard)
            await handler.handle_dashboard_request(context)

            # Verify send was called exactly once (initial send)
            self.assertEqual(context.send.call_count, 1)

            # Verify update_activity was called once (bootstrap update)
            context.api.conversations.update_activity.assert_called_once()

            # Verify the update used the captured activity ID
            update_call = context.api.conversations.update_activity.call_args
            self.assertEqual(update_call.kwargs["conversation_id"], "conv-123")
            self.assertEqual(update_call.kwargs["activity_id"], "dash-activity-456")

    async def test_apply_filters_with_activity_id_uses_update_not_send(self):
        """Test that apply filters with activity_id uses update_activity, not send."""
        handler = FinanceMessageHandler()
        context = MagicMock()
        context.activity.conversation.id = "conv-123"
        context.send = AsyncMock()
        context.api = MagicMock()
        context.api.conversations.update_activity = AsyncMock()

        value = {
            "activity_id": "dash-activity-existing",
            "filter_status": "APPROVED",
            "filter_category": "",
            "filter_year": "",
            "filter_date_from": "",
            "filter_date_to": "",
            "filter_amount_min": "",
            "filter_amount_max": "",
        }

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 1,
                "results": [{"id": "r1", "vendor_name": "V1", "total_amount": "100.00"}],
                "next": None,
            })
            mock_client.get_categories = AsyncMock(return_value=[])
            mock_client.get_available_years = AsyncMock(return_value=[])

            await handler.handle_apply_filters(context, value)

            # Should NOT send new message during normal filter apply
            context.send.assert_not_called()

            # Should update existing activity
            context.api.conversations.update_activity.assert_called_once()
            update_call = context.api.conversations.update_activity.call_args
            self.assertEqual(update_call.kwargs["activity_id"], "dash-activity-existing")

    async def test_apply_filters_without_activity_id_logs_warning(self):
        """Test that apply filters without activity_id logs a warning."""
        handler = FinanceMessageHandler()
        context = MagicMock()
        context.activity.conversation.id = "conv-123"
        context.send = AsyncMock()
        context.api = MagicMock()
        context.api.conversations.update_activity = AsyncMock()

        value = {
            # No activity_id
            "filter_status": "",
            "filter_category": "",
            "filter_year": "",
            "filter_date_from": "",
            "filter_date_to": "",
            "filter_amount_min": "",
            "filter_amount_max": "",
        }

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={"count": 0, "results": [], "next": None})
            mock_client.get_categories = AsyncMock(return_value=[])
            mock_client.get_available_years = AsyncMock(return_value=[])

            with patch('teams_service.handlers.message_handlers.logger') as mock_logger:
                await handler.handle_apply_filters(context, value)
                # Should log a warning about missing activity_id
                mock_logger.warning.assert_called()

    async def test_card_builder_includes_activity_id_in_actions(self):
        """Test that card builder properly includes activity_id in action payloads."""
        from teams_service.cards.receipt_cards import get_receipt_dashboard_card

        receipts = [{"id": "r1", "vendor_name": "V1", "total_amount": "100.00", "status": "APPROVED"}]
        categories = ["Travel"]
        years = [2026]

        # Build card with activity_id
        card_dict = get_receipt_dashboard_card(
            receipts,
            categories=categories,
            years=years,
            activity_id="test-dash-activity-id",
        )

        # Verify action payloads contain activity_id
        found_activity_id_in_action = False
        for body_item in card_dict.get("body", []):
            if body_item.get("type") == "ActionSet" and "actions" in body_item:
                for action in body_item["actions"]:
                    if action.get("data", {}).get("action") in ["apply_filters", "clear_filters", "dashboard_next", "dashboard_previous"]:
                        if action["data"].get("activity_id") == "test-dash-activity-id":
                            found_activity_id_in_action = True

        self.assertTrue(found_activity_id_in_action, "No action found with activity_id in card")

    async def test_card_builder_without_activity_id_has_none(self):
        """Test that card builder correctly sets activity_id to None when not provided."""
        from teams_service.cards.receipt_cards import get_receipt_dashboard_card

        receipts = [{"id": "r1", "vendor_name": "V1", "total_amount": "100.00"}]
        categories = []
        years = []

        # Build card without activity_id
        card_dict = get_receipt_dashboard_card(
            receipts,
            categories=categories,
            years=years,
            activity_id=None,
        )

        # Verify that actions have activity_id=None
        for body_item in card_dict.get("body", []):
            if body_item.get("type") == "ActionSet" and "actions" in body_item:
                for action in body_item["actions"]:
                    if action.get("data", {}).get("action") in ["apply_filters", "clear_filters"]:
                        self.assertIsNone(action["data"].get("activity_id"))
