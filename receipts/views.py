from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from receipts.models import Receipt
from receipts.serializers import (
    ReceiptDetailSerializer,
    ReceiptStatusSerializer,
    ReceiptListSerializer,
    ReceiptUploadSerializer,
)
from receipts.tasks import process_receipt_task, process_receipt_task_sync
from receipts.exceptions import ReceiptAppException
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
            return ReceiptStatusSerializer
        elif self.action == 'list':
            return ReceiptListSerializer
        return ReceiptDetailSerializer

    def get_queryset(self):
        owner = self.request.query_params.get('owner', 'default-user')
        return Receipt.objects.filter(owner=owner)

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
                {'error': str(e)},
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


def upload_form_view(request):
    return render(request, 'receipts/upload.html')
