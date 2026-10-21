"""
Teams Message Handlers

Handles Teams bot messages and invocations for Finance receipt review.
"""
import logging
from typing import Optional, Any, Dict
from microsoft_teams.apps.routing.activity_context import ActivityContext
from microsoft_teams.cards import AdaptiveCard
from teams_service.services.django_client import django_client
from teams_service.config import config
from teams_service.cards.receipt_cards import (
    get_receipt_list_card,
    get_receipt_detail_card,
    get_decision_confirmation_card,
    get_error_card,
    get_receipt_dashboard_card,
    get_filtered_results_card,
    get_user_manual_card,
)

logger = logging.getLogger(__name__)


class FinanceMessageHandler:
    """Handles Finance-related Teams messages."""

    async def handle_message(self, context: ActivityContext) -> None:
        """
        Handle incoming Teams message.

        Routes based on message content or Adaptive Card action to appropriate handler.
        """
        activity = context.activity
        message_text = activity.text if hasattr(activity, "text") else ""
        message_text = (message_text or "").lower().strip()

        logger.info(f"Received message: {message_text}")

        # Check if this is an Adaptive Card action submission
        value = getattr(activity, "value", None)
        if value and isinstance(value, dict):
            action = value.get("action", "").lower()
            receipt_id = value.get("receipt_id", "")

            logger.info(f"Received action: {action} for receipt: {receipt_id}")

            if action == "open_receipt":
                await self.handle_open_receipt(context, receipt_id)
            elif action == "approve":
                rejection_reason = value.get("rejection_reason", "").strip()
                await self.handle_receipt_action(context, receipt_id, "approve", rejection_reason)
            elif action == "reject":
                rejection_reason = value.get("rejection_reason", "").strip()
                await self.handle_receipt_action(context, receipt_id, "reject", rejection_reason)
            elif action == "preview_receipt":
                await self.handle_preview_action(context, receipt_id)
            elif action == "apply_filters":
                await self.handle_apply_filters(context, value)
            elif action == "clear_filters":
                dashboard_activity_id = value.get("activity_id")
                if not dashboard_activity_id:
                    logger.warning("Clear Filters action missing activity_id in payload. Dashboard may not update in-place.")
                logger.debug(f"Clearing filters, activity_id={dashboard_activity_id}")
                await self.handle_dashboard_request(context, dashboard_activity_id=dashboard_activity_id)
            elif action == "dashboard_next":
                page = value.get("page", 1)
                dashboard_activity_id = value.get("activity_id")
                if not dashboard_activity_id:
                    logger.warning("Next page action missing activity_id in payload. Dashboard may not update in-place.")
                filters = self._extract_filters_from_value(value)
                logger.debug(f"Paginating to page {page}, activity_id={dashboard_activity_id}")
                await self.handle_dashboard_request(context, page=page, dashboard_activity_id=dashboard_activity_id, **filters)
            elif action == "dashboard_previous":
                page = value.get("page", 1)
                dashboard_activity_id = value.get("activity_id")
                if not dashboard_activity_id:
                    logger.warning("Previous page action missing activity_id in payload. Dashboard may not update in-place.")
                filters = self._extract_filters_from_value(value)
                logger.debug(f"Paginating to page {page}, activity_id={dashboard_activity_id}")
                await self.handle_dashboard_request(context, page=page, dashboard_activity_id=dashboard_activity_id, **filters)
            else:
                logger.warning(f"Unknown action: {action}")
                card_dict = get_error_card(f"Unknown action: {action}")
                card = AdaptiveCard.model_validate(card_dict)
                await context.send(card)
            return

        # Text-based message routing
        if "dashboard" in message_text:
            await self.handle_dashboard_request(context)
        elif "manual" in message_text or "user manual" in message_text:
            await self.handle_user_manual(context)
        elif "list" in message_text or "receipts" in message_text or message_text == "" or message_text == "hi" or message_text == "hello":
            await self.handle_list_receipts(context)
        elif "detail" in message_text or "open" in message_text:
            await self.handle_open_receipt(context)
        elif "help" in message_text:
            await context.send(self._get_help_message())
        else:
            await self.handle_list_receipts(context)

    async def handle_user_manual(self, context: ActivityContext) -> None:
        """Handle request to view User Manual."""
        logger.info("Received user manual request")

        try:
            card_dict = get_user_manual_card(config.PUBLIC_FRONTEND_URL)
            card = AdaptiveCard.model_validate(card_dict)
            await context.send(card)
        except Exception as e:
            logger.error(f"Error generating user manual card: {e}")
            card_dict = get_error_card("Failed to load user manual. Please try again later.")
            card = AdaptiveCard.model_validate(card_dict)
            await context.send(card)

    async def handle_list_receipts(self, context: ActivityContext) -> None:
        """Handle request to list Finance-pending receipts."""
        try:
            response = await django_client.get_receipts(status="NEEDS_REVIEW", page=1)

            card_dict = get_receipt_list_card(response.get("results", []))
            card = AdaptiveCard.model_validate(card_dict)

            await context.send(card)
        except Exception as e:
            logger.error(f"Error listing receipts: {e}")
            card_dict = get_error_card("Could not retrieve receipts. Please try again later.")
            card = AdaptiveCard.model_validate(card_dict)
            await context.send(card)

    async def handle_open_receipt(self, context: ActivityContext, receipt_id: Optional[str] = None) -> None:
        """
        Handle request to open/view receipt details.

        If receipt_id is provided (from action), fetch and display that receipt.
        Otherwise, return error message.
        """
        if not receipt_id:
            await context.send("Please select a receipt from the list above.")
            return

        try:
            receipt = await django_client.get_receipt_detail(receipt_id)

            if receipt is None:
                card_dict = get_error_card(f"Receipt {receipt_id} not found.")
                card = AdaptiveCard.model_validate(card_dict)
                await context.send(card)
                return

            card_dict = get_receipt_detail_card(receipt)
            card = AdaptiveCard.model_validate(card_dict)

            await context.send(card)

        except Exception as e:
            logger.error(f"Error opening receipt {receipt_id}: {e}")
            card_dict = get_error_card(f"Could not load receipt {receipt_id}. Please try again later.")
            card = AdaptiveCard.model_validate(card_dict)
            await context.send(card)

    async def handle_receipt_action(
        self, context: ActivityContext, receipt_id: str, action: str, notes: str = ""
    ) -> None:
        """
        Handle Finance decision action (approve/reject).

        Called from Teams adaptive card action.

        Backend validation ensures:
        - Receipt must be in NEEDS_REVIEW or UNIQUE status
        - Cannot change APPROVED to REJECTED or vice versa
        - Cannot approve/reject the same receipt twice

        Args:
            context: Activity context
            receipt_id: Receipt UUID
            action: "approve" or "reject"
            notes: Optional rejection reason or approval notes
        """
        if not receipt_id:
            card_dict = get_error_card("Receipt ID is missing.")
            card = AdaptiveCard.model_validate(card_dict)
            await context.send(card)
            return

        if action not in ["approve", "reject"]:
            card_dict = get_error_card(f"Invalid action: {action}")
            card = AdaptiveCard.model_validate(card_dict)
            await context.send(card)
            return

        decision = "APPROVED" if action == "approve" else "REJECTED"

        try:
            # Submit decision to Django
            result = await django_client.make_receipt_decision(receipt_id, decision, notes=notes if notes else None)

            if result is None:
                card_dict = get_error_card(f"Receipt {receipt_id} not found.")
                card = AdaptiveCard.model_validate(card_dict)
                await context.send(card)
                return

            # Check for backend validation errors
            if "error" in result and isinstance(result, dict):
                error_msg = result.get("error", "Decision could not be submitted")
                card_dict = get_error_card(error_msg)
                card = AdaptiveCard.model_validate(card_dict)
                await context.send(card)
                return

            card_dict = get_decision_confirmation_card(receipt_id, decision, notes=notes if notes else None)
            card = AdaptiveCard.model_validate(card_dict)

            await context.send(card)

        except Exception as e:
            logger.error(f"Error making decision for receipt {receipt_id}: {e}")
            card_dict = get_error_card(
                f"Could not submit decision for receipt {receipt_id}. Please try again."
            )
            card = AdaptiveCard.model_validate(card_dict)
            await context.send(card)

    async def handle_preview_action(self, context: ActivityContext, receipt_id: str) -> None:
        """
        Handle receipt preview action.

        Returns a message with preview URL that Finance can use to view the receipt.
        """
        if not receipt_id:
            card_dict = get_error_card("Receipt ID is missing.")
            card = AdaptiveCard.model_validate(card_dict)
            await context.send(card)
            return

        try:
            preview_url = await django_client.get_receipt_preview_url(receipt_id)

            card_dict = {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Receipt Preview",
                        "weight": "bolder",
                        "size": "large",
                    }
                ],
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "🔗 View Receipt File",
                        "url": preview_url,
                    }
                ]
            }
            card = AdaptiveCard.model_validate(card_dict)
            await context.send(card)

        except Exception as e:
            logger.error(f"Error getting preview for receipt {receipt_id}: {e}")
            card_dict = get_error_card(f"Could not load preview for receipt {receipt_id}.")
            card = AdaptiveCard.model_validate(card_dict)
            await context.send(card)

    async def handle_dashboard_request(
        self,
        context: ActivityContext,
        page: int = 1,
        status: Optional[str] = None,
        category: Optional[str] = None,
        year: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        amount_min: Optional[str] = None,
        amount_max: Optional[str] = None,
        dashboard_activity_id: Optional[str] = None,
    ) -> None:
        """Handle request to display Finance Dashboard with all receipts and optional filters.

        Behavior:
        - No filters provided: Send full Dashboard card WITH filter controls and bootstrap with activity_id
        - Filters provided: Send Filtered Results card WITHOUT filter controls (separate new message)
        """
        try:
            # Check if ANY filter is applied
            has_filters = any([status, category, year, date_from, date_to, amount_min, amount_max])

            date_from_api = None
            date_to_api = None
            if year and year != "":
                date_from_api = f"{year}-01-01"
                date_to_api = f"{year}-12-31"
            elif date_from or date_to:
                date_from_api = date_from
                date_to_api = date_to

            response = await django_client.get_receipts(
                status=status if status else None,
                category=category if category else None,
                date_from=date_from_api,
                date_to=date_to_api,
                amount_min=amount_min if amount_min else None,
                amount_max=amount_max if amount_max else None,
                page=page
            )

            receipts = response.get("results", [])
            has_next = response.get("next") is not None

            # If filters are applied, send filtered results card (simpler, no filter UI)
            if has_filters:
                logger.debug(f"Filters applied, sending filtered results card")
                card_dict = get_filtered_results_card(
                    receipts,
                    page=page,
                    has_next=has_next,
                    status=status,
                    category=category,
                    year=year,
                    date_from=date_from,
                    date_to=date_to,
                    amount_min=amount_min,
                    amount_max=amount_max,
                )
                card = AdaptiveCard.model_validate(card_dict)
                await context.send(card)
                return

            # No filters: send full dashboard card WITH filter controls
            categories = await django_client.get_categories()
            years = await django_client.get_available_years()

            # Build card with activity_id if we have one
            card_dict = get_receipt_dashboard_card(
                receipts,
                categories=categories,
                years=years,
                page=page,
                has_next=has_next,
                activity_id=dashboard_activity_id,
                status=status,
                category=category,
                year=year,
                date_from=date_from,
                date_to=date_to,
                amount_min=amount_min,
                amount_max=amount_max,
            )
            card = AdaptiveCard.model_validate(card_dict)

            if dashboard_activity_id:
                # Update existing dashboard activity with filtered/paginated results
                await self._update_dashboard_activity(context, dashboard_activity_id, card)
            else:
                # Initial dashboard: send it, capture ID, then immediately update with ID in actions
                sent_activity = await context.send(card)
                captured_activity_id = sent_activity.id
                logger.debug(f"Initial dashboard sent with activity ID: {captured_activity_id}")

                # Rebuild card with the captured activity_id in action payloads
                card_dict = get_receipt_dashboard_card(
                    receipts,
                    categories=categories,
                    years=years,
                    page=page,
                    has_next=has_next,
                    activity_id=captured_activity_id,
                    status=status,
                    category=category,
                    year=year,
                    date_from=date_from,
                    date_to=date_to,
                    amount_min=amount_min,
                    amount_max=amount_max,
                )
                card = AdaptiveCard.model_validate(card_dict)

                # Update the same activity with the card that now contains activity_id
                try:
                    await self._update_dashboard_activity(context, captured_activity_id, card)
                    logger.debug(f"Dashboard bootstrapped with activity_id in action payloads")
                except Exception as bootstrap_error:
                    logger.error(f"Failed to bootstrap dashboard with activity_id: {bootstrap_error}")
                    # Dashboard is already visible (from initial send), so just log the error
                    # Future filter actions won't be able to update, but card is still functional

        except Exception as e:
            logger.error(f"Error displaying dashboard: {e}")
            card_dict = get_error_card("Could not load Finance Dashboard. Please try again later.")
            card = AdaptiveCard.model_validate(card_dict)

            # Only send error if not updating (initial dashboard)
            if not dashboard_activity_id:
                await context.send(card)
            else:
                # If update fails when updating, try to update error card; if that fails, send new
                try:
                    await self._update_dashboard_activity(context, dashboard_activity_id, card)
                except Exception as fallback_error:
                    logger.error(f"Failed to update dashboard on error: {fallback_error}")
                    await context.send(card)

    async def _update_dashboard_activity(
        self,
        context: ActivityContext,
        dashboard_activity_id: str,
        card: AdaptiveCard,
    ) -> None:
        """Update an existing dashboard activity in-place using the Teams API.

        This prevents creating duplicate dashboard messages when filters change.
        """
        from microsoft_teams.api import MessageActivityInput

        conversation_id = context.activity.conversation.id

        # Convert AdaptiveCard to MessageActivityInput
        activity_input = MessageActivityInput(
            id=dashboard_activity_id,
            type="message",
            text="Finance Dashboard",
            attachments=[{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card.model_dump(exclude_unset=True),
            }]
        )

        await context.api.conversations.update_activity(
            conversation_id=conversation_id,
            activity_id=dashboard_activity_id,
            activity=activity_input,
        )

        logger.debug(f"Updated dashboard activity {dashboard_activity_id} in conversation {conversation_id}")

    async def handle_apply_filters(self, context: ActivityContext, value: Dict[str, Any]) -> None:
        """Handle apply filters action from dashboard.

        Updates the existing dashboard activity instead of sending a new message.
        The activity_id is embedded in the action payload by the dashboard card bootstrap.
        """
        dashboard_activity_id = value.get("activity_id")

        if not dashboard_activity_id:
            # Activity ID should be in the bootstrap card's action payloads
            logger.warning(
                "Apply Filters action missing activity_id in payload. "
                "This indicates the dashboard card was not properly bootstrapped. "
                "Dashboard will fall back to normal update behavior."
            )

        status = (value.get("filter_status") or "").strip()
        category = (value.get("filter_category") or "").strip()
        year = (value.get("filter_year") or "").strip()
        date_from = (value.get("filter_date_from") or "").strip()
        date_to = (value.get("filter_date_to") or "").strip()
        amount_min = (value.get("filter_amount_min") or "").strip()
        amount_max = (value.get("filter_amount_max") or "").strip()

        logger.debug(f"Applying filters: status={status}, category={category}, year={year}, activity_id={dashboard_activity_id}")

        await self.handle_dashboard_request(
            context,
            page=1,
            status=status if status else None,
            category=category if category else None,
            year=year if year else None,
            date_from=date_from if date_from else None,
            date_to=date_to if date_to else None,
            amount_min=amount_min if amount_min else None,
            amount_max=amount_max if amount_max else None,
            dashboard_activity_id=dashboard_activity_id,
        )

    @staticmethod
    def _extract_filters_from_value(value: Dict[str, Any]) -> Dict[str, Any]:
        """Extract filter parameters from action value."""
        return {
            "status": (value.get("filter_status") or "").strip() or None,
            "category": (value.get("filter_category") or "").strip() or None,
            "year": (value.get("filter_year") or "").strip() or None,
            "date_from": (value.get("filter_date_from") or "").strip() or None,
            "date_to": (value.get("filter_date_to") or "").strip() or None,
            "amount_min": (value.get("filter_amount_min") or "").strip() or None,
            "amount_max": (value.get("filter_amount_max") or "").strip() or None,
        }

    @staticmethod
    def _get_welcome_message() -> str:
        """Get welcome message."""
        return ("Welcome to Expense Policy Agent - Finance Review!\n\n"
                "Available commands:\n"
                "- **list** — View receipts\n"
                "- **help** — Get help\n\n"
                "Or use the Finance Review tab to see all receipts and make decisions.")

    @staticmethod
    def _get_help_message() -> str:
        """Get help message."""
        return ("**Expense Policy Agent - Finance Review**\n\n"
                "**Commands:**\n"
                "- **list** — List receipts\n"
                "- **detail** — View receipt details\n"
                "- **manual** — View user manual\n"
                "- **dashboard** — View finance dashboard\n\n"
                "**Actions in Finance Tab:**\n"
                "- View receipt list with filters\n"
                "- See receipt details and duplicate information\n"
                "- Preview receipt file\n"
                "- Approve or reject receipts\n\n"
                "Questions? Contact support.")


# Create global handler instance
finance_handler = FinanceMessageHandler()
