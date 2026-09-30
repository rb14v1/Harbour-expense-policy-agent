export interface ReceiptListItem {
  id: string;
  status: string;
  original_filename: string;
  vendor_name: string | null;
  transaction_date: string | null;
  total_amount: number | null;
  currency: string | null;
  category: string | null;
  processing_message: string | null;
  created_at: string;
}

export interface ReceiptDetail extends ReceiptListItem {
  category_confidence: number | null;
  category_reason: string | null;
  duplicate_score: number | null;
  duplicate_reason: string | null;
  policy_status: string | null;
  policy_result_json: Record<string, unknown> | null;
  updated_at: string;
}

export interface FinanceReceiptsResponse {
  count: number;
  next: number | null;
  previous: number | null;
  results: ReceiptListItem[];
}

export interface FinanceCategoriesResponse {
  categories: string[];
}

export interface DecisionResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export interface FilterParams {
  status?: string;
  category?: string;
  vendor?: string;
  filename?: string;
  date_from?: string;
  date_to?: string;
  amount_min?: string;
  amount_max?: string;
  page?: number;
}
