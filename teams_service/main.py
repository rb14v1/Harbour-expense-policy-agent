"""
Teams Service - Main Application

FastAPI-based Teams bot service for Expense Policy Agent.

Uses Microsoft Teams SDK (microsoft-teams-apps) to handle Teams protocol.
Delegates business logic to Django REST APIs.

Run:
    uvicorn teams_service.main:app --host 0.0.0.0 --port 8001

Environment variables (from .env):
    CLIENT_ID — Teams app client ID
    CLIENT_SECRET — Teams app client secret
    TENANT_ID — Azure tenant ID
    DJANGO_API_URL — Django backend API URL (default: http://localhost:8000/api/v1)
    DJANGO_FINANCE_API_URL — Django Finance API URL (default: http://localhost:8000/finance/api)
"""
import logging
from fastapi import FastAPI, Request, Response
from microsoft_teams.apps import App
from microsoft_teams.apps.http import FastAPIAdapter
from microsoft_teams.apps.options import AppOptions

from teams_service.config import config
from teams_service.handlers.message_handlers import finance_handler
from teams_service.services.django_client import django_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Expense Policy Agent - Teams Service",
    description="Teams SDK service for expense receipt review",
    version="1.0.0",
)

# Initialize Teams SDK
logger.info("Initializing Teams SDK...")

try:
    teams_options = config.get_teams_options()

    teams_app = App(
        **teams_options,
        dangerously_allow_unauthenticated_requests=config.SKIP_TEAMS_AUTH,
    )

    # Create FastAPI adapter for Teams SDK
    adapter = FastAPIAdapter(app=app)

    logger.info("Teams SDK initialized successfully")

except Exception as e:
    logger.error(f"Failed to initialize Teams SDK: {e}")
    raise


# Register message handlers
@teams_app.on_message()
async def on_message(context):
    """Handle incoming Teams messages."""
    activity = context.activity
    from_id = activity.from_property.id if activity.from_property else "unknown"
    logger.info(f"Message received from {from_id}")

    try:
        response = await finance_handler.handle_message(context)

        if response:
            # Return response through Teams SDK
            return response
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return {
            "type": "message",
            "text": "An error occurred. Please try again later.",
        }


# HTTP endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Expense Policy Agent Teams Service",
        "version": "1.0.0",
    }


@app.get("/config", tags=["Configuration"])
async def get_config_info():
    """Get configuration info (no secrets exposed)."""
    return {
        "service": "Expense Policy Agent Teams Service",
        "teams_app_id": config.TEAMS_APP_ID[:8] + "...",
        "django_api": config.DJANGO_API_URL,
        "debug": config.DEBUG,
    }


@app.post("/api/messages", tags=["Teams"])
async def messages(request: Request):
    """
    Teams messaging endpoint.

    Receives Teams activities and routes them to Teams SDK.
    This endpoint is configured in Teams manifest.
    """
    # The FastAPIAdapter handles routing to the Teams SDK
    # This endpoint is called by Teams for all activities
    logger.debug(f"Received Teams activity on /api/messages")
    return Response(status_code=202)  # Accepted


# Finance API Proxy Endpoints
# These endpoints proxy requests to Django Finance APIs
# allowing the browser Finance tab to call relative URLs

@app.get("/finance/api/receipts/", tags=["Finance API"])
async def finance_receipts_list(
    page: int = 1,
    status: str = None,
    category: str = None,
    vendor: str = None,
    filename: str = None,
    date_from: str = None,
    date_to: str = None,
    amount_min: float = None,
    amount_max: float = None,
):
    """Proxy: Get receipts list with filters."""
    try:
        # Build query parameters for Django API
        params = {
            'page': page,
        }
        if status:
            params['status'] = status
        if category:
            params['category'] = category
        if vendor:
            params['vendor'] = vendor
        if filename:
            params['filename'] = filename
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        if amount_min is not None:
            params['amount_min'] = amount_min
        if amount_max is not None:
            params['amount_max'] = amount_max

        # Call Django Finance API
        result = await django_client.get_receipts(**params)
        return result
    except Exception as e:
        logger.error(f"Error proxying receipt list: {e}")
        return Response(
            content='{"error": "Failed to retrieve receipts"}',
            status_code=500,
            media_type="application/json"
        )


