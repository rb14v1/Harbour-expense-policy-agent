import type {
  ReceiptDetail,
  FinanceReceiptsResponse,
  FinanceCategoriesResponse,
  DecisionResponse,
  FilterParams
} from '../types/Finance';
import { normalizeReceiptDetail, normalizeReceiptList, type RawReceiptDetail, type RawReceiptListItem } from './normalizeResponse';

export async function getFinanceReceipts(params: FilterParams): Promise<FinanceReceiptsResponse> {
  const queryParams = new URLSearchParams();

  if (params.status) queryParams.append('status', params.status);
  if (params.category) queryParams.append('category', params.category);
  if (params.vendor) queryParams.append('vendor', params.vendor);
  if (params.filename) queryParams.append('filename', params.filename);
  if (params.date_from) queryParams.append('date_from', params.date_from);
  if (params.date_to) queryParams.append('date_to', params.date_to);
  if (params.amount_min) queryParams.append('amount_min', params.amount_min);
  if (params.amount_max) queryParams.append('amount_max', params.amount_max);
  if (params.page) queryParams.append('page', params.page.toString());

  const response = await fetch(`/finance/api/receipts/?${queryParams.toString()}`, {
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  });

  if (!response.ok) {
    throw new Error('Failed to load receipts');
  }

  const raw = await response.json();
  return normalizeReceiptList(raw);
}

export async function getFinanceReceiptDetail(receiptId: string): Promise<ReceiptDetail> {
  const response = await fetch(`/finance/api/receipts/${receiptId}/`, {
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  });

  if (!response.ok) {
    throw new Error('Failed to load receipt details');
  }

  const raw: RawReceiptDetail = await response.json();
  return normalizeReceiptDetail(raw);
}

export async function getFinanceCategories(): Promise<string[]> {
  const response = await fetch('/api/v1/receipts/categories/', {
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  });

  if (!response.ok) {
    throw new Error('Failed to load categories');
  }

  const data: FinanceCategoriesResponse = await response.json();
  return data.categories || [];
}

export async function submitFinanceDecision(
  receiptId: string,
  decision: 'APPROVED' | 'REJECTED',
  notes?: string
): Promise<ReceiptDetail> {
  const response = await fetch(`/finance/api/receipts/${receiptId}/decision/`, {
    method: 'POST',
    body: JSON.stringify({
      decision,
      notes: notes || ''
    }),
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    }
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    if (errorData.error) {
      throw new Error(errorData.error);
    }
    throw new Error('Failed to submit decision');
  }

  const raw: RawReceiptDetail = await response.json();
  return normalizeReceiptDetail(raw);
}

export function getReceiptPreviewUrl(receiptId: string): string {
  return `/api/v1/receipts/${receiptId}/preview/?owner=default-user`;
}
