from django.urls import path, include
from receipts.views import upload_form_view
from teams_app.views import teams_messages_proxy

urlpatterns = [
    path('upload/', upload_form_view, name='upload-form'),
    path('api/messages', teams_messages_proxy, name='teams-messages-proxy'),
    path('api/v1/', include('receipts.urls')),
    path('api/v1/teams/', include('teams_app.urls')),
    path('finance/', include('finance.urls')),
]
