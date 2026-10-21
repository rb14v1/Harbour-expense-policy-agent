from django.conf import settings
from django.db.models import Q
from receipts.models import Receipt


class DuplicateService:
    WEIGHTS = {
        'invoice_match': 40,
        'vendor_match': 20,
        'date_match': 15,
        'total_match': 15,
        'tax_match': 5,
        'currency_match': 5,
    }

    @staticmethod
    def find_exact_duplicate(sha256_hash: str, user: str = None):

        query = Receipt.objects.filter(sha256_hash=sha256_hash)
        if user:
            query = query.filter(owner=user)
        query = query.exclude(status__in=['FAILED', 'HASHING'])
        return query.first()

    @staticmethod
    def evaluate_semantic_duplicate(receipt: Receipt):
        if not receipt.normalized_json:
            return None

        normalized = receipt.normalized_json
        vendor = normalized.get('vendor_normalized')
        invoice = normalized.get('invoice_number_normalized')
        date = normalized.get('transaction_date')
        total = normalized.get('total_amount')
        tax = normalized.get('tax_amount')
        currency = normalized.get('currency')

        existing_receipts = Receipt.objects.filter(
            owner=receipt.owner,
            status__in=['UNIQUE', 'NEEDS_REVIEW', 'APPROVED']
        ).exclude(id=receipt.id)

        best_match = None
        best_score = 0

        for existing in existing_receipts:
            if not existing.normalized_json:
                continue

            score = DuplicateService._calculate_duplicate_score(
                vendor, invoice, date, total, tax, currency,
                existing.normalized_json
            )

            if score > best_score:
                best_score = score
                best_match = existing

        if best_score >= settings.DUPLICATE_SCORE_THRESHOLD:
            reason = f"Matched with receipt {best_match.id} (score: {best_score})"
            return {
                'is_duplicate': True,
                'matched_receipt': best_match,
                'score': best_score,
                'reason': reason,
            }

        if best_score >= settings.REVIEW_SCORE_THRESHOLD:
            return {
                'is_duplicate': False,
                'needs_review': True,
                'matched_receipt': best_match,
                'score': best_score,
                'reason': f"Possible duplicate with score {best_score} (review threshold)",
            }

        return {
            'is_duplicate': False,
            'needs_review': False,
            'matched_receipt': None,
            'score': best_score,
        }

    @staticmethod
    def _calculate_duplicate_score(
        vendor: str,
        invoice: str,
        date: str,
        total: float,
        tax: float,
        currency: str,
        existing_normalized: dict
    ) -> int:
        score = 0

        existing_vendor = existing_normalized.get('vendor_normalized')
        existing_invoice = existing_normalized.get('invoice_number_normalized')
        existing_date = existing_normalized.get('transaction_date')
        existing_total = existing_normalized.get('total_amount')
        existing_tax = existing_normalized.get('tax_amount')
        existing_currency = existing_normalized.get('currency')

        if invoice and existing_invoice and invoice == existing_invoice:
            score += DuplicateService.WEIGHTS['invoice_match']

        if vendor and existing_vendor and vendor == existing_vendor:
            score += DuplicateService.WEIGHTS['vendor_match']

        if date and existing_date and date == existing_date:
            score += DuplicateService.WEIGHTS['date_match']

        if total is not None and existing_total is not None:
            if abs(float(total) - float(existing_total)) < 0.01:
                score += DuplicateService.WEIGHTS['total_match']

        if tax is not None and existing_tax is not None:
            if abs(float(tax) - float(existing_tax)) < 0.01:
                score += DuplicateService.WEIGHTS['tax_match']

        if currency and existing_currency and currency == existing_currency:
            score += DuplicateService.WEIGHTS['currency_match']

        return score
