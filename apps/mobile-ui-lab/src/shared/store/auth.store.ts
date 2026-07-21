import { create } from 'zustand';
import type { MobileUser } from '../types/auth';

type AuthState = {
  accessToken:        string | null;
  refreshToken:       string | null;
  user:               MobileUser | null;
  isHydrated:         boolean;
  isProfileComplete:  boolean | null;
  onboardingStep:     string | null;
  biometricSetupDone: boolean;

  setAuth: (data: {
    accessToken:         string;
    refreshToken:        string;
    user:                MobileUser;
    isProfileComplete?:  boolean | null;
    onboardingStep?:     string | null;
    biometricSetupDone?: boolean;
  }) => void;

  hydrateAuth: (data: {
    accessToken:         string | null;
    refreshToken:        string | null;
    user:                MobileUser | null;
    isProfileComplete?:  boolean | null;
    onboardingStep?:     string | null;
    biometricSetupDone?: boolean;
  }) => void;

  setOnboardingStep:     (step: string | null) => void;
  setProfileComplete:    (value: boolean)       => void;
  setBiometricSetupDone: (value: boolean)       => void;
  updateUser:            (patch: Partial<MobileUser>) => void;
  clearAuth:             ()                     => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken:        null,
  refreshToken:       null,
  user:               null,
  isHydrated:         false,
  isProfileComplete:  null,
  onboardingStep:     null,
  biometricSetupDone: false,

  setAuth: ({ accessToken, refreshToken, user, isProfileComplete = null, onboardingStep = null, biometricSetupDone = false }) =>
    set({ accessToken, refreshToken, user, isHydrated: true, isProfileComplete, onboardingStep, biometricSetupDone }),

  hydrateAuth: ({ accessToken, refreshToken, user, isProfileComplete = null, onboardingStep = null, biometricSetupDone = false }) =>
    set({ accessToken, refreshToken, user, isHydrated: true, isProfileComplete, onboardingStep, biometricSetupDone }),

  setOnboardingStep:     (step)  => set({ onboardingStep: step }),
  setProfileComplete:    (value) => set({ isProfileComplete: value }),
  setBiometricSetupDone: (value) => set({ biometricSetupDone: value }),
  updateUser:            (patch) => set((state) => ({
    user: state.user ? { ...state.user, ...patch } : state.user,
  })),

  clearAuth: () =>
    set({
      accessToken:        null,
      refreshToken:       null,
      user:               null,
      isHydrated:         true,
      isProfileComplete:  null,
      onboardingStep:     null,
      biometricSetupDone: false,
    }),
}));
