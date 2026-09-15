from pydantic import BaseModel
from typing import List, Optional


class ReceiptItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    amount: Optional[float] = None


class Receipt(BaseModel):
    receipt_id: str
    merchant_name: Optional[str] = None
    transaction_date: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    payment_method: Optional[str] = None
    items: List[ReceiptItem] = []