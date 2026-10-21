import { useEffect, useRef } from 'react';
import '../styles/userManualModal.css';

interface UserManualModalProps {
  isOpen: boolean;
  content: string | null;
  isLoading: boolean;
  error: string | null;
  onClose: () => void;
  onRetry: () => void;
}

export default function UserManualModal({
  isOpen,
  content,
  isLoading,
  error,
  onClose,
  onRetry,
}: UserManualModalProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const handleEscapeKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscapeKey);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscapeKey);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!iframeRef.current || !content) return;

    const iframe = iframeRef.current;
    const handleIframeLoad = () => {
      try {
        const iframeDoc = iframe.contentDocument;
        if (!iframeDoc) return;

        const links = iframeDoc.querySelectorAll('a[href^="#"]');
        links.forEach(link => {
          link.addEventListener('click', (e: Event) => {
            e.preventDefault();
            const href = (link as HTMLAnchorElement).getAttribute('href');
            if (href && href.startsWith('#')) {
              const targetId = href.substring(1);
              const target = iframeDoc.getElementById(targetId);
              if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
              }
            }
          });
        });
      } catch (err) {
        console.error('Failed to setup iframe anchor links:', err);
      }
    };

    iframe.addEventListener('load', handleIframeLoad);
    return () => {
      iframe.removeEventListener('load', handleIframeLoad);
    };
  }, [content]);

  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="manual-modal-backdrop" onClick={handleBackdropClick}>
      <div className="manual-modal-container">
        <div className="manual-modal-header">
          <h2>📖 User Manual</h2>
          <button
            className="manual-modal-close-btn"
            onClick={onClose}
            aria-label="Close manual"
          >
            ✕
          </button>
        </div>

        <div className="manual-modal-content">
          {isLoading && (
            <div className="manual-loading">
              <div className="manual-spinner"></div>
              <p>Loading user manual...</p>
            </div>
          )}

          {error && !isLoading && (
            <div className="manual-error">
              <p className="manual-error-title">Failed to load manual</p>
              <p className="manual-error-message">{error}</p>
              <button className="manual-retry-btn" onClick={onRetry}>
                Try Again
              </button>
            </div>
          )}

          {content && !isLoading && !error && (
            <div className="manual-html-content">
              <iframe
                ref={iframeRef}
                srcDoc={content}
                title="User Manual"
                className="manual-iframe"
                sandbox="allow-same-origin"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
