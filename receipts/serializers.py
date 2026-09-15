from rest_framework import serializers
from receipts.models import Receipt


class ReceiptDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = [
            'id', 'status', 'original_filename', 'vendor_name', 'transaction_date',
            'total_amount', 'currency', 'duplicate_score', 'duplicate_reason',
            'policy_status', 'policy_result_json', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class ReceiptStatusSerializer(serializers.ModelSerializer):
    is_final = serializers.SerializerMethodField()
    stage = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()

    class Meta:
        model = Receipt
        fields = [
            'id', 'status', 'stage', 'is_final', 'message', 'duplicate_score',
            'duplicate_reason', 'policy_status'
        ]
        read_only_fields = fields

    def get_is_final(self, obj):
        return obj.is_final()

    def get_stage(self, obj):
        stages = {
            'UPLOADED': 'upload',
            'HASHING': 'upload',
            'EXACT_DUPLICATE': 'duplicate_check',
            'QUEUED_FOR_OCR': 'ocr',
            'OCR_PROCESSING': 'ocr',
            'OCR_FAILED': 'ocr',
            'EXTRACTED': 'ocr',
            'NORMALIZED': 'duplicate_check',
            'DUPLICATE_CHECKING': 'duplicate_check',
            'SEMANTIC_DUPLICATE': 'duplicate_check',
            'UNIQUE': 'policy',
            'POLICY_PROCESSING': 'policy',
            'APPROVED': 'approved',
            'REJECTED': 'rejected',
            'FAILED': 'error',
        }
        return stages.get(obj.status, 'unknown')

    def get_message(self, obj):
        messages = {
            'UPLOADED': 'Receipt uploaded successfully.',
            'HASHING': 'Calculating file hash.',
            'EXACT_DUPLICATE': 'Duplicate receipt detected. This exact file has already been uploaded.',
            'QUEUED_FOR_OCR': 'Receipt queued for processing.',
            'OCR_PROCESSING': 'Reading receipt details.',
            'OCR_FAILED': f'OCR failed: {obj.duplicate_reason}',
            'EXTRACTED': 'Receipt details extracted.',
            'NORMALIZED': 'Normalizing receipt data.',
            'DUPLICATE_CHECKING': 'Checking for duplicate expenses.',
            'SEMANTIC_DUPLICATE': 'Possible duplicate expense detected. A matching expense already exists.',
            'UNIQUE': 'No duplicate found. Checking expense policy.',
            'POLICY_PROCESSING': 'Validating against expense policy.',
            'APPROVED': 'Receipt approved successfully.',
            'REJECTED': 'Receipt rejected by policy.',
            'FAILED': 'Receipt processing failed.',
        }
        return messages.get(obj.status, 'Processing...')


class ReceiptListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = [
            'id', 'status', 'original_filename', 'vendor_name', 'transaction_date',
            'total_amount', 'currency', 'created_at'
        ]
        read_only_fields = fields


class ReceiptUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def create(self, validated_data):
        from receipts.services import ReceiptService
        service = ReceiptService()
        file_obj = validated_data['file']
        receipt = service.create_and_upload_receipt(
            file_obj,
            file_obj.name,
            owner=self.context.get('owner', 'default-user')
        )
        return receipt
