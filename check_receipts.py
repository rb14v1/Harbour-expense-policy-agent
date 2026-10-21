#!/usr/bin/env python
"""Check receipt database status."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from receipts.models import Receipt
from django.db.models import Count

# Get all receipts
receipts = Receipt.objects.all()

print(f"Total receipts in database: {receipts.count()}\n")

if receipts.count() == 0:
    print("No receipts found in database.")
else:
    # Status counts
    print("Status breakdown:")
    status_data = receipts.values('status').annotate(count=Count('id')).order_by('status')
    for item in status_data:
        print(f"  {item['status']}: {item['count']}")

    print()

    # Check NEEDS_REVIEW specifically
    needs_review = receipts.filter(status='NEEDS_REVIEW')
    print(f"Receipts with NEEDS_REVIEW status: {needs_review.count()}")

    # Show recent receipts
    print("\nMost recent receipts (last 10):")
    for receipt in receipts.order_by('-created_at')[:10]:
        print(f"  {str(receipt.id)[:8]}... | {receipt.original_filename[:30]:30s} | Status: {receipt.status:20s} | Created: {receipt.created_at}")

    # If no NEEDS_REVIEW, check what statuses exist
    if needs_review.count() == 0:
        print("\nNo receipts with NEEDS_REVIEW status found.")
        print("Receipt workflow explanation:")
        print("  - Receipts start as QUEUED_FOR_PROCESSING")
        print("  - After OCR: UNIQUE, EXACT_DUPLICATE, or SEMANTIC_DUPLICATE")
        print("  - NEEDS_REVIEW is assigned by Finance for approval/rejection")
        print("  - Final statuses: APPROVED or REJECTED")
        print()
        print("Current receipt lifecycle statuses in database:")
        all_statuses = set(receipts.values_list('status', flat=True))
        for status in sorted(all_statuses):
            count = receipts.filter(status=status).count()
            print(f"  {status}: {count}")
