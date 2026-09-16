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
        ('Accommodation/Hotel', 'Accommodation/Hotel'),
        ('Australia - Mileage (KM) - electric vehicle', 'Australia - Mileage (KM) - electric vehicle'),
        ('Australia - Mileage (KM)- Petrol or diesel vehicle', 'Australia - Mileage (KM)- Petrol or diesel vehicle'),
        ('Bank Charges', 'Bank Charges'),
        ('Client Entertainment', 'Client Entertainment'),
        ('Computer Peripherals', 'Computer Peripherals'),
        ('Food: Breakfast or Lunch - Max Claim: €/$/AUD 15 / INR700', 'Food: Breakfast or Lunch - Max Claim: €/$/AUD 15 / INR700'),
        ('Food: Dinner - Max Claim: €/$/AUD 45 / INR700', 'Food: Dinner - Max Claim: €/$/AUD 45 / INR700'),
        ('Food: Per Diem - Max Claim: €/$/AUD 45 / INR 4000', 'Food: Per Diem - Max Claim: €/$/AUD 45 / INR 4000'),
        ('India - Mileage (KM) - electric vehicle - four wheeler', 'India - Mileage (KM) - electric vehicle - four wheeler'),
        ('India - Mileage (KM) - Petrol or diesel vehicle - four wheeler', 'India - Mileage (KM) - Petrol or diesel vehicle - four wheeler'),
        ('India - Mileage (KM) - Petrol or diesel vehicle - two wheeler', 'India - Mileage (KM) - Petrol or diesel vehicle - two wheeler'),
        ('India - Mileage (KM)- electric vehicle - two wheeler', 'India - Mileage (KM)- electric vehicle - two wheeler'),
        ('Other', 'Other'),
        ('Phone Bills/Broadband', 'Phone Bills/Broadband'),
        ('Prepaid Accommodation', 'Prepaid Accommodation'),
        ('Prepaid Car Rental & Fuel', 'Prepaid Car Rental & Fuel'),
        ('Prepaid Flights', 'Prepaid Flights'),
        ('Prepaid Luas/Bus/Train', 'Prepaid Luas/Bus/Train'),
        ('Prepaid Other', 'Prepaid Other'),
        ('Print & Postage', 'Print & Postage'),
        ('ROI - Mileage (KM) - electric vehicle - Lower Mileage Rate', 'ROI - Mileage (KM) - electric vehicle - Lower Mileage Rate'),
        ('ROI - Mileage (KM) - electric vehicle - Upper Mileage Rate', 'ROI - Mileage (KM) - electric vehicle - Upper Mileage Rate'),
        ('ROI - Mileage (KM) - Petrol or diesel vehicle - Lower Mileage Rate', 'ROI - Mileage (KM) - Petrol or diesel vehicle - Lower Mileage Rate'),
        ('ROI - Mileage (KM) - Petrol or diesel vehicle - Upper Mileage Rate', 'ROI - Mileage (KM) - Petrol or diesel vehicle - Upper Mileage Rate'),
        ('Slovenia - Mileage (KM) - electric vehicle - Residential', 'Slovenia - Mileage (KM) - electric vehicle - Residential'),
        ('Slovenia - Mileage (KM) - Petrol or diesel vehicle - Non-Residential', 'Slovenia - Mileage (KM) - Petrol or diesel vehicle - Non-Residential'),
        ('Slovenia - Mileage (KM) - Petrol or diesel vehicle - Residential', 'Slovenia - Mileage (KM) - Petrol or diesel vehicle - Residential'),
        ('Slovenia - Mileage (KM)- electric vehicle - Non-Residential', 'Slovenia - Mileage (KM)- electric vehicle - Non-Residential'),
        ('Software', 'Software'),
        ('Spain - Mileage (KM) - electric vehicle', 'Spain - Mileage (KM) - electric vehicle'),
        ('Spain - Mileage (KM)- Petrol or diesel vehicle', 'Spain - Mileage (KM)- Petrol or diesel vehicle'),
        ('Stationery Consumables', 'Stationery Consumables'),
        ('Training', 'Training'),
        ('Transport: Car Rental & Fuel', 'Transport: Car Rental & Fuel'),
        ('Transport: Flights', 'Transport: Flights'),
        ('Transport: Luas/Bus/Train', 'Transport: Luas/Bus/Train'),
        ('Transport: Taxis/Cab/Uber', 'Transport: Taxis/Cab/Uber'),
        ('Travel Other incl. Parking & Tolls', 'Travel Other incl. Parking & Tolls'),
        ('UK - Mileage (miles) - electric vehicle - Lower Mileage Rate', 'UK - Mileage (miles) - electric vehicle - Lower Mileage Rate'),
        ('UK - Mileage (miles) - electric vehicle - Upper Mileage Rate', 'UK - Mileage (miles) - electric vehicle - Upper Mileage Rate'),
        ('UK - Mileage (miles) - Petrol or diesel vehicle - Lower Mileage Rate', 'UK - Mileage (miles) - Petrol or diesel vehicle - Lower Mileage Rate'),
        ('UK - Mileage (miles) - Petrol or diesel vehicle - Upper Mileage Rate', 'UK - Mileage (miles) - Petrol or diesel vehicle - Upper Mileage Rate'),
        ('USA - Mileage (miles) - electric vehicle', 'USA - Mileage (miles) - electric vehicle'),
        ('USA - Mileage (miles)- Petrol or diesel vehicle', 'USA - Mileage (miles)- Petrol or diesel vehicle'),
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
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='Other', db_index=True)
    category_confidence = models.FloatField(default=0.0, null=True, blank=True)
    category_reason = models.TextField(null=True, blank=True)

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
