import { useRef, useState } from 'react';
import { formatFileSize } from '../utils/formatting';

interface FileUploadAreaProps {
  selectedFiles: File[];
  onFileSelect: (file: File) => void;
  onFileRemove: (index: number) => void;
  onUpload: () => void;
  onClear: () => void;
  isUploading: boolean;
}

export default function FileUploadArea({
  selectedFiles,
  onFileSelect,
  onFileRemove,
  onUpload,
  onClear,
  isUploading
}: FileUploadAreaProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    files.forEach(file => onFileSelect(file));
  };

  const handleInputClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    try {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);
      const files = Array.from(e.dataTransfer.files || []);
      files.forEach(file => onFileSelect(file));
    } catch (error) {
      setIsDragOver(false);
    }
  };

  return (
    <div>
      {selectedFiles.length > 0 && (
        <div className="selected-files-list">
          {selectedFiles.map((file, index) => (
            <div key={`${file.name}-${file.size}`} className="selected-file-item">
              <div className="selected-file-item-info">
                <span className="selected-file-item-icon">📄</span>
                <div>
                  <div className="selected-file-item-name">{file.name}</div>
                  <div className="selected-file-item-size">{formatFileSize(file.size)} MB</div>
                </div>
              </div>
              <button
                type="button"
                className="remove-file-btn"
                onClick={() => onFileRemove(index)}
                disabled={isUploading}
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="chat-input-area">
        <div
          className={`file-input-wrapper ${isDragOver ? 'drag-over' : ''}`}
          onDragOver={handleDragOver}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <label htmlFor="receiptFiles" className="file-input-label" onClick={handleInputClick}>
            <span className="file-input-label-icon">📤</span>
            <span className="file-input-label-text">Drop your receipt here</span>
            <span className="file-input-label-hint">or browse files from your device</span>
            <span className="file-input-label-hint" style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>
              PDF, JPG or PNG • Up to 50 MB
            </span>
          </label>
          <input
            ref={fileInputRef}
            id="receiptFiles"
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            multiple
            onChange={handleFileInputChange}
            disabled={isUploading}
          />
        </div>
        <div className="button-group">
          <button
            type="button"
            className="send-button"
            onClick={onUpload}
            disabled={selectedFiles.length === 0 || isUploading}
          >
            {isUploading ? 'Processing...' : '📤 Upload'}
          </button>
          <button
            type="button"
            className="clear-button"
            onClick={onClear}
            disabled={isUploading}
          >
            Clear
          </button>
        </div>
      </div>
    </div>
  );
}
