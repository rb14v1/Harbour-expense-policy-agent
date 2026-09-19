"""
Adaptive Cards for Receipt Display in Teams

Generates Adaptive Cards for:
- Receipt list
- Receipt details
- Duplicate warnings
- Decision prompts
"""
from typing import Dict, Any, Optional, List
from datetime import datetime


def get_receipt_list_card(receipts: List[Dict[str, Any]], page: int = 1) -> Dict[str, Any]:
    """Generate card for receipt list with summary."""
    if not receipts:
        return {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "No receipts found",
                    "weight": "bolder",
                    "size": "medium",
                }
            ],
        }

    body = [
        {
            "type": "TextBlock",
            "text": f"Receipts (Page {page})",
            "weight": "bolder",
            "size": "large",
        }
    ]

    for receipt in receipts:
        body.append({
            "type": "TextBlock",
            "text": f"📄 {receipt.get('original_filename', 'Unknown')}",
            "weight": "bolder",
            "size": "medium",
            "spacing": "medium",
        })

        details = []
        if receipt.get("vendor_name"):
            details.append(f"Vendor: {receipt['vendor_name']}")
        if receipt.get("transaction_date"):
            details.append(f"Date: {receipt['transaction_date']}")
        if receipt.get("total_amount"):
            details.append(f"Amount: {receipt['total_amount']} {receipt.get('currency', '')}")
        if receipt.get("status"):
            details.append(f"Status: {receipt['status']}")

        if details:
            body.append({
                "type": "TextBlock",
                "text": "\n".join(details),
                "wrap": True,
                "size": "small",
                "isSubtle": True,
            })

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": body,
    }


def get_receipt_detail_card(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """Generate detailed card for single receipt."""
    status = receipt.get("status", "UNKNOWN")
    status_color = _get_status_color(status)

    body = [
        {
            "type": "TextBlock",
            "text": f"Receipt: {receipt.get('original_filename', 'Unknown')}",
            "weight": "bolder",
            "size": "large",
            "color": status_color,
        },
        {
            "type": "TextBlock",
            "text": f"Status: {status}",
            "weight": "bolder",
            "size": "medium",
            "spacing": "medium",
        }
    ]

    # Receipt details
    details = []
    if receipt.get("vendor_name"):
        details.append(f"**Vendor:** {receipt['vendor_name']}")
    if receipt.get("transaction_date"):
        details.append(f"**Date:** {receipt['transaction_date']}")
    if receipt.get("total_amount"):
        details.append(f"**Amount:** {receipt['total_amount']} {receipt.get('currency', '')}")
    if receipt.get("category"):
        details.append(f"**Category:** {receipt['category']}")

    if details:
        body.append({
            "type": "TextBlock",
            "text": "\n".join(details),
            "wrap": True,
            "spacing": "medium",
        })

    # Duplicate information
    if status in ["EXACT_DUPLICATE", "SEMANTIC_DUPLICATE"]:
        dup_details = [f"**Type:** {status}"]
        if receipt.get("duplicate_score"):
            dup_details.append(f"**Score:** {receipt['duplicate_score']}")
        if receipt.get("duplicate_reason"):
            dup_details.append(f"**Reason:** {receipt['duplicate_reason']}")

        body.append({
            "type": "TextBlock",
            "text": "\n".join(dup_details),
            "wrap": True,
            "spacing": "medium",
            "color": "warning",
            "weight": "bolder",
        })

    # Policy information
    if receipt.get("policy_status"):
        body.append({
            "type": "TextBlock",
            "text": f"**Policy Status:** {receipt['policy_status']}",
            "wrap": True,
            "spacing": "medium",
        })

    # Action buttons
    actions = [
        {
            "type": "Action.OpenUrl",
            "title": "📋 View Full Details",
            "url": f"https://teams.microsoft.com/l/entity/finance-review/receipts/{receipt['id']}",
        },
        {
            "type": "Action.OpenUrl",
            "title": "👁️ Preview Receipt",
            "url": f"https://teams.microsoft.com/l/entity/finance-review/receipts/{receipt['id']}/preview",
        },
    ]

    # Add approve/reject actions if receipt is not yet decided
    if status not in ["APPROVED", "REJECTED", "EXACT_DUPLICATE", "SEMANTIC_DUPLICATE"]:
        actions.append({
            "type": "Action.Submit",
            "title": "✅ Approve",
            "data": {
                "action": "approve_receipt",
                "receipt_id": receipt["id"],
            }
        })
        actions.append({
            "type": "Action.Submit",
            "title": "❌ Reject",
            "data": {
                "action": "reject_receipt",
                "receipt_id": receipt["id"],
            }
        })

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": body,
        "actions": actions,
    }


def get_decision_confirmation_card(receipt_id: str, decision: str) -> Dict[str, Any]:
    """Generate confirmation card after decision."""
    icon = "✅" if decision == "APPROVED" else "❌"
    color = "good" if decision == "APPROVED" else "attention"

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": f"{icon} Receipt {decision}",
                "weight": "bolder",
                "size": "large",
                "color": color,
            },
            {
                "type": "TextBlock",
                "text": f"Receipt ID: {receipt_id}",
                "wrap": True,
                "size": "small",
                "isSubtle": True,
            },
            {
                "type": "TextBlock",
                "text": f"Timestamp: {datetime.utcnow().isoformat()}Z",
                "wrap": True,
                "size": "small",
                "isSubtle": True,
            }
        ]
    }


def get_error_card(error_message: str) -> Dict[str, Any]:
    """Generate error card."""
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "⚠️ Error",
                "weight": "bolder",
                "size": "medium",
                "color": "attention",
            },
            {
                "type": "TextBlock",
                "text": error_message,
                "wrap": True,
            }
        ]
    }


def _get_status_color(status: str) -> str:
    """Get color for receipt status."""
    colors = {
        "APPROVED": "good",
        "REJECTED": "attention",
        "UNIQUE": "good",
        "EXACT_DUPLICATE": "warning",
        "SEMANTIC_DUPLICATE": "warning",
        "PENDING": "accent",
        "FAILED": "attention",
    }
    return colors.get(status, "default")
