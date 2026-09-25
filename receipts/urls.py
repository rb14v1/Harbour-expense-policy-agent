from django.urls import path, include
from rest_framework.routers import DefaultRouter
from receipts.views import ReceiptViewSet, download_receipt

router = DefaultRouter()
router.register(r'receipts', ReceiptViewSet, basename='receipt')

urlpatterns = [
    # Explicit download endpoint (avoids DRF action routing and APPEND_SLASH redirect)
    path('receipts/<str:receipt_id>/download', download_receipt, name='receipt-download'),
    # DRF routed endpoints
    path('', include(router.urls)),
]
