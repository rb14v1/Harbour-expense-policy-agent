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
