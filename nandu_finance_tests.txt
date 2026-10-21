from django.test import TestCase, Client
from django.urls import reverse
from receipts.models import Receipt
from datetime import date, timedelta
from decimal import Decimal
import json


class FinanceDashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.approved_receipt = Receipt.objects.create(
            owner='finance-department',
            original_filename='approved.pdf',
            blob_name='receipts/finance-department/uuid1/approved.pdf',
            mime_type='application/pdf',
            file_size=1000,
            sha256_hash='hash1',
            status='APPROVED',
            vendor_name='ABC Restaurant',
            transaction_date=date.today() - timedelta(days=5),
            total_amount=Decimal('100.00'),
            currency='USD',
            category='Food: Dinner - Max Claim: €/$/AUD 45 / INR700',
            category_confidence=0.95,
            category_reason='Matched restaurant keywords',
            policy_status='APPROVED',
            policy_result_json={'status': 'APPROVED', 'rules': [{'code': 'RECEIPT_AGE_OK', 'passed': True, 'message': 'Within policy'}]},
        )

        self.rejected_receipt = Receipt.objects.create(
            owner='finance-department',
            original_filename='rejected.pdf',
            blob_name='receipts/finance-department/uuid2/rejected.pdf',
            mime_type='application/pdf',
            file_size=1000,
            sha256_hash='hash2',
            status='REJECTED',
            vendor_name='Old Restaurant',
            transaction_date=date.today() - timedelta(days=40),
            total_amount=Decimal('50.00'),
            currency='USD',
            category='Food: Dinner - Max Claim: €/$/AUD 45 / INR700',
            policy_status='REJECTED',
            policy_result_json={'status': 'REJECTED', 'rules': [{'code': 'RECEIPT_TOO_OLD', 'passed': False, 'message': 'Receipt is older than 35 days'}]},
        )

        self.duplicate_receipt = Receipt.objects.create(
            owner='finance-department',
            original_filename='duplicate.pdf',
            blob_name='',
            mime_type='application/pdf',
            file_size=1000,
            sha256_hash='hash3',
            status='SEMANTIC_DUPLICATE',
            vendor_name='Hotel XYZ',
            transaction_date=date.today() - timedelta(days=3),
            total_amount=Decimal('200.00'),
            currency='USD',
            category='Accommodation/Hotel',
            semantic_duplicate_of=self.approved_receipt,
            duplicate_score=95,
            duplicate_reason='Matched invoice and vendor',
        )

    def test_finance_dashboard_loads(self):
        response = self.client.get('/finance/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Finance Department', response.content)
        self.assertIn(b'Receipt Review Dashboard', response.content)

    def test_finance_receipts_list_all(self):
        response = self.client.get('/finance/api/receipts/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 3)
        self.assertEqual(len(data['results']), 3)

    def test_finance_receipts_filter_by_status_approved(self):
        response = self.client.get('/finance/api/receipts/?status=APPROVED')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['status'], 'APPROVED')

    def test_finance_receipts_filter_by_status_rejected(self):
        response = self.client.get('/finance/api/receipts/?status=REJECTED')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['status'], 'REJECTED')

    def test_finance_receipts_filter_by_status_duplicate(self):
        response = self.client.get('/finance/api/receipts/?status=SEMANTIC_DUPLICATE')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['status'], 'SEMANTIC_DUPLICATE')

    def test_finance_receipts_filter_by_category(self):
        response = self.client.get('/finance/api/receipts/?category=Accommodation/Hotel')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['category'], 'Accommodation/Hotel')

    def test_finance_receipts_filter_by_vendor(self):
        response = self.client.get('/finance/api/receipts/?vendor=ABC')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['vendor_name'], 'ABC Restaurant')

    def test_finance_receipts_filter_by_filename(self):
        response = self.client.get('/finance/api/receipts/?filename=approved')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['original_filename'], 'approved.pdf')

    def test_finance_receipts_filter_by_date_range(self):
        date_from = (date.today() - timedelta(days=10)).isoformat()
        date_to = date.today().isoformat()
        response = self.client.get(f'/finance/api/receipts/?date_from={date_from}&date_to={date_to}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 2)

    def test_finance_receipts_filter_by_date_from(self):
        date_from = (date.today() - timedelta(days=10)).isoformat()
        response = self.client.get(f'/finance/api/receipts/?date_from={date_from}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 2)

    def test_finance_receipts_filter_by_date_to(self):
        date_to = (date.today() - timedelta(days=30)).isoformat()
        response = self.client.get(f'/finance/api/receipts/?date_to={date_to}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)

    def test_finance_receipt_detail_approved(self):
        response = self.client.get(f'/finance/api/receipts/{self.approved_receipt.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'APPROVED')
        self.assertEqual(data['vendor_name'], 'ABC Restaurant')
        self.assertEqual(data['policy_status'], 'APPROVED')
        self.assertIn('policy_result_json', data)

    def test_finance_receipt_detail_rejected(self):
        response = self.client.get(f'/finance/api/receipts/{self.rejected_receipt.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'REJECTED')
        self.assertEqual(data['policy_status'], 'REJECTED')
        self.assertIsNotNone(data['policy_result_json'])
        self.assertEqual(data['policy_result_json']['status'], 'REJECTED')

    def test_finance_receipt_detail_rejection_reason(self):
        response = self.client.get(f'/finance/api/receipts/{self.rejected_receipt.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        rules = data['policy_result_json']['rules']
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]['code'], 'RECEIPT_TOO_OLD')
        self.assertFalse(rules[0]['passed'])
        self.assertIn('older than 35 days', rules[0]['message'])

    def test_finance_receipt_detail_duplicate_info(self):
        response = self.client.get(f'/finance/api/receipts/{self.duplicate_receipt.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'SEMANTIC_DUPLICATE')
        self.assertEqual(data['duplicate_score'], 95)
        self.assertIn('invoice and vendor', data['duplicate_reason'])

    def test_finance_receipt_detail_not_found(self):
        response = self.client.get('/finance/api/receipts/00000000-0000-0000-0000-000000000000/')
        self.assertEqual(response.status_code, 404)

    def test_finance_receipt_detail_unauthorized_owner(self):
        receipt = Receipt.objects.create(
            owner='other-owner',
            original_filename='other.pdf',
            blob_name='receipts/other/uuid/other.pdf',
            mime_type='application/pdf',
            file_size=1000,
            sha256_hash='hashother',
            status='APPROVED',
        )
        response = self.client.get(f'/finance/api/receipts/{receipt.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], str(receipt.id))

    def test_finance_receipts_pagination(self):
        for i in range(5):
            Receipt.objects.create(
                owner='finance-department',
                original_filename=f'receipt{i}.pdf',
                blob_name=f'receipts/finance-department/uuid{i}/receipt{i}.pdf',
                mime_type='application/pdf',
                file_size=1000,
                sha256_hash=f'hash{i}extra',
                status='APPROVED',
                transaction_date=date.today() - timedelta(days=i),
            )

        response = self.client.get('/finance/api/receipts/?page=1')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 8)
        self.assertIsNone(data['next'])

    def test_finance_category_confidence_displayed(self):
        response = self.client.get(f'/finance/api/receipts/{self.approved_receipt.id}/')
        data = response.json()
        self.assertEqual(data['category_confidence'], 0.95)
        self.assertEqual(data['category_reason'], 'Matched restaurant keywords')

    def test_finance_receipts_list_contains_all_required_fields(self):
        response = self.client.get('/finance/api/receipts/')
        data = response.json()
        receipt = data['results'][0]
        required_fields = ['id', 'status', 'original_filename', 'vendor_name', 'transaction_date',
                          'total_amount', 'currency', 'category', 'processing_message', 'created_at']
        for field in required_fields:
            self.assertIn(field, receipt)

    def test_finance_receipts_with_multiple_filters(self):
        response = self.client.get('/finance/api/receipts/?status=APPROVED&category=Food: Dinner - Max Claim: €/$/AUD 45 / INR700&vendor=ABC')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['status'], 'APPROVED')
        self.assertEqual(data['results'][0]['vendor_name'], 'ABC Restaurant')


class FinanceAuthorizationTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.finance_receipt = Receipt.objects.create(
            owner='finance-department',
            original_filename='finance.pdf',
            blob_name='receipts/finance-department/uuid/finance.pdf',
            mime_type='application/pdf',
            file_size=1000,
            sha256_hash='hashfin',
            status='APPROVED',
        )

        self.user_receipt = Receipt.objects.create(
            owner='user123',
            original_filename='user.pdf',
            blob_name='receipts/user123/uuid/user.pdf',
            mime_type='application/pdf',
            file_size=1000,
            sha256_hash='hashuser',
            status='APPROVED',
        )

    def test_finance_dashboard_shows_all_receipts(self):
        response = self.client.get('/finance/api/receipts/')
        data = response.json()
        self.assertEqual(data['count'], 2)
        ids = [r['id'] for r in data['results']]
        self.assertIn(str(self.finance_receipt.id), ids)
        self.assertIn(str(self.user_receipt.id), ids)

    def test_finance_can_access_all_owner_receipts(self):
        response = self.client.get(f'/finance/api/receipts/{self.user_receipt.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], str(self.user_receipt.id))

    def test_finance_can_access_own_receipts(self):
        response = self.client.get(f'/finance/api/receipts/{self.finance_receipt.id}/')
        self.assertEqual(response.status_code, 200)


class FinanceAmountFilteringTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.receipt1 = Receipt.objects.create(
            owner='finance-department',
            original_filename='r1.pdf',
            blob_name='receipts/finance-department/uuid1/r1.pdf',
            mime_type='application/pdf',
            file_size=1000,
            sha256_hash='hash1amt',
            status='APPROVED',
            total_amount=Decimal('50.00'),
            currency='USD',
        )

        self.receipt2 = Receipt.objects.create(
            owner='finance-department',
            original_filename='r2.pdf',
            blob_name='receipts/finance-department/uuid2/r2.pdf',
            mime_type='application/pdf',
            file_size=1000,
            sha256_hash='hash2amt',
            status='APPROVED',
            total_amount=Decimal('100.00'),
            currency='USD',
        )

        self.receipt3 = Receipt.objects.create(
            owner='finance-department',
            original_filename='r3.pdf',
            blob_name='receipts/finance-department/uuid3/r3.pdf',
            mime_type='application/pdf',
            file_size=1000,
            sha256_hash='hash3amt',
            status='APPROVED',
            total_amount=Decimal('200.00'),
            currency='USD',
        )

    def test_filter_by_amount_min(self):
        response = self.client.get('/finance/api/receipts/?amount_min=100')
        data = response.json()
        self.assertEqual(data['count'], 2)

    def test_filter_by_amount_max(self):
        response = self.client.get('/finance/api/receipts/?amount_max=100')
        data = response.json()
        self.assertEqual(data['count'], 2)

    def test_filter_by_amount_range(self):
        response = self.client.get('/finance/api/receipts/?amount_min=60&amount_max=150')
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(Decimal(data['results'][0]['total_amount']), Decimal('100.00'))


class FinancePendingReceiptListTests(TestCase):
    """Tests for Part 1: Finance-pending receipt list filtering."""

    def setUp(self):
        self.client = Client()

        self.needs_review_receipt1 = Receipt.objects.create(
            owner='user1',
            original_filename='needs_review1.pdf',
            blob_name='receipts/user1/uuid1/needs_review1.pdf',
            mime_type='application/pdf',
            file_size=1000,
            sha256_hash='hash1',
            status='NEEDS_REVIEW',
            vendor_name='Restaurant 1',
            transaction_date=date.today() - timedelta(days=5),
            total_amount=Decimal('100.00'),
            currency='USD',
            category='Food: Dinner - Max Claim: €/$/AUD 45 / INR700',
            policy_status='APPROVED',
            policy_result_json={'status': 'APPROVED', 'rules': [{'code': 'RECEIPT_AGE_OK', 'passed': True}]},
            processing_message='Receipt approved by policy. Awaiting Finance review.',
        )

        self.needs_review_receipt2 = Receipt.objects.create(
            owner='user2',
            original_filename='needs_review2.pdf',
            blob_name='receipts/user2/uuid2/needs_review2.pdf',
            mime_type='application/pdf',
            file_size=1000,
            sha256_hash='hash2',
            status='NEEDS_REVIEW',
            vendor_name='Hotel XYZ',
            transaction_date=date.today() - timedelta(days=3),
            total_amount=Decimal('200.00'),
            currency='USD',
            category='Accommodation/Hotel',
            policy_status='APPROVED',
            policy_result_json={'status': 'APPROVED', 'rules': [{'code': 'RECEIPT_AGE_OK', 'passed': True}]},
            processing_message='Receipt approved by policy. Awaiting Finance review.',
        )

        self.approved_receipt = Receipt.objects.create(
            owner='user3',
            original_filename='approved.pdf',
            blob_name='receipts/user3/uuid3/approved.pdf',
            mime_type='application/pdf',
            file_size=1000,
            sha256_hash='hash3',
            status='APPROVED',
            vendor_name='Restaurant 2',
            transaction_date=date.today() - timedelta(days=10),
            total_amount=Decimal('50.00'),
            currency='USD',
            category='Food: Dinner - Max Claim: €/$/AUD 45 / INR700',
        )

        self.rejected_receipt = Receipt.objects.create(
            owner='user4',
            original_filename='rejected.pdf',
            blob_name='receipts/user4/uuid4/rejected.pdf',
            mime_type='application/pdf',
            file_size=1000,
            sha256_hash='hash4',
            status='REJECTED',
            vendor_name='Restaurant 3',
            transaction_date=date.today() - timedelta(days=40),
            total_amount=Decimal('150.00'),
            currency='USD',
            category='Food: Dinner - Max Claim: €/$/AUD 45 / INR700',
        )

    def test_finance_pending_list_filters_needs_review(self):
        """Test that filtering by NEEDS_REVIEW returns only pending Finance receipts."""
        response = self.client.get('/finance/api/receipts/?status=NEEDS_REVIEW')
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Should return only NEEDS_REVIEW receipts
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['results']), 2)

        for receipt in data['results']:
            self.assertEqual(receipt['status'], 'NEEDS_REVIEW')

    def test_finance_pending_excludes_approved(self):
        """Test that APPROVED receipts are not included in NEEDS_REVIEW filter."""
        response = self.client.get('/finance/api/receipts/?status=NEEDS_REVIEW')
        data = response.json()

        statuses = [r['status'] for r in data['results']]
        self.assertNotIn('APPROVED', statuses)

    def test_finance_pending_excludes_rejected(self):
        """Test that REJECTED receipts are not included in NEEDS_REVIEW filter."""
        response = self.client.get('/finance/api/receipts/?status=NEEDS_REVIEW')
        data = response.json()

        statuses = [r['status'] for r in data['results']]
        self.assertNotIn('REJECTED', statuses)

    def test_finance_pending_list_has_required_fields(self):
        """Test that NEEDS_REVIEW receipts have all required fields for display."""
        response = self.client.get('/finance/api/receipts/?status=NEEDS_REVIEW')
        data = response.json()

        # Receipts should have required fields for Finance review
        required_fields = ['id', 'status', 'original_filename', 'vendor_name', 'transaction_date', 'total_amount', 'currency']
        for receipt in data['results']:
            for field in required_fields:
                self.assertIn(field, receipt, f"Receipt missing field: {field}")

    def test_finance_all_receipts_includes_pending(self):
        """Test that unfiltered list includes NEEDS_REVIEW receipts."""
        response = self.client.get('/finance/api/receipts/')
        data = response.json()

        # Should return all 4 receipts
        self.assertEqual(data['count'], 4)

        statuses = [r['status'] for r in data['results']]
        self.assertIn('NEEDS_REVIEW', statuses)
