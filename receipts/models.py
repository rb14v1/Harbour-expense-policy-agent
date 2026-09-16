import uuid
from django.db import models


class Receipt(models.Model):
    STATUS_CHOICES = [
        ('UPLOADED', 'Uploaded'),
        ('HASHING', 'Calculating Hash'),
        ('EXACT_DUPLICATE', 'Exact Duplicate'),
        ('QUEUED_FOR_OCR', 'Queued for OCR'),
        ('OCR_PROCESSING', 'OCR Processing'),
        ('OCR_FAILED', 'OCR Failed'),
        ('EXTRACTED', 'Extracted'),
        ('NORMALIZED', 'Normalized'),
        ('DUPLICATE_CHECKING', 'Checking for Duplicates'),
        ('SEMANTIC_DUPLICATE', 'Semantic Duplicate'),
        ('UNIQUE', 'Unique'),
        ('POLICY_PROCESSING', 'Policy Processing'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('NEEDS_REVIEW', 'Needs Review'),
        ('FAILED', 'Failed'),
    ]

    CATEGORY_CHOICES = [
        ('Accommodation', 'Accommodation'),
        ('Meals', 'Meals'),
        ('Travel', 'Travel'),
        ('Transportation', 'Transportation'),
        ('Car Rental', 'Car Rental'),
        ('Fuel', 'Fuel'),
        ('Client Entertainment', 'Client Entertainment'),
        ('Office Supplies', 'Office Supplies'),
        ('Other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.CharField(max_length=255, default='default-user')

    original_filename = models.CharField(max_length=255)
    blob_name = models.CharField(max_length=500, unique=True)
    mime_type = models.CharField(max_length=50)
    file_size = models.BigIntegerField()
    sha256_hash = models.CharField(max_length=64, db_index=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='UPLOADED')

    vendor_name = models.CharField(max_length=255, null=True, blank=True)
    vendor_normalized = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    invoice_number = models.CharField(max_length=255, null=True, blank=True)
    invoice_number_normalized = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    transaction_date = models.DateField(null=True, blank=True, db_index=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, db_index=True)
    currency = models.CharField(max_length=3, null=True, blank=True, db_index=True)
    payment_method = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Other', db_index=True)

    normalized_json = models.JSONField(null=True, blank=True)
    raw_document_intelligence_json = models.JSONField(null=True, blank=True)

    exact_duplicate_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exact_duplicates'
    )
    semantic_duplicate_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='semantic_duplicates'
    )
    duplicate_score = models.IntegerField(null=True, blank=True)
    duplicate_reason = models.TextField(null=True, blank=True)

    processing_message = models.TextField(null=True, blank=True)

    policy_status = models.CharField(max_length=50, null=True, blank=True)
    policy_result_json = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['sha256_hash']),
        ]

    def __str__(self):
        return f"{self.id} - {self.vendor_name or 'Unknown'} ({self.status})"

    def is_final(self):
        return self.status in ['EXACT_DUPLICATE', 'SEMANTIC_DUPLICATE', 'APPROVED', 'REJECTED', 'FAILED']

    def mark_exact_duplicate(self, original_receipt):
        self.status = 'EXACT_DUPLICATE'
        self.exact_duplicate_of = original_receipt
        self.duplicate_reason = "Same file content was already uploaded."
        self.processing_message = "This receipt has already been uploaded."
        self.save()

    def mark_semantic_duplicate(self, original_receipt, score, reason):
        self.status = 'SEMANTIC_DUPLICATE'
        self.semantic_duplicate_of = original_receipt
        self.duplicate_score = score
        self.duplicate_reason = reason
        self.processing_message = "This receipt appears to duplicate a previously uploaded receipt."
        self.save()

    def mark_unique(self):
        self.status = 'UNIQUE'
        self.save()

    def mark_ocr_processing(self):
        self.status = 'OCR_PROCESSING'
        self.save()

    def mark_ocr_failed(self, error_msg):
        self.status = 'OCR_FAILED'
        self.duplicate_reason = f"OCR failed: {error_msg}"
        self.save()
