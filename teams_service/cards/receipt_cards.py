"""
Adaptive Cards for Receipt Display in Teams

Generates mobile-optimized Adaptive Cards for:
- Receipt list
- Receipt details
- Duplicate warnings
- Decision prompts

Mobile considerations:
- Compact text sizing for small screens
- Proper wrapping and spacing
- Action buttons sized for mobile tapping
- Responsive layout that works on phones and tablets
"""
from typing import Dict, Any, Optional, List
from datetime import datetime


def get_receipt_list_card(receipts: List[Dict[str, Any]], page: int = 1) -> Dict[str, Any]:
    """Generate mobile-friendly card for receipt list with action buttons to select receipts."""
    if not receipts:
        return {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "No receipts pending review",
                    "weight": "bolder",
                    "size": "medium",
                }
            ],
        }

    body = [
        {
            "type": "TextBlock",
            "text": f"Pending Review",
            "weight": "bolder",
            "size": "medium",
        },
        {
            "type": "TextBlock",
            "text": f"Page {page}",
            "size": "small",
            "isSubtle": True,
            "spacing": "none",
        }
    ]

    for receipt in receipts:
        details = []
        if receipt.get("vendor_name"):
            details.append(f"**Vendor:** {receipt['vendor_name']}")
        if receipt.get("transaction_date"):
            details.append(f"**Date:** {receipt['transaction_date']}")
        if receipt.get("total_amount"):
            amt = receipt['total_amount']
            cur = receipt.get('currency', '')
            details.append(f"**Amount:** {amt} {cur}".strip())

        body.append({
            "type": "TextBlock",
            "text": f"📄 {receipt.get('original_filename', 'Unknown')}",
            "wrap": True,
            "size": "small",
            "weight": "bolder",
            "spacing": "medium",
        })

        if details:
            body.append({
                "type": "TextBlock",
                "text": "\n".join(details),
                "wrap": True,
                "size": "small",
                "spacing": "small",
            })

        body.append({
            "type": "ActionSet",
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Open Details",
                    "data": {
                        "action": "open_receipt",
                        "receipt_id": receipt["id"],
                    }
                }
            ]
        })

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": body,
    }


