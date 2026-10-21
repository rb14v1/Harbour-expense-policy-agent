from django.urls import path
from finance.views import (
    finance_dashboard,
    finance_receipts_list,
    finance_receipt_detail,
    finance_receipt_decision,
    finance_categories_list,
)

urlpatterns = [
    path('', finance_dashboard, name='finance-dashboard'),
    path('tab/', finance_dashboard, name='finance-tab'),
    path('api/receipts/', finance_receipts_list, name='finance-receipts-list'),
    path('api/receipts/categories/', finance_categories_list, name='finance-categories-list'),
    path('api/receipts/<str:receipt_id>/', finance_receipt_detail, name='finance-receipt-detail'),
    path('api/receipts/<str:receipt_id>/decision/', finance_receipt_decision, name='finance-receipt-decision'),
]
