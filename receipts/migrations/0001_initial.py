# Generated migration for Receipt model

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Receipt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('owner', models.CharField(default='default-user', max_length=255)),
                ('original_filename', models.CharField(max_length=255)),
                ('blob_name', models.CharField(max_length=500, unique=True)),
                ('mime_type', models.CharField(max_length=50)),
                ('file_size', models.BigIntegerField()),
                ('sha256_hash', models.CharField(db_index=True, max_length=64)),
                ('status', models.CharField(choices=[('UPLOADED', 'Uploaded'), ('HASHING', 'Calculating Hash'), ('EXACT_DUPLICATE', 'Exact Duplicate'), ('QUEUED_FOR_OCR', 'Queued for OCR'), ('OCR_PROCESSING', 'OCR Processing'), ('OCR_FAILED', 'OCR Failed'), ('EXTRACTED', 'Extracted'), ('NORMALIZED', 'Normalized'), ('DUPLICATE_CHECKING', 'Checking for Duplicates'), ('SEMANTIC_DUPLICATE', 'Semantic Duplicate'), ('UNIQUE', 'Unique'), ('POLICY_PROCESSING', 'Policy Processing'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('NEEDS_REVIEW', 'Needs Review'), ('FAILED', 'Failed')], default='UPLOADED', max_length=50)),
                ('vendor_name', models.CharField(blank=True, max_length=255, null=True)),
                ('vendor_normalized', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('invoice_number', models.CharField(blank=True, max_length=255, null=True)),
                ('invoice_number_normalized', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('transaction_date', models.DateField(blank=True, db_index=True, null=True)),
                ('subtotal', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('tax_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('total_amount', models.DecimalField(blank=True, db_index=True, decimal_places=2, max_digits=12, null=True)),
                ('currency', models.CharField(blank=True, db_index=True, max_length=3, null=True)),
                ('payment_method', models.CharField(blank=True, max_length=255, null=True)),
                ('normalized_json', models.JSONField(blank=True, null=True)),
                ('raw_document_intelligence_json', models.JSONField(blank=True, null=True)),
                ('duplicate_score', models.IntegerField(blank=True, null=True)),
                ('duplicate_reason', models.TextField(blank=True, null=True)),
                ('policy_status', models.CharField(blank=True, max_length=50, null=True)),
                ('policy_result_json', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('exact_duplicate_of', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='exact_duplicates', to='receipts.receipt')),
                ('semantic_duplicate_of', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='semantic_duplicates', to='receipts.receipt')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='receipt',
            index=models.Index(fields=['owner', 'created_at'], name='receipts_re_owner_idx'),
        ),
        migrations.AddIndex(
            model_name='receipt',
            index=models.Index(fields=['status'], name='receipts_re_status_idx'),
        ),
        migrations.AddIndex(
            model_name='receipt',
            index=models.Index(fields=['sha256_hash'], name='receipts_re_sha256_idx'),
        ),
    ]