@app.get("/finance/api/receipts/{receipt_id}/", tags=["Finance API"])
async def finance_receipt_detail(receipt_id: str):
    """Proxy: Get receipt details."""
    try:
        result = await django_client.get_receipt_detail(receipt_id)
        if result is None:
            return Response(
                content='{"error": "Receipt not found"}',
                status_code=404,
                media_type="application/json"
            )
        return result
    except Exception as e:
        logger.error(f"Error proxying receipt detail: {e}")
        return Response(
            content='{"error": "Failed to retrieve receipt"}',
            status_code=500,
            media_type="application/json"
        )


@app.post("/finance/api/receipts/{receipt_id}/decision/", tags=["Finance API"])
async def finance_receipt_decision(receipt_id: str, request: Request):
    """Proxy: Submit finance decision (approve/reject)."""
    try:
        body = await request.json()
        decision = body.get("decision")
        notes = body.get("notes")

        if decision not in ["APPROVED", "REJECTED"]:
            return Response(
                content='{"error": "Invalid decision"}',
                status_code=400,
                media_type="application/json"
            )

        result = await django_client.make_receipt_decision(
            receipt_id, decision, notes=notes
        )
        if result is None:
            return Response(
                content='{"error": "Receipt not found"}',
                status_code=404,
                media_type="application/json"
            )
        return result
    except Exception as e:
        logger.error(f"Error proxying receipt decision: {e}")
        return Response(
            content='{"error": "Failed to submit decision"}',
            status_code=500,
            media_type="application/json"
        )


@app.get("/finance/api/categories/", tags=["Finance API"])
async def finance_categories():
    """Proxy: Get available receipt categories."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{config.DJANGO_API_URL}/receipts/categories/"
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying categories: {e}")
        return Response(
            content='{"error": "Failed to retrieve categories"}',
            status_code=500,
            media_type="application/json"
        )


@app.get("/finance/api/receipts/{receipt_id}/preview/", tags=["Finance API"])
async def finance_receipt_preview(receipt_id: str):
    """Proxy: Get receipt file preview."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{config.DJANGO_API_URL}/receipts/{receipt_id}/preview/?owner=finance-department"
            )
            # Pass through the Django response (including errors) as-is
            return Response(
                content=response.content,
                status_code=response.status_code,
                media_type=response.headers.get("content-type", "application/octet-stream")
            )
    except Exception as e:
        logger.error(f"Error proxying receipt preview: {e}")
        return Response(
            content='{"error": "Failed to retrieve preview"}',
            status_code=500,
            media_type="application/json"
        )


