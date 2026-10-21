import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from receipts.models import Receipt
from receipts.serializers import ReceiptDetailSerializer, ReceiptListSerializer

logger = logging.getLogger(__name__)


def finance_dashboard(request):
    return render(request, 'finance/dashboard.html')


@api_view(['GET'])
def finance_categories_list(request):
    categories = [choice[0] for choice in Receipt.CATEGORY_CHOICES]
    return Response({'categories': categories})


@api_view(['GET'])
def finance_receipts_list(request):
    queryset = Receipt.objects.all().order_by('-created_at')

    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    category_filter = request.query_params.get('category')
    if category_filter:
        queryset = queryset.filter(category=category_filter)

    vendor_filter = request.query_params.get('vendor')
    if vendor_filter:
        queryset = queryset.filter(vendor_name__icontains=vendor_filter)

    filename_filter = request.query_params.get('filename')
    if filename_filter:
        queryset = queryset.filter(original_filename__icontains=filename_filter)

    date_from = request.query_params.get('date_from')
    if date_from:
        queryset = queryset.filter(transaction_date__gte=date_from)

    date_to = request.query_params.get('date_to')
    if date_to:
        queryset = queryset.filter(transaction_date__lte=date_to)

    amount_min = request.query_params.get('amount_min')
    if amount_min:
        queryset = queryset.filter(total_amount__gte=amount_min)

    amount_max = request.query_params.get('amount_max')
    if amount_max:
        queryset = queryset.filter(total_amount__lte=amount_max)

    paginator = request.query_params.get('page', 1)
    page_size = 50

    try:
        start = (int(paginator) - 1) * page_size
        end = start + page_size
        total_count = queryset.count()

        receipts = queryset[start:end]
        serializer = ReceiptListSerializer(receipts, many=True)

        return Response({
            'count': total_count,
            'next': int(paginator) + 1 if end < total_count else None,
            'previous': int(paginator) - 1 if int(paginator) > 1 else None,
            'results': serializer.data,
        })
    except (ValueError, IndexError):
        return Response({'error': 'Invalid pagination'}, status=400)


@api_view(['GET'])
def finance_receipt_detail(request, receipt_id):
    try:
        receipt = Receipt.objects.get(id=receipt_id)
        serializer = ReceiptDetailSerializer(receipt)
        return Response(serializer.data)
    except Receipt.DoesNotExist:
        return Response({'error': 'Receipt not found'}, status=404)


@api_view(['POST'])
def finance_receipt_decision(request, receipt_id):
    """
    Record Finance department decision on a receipt.

    POST /finance/api/receipts/{receipt_id}/decision/
    {
        "decision": "APPROVED" | "REJECTED",
        "notes": "optional notes"
    }

    Concurrency-safe implementation using select_for_update():
    - Acquires row-level lock before checking status
    - Only one decision can succeed for a given receipt
    - Prevents APPROVED → REJECTED and REJECTED → APPROVED transitions
    - Prevents approving/rejecting the same receipt twice

    Validation:
    - Receipt must be in NEEDS_REVIEW or UNIQUE status to accept a decision
    - Once APPROVED, cannot be changed to REJECTED
    - Once REJECTED, cannot be changed to APPROVED
    - Cannot approve/reject the same receipt twice
    """
    decision = request.data.get('decision', '').upper()
    notes = request.data.get('notes', '')

    valid_decisions = ['APPROVED', 'REJECTED']
    if decision not in valid_decisions:
        return Response(
            {'error': f'Invalid decision. Must be one of: {", ".join(valid_decisions)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Use atomic transaction with row-level lock to prevent concurrent decisions
    try:
        with transaction.atomic():
            # select_for_update() locks the row until transaction commits
            # Other requests will wait, preventing race conditions
            receipt = Receipt.objects.select_for_update().get(id=receipt_id)

            # Re-check status after acquiring lock (status may have changed while waiting)
            if receipt.status not in ['NEEDS_REVIEW', 'UNIQUE']:
                return Response(
                    {
                        'error': f'Cannot change decision for receipt with status {receipt.status}. '
                                 'Only receipts in NEEDS_REVIEW or UNIQUE status can receive a decision.',
                        'current_status': receipt.status,
                        'code': 'INVALID_STATUS_FOR_DECISION'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update status and optionally update notes
            receipt.status = decision
            if notes:
                receipt.processing_message = notes
            receipt.save()

            logger.info(f"Receipt {receipt_id} marked as {decision} by Finance")

    except Receipt.DoesNotExist:
        return Response({'error': 'Receipt not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ReceiptDetailSerializer(receipt)
    return Response(serializer.data, status=status.HTTP_200_OK)
