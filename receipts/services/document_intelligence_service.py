from django.conf import settings
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from receipts.exceptions import DocumentExtractionError
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class DocumentIntelligenceService:
    def __init__(self):
        self.endpoint = settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
        self.key = settings.AZURE_DOCUMENT_INTELLIGENCE_KEY
        self.client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )

    def analyze_receipt(self, content: bytes, content_type: str) -> dict:
        if not self.endpoint or not self.key:
            raise DocumentExtractionError(
                "Azure Document Intelligence credentials not configured. "
                "Set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY."
            )

        try:
            poller = self.client.begin_analyze_document(
                "prebuilt-receipt",
                body=content,
                content_type=content_type
            )
            result = poller.result()

            extracted = self._parse_result(result)
            logger.info(f"Successfully extracted receipt data from Document Intelligence")
            return extracted

        except DocumentExtractionError:
            raise
        except Exception as e:
            logger.error(f"Document Intelligence analysis failed: {str(e)}", exc_info=True)
            raise DocumentExtractionError(f"Failed to analyze receipt: {str(e)}")

    @staticmethod
    def _get_field_value(field):
        """Extract the typed value from an Azure DocumentField."""
        if field is None:
            return None

        # String
        value_string = getattr(field, "value_string", None)
        if value_string is not None:
            return value_string

        # Number
        value_number = getattr(field, "value_number", None)
        if value_number is not None:
            return value_number

        # Integer
        value_integer = getattr(field, "value_integer", None)
        if value_integer is not None:
            return value_integer

        # Date
        value_date = getattr(field, "value_date", None)
        if value_date is not None:
            return value_date

        # Phone
        value_phone = getattr(field, "value_phone_number", None)
        if value_phone is not None:
            return value_phone

        # Currency - extract amount
        value_currency = getattr(field, "value_currency", None)
        if value_currency is not None:
            amount = getattr(value_currency, "amount", None)
            if amount is not None:
                return amount
            if isinstance(value_currency, dict):
                return value_currency.get("amount")

        return None

    @staticmethod
    def _clean_vendor_name(vendor_name: str) -> str:
        """Remove address/location lines from merchant name when clearly separate."""
        if not vendor_name or not isinstance(vendor_name, str):
            return vendor_name

        lines = vendor_name.split('\n')
        if len(lines) <= 1:
            return vendor_name

        last_line = lines[-1].strip()
        word_count = len(last_line.split())
        if word_count <= 3 and len(last_line) < 30:
            logger.debug(f"Removing location from vendor name: {vendor_name} -> {lines[0]}")
            return lines[0].strip()

        return vendor_name

    @staticmethod
    def _get_currency_code(field):
        """Extract currency code from DocumentField value_currency."""
        if field is None:
            return None

        currency = getattr(field, "value_currency", None)
        if currency is None:
            return None

        code = getattr(currency, "currency_code", None)
        if code:
            return code

        if isinstance(currency, dict):
            return currency.get("currencyCode") or currency.get("currency_code")

        return None

    def _extract_from_ocr_text(self, content: str) -> dict:
        """Fallback extraction from raw OCR text for fields Azure doesn't provide."""
        result = {
            "invoice_number": None,
            "payment_method": None,
            "transaction_date": None,
            "subtotal": None,
            "tax": None,
        }

        if not content:
            logger.debug("No OCR content available for fallback extraction")
            return result

        logger.debug(f"OCR content available ({len(content)} chars): {content[:200]}...")

        invoice_patterns = [
            r'RECEIPT\s*(?:NO\.?|NUMBER)?\s*[:=]?\s*([A-Z0-9\-]+)',
            r'INVOICE\s*(?:NO\.?|NUMBER)?\s*[:=]?\s*([A-Z0-9\-]+)',
        ]

        for pattern in invoice_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                result["invoice_number"] = match.group(1).strip()
                logger.debug(f"Extracted invoice number from OCR text: {result['invoice_number']}")
                break

        payment_patterns = [
            r'PAYMENT\s*(?:METHOD)?\s*[:=]\s*([^\n]+)',
        ]

        for pattern in payment_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                result["payment_method"] = match.group(1).strip()
                logger.debug(f"Extracted payment method from OCR text: {result['payment_method']}")
                break

        month_name_date = self._extract_month_name_date(content)
        if month_name_date:
            result["transaction_date"] = month_name_date
            logger.debug(f"Extracted textual month-name transaction date from OCR: {result['transaction_date']}")
        else:
            date_pattern = r'(\d{4}-\d{2}-\d{2})(?:\s+\d{2}:\d{2})?'
            match = re.search(date_pattern, content)
            if match:
                result["transaction_date"] = match.group(1)
                logger.debug(f"Extracted ISO transaction date from OCR text: {result['transaction_date']}")

        subtotal_pattern = r'SUBTOTAL\s*[:=]?\s*[₹$€£¥]?\s*([\d,]+\.?\d*)'
        match = re.search(subtotal_pattern, content, re.IGNORECASE)
        if match:
            try:
                amount_str = match.group(1).replace(',', '')
                result["subtotal"] = float(amount_str)
                logger.debug(f"Extracted subtotal from OCR text: {result['subtotal']}")
            except (ValueError, AttributeError) as e:
                logger.debug(f"Failed to parse subtotal amount: {str(e)}")

        tax_pattern = r'TAX\s*[:=]?\s*[₹$€£¥]?\s*([\d,]+\.?\d*)'
        match = re.search(tax_pattern, content, re.IGNORECASE)
        if match:
            try:
                amount_str = match.group(1).replace(',', '')
                result["tax"] = float(amount_str)
                logger.debug(f"Extracted tax from OCR text: {result['tax']}")
            except (ValueError, AttributeError) as e:
                logger.debug(f"Failed to parse tax amount: {str(e)}")

        return result

    def _extract_month_name_date(self, content: str) -> str:
        """
        Extract textual month-name dates from OCR text.
        Month-name dates are unambiguous (e.g., "5 Sept 2026" is always September 5, 2026).
        Returns ISO format date string (YYYY-MM-DD) or None if not found.
        """
        if not content or not isinstance(content, str):
            return None

        month_map = {
            'jan': 1, 'january': 1,
            'feb': 2, 'february': 2,
            'mar': 3, 'march': 3,
            'apr': 4, 'april': 4,
            'may': 5,
            'jun': 6, 'june': 6,
            'jul': 7, 'july': 7,
            'aug': 8, 'august': 8,
            'sep': 9, 'sept': 9, 'september': 9,
            'oct': 10, 'october': 10,
            'nov': 11, 'november': 11,
            'dec': 12, 'december': 12,
        }

        month_names = '|'.join(month_map.keys())
        date_patterns = [
            r'(\d{1,2})\s+(' + month_names + r')\s+(\d{4})',
            r'(' + month_names + r')\s+(\d{1,2}),?\s+(\d{4})',
        ]

        try:
            for pattern in date_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    try:
                        groups = match.groups()
                        if len(groups) == 3:
                            if groups[0].isdigit():
                                day = int(groups[0])
                                month_str = groups[1].lower()
                                year = int(groups[2])
                            else:
                                month_str = groups[0].lower()
                                day = int(groups[1])
                                year = int(groups[2])

                            month_num = month_map.get(month_str)
                            if month_num and 1 <= day <= 31 and 1900 <= year <= 2100:
                                try:
                                    parsed_date = datetime(year, month_num, day)
                                    iso_date = parsed_date.date().isoformat()
                                    logger.debug(f"Extracted month-name date from OCR: {match.group(0)} -> {iso_date}")
                                    return iso_date
                                except ValueError:
                                    continue

                    except (ValueError, AttributeError, TypeError):
                        continue

        except Exception as e:
            logger.debug(f"Error extracting month-name date: {str(e)}")

        return None

    def _parse_result(self, result) -> dict:
        extracted = {
            "merchant": {
                "name": None,
                "address": None,
                "phone": None,
            },
            "invoice": {
                "invoice_number": None,
                "transaction_date": None,
            },
            "amounts": {
                "subtotal": None,
                "tax": None,
                "total": None,
                "currency": None,
            },
            "payment": {
                "method": None,
            },
            "line_items": [],
            "extraction": {
                "provider": "azure_ai_document_intelligence",
                "model": "prebuilt-receipt",
                "confidence": {},
            },
        }

        if not result or not result.documents:
            logger.warning("Document Intelligence returned no documents in result")
            return extracted

        try:
            doc = result.documents[0]
            fields = doc.fields
            ocr_content = result.content if hasattr(result, 'content') else None

            if ocr_content:
                extracted['extraction']['ocr_content'] = ocr_content

            logger.info("=== AZURE FIELDS RETURNED ===")
            for field_name, field in fields.items():
                if field:
                    field_type = getattr(field, 'type', 'unknown')
                    field_content = getattr(field, 'content', None)
                    logger.info(f"{field_name}: type={field_type}, content={field_content[:50] if field_content else None}...")
                else:
                    logger.info(f"{field_name}: None")
            logger.info("=== END AZURE FIELDS ===")

            fallback = {}
            month_name_date = None
            if ocr_content:
                fallback = self._extract_from_ocr_text(ocr_content)
                month_name_date = self._extract_month_name_date(ocr_content)

            merchant_name = self._get_field_value(fields.get('MerchantName'))
            if merchant_name:
                merchant_name = self._clean_vendor_name(merchant_name)
                extracted['merchant']['name'] = merchant_name
                logger.debug(f"Extracted merchant name: {merchant_name}")

            merchant_address = self._get_field_value(fields.get('MerchantAddress'))
            if merchant_address:
                extracted['merchant']['address'] = merchant_address
                logger.debug(f"Extracted merchant address: {merchant_address}")

            merchant_phone = self._get_field_value(fields.get('MerchantPhoneNumber'))
            if merchant_phone:
                extracted['merchant']['phone'] = merchant_phone
                logger.debug(f"Extracted merchant phone: {merchant_phone}")

            receipt_number = self._get_field_value(fields.get('ReceiptNumber'))
            if receipt_number:
                extracted['invoice']['invoice_number'] = receipt_number
                logger.debug(f"Extracted invoice number from structured field: {receipt_number}")
            elif fallback.get('invoice_number'):
                extracted['invoice']['invoice_number'] = fallback['invoice_number']
                logger.debug(f"Extracted invoice number from OCR text fallback: {fallback['invoice_number']}")

            transaction_date = self._get_field_value(fields.get('TransactionDate'))

            if month_name_date:
                extracted['invoice']['transaction_date'] = month_name_date
                logger.info(f"Preferred textual month-name transaction date from OCR: {month_name_date}")
            elif transaction_date:
                extracted['invoice']['transaction_date'] = str(transaction_date)
                logger.debug(f"Extracted transaction date from structured field: {transaction_date}")
            elif fallback.get('transaction_date'):
                extracted['invoice']['transaction_date'] = fallback['transaction_date']
                logger.debug(f"Extracted transaction date from OCR text fallback: {fallback['transaction_date']}")

            subtotal = self._get_field_value(fields.get('Subtotal'))
            if subtotal is not None:
                try:
                    extracted['amounts']['subtotal'] = float(subtotal)
                    logger.debug(f"Extracted subtotal from structured field: {subtotal}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse subtotal: {subtotal} ({str(e)})")
            elif fallback.get('subtotal') is not None:
                extracted['amounts']['subtotal'] = fallback['subtotal']
                logger.debug(f"Extracted subtotal from OCR text fallback: {fallback['subtotal']}")

            total_tax = self._get_field_value(fields.get('TotalTax'))
            if total_tax is not None:
                try:
                    extracted['amounts']['tax'] = float(total_tax)
                    logger.debug(f"Extracted tax from structured field: {total_tax}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse tax: {total_tax} ({str(e)})")
            elif fallback.get('tax') is not None:
                extracted['amounts']['tax'] = fallback['tax']
                logger.debug(f"Extracted tax from OCR text fallback: {fallback['tax']}")

            total = self._get_field_value(fields.get('Total'))
            if total is not None:
                try:
                    extracted['amounts']['total'] = float(total)
                    logger.debug(f"Extracted total amount: {total}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse total: {total} ({str(e)})")

            currency = self._get_field_value(fields.get('Currency'))
            if currency:
                extracted['amounts']['currency'] = currency
                logger.debug(f"Extracted currency: {currency}")

            if not currency:
                total_field = fields.get('Total')
                if total_field and hasattr(total_field, 'value_currency') and total_field.value_currency:
                    currency_value = total_field.value_currency
                    if isinstance(currency_value, dict):
                        currency_code = currency_value.get('currencyCode')
                    else:
                        currency_code = getattr(currency_value, 'currency_code', None)
                        if not currency_code:
                            currency_code = getattr(currency_value, 'currencyCode', None)

                    if currency_code:
                        extracted['amounts']['currency'] = currency_code
                        logger.info(f"Extracted currency from Total field: {currency_code}")

            payment_method = self._get_field_value(fields.get('PaymentMethod'))
            if payment_method:
                extracted['payment']['method'] = payment_method
                logger.debug(f"Extracted payment method from structured field: {payment_method}")
            elif fallback.get('payment_method'):
                extracted['payment']['method'] = fallback['payment_method']
                logger.debug(f"Extracted payment method from OCR text fallback: {fallback['payment_method']}")

            items_field = fields.get('Items')
            if items_field and hasattr(items_field, 'value_array') and items_field.value_array:
                logger.info(f"Found {len(items_field.value_array)} line items to extract")
                for idx, item in enumerate(items_field.value_array):
                    try:
                        item_dict = {
                            "description": None,
                            "quantity": None,
                            "unit_price": None,
                            "amount": None,
                        }

                        if item.value_object:
                            logger.info(f"Item {idx} available fields: {list(item.value_object.keys())}")

                            description_field = item.value_object.get('Description') or item.value_object.get('Name')
                            if description_field:
                                description = self._get_field_value(description_field)
                                if description:
                                    item_dict["description"] = description
                                    logger.debug(f"Item {idx} description: {description}")

                            quantity_field = item.value_object.get('Quantity')
                            if quantity_field:
                                quantity = self._get_field_value(quantity_field)
                                if quantity is not None:
                                    try:
                                        item_dict["quantity"] = float(quantity)
                                        logger.debug(f"Item {idx} quantity: {quantity}")
                                    except (ValueError, TypeError):
                                        logger.debug(f"Could not convert quantity to float: {quantity}")
                            else:
                                logger.debug(f"Item {idx} has no Quantity field")

                            price_field = item.value_object.get('Price')
                            if price_field:
                                price = self._get_field_value(price_field)
                                if price is not None:
                                    try:
                                        item_dict["unit_price"] = float(price)
                                        logger.debug(f"Item {idx} unit price: {price}")
                                    except (ValueError, TypeError):
                                        logger.debug(f"Could not convert price to float: {price}")
                            else:
                                logger.debug(f"Item {idx} has no Price field")

                            total_price_field = item.value_object.get('TotalPrice')
                            if total_price_field:
                                total_price = self._get_field_value(total_price_field)
                                if total_price is not None:
                                    try:
                                        item_dict["amount"] = float(total_price)
                                        logger.debug(f"Item {idx} total price: {total_price}")
                                    except (ValueError, TypeError):
                                        logger.debug(f"Could not convert total price to float: {total_price}")

                        extracted['line_items'].append(item_dict)
                    except Exception as e:
                        logger.warning(f"Failed to parse line item {idx}: {str(e)}", exc_info=True)

            logger.info(f"Successfully parsed Document Intelligence result with "
                       f"merchant={extracted['merchant']['name']}, "
                       f"invoice={extracted['invoice']['invoice_number']}, "
                       f"total={extracted['amounts']['total']}")

        except Exception as e:
            logger.error(f"Error parsing Document Intelligence result: {str(e)}", exc_info=True)
            raise DocumentExtractionError(f"Failed to parse extraction result: {str(e)}")

        return extracted
