#!/usr/bin/env python
"""
End-to-end test for receipt deletion functionality using Django TestCase.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import TestCase, Client, override_settings
from receipts.models import Receipt
from decimal import Decimal
from datetime import date
import uuid

@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class ReceiptDeleteTests(TestCase):
    """Tests for receipt deletion functionality."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_finance_can_delete_receipt(self):
        """Test that finance user can delete a receipt."""
        # Create test receipt
        receipt = Receipt.objects.create(
            owner='finance-department',
            original_filename='test.pdf',
            blob_name=f'test_blob_{uuid.uuid4()}',
            mime_type='application/pdf',
            file_size=1024,
            sha256_hash=f'hash_{uuid.uuid4()}',
            status='NEEDS_REVIEW',
            vendor_name='Test Vendor',
            total_amount=Decimal('50.00'),
            currency='USD',
            category='Other'
        )
        receipt_id = receipt.id

        # Verify it exists
        self.assertTrue(Receipt.objects.filter(id=receipt_id).exists())

        # Delete it
        response = self.client.delete(
            f'/api/v1/receipts/{receipt_id}/delete_receipt/?owner=finance-department',
            content_type='application/json'
        )

        # Should return 204
        self.assertEqual(response.status_code, 204, f"Got {response.status_code}: {response.content}")

        # Verify it's deleted
        self.assertFalse(Receipt.objects.filter(id=receipt_id).exists())

    def test_non_finance_cannot_delete(self):
        """Test that non-finance user cannot delete a receipt."""
        # Create test receipt
        receipt = Receipt.objects.create(
            owner='finance-department',
            original_filename='test.pdf',
            blob_name=f'test_blob_{uuid.uuid4()}',
            mime_type='application/pdf',
            file_size=1024,
            sha256_hash=f'hash_{uuid.uuid4()}',
            status='NEEDS_REVIEW',
            vendor_name='Test Vendor',
            total_amount=Decimal('50.00'),
            currency='USD',
            category='Other'
        )
        receipt_id = receipt.id

        # Try to delete as non-finance user
        response = self.client.delete(
            f'/api/v1/receipts/{receipt_id}/delete_receipt/?owner=default-user',
            content_type='application/json'
        )

        # Should return 403
        self.assertEqual(response.status_code, 403, f"Got {response.status_code}")

        # Verify it still exists
        self.assertTrue(Receipt.objects.filter(id=receipt_id).exists())

        # Clean up
        receipt.delete()

    def test_delete_nonexistent_receipt(self):
        """Test deleting a receipt that doesn't exist."""
        fake_id = '00000000-0000-0000-0000-000000000000'
        response = self.client.delete(
            f'/api/v1/receipts/{fake_id}/delete_receipt/?owner=finance-department',
            content_type='application/json'
        )

        # Should return 404
        self.assertEqual(response.status_code, 404)

    def test_delete_one_does_not_affect_other(self):
        """Test that deleting one receipt doesn't affect others."""
        # Create two receipts
        receipt1 = Receipt.objects.create(
            owner='finance-department',
            original_filename='test1.pdf',
            blob_name=f'test_blob_1_{uuid.uuid4()}',
            mime_type='application/pdf',
            file_size=1024,
            sha256_hash=f'hash1_{uuid.uuid4()}',
            status='NEEDS_REVIEW',
            vendor_name='Vendor 1',
            total_amount=Decimal('100.00'),
            currency='USD',
            category='Other'
        )

        receipt2 = Receipt.objects.create(
            owner='finance-department',
            original_filename='test2.pdf',
            blob_name=f'test_blob_2_{uuid.uuid4()}',
            mime_type='application/pdf',
            file_size=1024,
            sha256_hash=f'hash2_{uuid.uuid4()}',
            status='NEEDS_REVIEW',
            vendor_name='Vendor 2',
            total_amount=Decimal('200.00'),
            currency='USD',
            category='Other'
        )

        receipt1_id = receipt1.id
        receipt2_id = receipt2.id

        # Delete receipt1
        response = self.client.delete(
            f'/api/v1/receipts/{receipt1_id}/delete_receipt/?owner=finance-department',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)

        # Verify receipt1 is gone
        self.assertFalse(Receipt.objects.filter(id=receipt1_id).exists())

        # Verify receipt2 still exists
        self.assertTrue(Receipt.objects.filter(id=receipt2_id).exists())

        # Clean up
        receipt2.delete()

if __name__ == '__main__':
    import unittest
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(ReceiptDeleteTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
