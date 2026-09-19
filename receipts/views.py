from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from django.http import FileResponse, Http404
from receipts.models import Receipt
from receipts.serializers import (
    ReceiptDetailSerializer,
    ReceiptStatusSerializer,
    ReceiptListSerializer,
    ReceiptUploadSerializer,
)
from receipts.tasks import process_receipt_task, process_receipt_task_sync
from receipts.exceptions import ReceiptAppException, BlobUploadError
from receipts.services.blob_service import BlobService
import logging

logger = logging.getLogger(__name__)

try:
    from celery import current_app
    CELERY_AVAILABLE = current_app is not None
except:
    CELERY_AVAILABLE = False


class ReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Receipt.objects.all()
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ReceiptDetailSerializer
        elif self.action == 'list':
            return ReceiptListSerializer
        return ReceiptDetailSerializer

    def get_queryset(self):
        owner = self.request.query_params.get('owner', 'default-user')
        queryset = Receipt.objects.all().order_by('-created_at')

        if self.action not in ('preview', 'set_category'):
            queryset = queryset.filter(owner=owner)

            status_filter = self.request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            category_filter = self.request.query_params.get('category')
            if category_filter:
                queryset = queryset.filter(category=category_filter)

            vendor_filter = self.request.query_params.get('vendor')
            if vendor_filter:
                queryset = queryset.filter(vendor_name__icontains=vendor_filter)

            filename_filter = self.request.query_params.get('filename')
            if filename_filter:
                queryset = queryset.filter(original_filename__icontains=filename_filter)

            date_from = self.request.query_params.get('date_from')
            if date_from:
                queryset = queryset.filter(transaction_date__gte=date_from)

            date_to = self.request.query_params.get('date_to')
            if date_to:
                queryset = queryset.filter(transaction_date__lte=date_to)

            amount_min = self.request.query_params.get('amount_min')
            if amount_min:
                queryset = queryset.filter(total_amount__gte=amount_min)

            amount_max = self.request.query_params.get('amount_max')
            if amount_max:
                queryset = queryset.filter(total_amount__lte=amount_max)

        return queryset

    @action(detail=False, methods=['post'], parser_classes=(parsers.MultiPartParser,))
    def upload(self, request):
        serializer = ReceiptUploadSerializer(
            data=request.data,
            context={'owner': request.data.get('owner', 'default-user')}
        )

        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            receipt = serializer.save()

            if receipt.status == 'EXACT_DUPLICATE':
                return Response({
                    'receipt_id': str(receipt.id),
                    'status': receipt.status,
                    'message': receipt.duplicate_reason,
                    'is_final': True,
                }, status=status.HTTP_200_OK)

            if CELERY_AVAILABLE:
                process_receipt_task.delay(str(receipt.id))
                return Response({
                    'receipt_id': str(receipt.id),
                    'status': receipt.status,
                    'message': 'Receipt uploaded successfully and is being processed.',
                    'is_final': False,
                }, status=status.HTTP_201_CREATED)
            else:
                receipt = process_receipt_task_sync(str(receipt.id))
                updated_receipt = Receipt.objects.get(id=receipt['receipt_id'])
                return Response({
                    'receipt_id': str(updated_receipt.id),
                    'status': updated_receipt.status,
                    'message': 'Receipt processed successfully.',
                    'is_final': updated_receipt.is_final(),
                }, status=status.HTTP_201_CREATED)

        except ReceiptAppException as e:
            return Response(
                {'errors': {'file': [str(e)]}},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        receipt = self.get_object()
        serializer = ReceiptStatusSerializer(receipt)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        receipt = self.get_object()
        serializer = ReceiptDetailSerializer(receipt)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        receipt = self.get_object()
        owner = request.query_params.get('owner', 'default-user')

        # Allow finance-department to preview all receipts (reviewer role)
        if owner != 'finance-department' and receipt.owner != owner:
            return Response(
                {'error': 'Unauthorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        preview_receipt = receipt

        if not receipt.blob_name:
            if receipt.status == 'EXACT_DUPLICATE' and receipt.exact_duplicate_of:
                original = receipt.exact_duplicate_of
                if owner != 'finance-department' and original.owner != owner:
                    return Response(
                        {'error': 'Unauthorized'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                preview_receipt = original
            elif receipt.status == 'SEMANTIC_DUPLICATE' and receipt.semantic_duplicate_of:
                original = receipt.semantic_duplicate_of
                if owner != 'finance-department' and original.owner != owner:
                    return Response(
                        {'error': 'Unauthorized'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                preview_receipt = original
            else:
                return Response(
                    {'error': 'Unable to preview this receipt because the original file is no longer available'},
                    status=status.HTTP_404_NOT_FOUND
                )

        if not preview_receipt.blob_name:
            return Response(
                {'error': 'Unable to preview this receipt because the original file is no longer available'},
                status=status.HTTP_404_NOT_FOUND
            )

        blob_service = BlobService()
        try:
            file_bytes = blob_service.download(preview_receipt.blob_name)
        except BlobUploadError as e:
            logger.error(f"Failed to download blob {preview_receipt.blob_name}: {str(e)}")
            return Response(
                {'error': 'Unable to preview this receipt because the original file is no longer available'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error downloading blob {preview_receipt.blob_name}: {str(e)}")
            return Response(
                {'error': 'Unable to retrieve the receipt file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response = FileResponse(
            iter([file_bytes]),
            content_type=preview_receipt.mime_type,
            as_attachment=False
        )
        response['Content-Disposition'] = f'inline; filename="{preview_receipt.original_filename}"'
        return response

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Return the authoritative 45-category master list."""
        categories = [choice[0] for choice in Receipt.CATEGORY_CHOICES]
        return Response({'categories': categories})

    @action(detail=True, methods=['post'], parser_classes=(parsers.JSONParser,))
    def set_category(self, request, pk=None):
        """Allow manual category selection."""
        receipt = self.get_object()
        owner = request.query_params.get('owner', 'default-user')

        if receipt.owner != owner:
            return Response(
                {'error': 'Unauthorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        category = request.data.get('category')
        valid_categories = [choice[0] for choice in Receipt.CATEGORY_CHOICES]

        if category not in valid_categories:
            return Response(
                {'error': f'Invalid category. Must be one of {len(valid_categories)} valid categories.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        receipt.category = category
        receipt.category_confidence = 1.0
        receipt.category_reason = 'Manually selected by user'
        receipt.save()

        serializer = ReceiptDetailSerializer(receipt)
        return Response(serializer.data)


def upload_form_view(request):
    return render(request, 'receipts/upload.html')
