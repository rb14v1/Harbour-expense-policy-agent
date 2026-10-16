import { useState, useEffect } from 'react';
import {
  getFinanceReceipts,
  getFinanceReceiptDetail,
  getFinanceCategories,
  submitFinanceDecision,
  getReceiptPreviewUrl
} from '../api/financeAPI';
import { useUserManual } from '../hooks/useUserManual';
import UserManualModal from '../components/UserManualModal';
import type { ReceiptListItem, ReceiptDetail, FilterParams } from '../types/Finance';
import '../styles/finance.css';

interface FiltersState extends FilterParams {
  page: number;
}

export default function FinanceDashboard() {
  const [receipts, setReceipts] = useState<ReceiptListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [pagination, setPagination] = useState<{ count: number; next: number | null; previous: number | null }>({ count: 0, next: null, previous: null });
  const [filters, setFilters] = useState<FiltersState>({
    status: '',
    category: '',
    vendor: '',
    filename: '',
    date_from: '',
    date_to: '',
    amount_min: '',
    amount_max: '',
    page: 1
  });
  const [selectedReceipt, setSelectedReceipt] = useState<ReceiptDetail | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [deciding, setDeciding] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const { state: manualState, open: openManual, close: closeManual, retry: retryManual } = useUserManual();

  useEffect(() => {
    loadCategories();
    loadReceipts(filters);
  }, []);

  const loadCategories = async () => {
    try {
      const cats = await getFinanceCategories();
      setCategories(cats);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const loadReceipts = async (params: FiltersState) => {
    setLoading(true);
    setError(null);
    try {
      const response = await getFinanceReceipts(params);
      setReceipts(response.results);
      setPagination({ count: response.count, next: response.next, previous: response.previous });
    } catch (err) {
      setError('Failed to load receipts. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field: keyof FiltersState, value: string) => {
    const newFilters = { ...filters, [field]: value, page: 1 };
    setFilters(newFilters);
  };

  const handleApplyFilters = () => {
    loadReceipts(filters);
  };

  const handleClearFilters = () => {
    const cleared = {
      status: '',
      category: '',
      vendor: '',
      filename: '',
      date_from: '',
      date_to: '',
      amount_min: '',
      amount_max: '',
      page: 1
    };
    setFilters(cleared);
    setRejectionReason('');
    setTimeout(() => loadReceipts(cleared), 0);
  };

  const handleViewDetails = async (receipt: ReceiptListItem) => {
    try {
      const detail = await getFinanceReceiptDetail(receipt.id);
      setSelectedReceipt(detail);
      setShowModal(true);
      setRejectionReason('');
    } catch (err) {
      setError('Failed to load receipt details');
    }
  };

  const handleDecision = async (decision: 'APPROVED' | 'REJECTED') => {
    if (!selectedReceipt) return;
    if (decision === 'REJECTED' && !rejectionReason.trim()) {
      setError('Please provide a rejection reason');
      return;
    }

    setDeciding(true);
    try {
      await submitFinanceDecision(selectedReceipt.id, decision, rejectionReason);
      setShowModal(false);
      setSelectedReceipt(null);
      setRejectionReason('');
      await loadReceipts(filters);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Failed to submit decision';
      setError(errMsg);
    } finally {
      setDeciding(false);
    }
  };

  const handleDeleteReceipt = async () => {
    if (!selectedReceipt) return;

    setDeleting(true);
    try {
      const response = await fetch(`/api/v1/receipts/${selectedReceipt.id}/delete_receipt/?owner=finance-department`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 204) {
        setShowModal(false);
        setSelectedReceipt(null);
        setShowDeleteConfirm(false);
        setError(null);
        // Reload receipts to reflect deletion
        await loadReceipts(filters);
      } else if (response.status === 404) {
        setError('Receipt not found');
      } else if (response.status === 403) {
        setError('Unauthorized to delete receipt');
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to delete receipt');
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Failed to delete receipt';
      setError(errMsg);
    } finally {
      setDeleting(false);
    }
  };

  const handlePaginate = (page: number) => {
    const newFilters = { ...filters, page };
    setFilters(newFilters);
    loadReceipts(newFilters);
  };

  const countByStatus = {
    needs_review: receipts.filter(r => r.status === 'NEEDS_REVIEW').length,
    approved: receipts.filter(r => r.status === 'APPROVED').length,
    rejected: receipts.filter(r => r.status === 'REJECTED').length,
    duplicate: receipts.filter(r => ['EXACT_DUPLICATE', 'SEMANTIC_DUPLICATE'].includes(r.status)).length
  };

  return (
    <div className="finance-container">
      <div className="finance-wrapper">
        {/* Header */}
        <div className="finance-header">
          <div className="finance-header-content">
            <h1>Finance Dashboard</h1>
            <p>Review, validate and manage submitted expense receipts</p>
          </div>
          <button
            className="finance-header-manual-btn"
            onClick={openManual}
            aria-label="Open user manual"
            title="View user manual"
          >
            📖 User Manual
          </button>
        </div>

        {/* Stats */}
        <div className="stats-grid">
          <div className="stat-card review">
            <div className="stat-label">Pending Review</div>
            <div className="stat-value">{countByStatus.needs_review}</div>
          </div>
          <div className="stat-card approved">
            <div className="stat-label">Approved</div>
            <div className="stat-value">{countByStatus.approved}</div>
          </div>
          <div className="stat-card rejected">
            <div className="stat-label">Rejected</div>
            <div className="stat-value">{countByStatus.rejected}</div>
          </div>
          <div className="stat-card duplicate">
            <div className="stat-label">Duplicates</div>
            <div className="stat-value">{countByStatus.duplicate}</div>
          </div>
        </div>

        {/* Filters */}
        <div className="filters-section">
          <div className="filters-header">🔍 Filters</div>
          <div className="filters-grid">
            <div className="filter-group">
              <label className="filter-label">Status</label>
              <select
                className="filter-input"
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
              >
                <option value="">All Statuses</option>
                <option value="NEEDS_REVIEW">Needs Review</option>
                <option value="APPROVED">Approved</option>
                <option value="REJECTED">Rejected</option>
                <option value="UNIQUE">Unique</option>
                <option value="EXACT_DUPLICATE">Exact Duplicate</option>
                <option value="SEMANTIC_DUPLICATE">Semantic Duplicate</option>
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Category</label>
              <select
                className="filter-input"
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
              >
                <option value="">All Categories</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Vendor</label>
              <input
                type="text"
                className="filter-input"
                placeholder="Search vendor..."
                value={filters.vendor}
                onChange={(e) => handleFilterChange('vendor', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label className="filter-label">Filename</label>
              <input
                type="text"
                className="filter-input"
                placeholder="Search filename..."
                value={filters.filename}
                onChange={(e) => handleFilterChange('filename', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label className="filter-label">Date From</label>
              <input
                type="date"
                className="filter-input"
                value={filters.date_from}
                onChange={(e) => handleFilterChange('date_from', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label className="filter-label">Date To</label>
              <input
                type="date"
                className="filter-input"
                value={filters.date_to}
                onChange={(e) => handleFilterChange('date_to', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label className="filter-label">Amount Min</label>
              <input
                type="number"
                className="filter-input"
                placeholder="0.00"
                step="0.01"
                value={filters.amount_min}
                onChange={(e) => handleFilterChange('amount_min', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label className="filter-label">Amount Max</label>
              <input
                type="number"
                className="filter-input"
                placeholder="0.00"
                step="0.01"
                value={filters.amount_max}
                onChange={(e) => handleFilterChange('amount_max', e.target.value)}
              />
            </div>
          </div>

          <div className="filter-actions">
            <button className="btn btn-primary" onClick={handleApplyFilters}>
              🔍 Search
            </button>
            <button className="btn btn-secondary" onClick={handleClearFilters}>
              ✕ Clear Filters
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="error-state" style={{ marginBottom: '1.5rem' }}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Results */}
        <div className="results-section">
          <div className="results-header">
            <span>Receipts</span>
            <span className="result-count">{pagination.count} total</span>
          </div>

          {loading ? (
            <div className="state-message loading-state">
              <div className="spinner"></div>
              <p>Loading receipts...</p>
            </div>
          ) : receipts.length === 0 ? (
            <div className="state-message empty-state">
              <div className="empty-icon">📭</div>
              <p>No receipts found. Try adjusting your filters.</p>
            </div>
          ) : (
            <>
              <table className="receipts-table">
                <thead>
                  <tr>
                    <th>Filename</th>
                    <th>Vendor</th>
                    <th>Date</th>
                    <th>Amount</th>
                    <th>Category</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {receipts.map(receipt => (
                    <tr key={receipt.id}>
                      <td className="receipt-filename">{receipt.original_filename}</td>
                      <td className="receipt-vendor">{receipt.vendor_name || '—'}</td>
                      <td>{receipt.transaction_date ? new Date(receipt.transaction_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'}</td>
                      <td className="receipt-amount">
                        {receipt.currency || 'N/A'} {receipt.total_amount ? receipt.total_amount.toFixed(2) : '0.00'}
                      </td>
                      <td>{receipt.category || '—'}</td>
                      <td>
                        <span className={`status-badge status-${receipt.status.toLowerCase().replace(/_/g, '-')}`}>
                          {receipt.status.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td>
                        <div className="table-actions">
                          <button
                            className="action-btn action-btn-view"
                            onClick={() => handleViewDetails(receipt)}
                          >
                            View
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Pagination */}
              {(pagination.next || pagination.previous) && (
                <div className="pagination">
                  <button
                    className="pagination-btn"
                    disabled={!pagination.previous}
                    onClick={() => handlePaginate(filters.page - 1)}
                  >
                    ← Previous
                  </button>
                  <span className="pagination-info">Page {filters.page}</span>
                  <button
                    className="pagination-btn"
                    disabled={!pagination.next}
                    onClick={() => handlePaginate(filters.page + 1)}
                  >
                    Next →
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && selectedReceipt && (
        <div className="modal-overlay" onClick={() => !deleting && setShowDeleteConfirm(false)} style={{ zIndex: 1001 }}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <div className="modal-header">
              <h2>Confirm Delete Receipt</h2>
              <button className="modal-close" onClick={() => !deleting && setShowDeleteConfirm(false)}>×</button>
            </div>

            <div className="modal-content">
              <div className="modal-section">
                <div style={{ marginBottom: '1.5rem' }}>
                  <p style={{ marginBottom: '1rem', fontWeight: 'bold' }}>
                    Are you sure you want to delete this receipt?
                  </p>
                  <div style={{ padding: '1rem', backgroundColor: '#fef3cd', borderRadius: '4px', marginBottom: '1rem' }}>
                    <p style={{ marginBottom: '0.5rem' }}>
                      <strong>Vendor:</strong> {selectedReceipt.vendor_name || 'Unknown'}
                    </p>
                    <p style={{ marginBottom: '0.5rem' }}>
                      <strong>Amount:</strong> {selectedReceipt.currency || 'N/A'} {selectedReceipt.total_amount ? selectedReceipt.total_amount.toFixed(2) : '0.00'}
                    </p>
                    <p style={{ marginBottom: '0.5rem' }}>
                      <strong>Date:</strong> {selectedReceipt.transaction_date
                        ? new Date(selectedReceipt.transaction_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
                        : '—'}
                    </p>
                  </div>
                  <div style={{ padding: '1rem', backgroundColor: '#f8d7da', borderRadius: '4px', marginBottom: '1.5rem', borderLeft: '4px solid #d13438' }}>
                    <p style={{ margin: 0, color: '#721c24', fontWeight: 'bold' }}>
                      ⚠ Warning: This action is permanent and cannot be undone. The receipt will be deleted from the database and cloud storage.
                    </p>
                  </div>
                </div>
              </div>

              <div className="modal-actions" style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={deleting}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-danger"
                  onClick={handleDeleteReceipt}
                  disabled={deleting}
                  style={{ backgroundColor: '#d13438', borderColor: '#d13438', color: 'white' }}
                >
                  {deleting ? 'Deleting...' : 'Confirm Delete'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal */}
      {showModal && selectedReceipt && (
        <div className="modal-overlay" onClick={() => !deciding && !deleting && setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Receipt Details</h2>
              <button className="modal-close" onClick={() => !deciding && !deleting && setShowModal(false)}>×</button>
            </div>

            <div className="modal-content">
              {/* Receipt Info */}
              <div className="modal-section">
                <div className="modal-section-title">Receipt Information</div>
                <div className="modal-field">
                  <div className="modal-field-label">Filename</div>
                  <div className="modal-field-value">{selectedReceipt.original_filename}</div>
                </div>
                <div className="modal-field">
                  <div className="modal-field-label">Vendor</div>
                  <div className="modal-field-value">{selectedReceipt.vendor_name || '—'}</div>
                </div>
                <div className="modal-field">
                  <div className="modal-field-label">Date</div>
                  <div className="modal-field-value">
                    {selectedReceipt.transaction_date
                      ? new Date(selectedReceipt.transaction_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
                      : '—'}
                  </div>
                </div>
                <div className="modal-field">
                  <div className="modal-field-label">Amount</div>
                  <div className="modal-field-value">
                    {selectedReceipt.currency || 'N/A'} {selectedReceipt.total_amount ? selectedReceipt.total_amount.toFixed(2) : '0.00'}
                  </div>
                </div>
                <div className="modal-field">
                  <div className="modal-field-label">Category</div>
                  <div className="modal-field-value">{selectedReceipt.category || '—'}</div>
                </div>
              </div>

              {/* Processing */}
              <div className="modal-section">
                <div className="modal-section-title">Processing Status</div>
                <div className="modal-field">
                  <div className="modal-field-label">Status</div>
                  <div>
                    <span className={`status-badge status-${selectedReceipt.status.toLowerCase().replace(/_/g, '-')}`}>
                      {selectedReceipt.status.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>
                {selectedReceipt.duplicate_reason && (
                  <div className="modal-field">
                    <div className="modal-field-label">Duplicate Info</div>
                    <div className="modal-field-value">{selectedReceipt.duplicate_reason}</div>
                  </div>
                )}
                {selectedReceipt.policy_status && (
                  <div className="modal-field">
                    <div className="modal-field-label">Policy Status</div>
                    <div className="modal-field-value">{selectedReceipt.policy_status}</div>
                  </div>
                )}
              </div>

              {/* Actions */}
              {['NEEDS_REVIEW', 'UNIQUE'].includes(selectedReceipt.status) && (
                <div className="modal-section">
                  <div className="modal-section-title">Finance Decision</div>

                  {rejectionReason === 'reject' && (
                    <div className="decision-form">
                      <div className="form-group">
                        <label className="form-label">Rejection Reason (Required)</label>
                        <textarea
                          className="form-textarea"
                          placeholder="Provide a reason for rejection..."
                          value={rejectionReason === 'reject' ? '' : rejectionReason}
                          onChange={(e) => setRejectionReason(e.target.value)}
                          disabled={deciding || deleting}
                        />
                      </div>
                      <div style={{ display: 'flex', gap: '1rem' }}>
                        <button
                          className="btn btn-primary"
                          onClick={() => handleDecision('REJECTED')}
                          disabled={deciding || deleting}
                        >
                          {deciding ? 'Submitting...' : 'Confirm Rejection'}
                        </button>
                        <button
                          className="btn btn-secondary"
                          onClick={() => setRejectionReason('')}
                          disabled={deciding || deleting}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}

                  {rejectionReason !== 'reject' && (
                    <div className="modal-actions">
                      <button
                        className="btn btn-primary"
                        onClick={() => handleDecision('APPROVED')}
                        disabled={deciding || deleting}
                      >
                        ✓ Approve
                      </button>
                      <button
                        className="btn btn-secondary"
                        onClick={() => setRejectionReason('reject')}
                        disabled={deciding || deleting}
                      >
                        ✗ Reject
                      </button>
                      <a
                        href={getReceiptPreviewUrl(selectedReceipt.id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-secondary"
                        style={{ textDecoration: 'none', textAlign: 'center' }}
                      >
                        📄 Preview
                      </a>
                      <button
                        className="btn btn-danger"
                        onClick={() => setShowDeleteConfirm(true)}
                        disabled={deciding || deleting}
                        style={{ backgroundColor: '#d13438', borderColor: '#d13438' }}
                      >
                        🗑 Delete
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <UserManualModal
        isOpen={manualState.isOpen}
        content={manualState.content}
        isLoading={manualState.isLoading}
        error={manualState.error}
        onClose={closeManual}
        onRetry={retryManual}
      />
    </div>
  );
}
