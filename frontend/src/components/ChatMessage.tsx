import { escapeHtml, formatDate, formatFileSize, getFileTypeLabel } from '../utils/formatting';
import { getPreviewUrl } from '../api/receiptAPI';
import type { UploadMessage } from '../hooks/useReceiptUpload';

interface ChatMessageProps {
  message: UploadMessage;
  onCategorySelect?: (receiptId: string, category: string, fileName: string) => void;
  isSelectingCategory?: boolean;
}

export default function ChatMessage({
  message,
  onCategorySelect,
  isSelectingCategory
}: ChatMessageProps) {
  const handleCategorySubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const category = formData.get('category') as string;

    if (message.receiptId && message.fileName && onCategorySelect) {
      onCategorySelect(message.receiptId, category, message.fileName);
    }
  };

  const getStatusClass = (status: string): string => {
    if (['APPROVED'].includes(status)) return 'approved';
    if (['REJECTED', 'FAILED'].includes(status)) return 'rejected';
    if (['EXACT_DUPLICATE', 'SEMANTIC_DUPLICATE'].includes(status)) return 'duplicate';
    if (['NEEDS_REVIEW'].includes(status)) return 'processing';
    return 'processing';
  };

  const getStatusText = (status: string): string => {
    switch (status) {
      case 'APPROVED':
        return '✅ APPROVED';
      case 'REJECTED':
        return '❌ REJECTED';
      case 'NEEDS_REVIEW':
        return '⏳ PENDING FINANCE REVIEW';
      case 'EXACT_DUPLICATE':
        return '⚠️ EXACT DUPLICATE';
      case 'SEMANTIC_DUPLICATE':
        return '⚠️ POSSIBLE DUPLICATE';
      case 'FAILED':
        return '❌ FAILED';
      default:
        return status;
    }
  };

  if (message.type === 'text' || message.type === 'attachment') {
    return (
      <div className={`message ${message.role}`}>
        <div className="message-bubble">
          {message.type === 'attachment' && (
            <div className="attachment-card">
              <div className="attachment-info">
                <div className="attachment-name">{message.content}</div>
              </div>
            </div>
          )}
          {message.type === 'text' && message.content}
        </div>
      </div>
    );
  }

  if (message.type === 'loading') {
    return (
      <div className="message assistant">
        <div className="message-bubble">
          <div className="loading">
            <span>Processing {escapeHtml(message.fileName || '')}...</span>
            <div className="spinner"></div>
          </div>
        </div>
      </div>
    );
  }

  if (message.type === 'result' && message.receipt) {
    const receipt = message.receipt;
    const statusClass = getStatusClass(receipt.status);
    const statusText = getStatusText(receipt.status);

    return (
      <div className="message assistant">
        <div className="message-bubble">
          <div className={`result-card ${statusClass}`}>
            {receipt.total_amount && (
              <div style={{ marginBottom: '1.5rem', paddingBottom: '1.5rem', borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
                <div className="amount-label">Total Expense</div>
                <div className="amount-highlight">{receipt.currency || 'N/A'} {receipt.total_amount.toFixed(2)}</div>
              </div>
            )}

            <div className="result-row">
              <div className="result-label">Status</div>
              <div className="result-value">
                <span className={`status-badge ${statusClass}`}>{statusText}</span>
              </div>
            </div>

            <div className="result-row">
              <div className="result-label">Filename</div>
              <div className="result-value">
                <strong>{escapeHtml(message.fileName || receipt.original_filename)}</strong>
              </div>
            </div>

            {receipt.vendor_name && (
              <div className="result-row">
                <div className="result-label">Vendor</div>
                <div className="result-value">{escapeHtml(receipt.vendor_name)}</div>
              </div>
            )}

            {receipt.transaction_date && (
              <div className="result-row">
                <div className="result-label">Date</div>
                <div className="result-value">{formatDate(receipt.transaction_date)}</div>
              </div>
            )}

            {receipt.category && (
              <>
                <div className="result-row">
                  <div className="result-label">Category</div>
                  <div className="result-value">{escapeHtml(receipt.category)}</div>
                </div>

                {receipt.category_confidence !== null && receipt.category_confidence !== undefined && (
                  <div className="result-row">
                    <div className="result-label">Confidence</div>
                    <div className="result-value">{(receipt.category_confidence * 100).toFixed(0)}%</div>
                  </div>
                )}

                {receipt.category_reason && !['REJECTED', 'APPROVED', 'FAILED', 'NEEDS_REVIEW'].includes(receipt.status) && (
                  <div className="result-row">
                    <div className="result-label">Reason</div>
                    <div className="result-value">{escapeHtml(receipt.category_reason)}</div>
                  </div>
                )}
              </>
            )}

            {receipt.duplicate_reason && (
              <div className="result-row">
                <div className="result-label">Duplicate Info</div>
                <div className="result-value">{escapeHtml(receipt.duplicate_reason)}</div>
              </div>
            )}

            {receipt.processing_message && ['REJECTED', 'APPROVED', 'FAILED', 'NEEDS_REVIEW'].includes(receipt.status) && (
              <div className="result-row">
                <div className="result-label">Reason</div>
                <div className="result-value">{escapeHtml(receipt.processing_message)}</div>
              </div>
            )}

            <div className="action-buttons">
              <a
                className="action-button"
                href={getPreviewUrl(receipt.id)}
                target="_blank"
                rel="noopener noreferrer"
              >
                📄 Preview Receipt
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (message.type === 'category-selector' && message.categories) {
    return (
      <div className="message assistant">
        <div className="message-bubble">
          <form onSubmit={handleCategorySubmit}>
            <div className="category-selector">
              <select name="category" required disabled={isSelectingCategory}>
                <option value="">Select a category...</option>
                {message.categories.map(cat => (
                  <option key={cat} value={cat}>
                    {escapeHtml(cat)}
                  </option>
                ))}
              </select>
              <button type="submit" disabled={isSelectingCategory}>
                {isSelectingCategory ? 'Confirming...' : 'Confirm'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return null;
}
