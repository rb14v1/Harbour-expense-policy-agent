import { useEffect, useRef } from 'react';
import { useReceiptUpload } from '../hooks/useReceiptUpload';
import ChatMessage from '../components/ChatMessage';
import FileUploadArea from '../components/FileUploadArea';
import '../styles/upload.css';

export default function UploadPage() {
  const [state, actions] = useReceiptUpload();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

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
    </div>
  );
}
