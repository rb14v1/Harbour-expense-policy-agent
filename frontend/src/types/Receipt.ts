export interface UploadResponse {
  receipt_id: string;
  status: string;
  message: string;
  is_final: boolean;
}

export interface ReceiptStatus {
  id: string;
  status: string;
  stage: string;
  is_final: boolean;
  message: string;
  category: string | null;
  duplicate_score: number | null;
  duplicate_reason: string | null;
  processing_message: string | null;
  policy_status: string | null;
}

export interface ReceiptDetail {
  id: string;
  status: string;
  original_filename: string;
  vendor_name: string | null;
  transaction_date: string | null;
  total_amount: number | null;
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

export interface CategoriesResponse {
  categories: string[];
}

export interface SetCategoryResponse {
  id: string;
  status: string;
  category: string;
  category_confidence: number | null;
}
