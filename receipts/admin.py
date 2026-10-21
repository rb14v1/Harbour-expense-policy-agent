from django.contrib import admin
from receipts.models import Receipt


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'owner', 'status', 'vendor_name', 'total_amount', 'transaction_date', 'created_at'
    )
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('vendor_name', 'invoice_number', 'sha256_hash', 'id')
    readonly_fields = (
        'id', 'sha256_hash', 'blob_name', 'created_at', 'updated_at',
        'raw_document_intelligence_json', 'normalized_json', 'policy_result_json'
    )
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'owner', 'status', 'created_at', 'updated_at')
        }),
        ('File Information', {
            'fields': ('original_filename', 'blob_name', 'mime_type', 'file_size', 'sha256_hash')
        }),
        ('Receipt Data', {
            'fields': (
                'vendor_name', 'vendor_normalized', 'invoice_number', 'invoice_number_normalized',
                'transaction_date', 'subtotal', 'tax_amount', 'total_amount', 'currency', 'payment_method'
            )
        }),
        ('Extracted Data', {
            'fields': ('raw_document_intelligence_json', 'normalized_json'),
            'classes': ('collapse',)
        }),
        ('Duplicate Information', {
            'fields': (
                'exact_duplicate_of', 'semantic_duplicate_of', 'duplicate_score', 'duplicate_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Policy Information', {
            'fields': ('policy_status', 'policy_result_json'),
            'classes': ('collapse',)
        }),
    )