def get_receipt_detail_card(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """Generate mobile-friendly detailed card for single receipt with Finance review support."""
    status = receipt.get("status", "UNKNOWN")
    status_color = _get_status_color(status)

    body = [
        {
            "type": "TextBlock",
            "text": receipt.get('original_filename', 'Receipt'),
            "weight": "bolder",
            "size": "medium",
            "color": status_color,
            "wrap": True,
        },
        {
            "type": "TextBlock",
            "text": status,
            "size": "small",
            "weight": "bolder",
            "spacing": "small",
        }
    ]

    # Receipt details - core information
    details = []
    if receipt.get("vendor_name"):
        details.append(f"**Vendor:** {receipt['vendor_name']}")
    if receipt.get("transaction_date"):
        details.append(f"**Date:** {receipt['transaction_date']}")
    if receipt.get("total_amount"):
        amt = receipt['total_amount']
        cur = receipt.get('currency', '')
        details.append(f"**Amount:** {amt} {cur}".strip())

    if details:
        body.append({
            "type": "TextBlock",
            "text": "\n".join(details),
            "wrap": True,
            "spacing": "small",
            "size": "small",
        })

    # Category information
    if receipt.get("category"):
        cat_line = f"**Category:** {receipt['category']}"
        if receipt.get("category_confidence") is not None:
            confidence_pct = int(receipt.get("category_confidence", 0) * 100)
            cat_line += f" ({confidence_pct}%)"
        body.append({
            "type": "TextBlock",
            "text": cat_line,
            "wrap": True,
            "spacing": "small",
            "size": "small",
        })

    # Duplicate information - only if applicable
    if status in ["EXACT_DUPLICATE", "SEMANTIC_DUPLICATE"]:
        dup_text = f"**{status}**"
        if receipt.get("duplicate_score"):
            dup_text += f" (Score: {receipt['duplicate_score']})"
        if receipt.get("duplicate_reason"):
            dup_text += f"\n{receipt['duplicate_reason']}"
        body.append({
            "type": "TextBlock",
            "text": dup_text,
            "wrap": True,
            "spacing": "medium",
            "color": "warning",
            "size": "small",
        })

    # Policy status - only if present
    if receipt.get("policy_status"):
        body.append({
            "type": "TextBlock",
            "text": f"**Policy:** {receipt['policy_status']}",
            "wrap": True,
            "spacing": "small",
            "size": "small",
        })

    # Notes/message - only if present
    if receipt.get("processing_message"):
        body.append({
            "type": "TextBlock",
            "text": f"**Notes:** {receipt['processing_message']}",
            "wrap": True,
            "spacing": "small",
            "size": "small",
            "isSubtle": True,
        })

    # Employee info - only if present
    if receipt.get("employee_name"):
        body.append({
            "type": "TextBlock",
            "text": f"**Employee:** {receipt['employee_name']}",
            "wrap": True,
            "spacing": "small",
            "size": "small",
            "isSubtle": True,
        })

    # Rejection reason input - only when approval is pending
    if status not in ["APPROVED", "REJECTED", "EXACT_DUPLICATE", "SEMANTIC_DUPLICATE"]:
        body.append({
            "type": "TextBlock",
            "text": "Reason (if rejecting):",
            "weight": "bolder",
            "size": "small",
            "spacing": "medium",
        })
        body.append({
            "type": "Input.Text",
            "id": "rejection_reason",
            "placeholder": "Optional rejection reason",
            "multiline": True,
        })

    # Action buttons - stack on mobile for easy tapping
    actions = [
        {
            "type": "Action.Submit",
            "title": "Preview",
            "data": {
                "action": "preview_receipt",
                "receipt_id": receipt["id"],
            }
        },
    ]

    # Add approve/reject actions if receipt is not yet decided
    if status not in ["APPROVED", "REJECTED", "EXACT_DUPLICATE", "SEMANTIC_DUPLICATE"]:
        actions.append({
            "type": "Action.Submit",
            "title": "Approve",
            "data": {
                "action": "approve",
                "receipt_id": receipt["id"],
            }
        })
        actions.append({
            "type": "Action.Submit",
            "title": "Reject",
            "data": {
                "action": "reject",
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


def get_decision_confirmation_card(receipt_id: str, decision: str, notes: Optional[str] = None) -> Dict[str, Any]:
    """Generate mobile-friendly confirmation card after Finance decision (approve/reject).

    Args:
        receipt_id: Receipt UUID
        decision: "APPROVED" or "REJECTED"
        notes: Optional rejection reason or approval notes
    """
    icon = "✅" if decision == "APPROVED" else "❌"
    color = "good" if decision == "APPROVED" else "attention"

    body = [
        {
            "type": "TextBlock",
            "text": f"{icon} {decision}",
            "weight": "bolder",
            "size": "medium",
            "color": color,
        },
        {
            "type": "TextBlock",
            "text": f"ID: {receipt_id}",
            "wrap": True,
            "size": "small",
            "isSubtle": True,
            "spacing": "small",
        },
    ]

    # Add approval confirmation
    if decision == "APPROVED":
        body.append({
            "type": "TextBlock",
            "text": "Reviewed by Finance",
            "wrap": True,
            "spacing": "small",
            "size": "small",
            "color": "good",
        })

    # Add rejection reason if provided
    if decision == "REJECTED" and notes:
        body.append({
            "type": "TextBlock",
            "text": f"**Reason:** {notes}",
            "wrap": True,
            "spacing": "small",
            "size": "small",
        })

    body.append({
        "type": "TextBlock",
        "text": datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        "wrap": True,
        "spacing": "small",
        "size": "small",
        "isSubtle": True,
    })

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": body,
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
