import uuid
import json
from django.utils import timezone
from receipts.models import Receipt
from receipts.services.file_validation_service import FileValidationService
from receipts.services.hashing_service import HashingService
from receipts.services.blob_service import BlobService
from receipts.services.document_intelligence_service import DocumentIntelligenceService
from receipts.services.normalization_service import NormalizationService
from receipts.services.duplicate_service import DuplicateService
from receipts.services.policy_service import PolicyService
from receipts.exceptions import BlobUploadError, DocumentExtractionError


class ReceiptService:
    def __init__(self):
        self.blob_service = BlobService()
        self.hashing_service = HashingService()
        self.doc_intel_service = DocumentIntelligenceService()
        self.normalization_service = NormalizationService()
        self.duplicate_service = DuplicateService()
        self.policy_service = PolicyService()

    def create_and_upload_receipt(self, file_obj, filename: str, owner: str = "default-user") -> Receipt:
        FileValidationService.validate(file_obj, filename)

        receipt_id = uuid.uuid4()
        blob_name = self._generate_blob_name(owner, receipt_id, filename)

        receipt = Receipt.objects.create(
            id=receipt_id,
            owner=owner,
            original_filename=filename,
            blob_name=blob_name,
            mime_type=self._get_mime_type(filename),
            file_size=file_obj.size,
            sha256_hash="",
            status="UPLOADED",
        )

        try:
            sha256 = self.hashing_service.sha256(file_obj)
            receipt.sha256_hash = sha256
            receipt.status = "HASHING"
            receipt.save()

            exact_dup = self.duplicate_service.find_exact_duplicate(sha256, owner)
            if exact_dup:
                receipt.mark_exact_duplicate(exact_dup)
                return receipt

            receipt.status = "QUEUED_FOR_OCR"
            receipt.save()

            self.blob_service.upload(file_obj, blob_name, receipt.mime_type)

        except BlobUploadError as e:
            receipt.status = "FAILED"
            receipt.duplicate_reason = f"Blob upload failed: {str(e)}"
            receipt.processing_message = "Unable to store the receipt file. Please try uploading again."
            receipt.save()
            raise

        return receipt

    def process_receipt(self, receipt_id: str) -> Receipt:
        receipt = Receipt.objects.get(id=receipt_id)

        if receipt.is_final():
            return receipt

        try:
            receipt.mark_ocr_processing()

            file_bytes = self.blob_service.download(receipt.blob_name)

            try:
                extracted = self.doc_intel_service.analyze_receipt(
                    content=file_bytes,
                    content_type=receipt.mime_type,
                )
            except DocumentExtractionError as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"OCR extraction failed for receipt {receipt_id}: {str(e)}")
                receipt.status = "FAILED"
                receipt.duplicate_reason = f"Document extraction failed: {str(e)}"
                receipt.processing_message = "We couldn't read the receipt. The document may be blurry, unclear, or contain unreadable content. Please upload a clearer image or PDF."
                receipt.save()
                return receipt

            receipt.raw_document_intelligence_json = extracted
            receipt.status = "EXTRACTED"
            receipt.save()

            if self._is_ocr_result_blank(extracted):
                receipt.status = "FAILED"
                receipt.duplicate_reason = "Receipt appears to be blank. No meaningful content was extracted."
                receipt.processing_message = "The uploaded receipt appears to be blank. Please upload a receipt with visible content."
                receipt.save()
                return receipt

            if not self._is_valid_receipt(extracted):
                receipt.status = "FAILED"
                receipt.duplicate_reason = "Document does not appear to be a receipt. Required receipt information is missing."
                receipt.processing_message = "The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items."
                receipt.save()
                return receipt

            normalized = self.normalization_service.normalize(extracted)
            normalized['receipt_id'] = str(receipt.id)
            if 'source' not in normalized:
                normalized['source'] = {}
            normalized['source']['original_filename'] = receipt.original_filename
            normalized['source']['blob_reference'] = receipt.blob_name
            normalized['source']['sha256'] = receipt.sha256_hash

            receipt.normalized_json = normalized
            receipt.status = "NORMALIZED"

            category_result = self.determine_category(extracted)
            receipt.category = category_result.get('category', 'Other')
            receipt.category_confidence = category_result.get('confidence', 0.0)
            receipt.category_reason = category_result.get('reason', '')

            # Populate Receipt model from normalized data
            if normalized.get('vendor_name'):
                receipt.vendor_name = normalized['vendor_name']
            if normalized.get('vendor_normalized'):
                receipt.vendor_normalized = normalized['vendor_normalized']

            if normalized.get('invoice_number'):
                receipt.invoice_number = normalized['invoice_number']
            if normalized.get('invoice_number_normalized'):
                receipt.invoice_number_normalized = normalized['invoice_number_normalized']

            if normalized.get('transaction_date'):
                from datetime import datetime
                date_str = normalized['transaction_date']
                if date_str:
                    try:
                        receipt.transaction_date = datetime.fromisoformat(
                            date_str.replace('Z', '+00:00')
                        ).date()
                    except:
                        pass

            if normalized.get('subtotal') is not None:
                receipt.subtotal = normalized['subtotal']

            if normalized.get('tax_amount') is not None:
                receipt.tax_amount = normalized['tax_amount']

            if normalized.get('total_amount') is not None:
                receipt.total_amount = normalized['total_amount']

            if normalized.get('currency'):
                receipt.currency = normalized['currency']

            if normalized.get('payment_method'):
                receipt.payment_method = normalized['payment_method']

            receipt.save()

            receipt.status = "DUPLICATE_CHECKING"
            receipt.save()

            dup_result = self.duplicate_service.evaluate_semantic_duplicate(receipt)

            if dup_result and dup_result.get('is_duplicate'):
                receipt.mark_semantic_duplicate(
                    dup_result['matched_receipt'],
                    dup_result['score'],
                    dup_result['reason']
                )
                return receipt

            receipt.mark_unique()

            receipt.status = "POLICY_PROCESSING"
            receipt.save()

            policy_result = self.policy_service.evaluate(receipt)
            receipt.policy_result_json = policy_result
            receipt.policy_status = policy_result['status']

            if policy_result['status'] == 'APPROVED':
                receipt.status = 'APPROVED'
                receipt.processing_message = "Receipt has been validated and approved."
            else:
                receipt.status = 'REJECTED'
                rejection_reasons = []
                for rule in policy_result.get('rules', []):
                    if not rule.get('passed'):
                        rejection_reasons.append(rule.get('message', 'Policy rule violation'))
                receipt.processing_message = f"Receipt rejected because: {'; '.join(rejection_reasons)}" if rejection_reasons else "Receipt failed policy validation."

            receipt.save()

        except Exception as e:
            error_msg = str(e)
            receipt.mark_ocr_failed(error_msg)
            receipt.processing_message = "Unable to process the receipt. Please try again."
            receipt.save()
            raise

        return receipt

    @staticmethod
    def determine_category(extracted: dict) -> dict:
        """
        Determine receipt category with confidence score.

        Returns dict:
        {
            'category': 'Category Name',
            'confidence': 0.0-1.0,
            'reason': 'Why this category was selected'
        }

        Confidence >= 0.80 suggests automatic assignment.
        Confidence < 0.80 suggests user confirmation needed.
        """
        if not extracted:
            return {
                'category': 'Other',
                'confidence': 0.0,
                'reason': 'No receipt data available'
            }

        merchant_name = (extracted.get('merchant', {}).get('name') or '').lower()
        line_items = extracted.get('line_items', [])
        line_items_desc = ' '.join([str(item.get('description', '')).lower() for item in line_items])
        payment_method = (extracted.get('payment', {}).get('method') or '').lower()
        all_text = merchant_name + ' ' + line_items_desc + ' ' + payment_method

        category_keywords = {
            'Accommodation/Hotel': {
                'keywords': ['hotel', 'motel', 'resort', 'airbnb', 'lodging', 'inn', 'accommodation'],
                'confidence_boost': 0.95
            },
            'Transport: Flights': {
                'keywords': ['airline', 'flight', 'aircraft', 'airfare', 'aviation'],
                'confidence_boost': 0.90
            },
            'Transport: Luas/Bus/Train': {
                'keywords': ['train', 'railway', 'luas', 'bus', 'transit', 'metro'],
                'confidence_boost': 0.85
            },
            'Transport: Taxis/Cab/Uber': {
                'keywords': ['taxi', 'uber', 'lyft', 'cab', 'ride share'],
                'confidence_boost': 0.90
            },
            'Transport: Car Rental & Fuel': {
                'keywords': ['car rental', 'rental', 'hertz', 'enterprise', 'avis'],
                'confidence_boost': 0.90
            },
            'Software': {
                'keywords': ['software', 'subscription', 'saas', 'cloud', 'license', 'app store', 'microsoft', 'adobe'],
                'confidence_boost': 0.85
            },
            'Food: Dinner - Max Claim: €/$/AUD 45 / INR700': {
                'keywords': ['restaurant', 'dinner', 'dinner time'],
                'confidence_boost': 0.85
            },
            'Food: Breakfast or Lunch - Max Claim: €/$/AUD 15 / INR700': {
                'keywords': ['breakfast', 'lunch', 'cafe', 'coffee', 'bistro', 'pizzeria', 'bakery'],
                'confidence_boost': 0.80
            },
            'Stationery Consumables': {
                'keywords': ['stationery', 'office supplies', 'paper', 'pen', 'ink', 'supplies'],
                'confidence_boost': 0.80
            },
            'Training': {
                'keywords': ['training', 'course', 'workshop', 'seminar', 'education'],
                'confidence_boost': 0.85
            },
            'Phone Bills/Broadband': {
                'keywords': ['phone', 'mobile', 'broadband', 'internet', 'vodafone', 'telstra', 'telecom'],
                'confidence_boost': 0.85
            },
            'Bank Charges': {
                'keywords': ['bank', 'banking fee', 'overdraft', 'wire transfer fee'],
                'confidence_boost': 0.80
            },
            'Client Entertainment': {
                'keywords': ['entertainment', 'movie', 'cinema', 'theatre', 'theater', 'bar', 'lounge', 'club'],
                'confidence_boost': 0.80
            },
            'Computer Peripherals': {
                'keywords': ['mouse', 'keyboard', 'monitor', 'laptop', 'computer', 'hardware'],
                'confidence_boost': 0.80
            },
            'Travel Other incl. Parking & Tolls': {
                'keywords': ['parking', 'toll', 'petrol station', 'gas station'],
                'confidence_boost': 0.85
            },
            'Print & Postage': {
                'keywords': ['print', 'postage', 'shipping', 'courier', 'post office'],
                'confidence_boost': 0.80
            },
            'Prepaid Flights': {
                'keywords': ['flight booking', 'airline booking', 'ticket booking'],
                'confidence_boost': 0.85
            },
            'Prepaid Accommodation': {
                'keywords': ['hotel booking', 'accommodation booking', 'airbnb booking'],
                'confidence_boost': 0.85
            },
            'Prepaid Car Rental & Fuel': {
                'keywords': ['car rental booking', 'fuel prepaid'],
                'confidence_boost': 0.85
            }
        }

        best_match = None
        best_confidence = 0.0
        match_reason = ''
        all_text_words = all_text.split()

        for category, config in category_keywords.items():
            for keyword in config['keywords']:
                keyword_words = keyword.split()
                match_found = False

                if len(keyword_words) == 1:
                    match_found = keyword_words[0] in all_text_words
                else:
                    match_found = keyword in all_text

                if match_found:
                    confidence = config['confidence_boost']
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = category
                        match_reason = f"Matched keyword '{keyword}' in receipt details"
                    break

        if best_match and best_confidence >= 0.75:
            return {
                'category': best_match,
                'confidence': best_confidence,
                'reason': match_reason
            }

        return {
            'category': 'Other',
            'confidence': 0.5,
            'reason': 'No reliable category match found'
        }

    @staticmethod
    def _is_valid_receipt(extracted: dict) -> bool:
        """
        Validate that the document is actually a receipt.

        Requires:
        - merchant/vendor name (evidence of where transaction occurred)
        - monetary/total amount (evidence of transaction value)
        - at least one additional receipt indicator (date, invoice number, payment method, or line items)
        """
        if not extracted:
            return False

        merchant_name = extracted.get('merchant', {}).get('name')
        total_amount = extracted.get('amounts', {}).get('total')
        transaction_date = extracted.get('invoice', {}).get('transaction_date')
        invoice_number = extracted.get('invoice', {}).get('invoice_number')
        payment_method = extracted.get('payment', {}).get('method')
        line_items = extracted.get('line_items', [])

        has_merchant = bool(merchant_name and str(merchant_name).strip())
        has_total = total_amount is not None
        has_date = bool(transaction_date and str(transaction_date).strip())
        has_invoice = bool(invoice_number and str(invoice_number).strip())
        has_payment = bool(payment_method and str(payment_method).strip())
        has_line_items = bool(line_items) and len(line_items) > 0

        additional_indicators = sum([has_date, has_invoice, has_payment, has_line_items])

        return has_merchant and has_total and additional_indicators >= 1

    @staticmethod
    def _is_ocr_result_blank(extracted: dict) -> bool:
        """Check if OCR extraction result is completely empty/blank."""
        if not extracted:
            return True

        merchant_name = extracted.get('merchant', {}).get('name')
        total_amount = extracted.get('amounts', {}).get('total')
        transaction_date = extracted.get('invoice', {}).get('transaction_date')
        ocr_content = extracted.get('extraction', {}).get('ocr_content', '')

        has_merchant = bool(merchant_name and str(merchant_name).strip())
        has_amount = total_amount is not None
        has_date = bool(transaction_date and str(transaction_date).strip())
        has_ocr_text = bool(ocr_content and len(str(ocr_content).strip()) > 20)

        if not (has_merchant or has_amount or has_date or has_ocr_text):
            return True

        return False

    @staticmethod
    def _generate_blob_name(owner: str, receipt_id, filename: str) -> str:
        clean_filename = filename.replace('/', '_').replace('\\', '_')
        return f"receipts/{owner}/{receipt_id}/{clean_filename}"

    @staticmethod
    def _get_mime_type(filename: str) -> str:
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        mime_types = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
        }
        return mime_types.get(ext, 'application/octet-stream')
