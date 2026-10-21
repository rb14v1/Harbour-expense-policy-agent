import { useState, useCallback } from 'react';
import {
  uploadReceipt,
  getReceiptStatus,
  getReceiptDetail,
  setCategory,
  getCategories
} from '../api/receiptAPI';
import type { ReceiptDetail, ReceiptStatus } from '../types/Receipt';

const CATEGORY_CONFIDENCE_THRESHOLD = 0.75;
const MAX_FILE_SIZE_MB = 50;
const MAX_POLLING_ATTEMPTS = 30;
const POLL_INTERVAL_MS = 1000;

export interface UploadMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  type: 'text' | 'attachment' | 'loading' | 'result' | 'category-selector';
  receiptId?: string;
  fileName?: string;
  receipt?: ReceiptDetail;
  categories?: string[];
}

export interface UseReceiptUploadState {
  messages: UploadMessage[];
  selectedFiles: File[];
  isUploading: boolean;
  isLoadingCategories: boolean;
}

export interface UseReceiptUploadActions {
  addFile: (file: File) => void;
  removeFile: (index: number) => void;
  clearFiles: () => void;
  uploadFiles: () => Promise<void>;
  clearMessages: () => void;
  selectCategory: (receiptId: string, category: string, fileName: string) => Promise<void>;
}

