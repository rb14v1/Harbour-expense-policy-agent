export function escapeHtml(text: string | null | undefined): string {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return 'N/A';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  } catch {
    return dateStr || 'N/A';
  }
}

export function formatFileSize(bytes: number): string {
  return (bytes / 1024 / 1024).toFixed(2);
}

export function formatErrorMessage(backendError: string | null | undefined): string {
  if (!backendError || typeof backendError !== 'string') {
    return 'Upload failed. Please try again.';
  }

  const error = backendError.toLowerCase();

  if (error.includes('extraction failed') || error.includes("couldn't read")) {
    return "We couldn't read the receipt. The document may be blurry, unclear, or contain unreadable content. Please upload a clearer image or PDF.";
  }
  if (error.includes('empty') && !error.includes('extraction')) {
    return 'The uploaded file is empty. Please select a valid receipt.';
  }
  if (error.includes('too large') || error.includes('exceeds')) {
    const match = backendError.match(/(\d+(?:\.\d+)?)\s*(?:MB|mb)/);
    if (match) {
      return `File is too large (${match[1]} MB). Maximum allowed size is 50 MB.`;
    }
    return 'File is too large. Maximum allowed size is 50 MB.';
  }
  if (error.includes('unsupported') && error.includes('extension')) {
    return 'Unsupported file type. Please upload a PDF, JPG, JPEG, or PNG file.';
  }
  if (error.includes('unsupported')) {
    return 'Unsupported file type. Please upload a PDF, JPG, JPEG, or PNG file.';
  }
  if (error.includes('not appear to be a valid pdf')) {
    return 'The file does not appear to be a valid PDF. Please check the file and try again.';
  }
  if (error.includes('zero pages') || error.includes('empty pdf')) {
    return 'The PDF file is empty. Please upload a PDF with content.';
  }
  if (error.includes('corrupted') || error.includes('malformed')) {
    return 'The file appears to be corrupted. Please select a different file.';
  }
  if (error.includes('blank') || error.includes('mostly white')) {
    return 'The image appears to be blank or mostly white. Please upload an image with visible receipt content.';
  }
  if (error.includes('too small') || error.includes('invalid dimensions')) {
    return 'The image is too small. Please upload a higher resolution image.';
  }
  if (error.includes('not appear to be a valid')) {
    return 'The file does not appear to be a valid receipt image. Please check the file and try again.';
  }

  return `Upload failed: ${escapeHtml(backendError)}`;
}

export function getFileTypeLabel(mimeType: string): string {
  const typeMap: Record<string, string> = {
    'application/pdf': 'PDF',
    'image/jpeg': 'JPG',
    'image/png': 'PNG'
  };
  return typeMap[mimeType] || 'File';
}
