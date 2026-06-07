import { useEffect } from 'react';
import * as Notifications from 'expo-notifications';
import type { NavigationContainerRefWithCurrent } from '@react-navigation/native';
import type { ParamListBase } from '@react-navigation/native';

/**
 * Configure foreground notification display once at module load.
 * Notifications arriving while the app is open will show a banner, play a
 * sound, and update the badge.
 */
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

/**
 * Notification data shape sent by the backend:
 *   { screen: 'HomeTab' | 'JobsTab' | 'ComplaintsTab' | 'AttendanceTab' }
 *
 * The backend is responsible for using the correct tab name for each variant.
 */
function navigateFromData(
  navigationRef: NavigationContainerRefWithCurrent<ParamListBase>,
  data: Record<string, unknown>,
): void {
  const raw = typeof data?.screen === 'string' ? data.screen : null;
  if (!raw) return;
  if (!navigationRef.isReady()) return;
  // Backend still sends 'JobsTab' — remap to HomeTab since the tab was removed
  const screen = raw === 'JobsTab' ? 'HomeTab' : raw;
  navigationRef.navigate(screen as never);
}

/**
 * Wires up:
 * - Foreground notification display (via `setNotificationHandler` above)
 * - Tap-on-notification navigation using the provided navigation ref
 *
 * Also handles the case where the app was killed and relaunched via a
 * notification tap (lastNotificationResponse).
 */
export function useNotificationHandlers(
  navigationRef: NavigationContainerRefWithCurrent<ParamListBase>,
): void {
  useEffect(() => {
    // Handle taps on notifications that arrive while the app is running
    const responseSub = Notifications.addNotificationResponseReceivedListener((response) => {
      const data = response.notification.request.content.data as Record<string, unknown>;
      navigateFromData(navigationRef, data);
    });

    return () => {
      responseSub.remove();
    };
  }, [navigationRef]);

  // Handle cold-start via notification tap (app was not running)
  useEffect(() => {
    Notifications.getLastNotificationResponseAsync().then((response) => {
      if (!response) return;
      const data = response.notification.request.content.data as Record<string, unknown>;
      // Navigation container may not be ready yet — defer to next frame
      const timer = setTimeout(() => navigateFromData(navigationRef, data), 0);
      return () => clearTimeout(timer);
    });
  }, [navigationRef]);
}
