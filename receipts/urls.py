from django.urls import path, include
from rest_framework.routers import DefaultRouter
from receipts.views import ReceiptViewSet, download_receipt, user_manual_view, user_manual_info_view

router = DefaultRouter()
router.register(r'receipts', ReceiptViewSet, basename='receipt')

urlpatterns = [
    # Explicit download endpoint (avoids DRF action routing and APPEND_SLASH redirect)
    path('receipts/<str:receipt_id>/download', download_receipt, name='receipt-download'),
    # User manual endpoints
    path('user-manual/', user_manual_view, name='user-manual'),
    path('user-manual/info/', user_manual_info_view, name='user-manual-info'),
    # DRF routed endpoints (includes delete_receipt action at /receipts/{id}/delete_receipt/)
    path('', include(router.urls)),
]
