import type {
  UploadResponse,
  ReceiptStatus,
  ReceiptDetail,
  CategoriesResponse,
  SetCategoryResponse
} from '../types/Receipt';
import { normalizeReceiptDetail, type RawReceiptDetail } from './normalizeResponse';

const OWNER = 'default-user';

export async function uploadReceipt(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('owner', OWNER);
  const response = await fetch('/api/v1/receipts/upload/', {
    method: 'POST',
    body: formData,
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    if (errorData.errors?.file?.[0]) {
      throw new Error(errorData.errors.file[0]);
    }
    if (errorData.error) {
      throw new Error(errorData.error);
    }
    throw new Error('Upload failed. Please try again.');
  }
  return response.json();
}

export async function getReceiptStatus(receiptId: string): Promise<ReceiptStatus> {
  const response = await fetch(
    `/api/v1/receipts/${receiptId}/?owner=${OWNER}`,
    {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    }
  );
  if (!response.ok) {
    throw new Error('Unable to retrieve receipt status');
  }
  return response.json();
}

export async function getReceiptDetail(receiptId: string): Promise<ReceiptDetail> {
  const response = await fetch(
    `/api/v1/receipts/${receiptId}/?owner=${OWNER}`,
    {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    }
  );
  if (!response.ok) {
    throw new Error('Unable to retrieve receipt details');
  }
  const raw: RawReceiptDetail = await response.json();
  return normalizeReceiptDetail(raw);
}

export async function getCategories(): Promise<string[]> {
  const response = await fetch('/api/v1/receipts/categories/', {
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  });
  if (!response.ok) {
    throw new Error('Could not load categories');
  }
  const data: CategoriesResponse = await response.json();
  return data.categories || [];
}

export async function setCategory(
  receiptId: string,
  category: string
): Promise<ReceiptDetail> {
  const response = await fetch(
    `/api/v1/receipts/${receiptId}/set_category/?owner=${OWNER}`,
    {
      method: 'POST',
      body: JSON.stringify({ category }),
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    }
  );
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    if (errorData.error) {
      throw new Error(errorData.error);
    }
    throw new Error('Failed to save category. Please try again.');
  }
  const raw: RawReceiptDetail = await response.json();
  return normalizeReceiptDetail(raw);
}

export function getPreviewUrl(receiptId: string): string {
  return `/api/v1/receipts/${receiptId}/preview/?owner=${OWNER}`;
}
