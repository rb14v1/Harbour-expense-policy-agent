import logging
from receipts.services import ReceiptService

logger = logging.getLogger(__name__)

try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False


def process_receipt_task_sync(receipt_id: str):
    """Synchronous processing for development."""
    try:
        service = ReceiptService()
        receipt = service.process_receipt(receipt_id)
        logger.info(f"Receipt {receipt_id} processed successfully. Status: {receipt.status}")
        return {"receipt_id": str(receipt.id), "status": receipt.status}
    except Exception as e:
        logger.error(f"Failed to process receipt {receipt_id}: {str(e)}")
        raise


if CELERY_AVAILABLE:
    @shared_task
    def process_receipt_task(receipt_id: str):
        return process_receipt_task_sync(receipt_id)
else:
    def process_receipt_task(receipt_id: str):
        return process_receipt_task_sync(receipt_id)
