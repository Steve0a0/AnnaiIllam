import { useEffect } from 'react';
import { Platform } from 'react-native';
import Constants from 'expo-constants';
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import { pushTokenService } from '../services/push-token.service';

async function requestAndRegister(): Promise<void> {
  // Expo push tokens only work on physical devices — skip simulators/emulators
  if (!Device.isDevice) return;

  // Android 13+ (API 33+) needs explicit POST_NOTIFICATIONS permission at runtime.
  // Also create a default notification channel (required for Android 8+).
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'Annai Illam',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#203428',
    });
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;
  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  // User denied — nothing to register
  if (finalStatus !== 'granted') return;

  const projectId = Constants.expoConfig?.extra?.eas?.projectId;
  const tokenData = await Notifications.getExpoPushTokenAsync(projectId ? { projectId } : undefined);
  await pushTokenService.register(tokenData.data);
}

/**
 * Requests push permission and registers the Expo push token with the backend.
 * Call this hook once the user is authenticated — it is a no-op when
 * `isAuthenticated` is false, and re-runs only when auth state changes.
 */
export function usePushToken(isAuthenticated: boolean): void {
  useEffect(() => {
    if (!isAuthenticated) return;

    requestAndRegister().catch(() => {
      // Non-fatal: push token failure must never break the app.
    });
  }, [isAuthenticated]);
}
