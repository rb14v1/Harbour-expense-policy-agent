from datetime import datetime
from receipts.exceptions import ReceiptNormalizationError


class NormalizationService:
    @staticmethod
    def normalize(extracted: dict) -> dict:
        try:
            normalized = {
                "receipt_id": None,
                "source": {
                    "original_filename": None,
                    "blob_reference": None,
                    "sha256": None,
                },
                "merchant": {
                    "name": NormalizationService._normalize_vendor(
                        extracted.get("merchant", {}).get("name")
                    ),
                    "name_original": extracted.get("merchant", {}).get("name"),
                    "address": extracted.get("merchant", {}).get("address"),
                    "phone": extracted.get("merchant", {}).get("phone"),
                },
                "invoice": {
                    "invoice_number": NormalizationService._normalize_invoice_number(
                        extracted.get("invoice", {}).get("invoice_number")
                    ),
                    "invoice_number_original": extracted.get("invoice", {}).get("invoice_number"),
                    "transaction_date": NormalizationService._normalize_date(
                        extracted.get("invoice", {}).get("transaction_date")
                    ),
                },
                "amounts": {
                    "subtotal": extracted.get("amounts", {}).get("subtotal"),
                    "tax": extracted.get("amounts", {}).get("tax"),
                    "total": extracted.get("amounts", {}).get("total"),
                    "currency": NormalizationService._normalize_currency(
                        extracted.get("amounts", {}).get("currency")
                    ),
                },
                "payment": {
                    "method": extracted.get("payment", {}).get("method"),
                },
                "line_items": extracted.get("line_items", []),
                "extraction": extracted.get("extraction", {}),
            }
            return normalized
        except Exception as e:
            raise ReceiptNormalizationError(f"Failed to normalize receipt: {str(e)}")

    @staticmethod
    def _normalize_vendor(vendor_name: str) -> str:
        if not vendor_name:
            return None
        return vendor_name.lower().strip()

    @staticmethod
    def _normalize_invoice_number(invoice_number: str) -> str:
        if not invoice_number:
            return None
        return invoice_number.lower().strip()

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        if not date_str:
            return None
        try:
            parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return parsed.date().isoformat()
        except:
            try:
                parsed = datetime.strptime(date_str[:10], '%Y-%m-%d')
                return parsed.date().isoformat()
            except:
                return None

    @staticmethod
    def _normalize_currency(currency: str) -> str:
        if not currency:
            return None
        return currency.upper().strip()
