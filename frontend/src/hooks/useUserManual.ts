import { useState, useCallback } from 'react';
import { fetchUserManual } from '../api/manualAPI';

interface UserManualState {
  isOpen: boolean;
  content: string | null;
  isLoading: boolean;
  error: string | null;
}

export function useUserManual() {
  const [state, setState] = useState<UserManualState>({
    isOpen: false,
    content: null,
    isLoading: false,
    error: null,
  });

  const open = useCallback(async () => {
    setState(prev => ({
      ...prev,
      isOpen: true,
      isLoading: true,
      error: null,
    }));

    try {
      const content = await fetchUserManual();
      setState(prev => ({
        ...prev,
        content,
        isLoading: false,
        error: null,
      }));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load manual';
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
    }
  }, []);

  const close = useCallback(() => {
    setState(prev => ({
      ...prev,
      isOpen: false,
    }));
  }, []);

  const retry = useCallback(async () => {
    setState(prev => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const content = await fetchUserManual();
      setState(prev => ({
        ...prev,
        content,
        isLoading: false,
        error: null,
      }));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load manual';
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
    }
  }, []);

  return { state, open, close, retry };
}
