const API_BASE = '/finance/api';
let currentPage = 1;
let currentReceipt = null;

document.addEventListener('DOMContentLoaded', function() {
    loadCategories();
    loadReceipts();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('searchButton').addEventListener('click', () => {
        currentPage = 1;
        loadReceipts();
    });

    document.getElementById('clearButton').addEventListener('click', clearFilters);
    document.getElementById('prevPageBtn').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadReceipts();
        }
    });

    document.getElementById('nextPageBtn').addEventListener('click', () => {
        currentPage++;
        loadReceipts();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeDetailsModal();
            closePreviewModal();
        }
    });
}

function loadCategories() {
    fetch('/api/v1/receipts/categories/')
        .then(r => r.json())
        .then(data => {
            const select = document.getElementById('categoryFilter');
            const categories = data.categories || [];
            categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat;
                option.textContent = cat;
                select.appendChild(option);
            });
        })
        .catch(err => console.error('Failed to load categories:', err));
}

function getFilterParams() {
    const params = new URLSearchParams();

    const status = document.getElementById('statusFilter').value;
    if (status) params.append('status', status);

    const category = document.getElementById('categoryFilter').value;
    if (category) params.append('category', category);

    const vendor = document.getElementById('vendorSearch').value.trim();
    if (vendor) params.append('vendor', vendor);

    const filename = document.getElementById('filenameSearch').value.trim();
    if (filename) params.append('filename', filename);

    const dateFrom = document.getElementById('dateFromFilter').value;
    if (dateFrom) params.append('date_from', dateFrom);

    const dateTo = document.getElementById('dateToFilter').value;
    if (dateTo) params.append('date_to', dateTo);

    const amountMin = document.getElementById('amountMinFilter').value;
    if (amountMin) params.append('amount_min', amountMin);

    const amountMax = document.getElementById('amountMaxFilter').value;
    if (amountMax) params.append('amount_max', amountMax);

    params.append('page', currentPage);

    return params.toString();
}

function loadReceipts() {
    const params = getFilterParams();
    const url = `${API_BASE}/receipts/?${params}`;

    showLoadingState();

    fetch(url)
        .then(r => r.json())
        .then(data => {
            displayReceipts(data);
        })
        .catch(err => {
            console.error('Error loading receipts:', err);
            showErrorState('Failed to load receipts. Please try again.');
        });
}

