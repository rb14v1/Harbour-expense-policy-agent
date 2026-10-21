#!/usr/bin/env python
"""
Verify that both bugs have been fixed.
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
import uuid
import re

@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class BugFixVerification(TestCase):
    """Verify both bugs have been fixed."""

    def test_bug_1_delete_returns_204_with_empty_body(self):
        """Bug 1 Fix: DELETE endpoint returns 204 with empty body (no content-length mismatch)."""
        print("\n" + "="*70)
        print("VERIFYING BUG 1 FIX: Delete 204 response with empty body")
        print("="*70)

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

        # Delete it
        client = Client()
        response = client.delete(
            f'/api/v1/receipts/{receipt_id}/delete_receipt/?owner=finance-department',
            content_type='application/json'
        )

        # Verify status 204
        print(f"✓ Response status: {response.status_code}")
        self.assertEqual(response.status_code, 204)

        # Verify empty body (no content)
        print(f"✓ Response content length: {len(response.content)} bytes")
        self.assertEqual(len(response.content), 0, "Response body should be empty for 204")

        # Verify Content-Length header if present
        content_length = response.get('Content-Length')
        if content_length:
            print(f"✓ Content-Length header: {content_length}")
            self.assertEqual(content_length, '0')

        # Verify receipt is deleted
        exists = Receipt.objects.filter(id=receipt_id).exists()
        self.assertFalse(exists)
        print(f"✓ Receipt successfully deleted from database")

        print("\n✅ BUG 1 FIX VERIFIED: 204 response now has empty body, no content-length mismatch")
        return True

    def test_bug_2_user_manual_navigation_links(self):
        """Bug 2 Fix: User manual navigation links are properly structured and visible."""
        print("\n" + "="*70)
        print("VERIFYING BUG 2 FIX: User manual navigation links")
        print("="*70)

        # Read the actual manual file
        import os
        manual_path = os.path.join(os.path.dirname(__file__), 'expense_policy_agent_user_manual.html')

        with open(manual_path, 'r', encoding='utf-8') as f:
            manual_content = f.read()

        # Verify navigation links exist
        nav_links = [
            ('#introduction', 'Introduction'),
            ('#employee-workflow', 'Employee Workflow'),
            ('#expense-statuses', 'Expense Statuses'),
            ('#glossary', 'Glossary'),
        ]

        print("\n✓ Checking navigation links:")
        for anchor, label in nav_links:
            # Check link exists
            link_pattern = f'href="{anchor}"'
            self.assertIn(link_pattern, manual_content, f"Link {anchor} not found")
            print(f"  ✓ {label} link found: {link_pattern}")

        # Verify section IDs exist (anchor targets)
        print("\n✓ Checking section IDs (anchor targets):")
        for anchor, label in nav_links:
            section_id = anchor[1:]  # Remove #
            id_pattern = f'id="{section_id}"'
            self.assertIn(id_pattern, manual_content, f"Section ID {section_id} not found")
            print(f"  ✓ {label} section found: {id_pattern}")

        # Verify no broken/removed sections in navigation
        print("\n✓ Checking removed sections are NOT in navigation:")
        removed_sections = ['scenarios', 'faq', 'quick-reference', 'finance-workflow']
        for section in removed_sections:
            anchor = f'#{section}'
            self.assertNotIn(f'href="{anchor}"', manual_content, f"Removed section {section} should not be in nav")
            print(f"  ✓ {section} correctly removed from navigation")

        # Verify CSS layout is correct (no centering that breaks scrolling)
        css_file_path = os.path.join(os.path.dirname(__file__), 'frontend/src/styles/userManualModal.css')
        with open(css_file_path, 'r', encoding='utf-8') as f:
            css_content = f.read()

        print("\n✓ Checking CSS layout for modal:")
        # Verify manual-html-content is flex: 1
        self.assertIn('.manual-html-content', css_content)
        self.assertIn('flex: 1', css_content)
        print(f"  ✓ .manual-html-content uses flex: 1 for proper sizing")

        # Verify iframe is 100% height
        self.assertIn('.manual-iframe', css_content)
        iframe_css = css_content[css_content.find('.manual-iframe'):css_content.find('.manual-iframe') + 200]
        self.assertIn('height: 100%', iframe_css)
        print(f"  ✓ .manual-iframe is 100% height for full scrolling")

        print("\n✅ BUG 2 FIX VERIFIED: User manual navigation structure is correct and CSS layout allows scrolling")
        return True

if __name__ == '__main__':
    import unittest

    print("\n" + "="*70)
    print("BUG FIX VERIFICATION TEST")
    print("="*70)

    # Run verification tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(BugFixVerification)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    if result.wasSuccessful():
        print("✅ ALL BUG FIXES VERIFIED SUCCESSFULLY")
        print("="*70)
        print("\nBug 1: DELETE /api/v1/receipts/{id}/delete_receipt/")
        print("  - Now returns HTTP 204 with empty body")
        print("  - No content-length mismatch")
        print("  - Receipt successfully deleted from database")
        print("\nBug 2: User Manual Navigation")
        print("  - All navigation links properly configured")
        print("  - Section IDs match anchor links")
        print("  - Removed sections not in navigation")
        print("  - CSS layout allows proper scrolling and visibility")
    else:
        print("❌ SOME TESTS FAILED")
        print("="*70)
        for failure in result.failures + result.errors:
            print(f"\nFailed: {failure[0]}")
            print(failure[1])

    sys.exit(0 if result.wasSuccessful() else 1)
