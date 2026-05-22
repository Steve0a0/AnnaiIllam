import * as SecureStore from 'expo-secure-store';
import { appVariantConfig } from '../config/app-variant';

const { storagePrefix: p } = appVariantConfig;

const KEYS = {
  accessToken:        `${p}_access_token`,
  refreshToken:       `${p}_refresh_token`,
  user:               `${p}_user`,
  onboardingStep:     `${p}_onboarding_step`,
  biometricSetupDone: `${p}_biometric_setup`,
  isProfileComplete:  `${p}_profile_complete`,
} as const;

export const authStorage = {
  setTokens: (access: string, refresh: string) =>
    Promise.all([
      SecureStore.setItemAsync(KEYS.accessToken, access),
      SecureStore.setItemAsync(KEYS.refreshToken, refresh),
    ]),

  getAccessToken: () => SecureStore.getItemAsync(KEYS.accessToken),
  getRefreshToken: () => SecureStore.getItemAsync(KEYS.refreshToken),

  setUser: (user: unknown) =>
    SecureStore.setItemAsync(KEYS.user, JSON.stringify(user)),

  getUser: async () => {
    const raw = await SecureStore.getItemAsync(KEYS.user);
    return raw ? JSON.parse(raw) : null;
  },

  setOnboardingStep: (step: string | null) =>
    step
      ? SecureStore.setItemAsync(KEYS.onboardingStep, step)
      : SecureStore.deleteItemAsync(KEYS.onboardingStep),

  getOnboardingStep: () => SecureStore.getItemAsync(KEYS.onboardingStep),

  setBiometricSetupDone: (value: boolean) =>
    value
      ? SecureStore.setItemAsync(KEYS.biometricSetupDone, 'true')
      : SecureStore.deleteItemAsync(KEYS.biometricSetupDone),

  getBiometricSetupDone: async () => {
    const raw = await SecureStore.getItemAsync(KEYS.biometricSetupDone);
    return raw === 'true';
  },

  setIsProfileComplete: (value: boolean) =>
    SecureStore.setItemAsync(KEYS.isProfileComplete, value ? 'true' : 'false'),

  getIsProfileComplete: async (): Promise<boolean | null> => {
    const raw = await SecureStore.getItemAsync(KEYS.isProfileComplete);
    if (raw === 'true') return true;
    if (raw === 'false') return false;
    return null;
  },

  clear: () =>
    Promise.all([
      SecureStore.deleteItemAsync(KEYS.accessToken),
      SecureStore.deleteItemAsync(KEYS.refreshToken),
      SecureStore.deleteItemAsync(KEYS.user),
      SecureStore.deleteItemAsync(KEYS.onboardingStep),
      SecureStore.deleteItemAsync(KEYS.biometricSetupDone),
      SecureStore.deleteItemAsync(KEYS.isProfileComplete),
    ]),
};
