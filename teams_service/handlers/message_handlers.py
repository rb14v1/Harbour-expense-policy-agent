"""
Teams Message Handlers

Handles Teams bot messages and invocations for Finance receipt review.
"""
import logging
from typing import Optional, Any
from microsoft_teams.apps.routing.activity_context import ActivityContext
from teams_service.services.django_client import django_client
from teams_service.cards.receipt_cards import (
    get_receipt_list_card,
    get_receipt_detail_card,
    get_decision_confirmation_card,
    get_error_card,
)

logger = logging.getLogger(__name__)


class FinanceMessageHandler:
    """Handles Finance-related Teams messages."""

    async def handle_message(self, context: ActivityContext) -> Optional[Any]:
        """
        Handle incoming Teams message.

        Routes based on message content to appropriate handler.
        """
        activity = context.activity
        message_text = activity.text if hasattr(activity, "text") else ""
        message_text = (message_text or "").lower().strip()

        logger.info(f"Received message: {message_text}")

        if "list" in message_text or "receipts" in message_text or message_text == "" or message_text == "hi" or message_text == "hello":
            return await self.handle_list_receipts(context)
        elif "detail" in message_text or "open" in message_text:
            return await self.handle_open_receipt(context)
        elif "help" in message_text:
            return self._get_help_message()
        else:
            return await self.handle_list_receipts(context)

    async def handle_list_receipts(self, context: ActivityContext) -> dict:
        """Handle request to list Finance-pending receipts."""
        try:
            response = await django_client.get_receipts(status="NEEDS_REVIEW", page=1)

            card = get_receipt_list_card(response.get("results", []))

            return {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "contentUrl": None,
                        "content": card,
                    }
                ],
            }
        except Exception as e:
            logger.error(f"Error listing receipts: {e}")
            card = get_error_card("Could not retrieve receipts. Please try again later.")
            return {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "contentUrl": None,
                        "content": card,
                    }
                ],
            }

    async def handle_open_receipt(self, context: ActivityContext) -> dict:
        """
        Handle request to open/view receipt details.

        In a real implementation, this would parse receipt ID from message
        or use Teams deep link data.
        """
        return {
            "type": "message",
            "text": "Please use the Finance Review tab to open receipt details and make decisions.",
        }

    async def handle_receipt_action(
        self, context: ActivityContext, receipt_id: str, action: str
    ) -> dict:
        """
        Handle Finance decision action (approve/reject).

        Called from Teams adaptive card action.
        """
        if action not in ["approve", "reject"]:
            return get_error_card(f"Invalid action: {action}")

        decision = "APPROVED" if action == "approve" else "REJECTED"

        try:
            # Submit decision to Django
            result = await django_client.make_receipt_decision(receipt_id, decision)

            if result is None:
                return get_error_card(f"Receipt {receipt_id} not found.")

            card = get_decision_confirmation_card(receipt_id, decision)

            return {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "contentUrl": None,
                        "content": card,
                    }
                ],
            }

        except Exception as e:
            logger.error(f"Error making decision for receipt {receipt_id}: {e}")
            return get_error_card(
                f"Could not submit decision for receipt {receipt_id}. Please try again."
            )

    @staticmethod
    def _get_welcome_message() -> dict:
        """Get welcome message."""
        return {
            "type": "message",
            "text": "Welcome to Expense Policy Agent - Finance Review!\n\n"
            "Available commands:\n"
            "- **list** — View receipts\n"
            "- **help** — Get help\n\n"
            "Or use the Finance Review tab to see all receipts and make decisions.",
        }

    @staticmethod
    def _get_help_message() -> dict:
        """Get help message."""
        return {
            "type": "message",
            "text": "**Expense Policy Agent - Finance Review**\n\n"
            "**Commands:**\n"
            "- **list** — List receipts\n"
            "- **detail** — View receipt details\n\n"
            "**Actions in Finance Tab:**\n"
            "- View receipt list with filters\n"
            "- See receipt details and duplicate information\n"
            "- Preview receipt file\n"
            "- Approve or reject receipts\n\n"
            "Questions? Contact support.",
        }


# Create global handler instance
finance_handler = FinanceMessageHandler()
