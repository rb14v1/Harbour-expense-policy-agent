import json
import logging
import os
from typing import Dict, Any
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class TeamsBot:
    """
    Handles Teams bot messages and routes to Django backend.
    Keeps Teams logic thin - all business logic in Django.
    """

    def __init__(self, django_api_url: str = "http://localhost:8000/api/v1"):
        self.django_api_url = django_api_url

    def handle_message(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for Teams messages.
        Routes to appropriate handler based on message type.
        """
        try:
            activity_type = activity.get("type")

            if activity_type == "message":
                return self._handle_text_message(activity)

            elif activity_type == "conversationUpdate":
                return self._handle_conversation_update(activity)

            return {"status": "ok"}

        except Exception as e:
            logger.error(f"Error handling Teams message: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _handle_text_message(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text messages from Teams."""
        text = activity.get("text", "").lower()
        from_id = activity.get("from", {}).get("id")
        channel_id = activity.get("channelId")
        conversation_id = activity.get("conversation", {}).get("id")

        if "upload" in text or "receipt" in text:
            return {
                "type": "message",
                "text": "Please upload your receipt file. I'll process it and check for duplicates.",
                "attachments": [self._get_upload_card()]
            }

        elif "status" in text or "check" in text:
            return {
                "type": "message",
                "text": "Please provide a receipt ID to check status."
            }

        else:
            return {
                "type": "message",
                "text": "I can help you with expense receipts. Try:\n- 'upload receipt' to upload a file\n- 'check status' to check a receipt"
            }

    def _handle_conversation_update(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle when bot joins team."""
        members_added = activity.get("membersAdded", [])

        for member in members_added:
            if member.get("id") != activity.get("recipient", {}).get("id"):
                return {
                    "type": "message",
                    "text": "Welcome! I'm the Expense Policy Agent. Upload receipts and I'll:\n✓ Check for duplicates\n✓ Extract receipt details\n✓ Validate expense policies\n\nLet's get started!"
                }

        return {"status": "ok"}

    def handle_file_upload(self, file_content: bytes, filename: str, user_id: str) -> Dict[str, Any]:
        """
        Handle file upload from Teams.
        Calls Django backend to process receipt.
        """
        try:
            logger.info(f"Processing file upload: {filename} from user {user_id}")

            files = {"file": (filename, file_content)}
            data = {"owner": user_id}

            response = requests.post(
                f"{self.django_api_url}/receipts/upload",
                files=files,
                data=data,
                timeout=30
            )

            if response.status_code == 201:
                result = response.json()
                receipt_id = result.get("receipt_id")
                status = result.get("status")

                card = self._get_receipt_status_card(receipt_id, status, result.get("message"))

                logger.info(f"Receipt {receipt_id} uploaded successfully. Status: {status}")

                return {
                    "type": "message",
                    "attachments": [card]
                }

            else:
                error_msg = response.json().get("error", "Upload failed")
                logger.error(f"Upload failed: {error_msg}")

                return {
                    "type": "message",
                    "text": f"❌ Upload failed: {error_msg}"
                }

        except Exception as e:
            logger.error(f"Error handling file upload: {str(e)}")
            return {
                "type": "message",
                "text": f"❌ Error processing file: {str(e)}"
            }

    def get_receipt_status(self, receipt_id: str) -> Dict[str, Any]:
        """
        Get receipt status from Django backend.
        Returns Adaptive Card with status.
        """
        try:
            response = requests.get(
                f"{self.django_api_url}/receipts/{receipt_id}/",
                timeout=10
            )

            if response.status_code == 200:
                receipt = response.json()
                card = self._get_receipt_status_card(
                    receipt_id,
                    receipt.get("status"),
                    receipt.get("message"),
                    receipt.get("duplicate_reason")
                )

                return {
                    "type": "message",
                    "attachments": [card]
                }

            else:
                return {
                    "type": "message",
                    "text": f"❌ Receipt not found: {receipt_id}"
                }

        except Exception as e:
            logger.error(f"Error getting receipt status: {str(e)}")
            return {
                "type": "message",
                "text": f"❌ Error retrieving status: {str(e)}"
            }

    def _get_upload_card(self) -> Dict[str, Any]:
        """Get Adaptive Card for upload prompt."""
        return {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "contentUrl": None,
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Upload Receipt",
                        "weight": "bolder",
                        "size": "medium"
                    },
                    {
                        "type": "TextBlock",
                        "text": "Please upload your receipt (PDF, JPG, or PNG)",
                        "wrap": True
                    }
                ],
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "Upload File",
                        "url": "https://teams.microsoft.com"
                    }
                ]
            }
        }

    def _get_receipt_status_card(self, receipt_id: str, status: str, message: str, reason: str = None) -> Dict[str, Any]:
        """Get Adaptive Card for receipt status."""

        status_colors = {
            "EXACT_DUPLICATE": "warning",
            "SEMANTIC_DUPLICATE": "warning",
            "APPROVED": "good",
            "REJECTED": "attention",
            "UNIQUE": "good",
            "QUEUED_FOR_OCR": "accent",
            "OCR_PROCESSING": "accent",
            "FAILED": "attention",
        }

        color = status_colors.get(status, "default")

        body = [
            {
                "type": "TextBlock",
                "text": f"Receipt Status: {status}",
                "weight": "bolder",
                "size": "medium",
                "color": color
            },
            {
                "type": "TextBlock",
                "text": message or "Processing...",
                "wrap": True
            }
        ]

        if reason:
            body.append({
                "type": "TextBlock",
                "text": f"Details: {reason}",
                "wrap": True,
                "size": "small",
                "isSubtle": True
            })

        body.append({
            "type": "TextBlock",
            "text": f"ID: {receipt_id}",
            "wrap": True,
            "size": "small",
            "isSubtle": True
        })

        return {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": body
            }
        }


def create_teams_bot(django_api_url: str = None) -> TeamsBot:
    """Factory function to create Teams bot."""
    if django_api_url is None:
        django_api_url = os.getenv("DJANGO_API_URL", "http://localhost:8000/api/v1")

    return TeamsBot(django_api_url)
