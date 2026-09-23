"""
Tests for Teams Message Handlers

Tests for Part 1: Finance-pending receipt list functionality.
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

            response = await handler.handle_message(context)

            # Verify get_receipts was called with NEEDS_REVIEW filter
            mock_client.get_receipts.assert_called_once_with(status="NEEDS_REVIEW", page=1)

            # Verify response is an attachment with card
            self.assertEqual(response["type"], "message")
            self.assertIn("attachments", response)
            self.assertGreater(len(response["attachments"]), 0)

    async def test_handle_message_hello_returns_pending_receipts(self):
        """Test that 'hello' message triggers pending Finance receipt list."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = "hello"
        context.activity.from_property.id = "user123"

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 0,
                "results": [],
                "next": None,
                "previous": None,
            })

            response = await handler.handle_message(context)

            # Verify get_receipts was called with NEEDS_REVIEW filter
            mock_client.get_receipts.assert_called_once_with(status="NEEDS_REVIEW", page=1)
            self.assertEqual(response["type"], "message")

    async def test_handle_message_list_returns_pending_receipts(self):
        """Test that 'list' message triggers pending Finance receipt list."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = "list"
        context.activity.from_property.id = "user123"

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

            response = await handler.handle_message(context)

            # Verify get_receipts was called with NEEDS_REVIEW filter
            mock_client.get_receipts.assert_called_once_with(status="NEEDS_REVIEW", page=1)
            self.assertEqual(response["type"], "message")

    async def test_handle_message_empty_returns_pending_receipts(self):
        """Test that empty message triggers pending Finance receipt list."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = ""
        context.activity.from_property.id = "user123"

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 0,
                "results": [],
                "next": None,
                "previous": None,
            })

            response = await handler.handle_message(context)

            # Verify get_receipts was called with NEEDS_REVIEW filter
            mock_client.get_receipts.assert_called_once_with(status="NEEDS_REVIEW", page=1)
            self.assertEqual(response["type"], "message")

    async def test_handle_message_no_pending_receipts(self):
        """Test handling when there are no pending Finance receipts."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = "list"
        context.activity.from_property.id = "user123"

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(return_value={
                "count": 0,
                "results": [],
                "next": None,
                "previous": None,
            })

            response = await handler.handle_message(context)

            # Should still return a valid card (empty state)
            self.assertEqual(response["type"], "message")
            self.assertIn("attachments", response)
            self.assertGreater(len(response["attachments"]), 0)

    async def test_handle_message_api_error(self):
        """Test error handling when API call fails."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = "list"
        context.activity.from_property.id = "user123"

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            mock_client.get_receipts = AsyncMock(side_effect=Exception("API Error"))

            response = await handler.handle_message(context)

            # Should return error card
            self.assertEqual(response["type"], "message")
            self.assertIn("attachments", response)

    async def test_handle_message_help_not_pending_list(self):
        """Test that 'help' does NOT return pending receipts list."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = "help"
        context.activity.from_property.id = "user123"

        with patch('teams_service.handlers.message_handlers.django_client') as mock_client:
            response = await handler.handle_message(context)

            # Verify get_receipts was NOT called
            mock_client.get_receipts.assert_not_called()

            # Should return help message
            self.assertEqual(response["type"], "message")
            self.assertIn("Commands", response.get("text", "") or "")

    async def test_status_filter_is_needs_review(self):
        """Test that the handler specifically requests NEEDS_REVIEW status."""
        handler = FinanceMessageHandler()

        context = MagicMock()
        context.activity.text = "receipts"
        context.activity.from_property.id = "user123"

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
