/**
 * useNetworkStatus
 *
 * Lightweight hook to track online / offline state without requiring
 * @react-native-community/netinfo. It works by:
 *   - Wiring a response interceptor onto the shared axios instance that
 *     flips state to "online" on every successful response and to "offline"
 *     when an error has no `.response` (i.e. the request never reached the
 *     server — network down or DNS failure).
 *   - Providing a `checkOnline()` helper that can be called manually (e.g.
 *     after a user taps "Retry") which pings the backend health endpoint.
 *
 * The initial state is `null` (unknown) so callers can distinguish between
 * "we haven't made a request yet" and a confirmed offline state.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { AppState, type AppStateStatus } from 'react-native';
import { http, isNetworkError } from '../lib/http';

type NetworkStatus = 'online' | 'offline' | null;

// Module-level listeners so we share a single interceptor across hook instances.
type Listener = (status: NetworkStatus) => void;
const _listeners = new Set<Listener>();
let _currentStatus: NetworkStatus = null;

function _notify(status: NetworkStatus) {
  if (status === _currentStatus) return;
  _currentStatus = status;
  _listeners.forEach((fn) => fn(status));
}

// Install axios interceptors once.
let _interceptorsInstalled = false;
function _installInterceptors() {
  if (_interceptorsInstalled) return;
  _interceptorsInstalled = true;

  http.interceptors.response.use(
    (response) => {
      _notify('online');
      return response;
    },
    (error) => {
      if (isNetworkError(error)) {
        _notify('offline');
      } else if (error.response) {
        // Got a response → server is reachable even if it returned an error.
        _notify('online');
      }
      return Promise.reject(error);
    },
  );
}

export function useNetworkStatus(): NetworkStatus {
  const [status, setStatus] = useState<NetworkStatus>(_currentStatus);
  const appStateRef = useRef<AppStateStatus>(AppState.currentState);

  useEffect(() => {
    _installInterceptors();

    const listener: Listener = (s) => setStatus(s);
    _listeners.add(listener);

    // When the app comes back to the foreground, fire a lightweight ping so
    // the status updates quickly even if no regular API call has been made yet.
    const appStateSub = AppState.addEventListener('change', (next) => {
      const prev = appStateRef.current;
      appStateRef.current = next;
      if (prev.match(/inactive|background/) && next === 'active') {
        pingHealth();
      }
    });

    return () => {
      _listeners.delete(listener);
      appStateSub.remove();
    };
  }, []);

  return status;
}

/** Fire-and-forget lightweight health check. */
export function pingHealth(): void {
  http
    .get('/health', { timeout: 5_000 })
    .then(() => _notify('online'))
    .catch((err) => {
      if (isNetworkError(err)) _notify('offline');
    });
}

/**
 * Imperative helper for manual "Retry" buttons:
 * pings the health endpoint and returns the new status.
 */
export async function checkOnline(): Promise<boolean> {
  try {
    await http.get('/health', { timeout: 5_000 });
    _notify('online');
    return true;
  } catch (err) {
    if (isNetworkError(err)) _notify('offline');
    return false;
  }
}