@app.get("/finance/tab", tags=["Finance"])
async def finance_tab():
    """Finance Review tab HTML content for Teams - Full-featured dashboard."""
    html = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finance Department - Receipt Review Dashboard</title>
    <script src="https://res.cdn.office.net/teams-js/2.17.0/js/microsoft.teams.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; color: #333; }
        .dashboard-container { max-width: 1400px; margin: 0 auto; padding: 10px; }
        .dashboard-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 30px; border-radius: 8px; margin-bottom: 20px; }
        .dashboard-header h1 { font-size: 22px; margin-bottom: 4px; }
        .dashboard-header p { font-size: 13px; opacity: 0.9; }
        .filter-section { background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 15px; margin-bottom: 20px; }
        .filter-header { margin-bottom: 15px; }
        .filter-header h2 { font-size: 15px; color: #333; }
        .filter-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 12px; }
        .filter-group { display: flex; flex-direction: column; gap: 3px; }
        .filter-group label { font-size: 11px; font-weight: 600; color: #666; text-transform: uppercase; }
        .filter-input { padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; }
        .filter-input:focus { outline: none; border-color: #667eea; }
        .filter-actions { display: flex; gap: 8px; flex-wrap: wrap; }
        .btn { padding: 8px 16px; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 12px; }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5568d3; }
        .btn-secondary { background: #f0f0f0; color: #667eea; }
        .btn-secondary:hover { background: #e0e0e0; }
        .results-section { background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 15px; }
        .results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid #eee; }
        .results-header h2 { font-size: 15px; }
        .result-count { background: #667eea; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
        .state-message { text-align: center; padding: 30px 15px; color: #999; }
        .spinner { width: 30px; height: 30px; border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 10px; }
        @keyframes spin { to { transform: rotate(360deg); } }
        table { width: 100%; border-collapse: collapse; }
        thead { background: #f8f8f8; }
        th { padding: 10px; text-align: left; font-weight: 600; font-size: 11px; color: #666; text-transform: uppercase; border-bottom: 2px solid #eee; }
        td { padding: 10px; border-bottom: 1px solid #eee; font-size: 12px; }
        tbody tr:hover { background: #f9f9f9; }
        .status-badge { display: inline-block; padding: 3px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; }
        .status-approved { background: #d1fae5; color: #065f46; }
        .status-rejected { background: #fee2e2; color: #991b1b; }
        .status-duplicate { background: #fef3c7; color: #92400e; }
        .status-unique { background: #e0e7ff; color: #3730a3; }
        .status-failed { background: #fecaca; color: #7f1d1d; }
        .action-button { padding: 5px 10px; background: #667eea; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 600; }
        .action-button:hover { background: #5568d3; }
        .pagination-controls { display: flex; justify-content: center; gap: 10px; margin-top: 15px; padding-top: 12px; border-top: 1px solid #eee; }
        .page-indicator { display: flex; align-items: center; font-weight: 600; color: #666; }
        .modal { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center; padding: 10px; }
        .modal.active { display: flex; }
        .modal-content { background: white; border-radius: 8px; max-width: 600px; width: 100%; max-height: 85vh; overflow-y: auto; box-shadow: 0 5px 40px rgba(0,0,0,0.3); }
        .modal-header { display: flex; justify-content: space-between; align-items: center; padding: 15px; border-bottom: 1px solid #eee; sticky-top: 0; background: white; }
        .modal-header h2 { font-size: 16px; }
        .modal-close { background: none; border: none; font-size: 20px; cursor: pointer; color: #999; }
        .modal-close:hover { color: #333; }
        .modal-body { padding: 15px; }
        .details-section { margin-bottom: 15px; padding-bottom: 12px; border-bottom: 1px solid #eee; }
        .details-section:last-of-type { border-bottom: none; }
        .details-section h3 { font-size: 13px; margin-bottom: 10px; color: #333; }
        .details-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
        .detail-item { display: flex; flex-direction: column; gap: 3px; }
        .detail-item.full-width { grid-column: 1 / -1; }
        .detail-label { font-size: 10px; font-weight: 600; color: #999; text-transform: uppercase; }
        .detail-value { font-size: 12px; color: #333; word-break: break-word; }
        .decision-buttons { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
        .btn-danger { background: #ef4444; color: white; }
        .btn-danger:hover { background: #dc2626; }
        .decision-form { background: #f9f9f9; padding: 12px; border-radius: 4px; border: 1px solid #eee; margin-top: 10px; }
        .decision-form label { display: block; font-size: 11px; font-weight: 600; color: #666; margin-bottom: 6px; }
        .form-textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-family: inherit; font-size: 12px; resize: vertical; min-height: 60px; }
        .form-textarea:focus { outline: none; border-color: #667eea; }
        .form-actions { display: flex; gap: 8px; margin-top: 10px; }
        .modal-loading { text-align: center; padding: 30px; }
        .error-message { color: #dc2626; }
        .success-message { color: #10b981; }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <header class="dashboard-header">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1>📊 Finance Department - Receipt Review Dashboard</h1>
                    <p>Review and manage all submitted expense receipts</p>
                </div>
                <button id="uploadButton" class="btn btn-primary" style="margin-top: 0; white-space: nowrap;">📤 Upload Receipt</button>
            </div>
        </header>

        <section class="filter-section">
            <div class="filter-header">
                <h2>Search and Filter</h2>
            </div>
            <div class="filter-grid">
                <div class="filter-group">
                    <label for="statusFilter">Status</label>
                    <select id="statusFilter" class="filter-input">
                        <option value="">All Statuses</option>
                        <option value="APPROVED">Approved</option>
                        <option value="REJECTED">Rejected</option>
                        <option value="EXACT_DUPLICATE">Exact Duplicate</option>
                        <option value="SEMANTIC_DUPLICATE">Semantic Duplicate</option>
                        <option value="UNIQUE">Unique</option>
                        <option value="OCR_FAILED">OCR Failed</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="categoryFilter">Category</label>
                    <select id="categoryFilter" class="filter-input">
                        <option value="">All Categories</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="vendorSearch">Vendor</label>
                    <input type="text" id="vendorSearch" class="filter-input" placeholder="Search vendor...">
                </div>
                <div class="filter-group">
                    <label for="filenameSearch">Filename</label>
                    <input type="text" id="filenameSearch" class="filter-input" placeholder="Search filename...">
                </div>
                <div class="filter-group">
                    <label for="dateFromFilter">Date From</label>
                    <input type="date" id="dateFromFilter" class="filter-input">
                </div>
                <div class="filter-group">
                    <label for="dateToFilter">Date To</label>
                    <input type="date" id="dateToFilter" class="filter-input">
                </div>
                <div class="filter-group">
                    <label for="amountMinFilter">Amount Min</label>
                    <input type="number" id="amountMinFilter" class="filter-input" placeholder="0.00" step="0.01">
                </div>
                <div class="filter-group">
                    <label for="amountMaxFilter">Amount Max</label>
                    <input type="number" id="amountMaxFilter" class="filter-input" placeholder="0.00" step="0.01">
                </div>
            </div>
            <div class="filter-actions">
                <button id="searchButton" class="btn btn-primary">🔍 Search</button>
                <button id="clearButton" class="btn btn-secondary">✕ Clear Filters</button>
            </div>
        </section>

        <section class="results-section">
            <div class="results-header">
                <h2>Receipts</h2>
                <span id="resultCount" class="result-count">Loading...</span>
            </div>
            <div id="loadingState" class="state-message" style="display: block;">
                <div class="spinner"></div>
                <p>Loading receipts...</p>
            </div>
            <div id="emptyState" class="state-message" style="display: none;">
                <p>📭 No receipts found. Try adjusting your filters.</p>
            </div>
            <div id="errorState" class="state-message" style="display: none;">
                <p id="errorMessage" class="error-message">An error occurred while loading receipts.</p>
            </div>
            <div id="receiptsTable" style="display: none; overflow-x: auto;">
                <table>
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
                    <tbody id="receiptsBody">
                    </tbody>
                </table>
            </div>
            <div id="paginationControls" class="pagination-controls" style="display: none;">
                <button id="prevPageBtn" class="btn btn-secondary">← Previous</button>
                <span id="pageIndicator" class="page-indicator">Page 1</span>
                <button id="nextPageBtn" class="btn btn-secondary">Next →</button>
            </div>
        </section>
    </div>

    <div id="detailsModal" class="modal" style="display: none;">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Receipt Details</h2>
                <button class="modal-close" onclick="closeDetailsModal()">✕</button>
            </div>
            <div class="modal-body">
                <div id="detailsLoading" class="modal-loading" style="display: block;">
                    <div class="spinner"></div>
                    <p>Loading details...</p>
                </div>
                <div id="detailsContent" style="display: none;">
                    <div class="details-section">
                        <h3>Receipt Information</h3>
                        <div class="details-grid">
                            <div class="detail-item"><span class="detail-label">Filename</span><span id="detail-filename" class="detail-value">—</span></div>
                            <div class="detail-item"><span class="detail-label">Vendor</span><span id="detail-vendor" class="detail-value">—</span></div>
                            <div class="detail-item"><span class="detail-label">Transaction Date</span><span id="detail-date" class="detail-value">—</span></div>
                            <div class="detail-item"><span class="detail-label">Amount</span><span id="detail-amount" class="detail-value">—</span></div>
                            <div class="detail-item"><span class="detail-label">Currency</span><span id="detail-currency" class="detail-value">—</span></div>
                            <div class="detail-item"><span class="detail-label">Invoice Number</span><span id="detail-invoice" class="detail-value">—</span></div>
                        </div>
                    </div>

                    <div class="details-section">
                        <h3>Category</h3>
                        <div class="details-grid">
                            <div class="detail-item"><span class="detail-label">Category</span><span id="detail-category" class="detail-value">—</span></div>
                            <div class="detail-item"><span class="detail-label">Confidence</span><span id="detail-confidence" class="detail-value">—</span></div>
                        </div>
                    </div>

                    <div class="details-section">
                        <h3>Processing Information</h3>
                        <div class="details-grid">
                            <div class="detail-item"><span class="detail-label">Status</span><span id="detail-status" class="detail-value status-badge">—</span></div>
                            <div class="detail-item full-width"><span class="detail-label">Message</span><span id="detail-message" class="detail-value">—</span></div>
                        </div>
                    </div>

                    <div id="duplicateSection" class="details-section" style="display: none;">
                        <h3>Duplicate Information</h3>
                        <div class="details-grid">
                            <div class="detail-item"><span class="detail-label">Duplicate Type</span><span id="detail-duptype" class="detail-value">—</span></div>
                            <div class="detail-item"><span class="detail-label">Duplicate Score</span><span id="detail-dupscore" class="detail-value">—</span></div>
                            <div class="detail-item full-width"><span class="detail-label">Duplicate Reason</span><span id="detail-dupreason" class="detail-value">—</span></div>
                        </div>
                    </div>

                    <div id="policySection" class="details-section" style="display: none;">
                        <h3>Policy Information</h3>
                        <div class="details-grid">
                            <div class="detail-item"><span class="detail-label">Policy Status</span><span id="detail-polstatus" class="detail-value status-badge">—</span></div>
                        </div>
                    </div>

                    <div id="decisionSection" class="details-section" style="display: none;">
                        <h3>Finance Decision</h3>
                        <div class="decision-buttons">
                            <button class="btn btn-primary" onclick="showApproveForm()">✅ Approve</button>
                            <button class="btn btn-danger" onclick="showRejectForm()">❌ Reject</button>
                        </div>
                        <div id="approveForm" style="display: none;">
                            <div class="decision-form">
                                <label for="approveNotes">Notes (optional)</label>
                                <textarea id="approveNotes" class="form-textarea" placeholder="Add approval notes..."></textarea>
                                <div class="form-actions">
                                    <button class="btn btn-primary" onclick="submitApproval()">Submit Approval</button>
                                    <button class="btn btn-secondary" onclick="hideDecisionForms()">Cancel</button>
                                </div>
                            </div>
                        </div>
                        <div id="rejectForm" style="display: none;">
                            <div class="decision-form">
                                <label for="rejectNotes">Reason for rejection (required)</label>
                                <textarea id="rejectNotes" class="form-textarea" placeholder="Explain why this receipt is rejected..." required></textarea>
                                <div class="form-actions">
                                    <button class="btn btn-danger" onclick="submitRejection()">Submit Rejection</button>
                                    <button class="btn btn-secondary" onclick="hideDecisionForms()">Cancel</button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="details-section" style="margin-top: 15px; border-bottom: none;">
                        <button id="previewBtn" class="btn btn-primary" onclick="previewCurrentReceipt()">📄 Preview Receipt</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="previewModal" class="modal" style="display: none;">
        <div class="modal-content" style="max-width: 800px;">
            <div class="modal-header">
                <h2>Receipt Preview</h2>
                <button class="modal-close" onclick="closePreviewModal()">✕</button>
            </div>
            <div class="modal-body">
                <div id="previewLoading" class="modal-loading" style="display: block;">
                    <div class="spinner"></div>
                    <p>Loading preview...</p>
                </div>
                <div id="previewContent" style="display: none;">
                    <iframe id="previewFrame" style="width: 100%; height: 500px; border: none; border-radius: 4px;"></iframe>
                </div>
                <div id="previewError" class="state-message" style="display: none;">
                    <p id="previewErrorMessage" class="error-message">Unable to load preview.</p>
                </div>
            </div>
        </div>
    </div>

    <div id="uploadModal" class="modal" style="display: none;">
        <div class="modal-content" style="max-width: 1000px; height: 80vh;">
            <div class="modal-header">
                <h2>💰 Upload Receipt</h2>
                <button class="modal-close" onclick="closeUploadModal()">✕</button>
            </div>
            <div class="modal-body" style="overflow-y: auto; height: 100%;">
                <iframe id="uploadFrame" src="/upload/" style="width: 100%; height: 100%; border: none; border-radius: 4px;"></iframe>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = '/finance/api';
        let currentPage = 1;
        let currentReceipt = null;

        // Initialize immediately and in parallel with Teams SDK
        document.addEventListener('DOMContentLoaded', function() {
            loadCategories();
            loadReceipts();
            setupEventListeners();
            initializeTeamsSDK();
        });

        // Fallback in case DOMContentLoaded has already fired
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {});
        } else {
            loadCategories();
            loadReceipts();
            setupEventListeners();
            initializeTeamsSDK();
        }

        function initializeTeamsSDK() {
            if (typeof microsoftTeams === 'undefined') return;
            Promise.race([
                microsoftTeams.initialize(),
                new Promise((_, r) => setTimeout(() => r('timeout'), 2000))
            ]).catch(e => console.log('Teams SDK: ' + e));
        }

        function setupEventListeners() {
            document.getElementById('searchButton').addEventListener('click', () => {
                currentPage = 1;
                loadReceipts();
            });
            document.getElementById('clearButton').addEventListener('click', clearFilters);
            document.getElementById('prevPageBtn').addEventListener('click', () => {
                if (currentPage > 1) { currentPage--; loadReceipts(); }
            });
            document.getElementById('nextPageBtn').addEventListener('click', () => {
                currentPage++; loadReceipts();
            });
            document.getElementById('uploadButton').addEventListener('click', showUploadModal);
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') { closeDetailsModal(); closePreviewModal(); closeUploadModal(); }
            });
        }

        function loadCategories() {
            fetch('/finance/api/categories/')
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
            if (document.getElementById('statusFilter').value) params.append('status', document.getElementById('statusFilter').value);
            if (document.getElementById('categoryFilter').value) params.append('category', document.getElementById('categoryFilter').value);
            if (document.getElementById('vendorSearch').value.trim()) params.append('vendor', document.getElementById('vendorSearch').value.trim());
            if (document.getElementById('filenameSearch').value.trim()) params.append('filename', document.getElementById('filenameSearch').value.trim());
            if (document.getElementById('dateFromFilter').value) params.append('date_from', document.getElementById('dateFromFilter').value);
            if (document.getElementById('dateToFilter').value) params.append('date_to', document.getElementById('dateToFilter').value);
            if (document.getElementById('amountMinFilter').value) params.append('amount_min', document.getElementById('amountMinFilter').value);
            if (document.getElementById('amountMaxFilter').value) params.append('amount_max', document.getElementById('amountMaxFilter').value);
            params.append('page', currentPage);
            return params.toString();
        }

        function loadReceipts() {
            const params = getFilterParams();
            const url = API_BASE + '/receipts/?' + params;
            showLoadingState();
            fetch(url)
                .then(r => r.json())
                .then(data => displayReceipts(data))
                .catch(err => {
                    console.error('Error loading receipts:', err);
                    showErrorState('Failed to load receipts. Please try again.');
                });
        }

        function displayReceipts(data) {
            const { count, results, next, previous } = data;
            document.getElementById('resultCount').textContent = count + ' receipt' + (count !== 1 ? 's' : '');
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
                    <td>${receipt.total_amount ? (receipt.currency || 'N/A') + ' ' + parseFloat(receipt.total_amount).toFixed(2) : '—'}</td>
                    <td>${escapeHtml(receipt.category || '—')}</td>
                    <td><span class="status-badge ${statusClass}">${receipt.status}</span></td>
                    <td><button class="action-button" onclick="viewDetails('${receipt.id}')">View</button></td>
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
                document.getElementById('pageIndicator').textContent = 'Page ' + currentPage;
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
            const url = API_BASE + '/receipts/' + receiptId + '/';
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
            document.getElementById('detail-amount').textContent = receipt.total_amount ? parseFloat(receipt.total_amount).toFixed(2) : '—';
            document.getElementById('detail-currency').textContent = receipt.currency || '—';
            document.getElementById('detail-invoice').textContent = receipt.invoice_number || '—';
            document.getElementById('detail-category').textContent = receipt.category || '—';
            if (receipt.category_confidence !== null && receipt.category_confidence !== undefined) {
                document.getElementById('detail-confidence').textContent = (receipt.category_confidence * 100).toFixed(0) + '%';
            } else {
                document.getElementById('detail-confidence').textContent = '—';
            }
            document.getElementById('detail-status').textContent = receipt.status;
            document.getElementById('detail-status').className = 'detail-value status-badge ' + getStatusClass(receipt.status);
            document.getElementById('detail-message').textContent = receipt.processing_message || '—';
            showDuplicateSection(receipt);
            showPolicySection(receipt);
            showDecisionSection(receipt);
        }

        function showDuplicateSection(receipt) {
            const section = document.getElementById('duplicateSection');
            if (receipt.duplicate_score !== null || receipt.duplicate_reason) {
                section.style.display = 'block';
                let dupType = '—';
                if (receipt.status === 'EXACT_DUPLICATE') dupType = 'Exact Duplicate';
                else if (receipt.status === 'SEMANTIC_DUPLICATE') dupType = 'Semantic Duplicate';
                document.getElementById('detail-duptype').textContent = dupType;
                document.getElementById('detail-dupscore').textContent = receipt.duplicate_score !== null ? receipt.duplicate_score : '—';
                document.getElementById('detail-dupreason').textContent = receipt.duplicate_reason || '—';
            } else {
                section.style.display = 'none';
            }
        }

        function showPolicySection(receipt) {
            const section = document.getElementById('policySection');
            if (receipt.policy_status || receipt.policy_result_json) {
                section.style.display = 'block';
                if (receipt.policy_status) {
                    document.getElementById('detail-polstatus').textContent = receipt.policy_status;
                    document.getElementById('detail-polstatus').className = 'detail-value status-badge ' + getStatusClass(receipt.policy_status);
                }
            } else {
                section.style.display = 'none';
            }
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
            if (!notes) { alert('Please provide a reason for rejection.'); return; }
            await submitDecision('REJECTED', notes);
        }

        async function submitDecision(decision, notes) {
            const url = API_BASE + '/receipts/' + currentReceipt + '/decision/';
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
                    body: JSON.stringify({ decision: decision, notes: notes })
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

        function previewCurrentReceipt() {
            if (!currentReceipt) return;
            // Open the preview directly using HTTP URL, not blob URL
            // Teams/Browser handles the Content-Type natively
            window.open(`/finance/api/receipts/${currentReceipt}/preview/`, '_blank');
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

        function showDetailsModal() { document.getElementById('detailsModal').style.display = 'flex'; }
        function closeDetailsModal() { document.getElementById('detailsModal').style.display = 'none'; }
        function showPreviewModal() { document.getElementById('previewModal').style.display = 'flex'; }
        function closePreviewModal() { document.getElementById('previewModal').style.display = 'none'; }
        function showUploadModal() { document.getElementById('uploadModal').style.display = 'flex'; }
        function closeUploadModal() { document.getElementById('uploadModal').style.display = 'none'; }

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
            const s = (status || '').toLowerCase();
            if (s.includes('approved')) return 'status-approved';
            if (s.includes('rejected')) return 'status-rejected';
            if (s.includes('duplicate')) return 'status-duplicate';
            if (s.includes('unique')) return 'status-unique';
            if (s.includes('failed')) return 'status-failed';
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

        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>"""
    return Response(content=html, media_type="text/html")


# Documentation endpoint
@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with service info."""
    return {
        "service": "Expense Policy Agent - Teams Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "teams_messaging": "/api/messages",
            "finance_tab": "/finance/tab",
            "config": "/config",
            "docs": "/docs",
        },
    }


# Log startup
@app.on_event("startup")
async def startup_event():
    """Log when service starts."""
    logger.info("="*60)
    config.log_config_summary()
    logger.info("Expense Policy Agent Teams Service is ready")
    logger.info("Teams messaging endpoint: /api/messages")
    logger.info("="*60)


if __name__ == "__main__":
    import uvicorn

    config.log_config_summary()

    logger.info(f"Starting Teams service on {config.TEAMS_SERVICE_HOST}:{config.TEAMS_SERVICE_PORT}")

    uvicorn.run(
        "teams_service.main:app",
        host=config.TEAMS_SERVICE_HOST,
        port=config.TEAMS_SERVICE_PORT,
        reload=config.DEBUG,
        log_level="info",
    )
