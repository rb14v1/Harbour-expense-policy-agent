from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import render
from django.http import FileResponse, Http404, JsonResponse, HttpResponse
from django.conf import settings
from django.db import transaction
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
from teams_app.auth import require_finance_auth
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

        # Determine Content-Disposition based on file type
        # PDFs should download (attachment) on mobile
        # Images should display inline in browser where supported
        is_pdf = preview_receipt.mime_type and 'pdf' in preview_receipt.mime_type.lower()
        is_image = preview_receipt.mime_type and preview_receipt.mime_type.lower().startswith('image/')

        if is_pdf:
            # PDF: force download with attachment disposition for reliable mobile handling
            safe_filename = preview_receipt.original_filename
            if not safe_filename.lower().endswith('.pdf'):
                safe_filename = f"{safe_filename}.pdf"
            response = FileResponse(iter([file_bytes]), content_type=preview_receipt.mime_type)
            response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        elif is_image:
            # Image: display inline in browser for better mobile UX
            response = FileResponse(iter([file_bytes]), content_type=preview_receipt.mime_type)
            response['Content-Disposition'] = 'inline'
        else:
            # Other types: default to attachment for safety
            response = FileResponse(iter([file_bytes]), content_type=preview_receipt.mime_type, as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{preview_receipt.original_filename}"'

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

    @action(detail=True, methods=['delete'])
    @require_finance_auth
    def delete_receipt(self, request, pk=None):
        """
        Safely delete a receipt.
        Only Finance Department users can delete receipts.
        Deletes both database record and associated blob from Azure Storage.
        """
        owner = request.query_params.get('owner', 'default-user')

        if owner != 'finance-department':
            return Response(
                {'error': 'Unauthorized. Finance Department access required.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            receipt = self.get_object()
        except Http404:
            return Response(
                {'error': 'Receipt not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Use transaction to ensure atomicity
            with transaction.atomic():
                blob_name = receipt.blob_name
                receipt_id = receipt.id

                logger.info(f"[DELETE_START] receipt_id={receipt_id}, blob_name={blob_name}, deleted_by=finance-department")

                # Step 1: Delete from database first
                receipt.delete()
                logger.info(f"[DELETE_DB_SUCCESS] receipt_id={receipt_id}")

                # Step 2: Delete blob from Azure Storage (if exists)
                if blob_name:
                    try:
                        blob_service = BlobService()
                        blob_service.delete(blob_name)
                        logger.info(f"[DELETE_BLOB_SUCCESS] blob_name={blob_name}, receipt_id={receipt_id}")
                    except BlobUploadError as e:
                        logger.error(f"[DELETE_BLOB_FAILED] blob_name={blob_name}, receipt_id={receipt_id}, error={str(e)}")
                        # Log error but don't fail - database deletion is primary concern
                    except Exception as e:
                        logger.error(f"[DELETE_BLOB_UNEXPECTED] blob_name={blob_name}, receipt_id={receipt_id}, error={str(e)}")

                logger.info(f"[DELETE_SUCCESS] receipt_id={receipt_id}, blob_name={blob_name}")

                # HTTP 204 No Content must have empty body - return empty Response
                return Response(
                    status=status.HTTP_204_NO_CONTENT
                )

        except Exception as e:
            logger.error(f"[DELETE_ERROR] receipt_id={pk}, error={str(e)}")
            return Response(
                {'error': f'Failed to delete receipt: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def download_receipt(request, receipt_id):
    """
    Explicit endpoint to download/preview receipt files.
    Handles both GET and HEAD requests without 301 redirect.
    Properly supports Teams mobile webview PDF handling.
    """
    import logging
    diag_logger = logging.getLogger('download_receipt_diagnostic')

    owner = request.GET.get('owner', 'default-user')

    diag_logger.info(f"[DOWNLOAD_START] receipt_id={receipt_id}, method={request.method}, owner={owner}, query_params={dict(request.GET)}")

    try:
        receipt = Receipt.objects.get(id=receipt_id)
        diag_logger.info(f"[RECEIPT_FOUND] id={receipt.id}, owner={receipt.owner}, status={receipt.status}, blob_name={receipt.blob_name[:50] if receipt.blob_name else 'EMPTY'}, exact_dup={receipt.exact_duplicate_of}, semantic_dup={receipt.semantic_duplicate_of}")
    except Receipt.DoesNotExist:
        diag_logger.warning(f"[RECEIPT_NOT_FOUND] receipt_id={receipt_id}")
        return JsonResponse(
            {'error': 'Receipt not found'},
            status=404
        )

    # Authorization: allow owner or finance-department
    if owner != 'finance-department' and receipt.owner != owner:
        diag_logger.warning(f"[UNAUTHORIZED] receipt_owner={receipt.owner}, request_owner={owner}")
        return JsonResponse(
            {'error': 'Unauthorized'},
            status=403
        )

    preview_receipt = receipt

    # Handle duplicates: find the original file
    if not receipt.blob_name:
        diag_logger.info(f"[NO_BLOB_NAME] receipt_status={receipt.status}, checking for duplicates")
        if receipt.status == 'EXACT_DUPLICATE' and receipt.exact_duplicate_of:
            original = receipt.exact_duplicate_of
            diag_logger.info(f"[EXACT_DUPLICATE_FOUND] original_id={original.id}, original_blob={original.blob_name[:50] if original.blob_name else 'EMPTY'}")
            if owner != 'finance-department' and original.owner != owner:
                diag_logger.warning(f"[UNAUTHORIZED_DUPLICATE_ORIGINAL] original_owner={original.owner}, request_owner={owner}")
                return JsonResponse(
                    {'error': 'Unauthorized'},
                    status=403
                )
            preview_receipt = original
        elif receipt.status == 'SEMANTIC_DUPLICATE' and receipt.semantic_duplicate_of:
            original = receipt.semantic_duplicate_of
            diag_logger.info(f"[SEMANTIC_DUPLICATE_FOUND] original_id={original.id}, original_blob={original.blob_name[:50] if original.blob_name else 'EMPTY'}")
            if owner != 'finance-department' and original.owner != owner:
                diag_logger.warning(f"[UNAUTHORIZED_DUPLICATE_ORIGINAL] original_owner={original.owner}, request_owner={owner}")
                return JsonResponse(
                    {'error': 'Unauthorized'},
                    status=403
                )
            preview_receipt = original
        else:
            diag_logger.error(f"[ERROR_NO_BLOB_NOT_DUPLICATE] receipt_status={receipt.status}, no duplicate references found")
            return JsonResponse(
                {'error': 'Unable to download this receipt because the original file is no longer available'},
                status=404
            )

    if not preview_receipt.blob_name:
        diag_logger.error(f"[ERROR_PREVIEW_NO_BLOB] preview_receipt_id={preview_receipt.id}, preview_receipt_status={preview_receipt.status}")
        return JsonResponse(
            {'error': 'Unable to download this receipt because the original file is no longer available'},
            status=404
        )

    blob_service = BlobService()
    try:
        diag_logger.info(f"[BLOB_DOWNLOAD_START] blob_name={preview_receipt.blob_name[:50]}")
        file_bytes = blob_service.download(preview_receipt.blob_name)
        diag_logger.info(f"[BLOB_DOWNLOAD_SUCCESS] bytes={len(file_bytes)}")
    except BlobUploadError as e:
        diag_logger.error(f"[BLOB_UPLOAD_ERROR] blob_name={preview_receipt.blob_name[:50]}, error={str(e)}")
        return JsonResponse(
            {'error': 'Unable to download this receipt because the original file is no longer available'},
            status=404
        )
    except Exception as e:
        diag_logger.error(f"[BLOB_UNEXPECTED_ERROR] blob_name={preview_receipt.blob_name[:50]}, error_type={type(e).__name__}, error={str(e)}")
        return JsonResponse(
            {'error': 'Unable to retrieve the receipt file'},
            status=500
        )

    # Determine Content-Disposition and headers based on file type
    is_pdf = preview_receipt.mime_type and 'pdf' in preview_receipt.mime_type.lower()
    is_image = preview_receipt.mime_type and preview_receipt.mime_type.lower().startswith('image/')

    if is_pdf:
        safe_filename = preview_receipt.original_filename
        if not safe_filename.lower().endswith('.pdf'):
            safe_filename = f"{safe_filename}.pdf"
        response = FileResponse(iter([file_bytes]), content_type=preview_receipt.mime_type)
        response['Content-Disposition'] = f'inline; filename="{safe_filename}"'
        diag_logger.info(f"[RESPONSE_PDF] filename={safe_filename}")
    elif is_image:
        response = FileResponse(iter([file_bytes]), content_type=preview_receipt.mime_type)
        response['Content-Disposition'] = 'inline'
        diag_logger.info(f"[RESPONSE_IMAGE] mime_type={preview_receipt.mime_type}")
    else:
        response = FileResponse(iter([file_bytes]), content_type=preview_receipt.mime_type, as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{preview_receipt.original_filename}"'
        diag_logger.info(f"[RESPONSE_OTHER] mime_type={preview_receipt.mime_type}")

    # For HEAD requests, Django automatically strips the body but preserves headers
    # This ensures Teams mobile gets proper metadata without unnecessary redirect
    if request.method == 'HEAD':
        response['Content-Length'] = str(len(file_bytes))
        diag_logger.info(f"[RESPONSE_HEAD] content_length={len(file_bytes)}")

    diag_logger.info(f"[DOWNLOAD_SUCCESS] receipt_id={receipt_id}, method={request.method}, bytes={len(file_bytes)}")
    return response


def upload_form_view(request):
    return render(request, 'receipts/upload.html')


@api_view(['GET'])
def user_manual_view(request):
    """
    Retrieve the User Manual HTML document.
    Serves from Azure Blob Storage if available, falls back to local static file.
    """
    try:
        manual_blob_path = getattr(settings, 'MANUAL_BLOB_PATH', 'documentation/expense_policy_agent_user_manual.html')

        # Try to fetch from Blob Storage
        try:
            blob_service = BlobService()
            manual_bytes = blob_service.download(manual_blob_path)
            logger.info(f"[USER_MANUAL] Retrieved from Blob Storage: {manual_blob_path}")

            return HttpResponse(
                manual_bytes,
                content_type='text/html; charset=utf-8',
                headers={
                    'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
                    'Content-Disposition': 'inline',  # Display in browser, don't download
                }
            )
        except BlobUploadError as e:
            logger.warning(f"[USER_MANUAL] Blob Storage retrieval failed: {str(e)}. Trying local fallback.")

            # Fallback: Try to serve local HTML file
            import os
            manual_local_path = os.path.join(settings.BASE_DIR, 'expense_policy_agent_user_manual.html')

            if os.path.exists(manual_local_path):
                with open(manual_local_path, 'rb') as f:
                    manual_bytes = f.read()
                logger.info(f"[USER_MANUAL] Retrieved from local file: {manual_local_path}")

                return HttpResponse(
                    manual_bytes,
                    content_type='text/html; charset=utf-8',
                    headers={
                        'Cache-Control': 'public, max-age=3600',
                        'Content-Disposition': 'inline',
                    }
                )
            else:
                logger.error(f"[USER_MANUAL] Local file not found: {manual_local_path}")
                return Response(
                    {'error': 'User manual not available'},
                    status=status.HTTP_404_NOT_FOUND
                )

    except Exception as e:
        logger.error(f"[USER_MANUAL] Unexpected error retrieving manual: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to retrieve user manual'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def user_manual_info_view(request):
    """
    Get metadata about the user manual (availability, last updated).
    Useful for checking if manual is available before attempting to load.
    """
    try:
        manual_blob_path = getattr(settings, 'MANUAL_BLOB_PATH', 'documentation/expense_policy_agent_user_manual.html')
        blob_service = BlobService()

        try:
            # Try to get blob properties (this is a lightweight operation)
            blob_client = blob_service.container_client.get_blob_client(manual_blob_path)
            blob_properties = blob_client.get_blob_properties()

            return Response({
                'available': True,
                'last_updated': blob_properties.last_modified.isoformat() if blob_properties.last_modified else None,
                'size_bytes': blob_properties.size if blob_properties.size else 0,
            })
        except:
            # Check if local file exists
            import os
            manual_local_path = os.path.join(settings.BASE_DIR, 'expense_policy_agent_user_manual.html')

            if os.path.exists(manual_local_path):
                file_stats = os.stat(manual_local_path)
                from datetime import datetime
                last_modified = datetime.fromtimestamp(file_stats.st_mtime).isoformat()

                return Response({
                    'available': True,
                    'last_updated': last_modified,
                    'size_bytes': file_stats.st_size,
                    'source': 'local',
                })
            else:
                return Response({'available': False}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"[USER_MANUAL_INFO] Error: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to retrieve manual info'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
