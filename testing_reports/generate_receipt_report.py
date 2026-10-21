#!/usr/bin/env python
"""
Expense Policy Agent - Receipt Testing Report Generator

This utility reads existing receipt data from the Django database and generates
human-readable testing/presentation reports in Markdown and PDF formats.

IMPORTANT: This is a READ-ONLY utility. It does not modify the database.
"""

import os
import sys
import json
import django
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings
from receipts.models import Receipt


class ReceiptReportGenerator:
    """Generate comprehensive receipt testing reports."""

    def __init__(self, output_dir="output"):
        self.output_dir = Path(__file__).parent / output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.receipt_count = 0
        self.approved_count = 0
        self.rejected_count = 0
        self.pending_count = 0
        self.duplicate_count = 0

    def generate_all_reports(self):
        """Generate all report formats."""
        print(f"Generating reports from {Receipt.objects.count()} receipts...")

        # Generate markdown report
        markdown_path = self._generate_markdown_report()
        print(f"[OK] Markdown report: {markdown_path}")

        # Generate PDF report
        try:
            pdf_path = self._generate_pdf_report()
            print(f"[OK] PDF report: {pdf_path}")
        except ImportError:
            print("[WARN] PDF generation skipped (reportlab not installed)")
            print("       Install with: pip install reportlab")
            pdf_path = None

        return {
            'markdown': markdown_path,
            'pdf': pdf_path,
            'output_dir': self.output_dir
        }

    def _generate_markdown_report(self):
        """Generate markdown format report."""
        receipts = Receipt.objects.all().order_by('-created_at')
        self.receipt_count = receipts.count()

        lines = []
        lines.append("=" * 60)
        lines.append("EXPENSE POLICY AGENT - RECEIPT TEST REPORT")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Executive Summary
        lines.extend(self._get_executive_summary(receipts))

        # Detailed Receipt Information
        lines.extend(self._get_receipt_details(receipts))

        # Scoring Explanation
        lines.extend(self._get_scoring_explanation())

        # Workflow Summary
        lines.extend(self._get_workflow_summary())

        # Test Observations
        lines.extend(self._get_test_observations(receipts))

        # Technical Implementation Map
        lines.extend(self._get_technical_map())

        report_content = "\n".join(lines)

        # Write to file
        report_path = self.output_dir / "receipt_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return report_path

    def _get_executive_summary(self, receipts):
        """Generate executive summary section."""
        lines = ["## 1. EXECUTIVE SUMMARY", ""]

        # Count statuses
        approved = receipts.filter(status='APPROVED').count()
        rejected = receipts.filter(status='REJECTED').count()
        pending = receipts.filter(status='NEEDS_REVIEW').count()
        duplicates = receipts.filter(status__in=['EXACT_DUPLICATE', 'SEMANTIC_DUPLICATE']).count()
        policy_approved = receipts.filter(policy_status='APPROVED').count()
        policy_rejected = receipts.filter(policy_status='REJECTED').count()
        failed = receipts.filter(status='FAILED').count()

        self.approved_count = approved
        self.rejected_count = rejected
        self.pending_count = pending
        self.duplicate_count = duplicates

        lines.append(f"- **Total receipts:** {self.receipt_count}")
        lines.append(f"- **Approved by Finance:** {approved}")
        lines.append(f"- **Rejected by Finance:** {rejected}")
        lines.append(f"- **Pending Finance review:** {pending}")
        lines.append(f"- **Approved by Policy:** {policy_approved}")
        lines.append(f"- **Rejected by Policy:** {policy_rejected}")
        lines.append(f"- **Duplicate receipts:** {duplicates}")
        lines.append(f"- **Processing failures:** {failed}")
        lines.append("")

        return lines

    def _get_receipt_details(self, receipts):
        """Generate detailed receipt section."""
        lines = ["## 2. RECEIPT-BY-RECEIPT DETAILS", ""]

        if receipts.count() == 0:
            lines.append("No receipts found in database.")
            lines.append("")
            return lines

        for idx, receipt in enumerate(receipts, 1):
            lines.append("-" * 60)
            lines.append(f"Receipt #{idx}")
            lines.append("-" * 60)
            lines.append("")

            # Basic info
            lines.append("**Receipt ID:** " + str(receipt.id))
            lines.append("**Filename:** " + (receipt.original_filename or "N/A"))
            lines.append("**Owner:** " + (receipt.owner or "N/A"))
            lines.append("**Upload Date:** " + (receipt.created_at.strftime('%Y-%m-%d %H:%M:%S') if receipt.created_at else "N/A"))
            lines.append("**SHA-256 Hash:** " + (receipt.sha256_hash if receipt.sha256_hash else "N/A"))
            lines.append("")

            # Processing
            lines.append("### PROCESSING")
            lines.append("**Status:** " + receipt.status)
            lines.append("**Processing Message:** " + (receipt.processing_message or "N/A"))
            lines.append("")

            # Extracted Information
            lines.append("### EXTRACTED INFORMATION")
            lines.append("**Vendor:** " + (receipt.vendor_name or "N/A"))
            lines.append("**Transaction Date:** " + (receipt.transaction_date.strftime('%Y-%m-%d') if receipt.transaction_date else "N/A"))
            lines.append("**Amount:** " + (f"{receipt.total_amount} {receipt.currency or 'N/A'}" if receipt.total_amount else "N/A"))
            lines.append("**Currency:** " + (receipt.currency or "N/A"))
            lines.append("**Payment Method:** " + (receipt.payment_method or "N/A"))
            lines.append("**Invoice Number:** " + (receipt.invoice_number or "N/A"))
            lines.append("")

            # Classification
            lines.append("### CLASSIFICATION")
            lines.append("**Category:** " + (receipt.category or "N/A"))
            confidence_str = f"{receipt.category_confidence:.1%}" if receipt.category_confidence is not None else "N/A"
            lines.append("**Category Confidence:** " + confidence_str)
            lines.append("**Category Reason:** " + (receipt.category_reason or "N/A"))
            lines.append("")

            # Policy Validation
            lines.append("### POLICY VALIDATION")
            lines.append("**Policy Status:** " + (receipt.policy_status or "N/A"))
            if receipt.policy_result_json:
                policy_result = receipt.policy_result_json
                if isinstance(policy_result, str):
                    policy_result = json.loads(policy_result)
                lines.append("**Policy Result:** " + json.dumps(policy_result, indent=2))
            else:
                lines.append("**Policy Result:** N/A")
            lines.append("")

            # Duplicate Check
            lines.append("### DUPLICATE CHECK")
            duplicate_status = "Not a duplicate"
            if receipt.status == 'EXACT_DUPLICATE':
                duplicate_status = "Exact duplicate"
            elif receipt.status == 'SEMANTIC_DUPLICATE':
                duplicate_status = "Semantic duplicate"
            lines.append("**Duplicate Status:** " + duplicate_status)

            if receipt.exact_duplicate_of:
                lines.append(f"**Exact Duplicate Of:** {receipt.exact_duplicate_of.id}")
            if receipt.semantic_duplicate_of:
                lines.append(f"**Semantic Duplicate Of:** {receipt.semantic_duplicate_of.id}")
            if receipt.duplicate_score:
                lines.append(f"**Duplicate Score:** {receipt.duplicate_score}")
            lines.append("**Duplicate Reason:** " + (receipt.duplicate_reason or "N/A"))
            lines.append("")

            # Finance Review
            lines.append("### FINANCE REVIEW")
            finance_status = "Not reviewed"
            if receipt.status == 'APPROVED':
                finance_status = "Approved"
            elif receipt.status == 'REJECTED' and receipt.policy_status == 'APPROVED':
                finance_status = "Rejected"
            elif receipt.status == 'NEEDS_REVIEW':
                finance_status = "Pending"
            lines.append("**Finance Status:** " + finance_status)
            lines.append("**Finance Updated:** " + (receipt.updated_at.strftime('%Y-%m-%d %H:%M:%S') if receipt.updated_at else "N/A"))
            lines.append("")

            # Final Result
            lines.append("### FINAL RESULT")
            lines.append("**Final Receipt Status:** " + receipt.status)
            lines.append("**Final Explanation:** " + (receipt.processing_message or "Processing in progress"))
            lines.append("")

        return lines

    def _get_scoring_explanation(self):
        """Generate scoring explanation section."""
        lines = ["## 3. POLICY/SCORING EXPLANATION", ""]

        lines.append("### Category Confidence Scoring")
        lines.append("**Implementation:** `receipts/services/receipt_service.py`")
        lines.append("**Function:** `ReceiptService.determine_category()`")
        lines.append("**Purpose:** Classify receipt expense category with confidence score")
        lines.append("")
        lines.append("**Scoring Method:**")
        lines.append("- Keyword matching in merchant name (highest priority, +0.15 confidence boost)")
        lines.append("- Keyword matching in line items and payment method")
        lines.append("- Base confidence per category (0.80-0.95)")
        lines.append("")
        lines.append("**Confidence Threshold:** 0.75")
        lines.append("- Confidence ≥ 0.75: Automatic category assignment")
        lines.append("- Confidence < 0.75: Requires user confirmation")
        lines.append("")

        lines.append("### Duplicate Detection Scoring")
        lines.append("**Implementation:** `receipts/services/duplicate_service.py`")
        lines.append("**Class:** `DuplicateService`")
        lines.append("**Function:** `evaluate_semantic_duplicate()` and `_calculate_duplicate_score()`")
        lines.append("**Purpose:** Detect business duplicates using normalized receipt data")
        lines.append("")
        lines.append("**Scoring Model (100-point scale):**")
        lines.append("| Factor | Points |")
        lines.append("|--------|--------|")
        lines.append("| Invoice number exact match | 40 |")
        lines.append("| Vendor normalized match | 20 |")
        lines.append("| Transaction date match | 15 |")
        lines.append("| Total amount match | 15 |")
        lines.append("| Tax amount match | 5 |")
        lines.append("| Currency match | 5 |")
        lines.append("")
        lines.append("**Thresholds (from settings):**")
        dup_threshold = getattr(settings, 'DUPLICATE_SCORE_THRESHOLD', 90)
        review_threshold = getattr(settings, 'REVIEW_SCORE_THRESHOLD', 75)
        lines.append(f"- DUPLICATE_SCORE_THRESHOLD: {dup_threshold} (receipt marked as duplicate)")
        lines.append(f"- REVIEW_SCORE_THRESHOLD: {review_threshold} (flagged for review)")
        lines.append(f"- Below {review_threshold}: Receipt treated as unique")
        lines.append("")

        lines.append("### Policy Validation Scoring")
        lines.append("**Implementation:** `receipts/services/policy_service.py`")
        lines.append("**Class:** `PolicyService`")
        lines.append("**Function:** `evaluate()`")
        lines.append("**Purpose:** Validate receipt against business policy rules")
        lines.append("")
        lines.append("**Current Rules:**")
        max_age = getattr(settings, 'RECEIPT_MAX_AGE_DAYS', 35)
        lines.append(f"- **Receipt Age:** Maximum {max_age} days old")
        lines.append("  - Implementation: `_check_receipt_age()`")
        lines.append(f"  - If receipt is > {max_age} days old, policy status = REJECTED")
        lines.append("")

        return lines

    def _get_workflow_summary(self):
        """Generate workflow summary."""
        lines = ["## 4. WORKFLOW SUMMARY", ""]

        lines.append("### Processing Flow")
        lines.append("")
        lines.append("```")
        lines.append("Upload (POST /api/v1/receipts/)")
        lines.append("  ↓")
        lines.append("File Validation (file_validation_service.py)")
        lines.append("  - Check MIME type")
        lines.append("  - Check file size (max 50 MB)")
        lines.append("  - Validate PDF/JPG/PNG headers")
        lines.append("  ↓")
        lines.append("SHA-256 Hashing (hashing_service.py)")
        lines.append("  - Generate hash from file bytes")
        lines.append("  - Store in Receipt.sha256_hash")
        lines.append("  ↓")
        lines.append("Exact Duplicate Check (duplicate_service.py)")
        lines.append("  - Query Receipt.objects.filter(sha256_hash=hash)")
        lines.append("  - If found → status = EXACT_DUPLICATE")
        lines.append("  ↓")
        lines.append("Blob Storage (blob_service.py)")
        lines.append("  - Upload original file to Azure Blob Storage")
        lines.append("  - Store reference in Receipt.blob_name")
        lines.append("  ↓")
        lines.append("Queue for OCR (tasks.py)")
        lines.append("  - Enqueue process_receipt_task via Celery")
        lines.append("  ↓")
        lines.append("OCR & Extraction (document_intelligence_service.py)")
        lines.append("  - Send to Azure AI Document Intelligence")
        lines.append("  - Extract merchant, amounts, dates, invoice numbers")
        lines.append("  - Store raw result in raw_document_intelligence_json")
        lines.append("  ↓")
        lines.append("Normalization (normalization_service.py)")
        lines.append("  - Convert to internal JSON contract")
        lines.append("  - Normalize vendor names, invoice numbers, dates")
        lines.append("  - Store in normalized_json")
        lines.append("  ↓")
        lines.append("Category Classification (receipt_service.py)")
        lines.append("  - Determine category from merchant/items")
        lines.append("  - Calculate confidence (0.0-1.0)")
        lines.append("  - Store in category, category_confidence, category_reason")
        lines.append("  ↓")
        lines.append("Semantic Duplicate Check (duplicate_service.py)")
        lines.append("  - Compare normalized data against existing receipts")
        lines.append("  - Calculate similarity score (0-100)")
        lines.append("  - If score ≥ DUPLICATE_SCORE_THRESHOLD → SEMANTIC_DUPLICATE")
        lines.append("  ↓")
        lines.append("Policy Validation (policy_service.py)")
        lines.append("  - Check receipt age ≤ RECEIPT_MAX_AGE_DAYS")
        lines.append("  - Set policy_status and policy_result_json")
        lines.append("  - If policy passes → status = NEEDS_REVIEW")
        lines.append("  - If policy fails → status = REJECTED")
        lines.append("  ↓")
        lines.append("Finance Review (finance/views.py)")
        lines.append("  - Finance department reviews NEEDS_REVIEW receipts")
        lines.append("  - Finance decision: APPROVED or REJECTED")
        lines.append("  - Update status, updated_at, processing_message")
        lines.append("```")
        lines.append("")

        return lines

    def _get_test_observations(self, receipts):
        """Generate observations from actual data."""
        lines = ["## 5. TEST OBSERVATIONS", ""]

        # Processing status breakdown
        status_counts = {}
        for receipt in receipts:
            status = receipt.status
            status_counts[status] = status_counts.get(status, 0) + 1

        lines.append("### Processing Status Distribution")
        for status, count in sorted(status_counts.items()):
            lines.append(f"- {status}: {count} receipt(s)")
        lines.append("")

        # Low confidence categories
        low_conf = receipts.filter(category_confidence__lt=0.75).exclude(category_confidence__isnull=True)
        lines.append(f"### Category Confidence")
        lines.append(f"- Receipts with confidence < 0.75 (needs user confirmation): {low_conf.count()}")
        if low_conf.exists():
            lines.append("  - These would prompt user for category selection")
        lines.append("")

        # Duplicate observations
        exact_dups = receipts.filter(status='EXACT_DUPLICATE')
        semantic_dups = receipts.filter(status='SEMANTIC_DUPLICATE')
        lines.append(f"### Duplicate Detection")
        lines.append(f"- Exact duplicates (same file bytes): {exact_dups.count()}")
        lines.append(f"- Semantic duplicates (different files, same expense): {semantic_dups.count()}")
        if semantic_dups.exists():
            from django.db.models import Min, Max
            dup_scores = semantic_dups.filter(duplicate_score__isnull=False)
            if dup_scores.exists():
                agg = dup_scores.aggregate(min=Min('duplicate_score'), max=Max('duplicate_score'))
                lines.append(f"  - Score range: {agg['min']}-{agg['max']}")
        lines.append("")

        # Policy observations
        policy_approved = receipts.filter(policy_status='APPROVED')
        policy_rejected = receipts.filter(policy_status='REJECTED')
        lines.append(f"### Policy Validation")
        lines.append(f"- Approved by policy: {policy_approved.count()}")
        lines.append(f"- Rejected by policy: {policy_rejected.count()}")

        age_violations = receipts.filter(
            policy_result_json__icontains='RECEIPT_TOO_OLD'
        )
        lines.append(f"- Receipts rejected for being too old: {age_violations.count()}")
        lines.append("")

        # Finance review status
        lines.append(f"### Finance Review Status")
        lines.append(f"- Approved by Finance: {receipts.filter(status='APPROVED').count()}")
        lines.append(f"- Rejected by Finance: {receipts.filter(status='REJECTED', policy_status='APPROVED').count()}")
        lines.append(f"- Pending Finance review: {receipts.filter(status='NEEDS_REVIEW').count()}")
        lines.append("")

        # Processing failures
        failed = receipts.filter(status='FAILED')
        lines.append(f"### Processing Failures")
        lines.append(f"- Failed to process: {failed.count()}")
        if failed.exists():
            lines.append("  - Reasons:")
            for receipt in failed[:5]:
                msg = receipt.duplicate_reason or receipt.processing_message or "Unknown error"
                lines.append(f"    - {msg[:60]}...")
        lines.append("")

        return lines

    def _get_technical_map(self):
        """Generate technical implementation map."""
        lines = ["## 6. TECHNICAL IMPLEMENTATION MAP", ""]

        lines.append("| Feature | File | Function/Class | Purpose |")
        lines.append("|---------|------|----------------|---------|")
        lines.append("| File Validation | `receipts/services/file_validation_service.py` | `FileValidationService.validate()` | Validate file type, size, format |")
        lines.append("| SHA-256 Hashing | `receipts/services/hashing_service.py` | `HashingService.sha256()` | Generate hash for exact duplicate detection |")
        lines.append("| Blob Upload | `receipts/services/blob_service.py` | `BlobService.upload()` | Store original file in Azure Blob Storage |")
        lines.append("| Exact Duplicate Check | `receipts/services/duplicate_service.py` | `DuplicateService.find_exact_duplicate()` | Query by SHA-256 hash |")
        lines.append("| OCR & Extraction | `receipts/services/document_intelligence_service.py` | `DocumentIntelligenceService.analyze_receipt()` | Call Azure AI Document Intelligence |")
        lines.append("| Normalization | `receipts/services/normalization_service.py` | `ReceiptNormalizationService.normalize()` | Convert to internal JSON contract |")
        lines.append("| Category Classification | `receipts/services/receipt_service.py` | `ReceiptService.determine_category()` | Keyword-based category detection with confidence |")
        lines.append("| Semantic Duplicate Check | `receipts/services/duplicate_service.py` | `DuplicateService.evaluate_semantic_duplicate()` | Score-based duplicate detection |")
        lines.append("| Policy Validation | `receipts/services/policy_service.py` | `PolicyService.evaluate()` | Validate against business rules |")
        lines.append("| Receipt Age Check | `receipts/services/policy_service.py` | `PolicyService._check_receipt_age()` | Verify receipt ≤ 35 days old |")
        lines.append("| Finance Decision | `finance/views.py` | `finance_receipt_decision()` | Accept Finance approval/rejection |")
        lines.append("| Receipt Filtering | `receipts/views.py` | `ReceiptViewSet` | Filter by status, category, vendor, date, amount |")
        lines.append("")

        return lines

    def _generate_pdf_report(self):
        """Generate PDF report using reportlab."""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
        except ImportError:
            raise ImportError("reportlab not installed")

        pdf_path = self.output_dir / "receipt_report.pdf"
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            spaceBefore=12,
        )

        # Title
        story.append(Paragraph("EXPENSE POLICY AGENT", title_style))
        story.append(Paragraph("Receipt Test Report", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))

        # Executive Summary
        receipts = Receipt.objects.all()
        story.append(Paragraph("Executive Summary", heading_style))
        summary_data = [
            ["Total receipts", str(receipts.count())],
            ["Approved", str(receipts.filter(status='APPROVED').count())],
            ["Rejected", str(receipts.filter(status='REJECTED').count())],
            ["Pending Finance review", str(receipts.filter(status='NEEDS_REVIEW').count())],
            ["Duplicates", str(receipts.filter(status__in=['EXACT_DUPLICATE', 'SEMANTIC_DUPLICATE']).count())],
            ["Failed", str(receipts.filter(status='FAILED').count())],
        ]

        summary_table = Table(summary_data, colWidths=[3*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))

        # Receipt details (first 10 for PDF brevity)
        story.append(Paragraph("Receipt Details (First 10)", heading_style))
        for idx, receipt in enumerate(receipts[:10], 1):
            story.append(Paragraph(f"Receipt #{idx}: {receipt.original_filename}", styles['Heading3']))

            details_data = [
                ["ID", str(receipt.id)[:36]],
                ["Status", receipt.status],
                ["Vendor", receipt.vendor_name or "N/A"],
                ["Amount", f"{receipt.total_amount} {receipt.currency}" if receipt.total_amount else "N/A"],
                ["Category", receipt.category or "N/A"],
                ["Confidence", f"{receipt.category_confidence:.1%}" if receipt.category_confidence else "N/A"],
                ["Policy", receipt.policy_status or "N/A"],
            ]

            detail_table = Table(details_data, colWidths=[1.5*inch, 4*inch])
            detail_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8e8e8')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ]))
            story.append(detail_table)
            story.append(Spacer(1, 0.15*inch))

        story.append(PageBreak())

        # Scoring Explanation
        story.append(Paragraph("Scoring & Thresholds", heading_style))

        scoring_text = f"""
        <b>Duplicate Detection Score (0-100 points):</b><br/>
        Invoice number match: 40 points | Vendor match: 20 points | Date match: 15 points<br/>
        Total match: 15 points | Tax match: 5 points | Currency match: 5 points<br/>
        Threshold: {getattr(settings, 'DUPLICATE_SCORE_THRESHOLD', 90)}+ = Duplicate<br/>
        <br/>
        <b>Category Confidence (0.0-1.0):</b><br/>
        ≥ 0.75: Automatic assignment | &lt; 0.75: Requires user confirmation<br/>
        <br/>
        <b>Policy Rules:</b><br/>
        Receipt age ≤ {getattr(settings, 'RECEIPT_MAX_AGE_DAYS', 35)} days
        """
        story.append(Paragraph(scoring_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        # Build PDF
        doc.build(story)
        return pdf_path


def main():
    """Main entry point."""
    try:
        generator = ReceiptReportGenerator()
        results = generator.generate_all_reports()

        print("\n" + "=" * 60)
        print("REPORT GENERATION COMPLETE")
        print("=" * 60)
        print(f"Markdown: {results['markdown']}")
        if results['pdf']:
            print(f"PDF:      {results['pdf']}")
        print(f"\nTotal receipts analyzed: {generator.receipt_count}")
        print(f"Output directory: {results['output_dir']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