export function useReceiptUpload(): [UseReceiptUploadState, UseReceiptUploadActions] {
  const [messages, setMessages] = useState<UploadMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hi! I'm your Expense Policy Assistant. Send me your expense receipt (PDF, JPG, or PNG) and I'll process it for you.",
      type: 'text'
    }
  ]);

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingCategories, setIsLoadingCategories] = useState(false);

  const addMessage = useCallback((message: UploadMessage) => {
    setMessages(prev => [...prev, message]);
  }, []);

  const removeMessage = useCallback((id: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== id));
  }, []);

  const updateMessage = useCallback((id: string, updates: Partial<UploadMessage>) => {
    setMessages(prev =>
      prev.map(msg => (msg.id === id ? { ...msg, ...updates } : msg))
    );
  }, []);

  const addFile = useCallback((file: File) => {
    setSelectedFiles(prev => {
      if (!prev.some(f => f.name === file.name && f.size === file.size)) {
        return [...prev, file];
      }
      return prev;
    });
  }, []);

  const removeFile = useCallback((index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  const clearFiles = useCallback(() => {
    setSelectedFiles([]);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: '👋 Chat cleared. Ready for new receipts!',
        type: 'text'
      }
    ]);
    clearFiles();
  }, [clearFiles]);

  const pollReceiptStatus = useCallback(
    async (receiptId: string, fileName: string): Promise<ReceiptDetail | null> => {
      let attempts = 0;
      while (attempts < MAX_POLLING_ATTEMPTS) {
        try {
          const status = await getReceiptStatus(receiptId);
          if (
            ['APPROVED', 'REJECTED', 'NEEDS_REVIEW', 'EXACT_DUPLICATE', 'SEMANTIC_DUPLICATE', 'FAILED'].includes(
              status.status
            )
          ) {
            const receipt = await getReceiptDetail(receiptId);
            return receipt;
          }
          attempts++;
          await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS));
        } catch (error) {
          attempts++;
          if (attempts >= MAX_POLLING_ATTEMPTS) {
            throw new Error('Unable to retrieve processing status. Please refresh and try again.');
          }
          await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS));
        }
      }
      throw new Error('Receipt processing is taking longer than expected. Please refresh to check the status.');
    },
    []
  );

  const handleReceiptResult = useCallback(
    async (receipt: ReceiptDetail, fileName: string) => {
      const categoryConfidence = receipt.category_confidence || 0;
      if (
        categoryConfidence < CATEGORY_CONFIDENCE_THRESHOLD &&
        !['EXACT_DUPLICATE', 'SEMANTIC_DUPLICATE', 'FAILED'].includes(receipt.status)
      ) {
        addMessage({
          id: `category-prompt-${receipt.id}`,
          role: 'assistant',
          content: `I couldn't confidently determine the expense category for ${fileName}. Please select one:`,
          type: 'text'
        });
        try {
          setIsLoadingCategories(true);
          const categories = await getCategories();
          addMessage({
            id: `category-selector-${receipt.id}`,
            role: 'assistant',
            content: '',
            type: 'category-selector',
            receiptId: receipt.id,
            fileName,
            categories
          });
        } catch (error) {
          addMessage({
            id: `category-error-${receipt.id}`,
            role: 'assistant',
            content: 'Could not load categories. Please refresh the page.',
            type: 'text'
          });
        } finally {
          setIsLoadingCategories(false);
        }
      } else {
        addMessage({
          id: `result-${receipt.id}`,
          role: 'assistant',
          content: '',
          type: 'result',
          receipt,
          fileName
        });
      }
    },
    [addMessage]
  );

  const uploadSingleReceipt = useCallback(
    async (file: File) => {
      const processingMsgId = `processing-${Date.now()}-${Math.random()}`;

      addMessage({
        id: processingMsgId,
        role: 'assistant',
        content: `Processing ${file.name}...`,
        type: 'loading',
        fileName: file.name
      });

      try {
        const uploadResponse = await uploadReceipt(file);

        if (uploadResponse.status === 'EXACT_DUPLICATE') {
          removeMessage(processingMsgId);
          addMessage({
            id: `error-${uploadResponse.receipt_id}`,
            role: 'assistant',
            content: `⚠️ ${file.name}: ${uploadResponse.message}`,
            type: 'text'
          });
        } else {
          const receipt = await pollReceiptStatus(uploadResponse.receipt_id, file.name);
          removeMessage(processingMsgId);

          if (receipt) {
            await handleReceiptResult(receipt, file.name);
          }
        }
      } catch (error) {
        removeMessage(processingMsgId);

        const errorMessage = error instanceof Error ? error.message : 'Error uploading file';
        addMessage({
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `❌ ${file.name}: ${errorMessage}`,
          type: 'text'
        });
      }
    },
    [addMessage, removeMessage, pollReceiptStatus, handleReceiptResult]
  );

  const uploadFiles = useCallback(async () => {
    const filesToProcess = selectedFiles.filter(file => {
      const maxSizeBytes = MAX_FILE_SIZE_MB * 1024 * 1024;
      if (file.size > maxSizeBytes) {
        addMessage({
          id: `size-warning-${file.name}`,
          role: 'assistant',
          content: `⚠️ ${file.name} is too large (${(file.size / 1024 / 1024).toFixed(2)} MB). Maximum allowed is ${MAX_FILE_SIZE_MB} MB.`,
          type: 'text'
        });
        return false;
      }
      return true;
    });

    if (filesToProcess.length === 0) {
      if (selectedFiles.length === 0) {
        addMessage({
          id: `no-files-${Date.now()}`,
          role: 'assistant',
          content: 'Please select at least one receipt file.',
          type: 'text'
        });
      }
      return;
    }

    setIsUploading(true);

    // Show user attachments
    filesToProcess.forEach(file => {
      const fileType = file.type === 'application/pdf' ? 'PDF' : file.type === 'image/jpeg' ? 'JPG' : 'PNG';
      const fileSize = (file.size / 1024 / 1024).toFixed(2);

      addMessage({
        id: `attachment-${file.name}`,
        role: 'user',
        content: `📄 ${file.name} • ${fileType} • ${fileSize} MB`,
        type: 'attachment'
      });
    });

    // Upload each file
    for (const file of filesToProcess) {
      await uploadSingleReceipt(file);
    }

    setSelectedFiles([]);
    setIsUploading(false);
  }, [selectedFiles, addMessage, uploadSingleReceipt]);

  const selectCategory = useCallback(
    async (receiptId: string, category: string, fileName: string) => {
      if (!category) {
        addMessage({
          id: `category-empty-${Date.now()}`,
          role: 'assistant',
          content: 'Please select a category.',
          type: 'text'
        });
        return;
      }

      try {
        const receipt = await setCategory(receiptId, category);

        if (!receipt || !receipt.id) {
          throw new Error('Invalid response: receipt data missing');
        }

        removeMessage(`category-selector-${receiptId}`);
        removeMessage(`category-prompt-${receiptId}`);

        addMessage({
          id: `result-${receipt.id}`,
          role: 'assistant',
          content: '',
          type: 'result',
          receipt,
          fileName
        });
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Error saving category';
        addMessage({
          id: `category-error-${Date.now()}`,
          role: 'assistant',
          content: `❌ Failed to save category: ${errorMessage}`,
          type: 'text'
        });
      }
    },
    [addMessage, removeMessage]
  );

  return [
    {
      messages,
      selectedFiles,
      isUploading,
      isLoadingCategories
    },
    {
      addFile,
      removeFile,
      clearFiles,
      uploadFiles,
      clearMessages,
      selectCategory
    }
  ];
}
