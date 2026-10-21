/**
 * Normalize API responses to handle Django DecimalField serialization.
 * Django's DecimalField serializes to strings (e.g., "105.00"), but React
 * expects JavaScript numbers. This normalizes the boundary.
 */

export function normalizeNumericString(value: unknown): number | null {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  const num = typeof value === 'string' ? parseFloat(value) : Number(value);

  return isNaN(num) ? null : num;
}

export interface RawReceiptDetail {
  id: string;
  status: string;
  original_filename: string;
  vendor_name: string | null;
  transaction_date: string | null;
  total_amount: string | number | null;
  subtotal?: string | number | null;
  tax_amount?: string | number | null;
  currency: string | null;
  category: string | null;
  category_confidence: number | null;
  category_reason: string | null;
  duplicate_score: number | null;
  duplicate_reason: string | null;
  processing_message: string | null;
  policy_status: string | null;
  policy_result_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface NormalizedReceiptDetail extends RawReceiptDetail {
  total_amount: number | null;
  subtotal: number | null;
  tax_amount: number | null;
}

export function normalizeReceiptDetail(raw: RawReceiptDetail): NormalizedReceiptDetail {
  return {
    ...raw,
    total_amount: normalizeNumericString(raw.total_amount),
    subtotal: normalizeNumericString((raw as any).subtotal),
    tax_amount: normalizeNumericString((raw as any).tax_amount),
  };
}

export interface RawReceiptListItem {
  id: string;
  status: string;
  original_filename: string;
  vendor_name: string | null;
  transaction_date: string | null;
  total_amount: string | number | null;
  currency: string | null;
  category: string | null;
  processing_message: string | null;
  created_at: string;
}

export interface NormalizedReceiptListItem extends RawReceiptListItem {
  total_amount: number | null;
}

export function normalizeReceiptListItem(raw: RawReceiptListItem): NormalizedReceiptListItem {
  return {
    ...raw,
    total_amount: normalizeNumericString(raw.total_amount),
  };
}

export function normalizeReceiptList(raw: { count: number; next: number | null; previous: number | null; results: RawReceiptListItem[] }) {
  return {
    ...raw,
    results: raw.results.map(normalizeReceiptListItem),
  };
}