function displayReceipts(data) {
    const { count, results, next, previous } = data;

    document.getElementById('resultCount').textContent = `${count} receipt${count !== 1 ? 's' : ''}`;

    if (!results || results.length === 0) {
        showEmptyState();
        return;
    }

    const tbody = document.getElementById('receiptsBody');
    tbody.innerHTML = '';

    results.forEach(receipt => {
        const row = document.createElement('tr');
        const statusClass = getStatusClass(receipt.status);

        row.innerHTML = `
            <td>${escapeHtml(receipt.original_filename)}</td>
            <td>${escapeHtml(receipt.vendor_name || '—')}</td>
            <td>${formatDate(receipt.transaction_date)}</td>
            <td>${receipt.total_amount ? `${receipt.currency || 'N/A'} ${parseFloat(receipt.total_amount).toFixed(2)}` : '—'}</td>
            <td>${escapeHtml(receipt.category || '—')}</td>
            <td><span class="status-badge ${statusClass}">${receipt.status}</span></td>
            <td>
                <div class="action-buttons">
                    <button class="action-button" onclick="viewDetails('${receipt.id}')">View</button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });

    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('errorState').style.display = 'none';
    document.getElementById('receiptsTable').style.display = 'block';

    updatePaginationControls(next, previous);
}

function updatePaginationControls(next, previous) {
    const paginationDiv = document.getElementById('paginationControls');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    if (next || previous) {
        paginationDiv.style.display = 'flex';
        prevBtn.disabled = !previous;
        nextBtn.disabled = !next;
        document.getElementById('pageIndicator').textContent = `Page ${currentPage}`;
    } else {
        paginationDiv.style.display = 'none';
    }
}

function viewDetails(receiptId) {
    currentReceipt = receiptId;
    showDetailsModal();
    loadReceiptDetails(receiptId);
}

function loadReceiptDetails(receiptId) {
    const url = `${API_BASE}/receipts/${receiptId}/`;

    document.getElementById('detailsLoading').style.display = 'block';
    document.getElementById('detailsContent').style.display = 'none';

    fetch(url)
        .then(r => r.json())
        .then(receipt => {
            displayReceiptDetails(receipt);
            document.getElementById('detailsLoading').style.display = 'none';
            document.getElementById('detailsContent').style.display = 'block';
        })
        .catch(err => {
            console.error('Error loading receipt details:', err);
            document.getElementById('detailsLoading').style.display = 'none';
            alert('Failed to load receipt details.');
        });
}

function displayReceiptDetails(receipt) {
    document.getElementById('detail-filename').textContent = escapeHtml(receipt.original_filename);
    document.getElementById('detail-vendor').textContent = escapeHtml(receipt.vendor_name || '—');
    document.getElementById('detail-date').textContent = formatDate(receipt.transaction_date);
    document.getElementById('detail-amount').textContent = receipt.total_amount ? `${parseFloat(receipt.total_amount).toFixed(2)}` : '—';
    document.getElementById('detail-currency').textContent = receipt.currency || '—';
    document.getElementById('detail-invoice').textContent = receipt.invoice_number || '—';
    document.getElementById('detail-payment').textContent = receipt.payment_method || '—';

    document.getElementById('detail-category').textContent = receipt.category || '—';

    if (receipt.category_confidence !== null && receipt.category_confidence !== undefined) {
        const confidence = (receipt.category_confidence * 100).toFixed(0);
        document.getElementById('detail-confidence').textContent = `${confidence}%`;
    } else {
        document.getElementById('detail-confidence').textContent = '—';
    }

    document.getElementById('detail-reason').textContent = receipt.category_reason || '—';

    document.getElementById('detail-status').textContent = receipt.status;
    document.getElementById('detail-status').className = `detail-value status-badge ${getStatusClass(receipt.status)}`;

    document.getElementById('detail-message').textContent = receipt.processing_message || '—';

    document.getElementById('detail-created').textContent = formatDateTime(receipt.created_at);
    document.getElementById('detail-updated').textContent = formatDateTime(receipt.updated_at);

    showDuplicateSection(receipt);
    showPolicySection(receipt);
    showDecisionSection(receipt);
}

function showDuplicateSection(receipt) {
    const section = document.getElementById('duplicateSection');

    if (receipt.duplicate_score !== null || receipt.duplicate_reason) {
        section.style.display = 'block';

        let dupType = '—';
        if (receipt.status === 'EXACT_DUPLICATE') {
            dupType = 'Exact Duplicate';
        } else if (receipt.status === 'SEMANTIC_DUPLICATE') {
            dupType = 'Semantic Duplicate';
        }
        document.getElementById('detail-duptype').textContent = dupType;

        document.getElementById('detail-dupscore').textContent = receipt.duplicate_score !== null ? receipt.duplicate_score : '—';

        document.getElementById('detail-dupreason').textContent = receipt.duplicate_reason || '—';
    } else {
        section.style.display = 'none';
    }
}

function showPolicySection(receipt) {
    const section = document.getElementById('policySection');
    const rulesContainer = document.getElementById('policyRulesContainer');

    if (receipt.policy_status || receipt.policy_result_json) {
        section.style.display = 'block';

        if (receipt.policy_status) {
            document.getElementById('detail-polstatus').textContent = receipt.policy_status;
            document.getElementById('detail-polstatus').className = `detail-value status-badge ${getStatusClass(receipt.policy_status)}`;
        }

        if (receipt.policy_result_json && receipt.policy_result_json.rules && receipt.policy_result_json.rules.length > 0) {
            rulesContainer.style.display = 'block';
            const rulesDiv = document.getElementById('detail-polrules');
            rulesDiv.innerHTML = '';

            receipt.policy_result_json.rules.forEach(rule => {
                const ruleEl = document.createElement('div');
                ruleEl.className = `policy-rule ${rule.passed ? 'passed' : 'failed'}`;
                ruleEl.innerHTML = `
                    <div class="policy-rule-code">${escapeHtml(rule.code)} ${rule.passed ? '✓' : '✗'}</div>
                    <div class="policy-rule-message">${escapeHtml(rule.message)}</div>
                `;
                rulesDiv.appendChild(ruleEl);
            });
        } else {
            rulesContainer.style.display = 'none';
        }
    } else {
        section.style.display = 'none';
    }
}

function previewCurrentReceipt() {
    if (!currentReceipt) return;
    showPreviewModal();
    loadPreview(currentReceipt);
}

function loadPreview(receiptId) {
    const url = `/api/v1/receipts/${receiptId}/preview/?owner=finance-department`;

    document.getElementById('previewLoading').style.display = 'block';
    document.getElementById('previewContent').style.display = 'none';
    document.getElementById('previewError').style.display = 'none';

    const xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                const blob = xhr.response;
                const blobUrl = URL.createObjectURL(blob);
                const contentType = xhr.getResponseHeader('content-type');

                document.getElementById('previewLoading').style.display = 'none';
                document.getElementById('previewContent').style.display = 'block';

                const iframe = document.getElementById('previewFrame');
                iframe.src = blobUrl;
            } else {
                document.getElementById('previewLoading').style.display = 'none';
                document.getElementById('previewError').style.display = 'block';
                document.getElementById('previewErrorMessage').textContent = 'Unable to load preview. The receipt file may no longer be available.';
            }
        }
    };
    xhr.responseType = 'blob';
    xhr.open('GET', url, true);
    xhr.send();
}

function showLoadingState() {
    document.getElementById('loadingState').style.display = 'block';
    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('errorState').style.display = 'none';
    document.getElementById('receiptsTable').style.display = 'none';
    document.getElementById('paginationControls').style.display = 'none';
}

function showEmptyState() {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('emptyState').style.display = 'block';
    document.getElementById('errorState').style.display = 'none';
    document.getElementById('receiptsTable').style.display = 'none';
    document.getElementById('paginationControls').style.display = 'none';
}

function showErrorState(message) {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('errorState').style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('receiptsTable').style.display = 'none';
    document.getElementById('paginationControls').style.display = 'none';
}

function showDetailsModal() {
    document.getElementById('detailsModal').style.display = 'flex';
}

function closeDetailsModal() {
    document.getElementById('detailsModal').style.display = 'none';
}

function showPreviewModal() {
    document.getElementById('previewModal').style.display = 'flex';
}

function closePreviewModal() {
    document.getElementById('previewModal').style.display = 'none';
}

function clearFilters() {
    document.getElementById('statusFilter').value = '';
    document.getElementById('categoryFilter').value = '';
    document.getElementById('vendorSearch').value = '';
    document.getElementById('filenameSearch').value = '';
    document.getElementById('dateFromFilter').value = '';
    document.getElementById('dateToFilter').value = '';
    document.getElementById('amountMinFilter').value = '';
    document.getElementById('amountMaxFilter').value = '';
    currentPage = 1;
    loadReceipts();
}

function getStatusClass(status) {
    const statusLower = (status || '').toLowerCase();
    if (statusLower.includes('approved')) return 'approved';
    if (statusLower.includes('rejected')) return 'rejected';
    if (statusLower.includes('duplicate')) return 'duplicate';
    if (statusLower.includes('unique')) return 'unique';
    if (statusLower.includes('failed')) return 'failed';
    return '';
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
        return dateStr;
    }
}

function formatDateTime(dateStr) {
    if (!dateStr) return '—';
    try {
        const date = new Date(dateStr);
        return date.toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
        return dateStr;
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showDecisionSection(receipt) {
    const section = document.getElementById('decisionSection');
    const status = receipt.status || '';

    if (status === 'APPROVED' || status === 'REJECTED') {
        section.style.display = 'none';
    } else if (status === 'UNIQUE') {
        section.style.display = 'block';
    } else {
        section.style.display = 'none';
    }

    hideDecisionForms();
}

function showApproveForm() {
    document.getElementById('approveForm').style.display = 'block';
    document.getElementById('rejectForm').style.display = 'none';
}

function showRejectForm() {
    document.getElementById('rejectForm').style.display = 'block';
    document.getElementById('approveForm').style.display = 'none';
}

function hideDecisionForms() {
    document.getElementById('approveForm').style.display = 'none';
    document.getElementById('rejectForm').style.display = 'none';
    document.getElementById('approveNotes').value = '';
    document.getElementById('rejectNotes').value = '';
}

async function submitApproval() {
    if (!currentReceipt) return;

    const notes = document.getElementById('approveNotes').value.trim();
    await submitDecision('APPROVED', notes);
}

async function submitRejection() {
    if (!currentReceipt) return;

    const notes = document.getElementById('rejectNotes').value.trim();
    if (!notes) {
        alert('Please provide a reason for rejection.');
        return;
    }

    await submitDecision('REJECTED', notes);
}

async function submitDecision(decision, notes) {
    const url = `${API_BASE}/receipts/${currentReceipt}/decision/`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                decision: decision,
                notes: notes
            })
        });

        if (response.ok) {
            const updatedReceipt = await response.json();
            displayReceiptDetails(updatedReceipt);
            hideDecisionForms();
            loadReceipts();
        } else {
            alert('Failed to submit decision. Please try again.');
        }
    } catch (error) {
        console.error('Error submitting decision:', error);
        alert('Error submitting decision: ' + error.message);
    }
}
