import { useEffect, useRef } from 'react';
import { useReceiptUpload } from '../hooks/useReceiptUpload';
import { useUserManual } from '../hooks/useUserManual';
import ChatMessage from '../components/ChatMessage';
import FileUploadArea from '../components/FileUploadArea';
import UserManualModal from '../components/UserManualModal';
import '../styles/upload.css';

export default function UploadPage() {
  const [state, actions] = useReceiptUpload();
  const { state: manualState, open: openManual, close: closeManual, retry: retryManual } = useUserManual();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Auto-open manual if ?manual=true parameter is present
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('manual') === 'true' && !manualState.isOpen) {
      openManual();
    }
  }, []); // Empty dependency array ensures this runs only once on mount

  useEffect(() => {
    scrollToBottom();
  }, [state.messages]);

  const handleCategorySelect = async (receiptId: string, category: string, fileName: string) => {
    await actions.selectCategory(receiptId, category, fileName);
  };

  return (
    <div className="upload-container">
      <div className="upload-wrapper">
        {/* Header */}
        <div className="upload-header">
          <div className="header-icon">📄</div>
          <span className="header-label">Expense Management</span>
          <h1 className="header-title">Upload Your Receipt</h1>
          <p className="header-subtitle">
            We'll extract the details, validate the expense and prepare it for Finance review.
          </p>
          <button
            className="upload-header-manual-btn"
            onClick={openManual}
            aria-label="Open user manual"
            title="View user manual"
          >
            📖 User Manual
          </button>
        </div>

        {/* Process Steps */}
        <div className="process-steps">
          <div className="step-card">
            <div className="step-number">01</div>
            <div className="step-icon">📤</div>
            <div className="step-title">Upload</div>
          </div>
          <div className="step-card">
            <div className="step-number">02</div>
            <div className="step-icon">⚙️</div>
            <div className="step-title">We Process</div>
          </div>
          <div className="step-card">
            <div className="step-number">03</div>
            <div className="step-icon">✓</div>
            <div className="step-title">Finance Reviews</div>
          </div>
        </div>

        <div className="chat-container">
          <div className="chat-messages">
            {state.messages.map(message => (
              <ChatMessage
                key={message.id}
                message={message}
                onCategorySelect={handleCategorySelect}
                isSelectingCategory={state.isLoadingCategories}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>

          <FileUploadArea
            selectedFiles={state.selectedFiles}
            onFileSelect={actions.addFile}
            onFileRemove={actions.removeFile}
            onUpload={actions.uploadFiles}
            onClear={actions.clearMessages}
            isUploading={state.isUploading}
          />
        </div>
      </div>

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
