import axios from 'axios';

/**
 * Extracts a human-readable message from any thrown error.
 * Handles:
 *  - FastAPI 422 validation errors  (detail is an array of objects)
 *  - FastAPI/app HTTPException       (detail is a string)
 *  - Our envelope format             (message field on non-2xx)
 *  - Network / no-response errors
 */
export function getApiError(err: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (!axios.isAxiosError(err)) {
    return err instanceof Error ? err.message : fallback;
  }

  if (!err.response) {
    return 'Cannot reach server. Check your connection and try again.';
  }

  const data = err.response.data;

  // FastAPI validation error — detail is an array
  if (Array.isArray(data?.detail)) {
    const first = data.detail[0];
    if (first?.msg) return String(first.msg).replace(/^Value error,\s*/i, '');
    return fallback;
  }

  // Standard HTTPException / our app errors — detail is a string
  if (typeof data?.detail === 'string' && data.detail) {
    return data.detail;
  }

  // Envelope format { success: false, message: '...' }
  if (typeof data?.message === 'string' && data.message) {
    return data.message;
  }

  return `Server error (${err.response.status}). Please try again.`;
}
