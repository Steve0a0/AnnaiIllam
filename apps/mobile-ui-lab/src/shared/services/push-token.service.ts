import { Platform } from 'react-native';
import { http } from '../lib/http';

export const pushTokenService = {
  register: (token: string): Promise<unknown> =>
    http.post('/push-tokens', {
      token,
      platform: Platform.OS,
      app_variant: process.env.EXPO_PUBLIC_APP_VARIANT ?? 'worker',
    }),

  deactivate: (): Promise<unknown> => http.delete('/push-tokens'),
};
