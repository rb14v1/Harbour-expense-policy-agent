/**
 * User Manual API
 * Provides access to the User Manual from the Django backend
 */

export interface ManualInfo {
  available: boolean;
  last_updated?: string;
  size_bytes?: number;
  source?: string;
  error?: string;
}

/**
 * Fetch the user manual HTML content
 */
export async function fetchUserManual(): Promise<string> {
  const response = await fetch('/api/v1/user-manual/', {
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('User manual is not available');
    }
    throw new Error('Failed to load user manual');
  }

  return response.text();
}

/**
 * Check if user manual is available and get metadata
 */
export async function checkManualAvailability(): Promise<ManualInfo> {
  try {
    const response = await fetch('/api/v1/user-manual/info/', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });

    if (!response.ok) {
      if (response.status === 404) {
        return { available: false };
      }
      throw new Error('Failed to check manual availability');
    }

    return response.json();
  } catch {
    return { available: false };
  }
}
