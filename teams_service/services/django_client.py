"""
Django REST API Client

Handles communication with Django backend for receipt operations.
"""
import logging
from typing import Optional, List, Dict, Any
import httpx
from teams_service.config import config

logger = logging.getLogger(__name__)


class DjangoReceiptClient:
    """Client for Django Finance and Receipt APIs."""

    def __init__(self):
        self.finance_api_url = config.DJANGO_FINANCE_API_URL
        self.timeout = 30

    async def get_receipts(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        vendor: Optional[str] = None,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Retrieve list of receipts with optional filters.

        Args:
            status: Receipt status filter
            category: Expense category filter
            vendor: Vendor name filter
            page: Page number (1-indexed)

        Returns:
            Dictionary with receipt list, count, pagination
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            params = {"page": page}
            if status:
                params["status"] = status
            if category:
                params["category"] = category
            if vendor:
                params["vendor"] = vendor

            try:
                response = await client.get(
                    f"{self.finance_api_url}/receipts/",
                    params=params,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error fetching receipts: {e}")
                raise

    async def get_receipt_detail(self, receipt_id: str) -> Dict[str, Any]:
        """
        Retrieve receipt details.

        Args:
            receipt_id: Receipt UUID

        Returns:
            Receipt details dictionary
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.finance_api_url}/receipts/{receipt_id}/",
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Receipt not found: {receipt_id}")
                    return None
                logger.error(f"Error fetching receipt {receipt_id}: {e}")
                raise

    async def make_receipt_decision(
        self, receipt_id: str, decision: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit Finance decision on receipt (APPROVED or REJECTED).

        Args:
            receipt_id: Receipt UUID
            decision: "APPROVED" or "REJECTED"
            notes: Optional decision notes

        Returns:
            Updated receipt details
        """
        if decision not in ["APPROVED", "REJECTED"]:
            raise ValueError(f"Invalid decision: {decision}. Must be APPROVED or REJECTED")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {"decision": decision}
            if notes:
                payload["notes"] = notes

            try:
                response = await client.post(
                    f"{self.finance_api_url}/receipts/{receipt_id}/decision/",
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Receipt not found: {receipt_id}")
                    return None
                logger.error(f"Error making decision for receipt {receipt_id}: {e}")
                raise

    async def get_receipt_preview_url(self, receipt_id: str) -> Optional[str]:
        """
        Get preview/download URL for receipt file.

        Returns secure Django-served URL, not direct Blob access.
        """
        return f"{config.DJANGO_API_URL}/receipts/{receipt_id}/preview/"


class DjangoReceiptException(Exception):
    """Exception from Django API communication."""
    pass


# Create global client instance
django_client = DjangoReceiptClient()
