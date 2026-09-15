from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
import logging
from receipts.exceptions import ReceiptNormalizationError

logger = logging.getLogger(__name__)


class NormalizationService:
    CURRENCY_PATTERNS = {
        r'\binr\b': 'INR',
        r'\busd\b': 'USD',
        r'\beur\b': 'EUR',
        r'\bgbp\b': 'GBP',
        r'\bjpy\b': 'JPY',
        r'\baud\b': 'AUD',
        r'\bcad\b': 'CAD',
        r'\binr\b|\brs\b|\brupe': 'INR',
    }

    PAYMENT_METHOD_PATTERNS = {
        r'\b(credit\s*card|credit|cc|visa|mastercard|amex)\b': 'CARD',
        r'\b(debit\s*card|debit)\b': 'DEBIT',
        r'\b(cash|cheque|check)\b': 'CASH',
        r'\b(upi|digital)\b': 'DIGITAL',
    }

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
                "vendor_name": NormalizationService._extract_vendor_name(extracted),
                "vendor_normalized": NormalizationService._normalize_vendor(
                    extracted.get("merchant", {}).get("name")
                ),
                "invoice_number": NormalizationService._extract_invoice_number(extracted),
                "invoice_number_normalized": NormalizationService._normalize_invoice_number(
                    extracted.get("invoice", {}).get("invoice_number")
                ),
                "transaction_date": NormalizationService._normalize_date(
                    extracted.get("invoice", {}).get("transaction_date")
                ),
                "subtotal": NormalizationService._normalize_amount(
                    extracted.get("amounts", {}).get("subtotal")
                ),
                "tax_amount": NormalizationService._normalize_amount(
                    extracted.get("amounts", {}).get("tax")
                ),
                "total_amount": NormalizationService._normalize_amount(
                    extracted.get("amounts", {}).get("total")
                ),
                "currency": NormalizationService._normalize_currency(
                    extracted.get("amounts", {}).get("currency")
                ),
                "payment_method": NormalizationService._normalize_payment_method(
                    extracted.get("payment", {}).get("method")
                ),
                "merchant": {
                    "name": extracted.get("merchant", {}).get("name"),
                    "address": extracted.get("merchant", {}).get("address"),
                    "phone": extracted.get("merchant", {}).get("phone"),
                },
                "line_items": extracted.get("line_items", []),
                "extraction": extracted.get("extraction", {}),
            }
            return normalized
        except ReceiptNormalizationError:
            raise
        except Exception as e:
            logger.error(f"Failed to normalize receipt: {str(e)}", exc_info=True)
            raise ReceiptNormalizationError(f"Failed to normalize receipt: {str(e)}")

    @staticmethod
    def _extract_vendor_name(extracted: dict) -> str:
        vendor = extracted.get("merchant", {}).get("name")
        if not vendor:
            return None
        if not isinstance(vendor, str):
            return None
        vendor = vendor.strip()
        return vendor if vendor else None

    @staticmethod
    def _normalize_vendor(vendor_name: str) -> str:
        if not vendor_name:
            return None
        if not isinstance(vendor_name, str):
            return None

        normalized = vendor_name.strip().lower()
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized if normalized else None

    @staticmethod
    def _extract_invoice_number(extracted: dict) -> str:
        invoice = extracted.get("invoice", {}).get("invoice_number")
        if not invoice:
            return None
        if not isinstance(invoice, str):
            return None
        invoice = invoice.strip()
        return invoice if invoice else None

    @staticmethod
    def _normalize_invoice_number(invoice_number: str) -> str:
        if not invoice_number:
            return None
        if not isinstance(invoice_number, str):
            return None

        normalized = invoice_number.strip().upper()
        normalized = re.sub(r'\s+', '', normalized)
        return normalized if normalized else None

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        if not date_str:
            return None
        if not isinstance(date_str, str):
            return None

        date_str = date_str.strip()
        if not date_str:
            return None

        try:
            parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return parsed.date().isoformat()
        except (ValueError, TypeError):
            pass

        try:
            parsed = datetime.strptime(date_str[:10], '%Y-%m-%d')
            return parsed.date().isoformat()
        except (ValueError, TypeError):
            pass

        try:
            for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y',
                        '%d.%m.%Y', '%m.%d.%Y', '%d %b %Y', '%d %b %y']:
                try:
                    parsed = datetime.strptime(date_str[:10], fmt)
                    return parsed.date().isoformat()
                except (ValueError, TypeError):
                    continue
        except Exception:
            pass

        logger.warning(f"Could not parse date: {date_str}")
        return None

    @staticmethod
    def _normalize_amount(amount) -> float:
        if amount is None:
            return None
        if isinstance(amount, (int, float)):
            return float(amount)
        if isinstance(amount, str):
            amount = amount.strip()
            if not amount:
                return None
            amount = amount.replace(',', '')
            try:
                return float(amount)
            except (ValueError, InvalidOperation):
                logger.warning(f"Could not parse amount: {amount}")
                return None
        try:
            return float(amount)
        except (ValueError, TypeError, InvalidOperation):
            logger.warning(f"Could not parse amount: {amount}")
            return None

    @staticmethod
    def _normalize_currency(currency_str: str) -> str:
        if not currency_str:
            return None
        if not isinstance(currency_str, str):
            return None

        currency_str = currency_str.strip().lower()
        if not currency_str:
            return None

        if len(currency_str) == 3 and currency_str.isupper():
            return currency_str.upper()

        for pattern, code in NormalizationService.CURRENCY_PATTERNS.items():
            if re.search(pattern, currency_str, re.IGNORECASE):
                logger.debug(f"Matched currency pattern '{pattern}' to {code}")
                return code

        if len(currency_str) == 3:
            return currency_str.upper()

        logger.warning(f"Could not normalize currency: {currency_str}")
        return None

    @staticmethod
    def _normalize_payment_method(method_str: str) -> str:
        if not method_str:
            return None
        if not isinstance(method_str, str):
            return None

        original = method_str.strip()
        method_lower = original.lower()
        if not method_lower:
            return None

        for pattern, normalized in NormalizationService.PAYMENT_METHOD_PATTERNS.items():
            if re.search(pattern, method_lower, re.IGNORECASE):
                logger.debug(f"Matched payment pattern '{pattern}' to {normalized}")
                return normalized

        if 'card' in method_lower:
            logger.debug(f"Preserving company-qualified payment method: {original}")
            return original

        logger.warning(f"Could not normalize payment method: {method_str}")
        return None
