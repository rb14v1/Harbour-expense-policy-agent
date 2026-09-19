"""
Finance Tab endpoints for Teams.
Provides Finance department with a Teams tab for reviewing and approving receipts.
"""
import logging
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)


class FinanceTabHandler:
    """Handles Finance Tab interactions in Teams."""

    def __init__(self, django_api_url: str = "http://localhost:8000/api/v1"):
        self.django_api_url = django_api_url
        self.finance_api_url = f"{django_api_url.replace('/api/v1', '')}/finance/api"

    def get_tab_config(self) -> Dict[str, Any]:
        """
        Get tab configuration for Finance Tab.
        Returns the configuration that Teams will use to load the Finance dashboard.
        """
        return {
            "tabName": "Finance Review",
            "contentUrl": "https://localhost:3000/finance/tab",
            "website": "https://localhost:3000/finance",
            "entityId": "finance-review",
            "scopes": ["team"],
            "context": ["channelTab"]
        }

    def get_receipt_list_url(self, filters: Dict[str, Any] = None) -> str:
        """
        Build URL for fetching receipts with filters.
        Supports: status, category, vendor, filename, date_from, date_to, amount_min, amount_max, page
        """
        url = f"{self.finance_api_url}/receipts/"

        if filters:
            params = []
            for key, value in filters.items():
                if value is not None:
                    params.append(f"{key}={value}")

            if params:
                url += "?" + "&".join(params)

        return url

    def get_receipt_detail_url(self, receipt_id: str) -> str:
        """Get URL to fetch receipt details."""
        return f"{self.finance_api_url}/receipts/{receipt_id}/"

    def get_receipt_preview_url(self, receipt_id: str) -> str:
        """Get URL to preview receipt file."""
        return f"{self.django_api_url}/receipts/{receipt_id}/preview/"

    def get_receipt_decision_url(self, receipt_id: str) -> str:
        """Get URL to submit Finance decision (approve/reject)."""
        return f"{self.finance_api_url}/receipts/{receipt_id}/decision/"

    def get_adaptive_card_for_receipt(self, receipt: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build Adaptive Card for receipt display in Teams.
        Shows key information and action buttons for Finance review.
        """
        status = receipt.get('status', 'UNKNOWN')
        status_color = self._get_status_color(status)

        body = [
            {
                "type": "TextBlock",
                "text": f"Receipt: {receipt.get('original_filename', 'Unknown')}",
                "weight": "bolder",
                "size": "large",
                "color": status_color
            },
            {
                "type": "TextBlock",
                "text": f"Status: {status}",
                "weight": "bolder",
                "size": "medium"
            }
        ]

        # Receipt details
        details = []
        if receipt.get('vendor_name'):
            details.append(f"Vendor: {receipt['vendor_name']}")
        if receipt.get('transaction_date'):
            details.append(f"Date: {receipt['transaction_date']}")
        if receipt.get('total_amount'):
            details.append(f"Amount: {receipt['total_amount']} {receipt.get('currency', 'N/A')}")
        if receipt.get('category'):
            details.append(f"Category: {receipt['category']}")

        if details:
            body.append({
                "type": "TextBlock",
                "text": "\n".join(details),
                "wrap": True,
                "spacing": "medium"
            })

        # Duplicate information
        if status in ['EXACT_DUPLICATE', 'SEMANTIC_DUPLICATE']:
            duplicate_text = f"Duplicate Type: {status}"
            if receipt.get('duplicate_score'):
                duplicate_text += f"\nDuplicate Score: {receipt['duplicate_score']}"
            if receipt.get('duplicate_reason'):
                duplicate_text += f"\nReason: {receipt['duplicate_reason']}"

            body.append({
                "type": "TextBlock",
                "text": duplicate_text,
                "wrap": True,
                "spacing": "medium",
                "isSubtle": True,
                "color": "warning"
            })

        # Policy information
        if receipt.get('policy_status'):
            body.append({
                "type": "TextBlock",
                "text": f"Policy Status: {receipt['policy_status']}",
                "wrap": True,
                "spacing": "medium",
                "isSubtle": True
            })

        body.append({
            "type": "TextBlock",
            "text": f"ID: {receipt.get('id', 'N/A')}",
            "wrap": True,
            "spacing": "medium",
            "isSubtle": True,
            "size": "small"
        })

        # Action buttons
        actions = [
            {
                "type": "Action.OpenUrl",
                "title": "View Details",
                "url": f"https://localhost:3000/finance/receipts/{receipt.get('id')}"
            },
            {
                "type": "Action.OpenUrl",
                "title": "Preview Receipt",
                "url": f"https://localhost:3000/finance/receipts/{receipt.get('id')}/preview"
            }
        ]

        # Add approve/reject actions if receipt is awaiting decision
        if status not in ['APPROVED', 'REJECTED', 'EXACT_DUPLICATE', 'SEMANTIC_DUPLICATE']:
            actions.append({
                "type": "Action.OpenUrl",
                "title": "Approve",
                "url": f"https://localhost:3000/finance/receipts/{receipt.get('id')}/approve"
            })
            actions.append({
                "type": "Action.OpenUrl",
                "title": "Reject",
                "url": f"https://localhost:3000/finance/receipts/{receipt.get('id')}/reject"
            })

        return {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body,
            "actions": actions
        }

    @staticmethod
    def _get_status_color(status: str) -> str:
        """Get color for status display."""
        colors = {
            'APPROVED': 'good',
            'REJECTED': 'attention',
            'UNIQUE': 'good',
            'EXACT_DUPLICATE': 'warning',
            'SEMANTIC_DUPLICATE': 'warning',
            'NEEDS_REVIEW': 'accent',
            'FAILED': 'attention',
        }
        return colors.get(status, 'default')


def create_finance_tab_handler(django_api_url: str = None) -> FinanceTabHandler:
    """Factory function to create Finance Tab handler."""
    import os
    if django_api_url is None:
        django_api_url = os.getenv("DJANGO_API_URL", "http://localhost:8000/api/v1")

    return FinanceTabHandler(django_api_url)
