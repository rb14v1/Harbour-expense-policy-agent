from django.urls import path
from teams_app.views import (
    teams_message_handler,
    teams_file_upload_handler,
    teams_receipt_status,
    teams_health_check,
    finance_tab_config
)

urlpatterns = [
    path('health/', teams_health_check, name='teams-health'),
    path('messages/', teams_message_handler, name='teams-messages'),
    path('upload/', teams_file_upload_handler, name='teams-upload'),
    path('receipts/<str:receipt_id>/status/', teams_receipt_status, name='teams-receipt-status'),
    path('finance/tab/config/', finance_tab_config, name='finance-tab-config'),
]
