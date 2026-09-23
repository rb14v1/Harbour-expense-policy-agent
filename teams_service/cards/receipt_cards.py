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
    """Generate detailed card for single receipt with Finance review support."""
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

    # Optional: Employee information
    if receipt.get("employee_name"):
        body.append({
            "type": "TextBlock",
            "text": f"**Employee:** {receipt['employee_name']}",
            "wrap": True,
            "spacing": "medium",
            "size": "small",
        })

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

    # Optional: Category confidence and reason
    if receipt.get("category_confidence") is not None or receipt.get("category_reason"):
        category_info = []
        if receipt.get("category_confidence") is not None:
            confidence_pct = int(receipt.get("category_confidence", 0) * 100)
            category_info.append(f"**Confidence:** {confidence_pct}%")
        if receipt.get("category_reason"):
            category_info.append(f"**Reason:** {receipt['category_reason']}")

        if category_info:
            body.append({
                "type": "TextBlock",
                "text": "\n".join(category_info),
                "wrap": True,
                "spacing": "medium",
                "size": "small",
                "isSubtle": True,
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

    # Optional: Processing message or notes
    if receipt.get("processing_message"):
        body.append({
            "type": "TextBlock",
            "text": f"**Notes:** {receipt['processing_message']}",
            "wrap": True,
            "spacing": "medium",
            "size": "small",
            "isSubtle": True,
        })

    # Optional: Created timestamp
    if receipt.get("created_at"):
        body.append({
            "type": "TextBlock",
            "text": f"**Created:** {receipt['created_at']}",
            "wrap": True,
            "spacing": "medium",
            "size": "small",
            "isSubtle": True,
        })

    # Optional: Rejection reason input (only when approval is pending)
    if status not in ["APPROVED", "REJECTED", "EXACT_DUPLICATE", "SEMANTIC_DUPLICATE"]:
        body.append({
            "type": "TextBlock",
            "text": "Rejection Reason (optional, if rejecting):",
            "weight": "bolder",
            "size": "small",
            "spacing": "medium",
        })
        body.append({
            "type": "Input.Text",
            "id": "rejection_reason",
            "placeholder": "Enter reason for rejection (optional)",
            "multiline": True,
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


def get_decision_confirmation_card(receipt_id: str, decision: str, notes: Optional[str] = None) -> Dict[str, Any]:
    """Generate confirmation card after Finance decision (approve/reject).

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
    ]

    # Add approval confirmation
    if decision == "APPROVED":
        body.append({
            "type": "TextBlock",
            "text": "✓ Reviewed by Finance",
            "wrap": True,
            "spacing": "medium",
            "size": "small",
            "color": "good",
        })

    # Add rejection reason if provided
    if decision == "REJECTED" and notes:
        body.append({
            "type": "TextBlock",
            "text": f"**Reason:** {notes}",
            "wrap": True,
            "spacing": "medium",
            "size": "small",
        })

    body.append({
        "type": "TextBlock",
        "text": f"Timestamp: {datetime.utcnow().isoformat()}Z",
        "wrap": True,
        "spacing": "medium",
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
