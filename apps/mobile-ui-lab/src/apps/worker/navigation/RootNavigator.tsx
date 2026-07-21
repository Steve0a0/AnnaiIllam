import { useEffect } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { NavigationContainer, useNavigationContainerRef } from '@react-navigation/native';

import { authStorage } from '../../../shared/lib/auth-storage';
import { useAuthStore } from '../../../shared/store/auth.store';
import { usePushToken } from '../../../shared/hooks/use-push-token';
import { useNotificationHandlers } from '../../../shared/hooks/use-notification-handlers';
import type { MobileUser } from '../../../shared/types/auth';
import type { WorkerTabParamList } from './types';

import BiometricCheckScreen from '../screens/auth/BiometricCheckScreen';
import BiometricSetupScreen from '../screens/auth/BiometricSetupScreen';
import UnderReviewScreen    from '../screens/auth/UnderReviewScreen';
import AppNavigator         from './AppNavigator';
import AuthNavigator        from './AuthNavigator';
import LegalAcceptanceGate from '../../../shared/screens/LegalAcceptanceGate';

export default function RootNavigator() {
  const {
    accessToken,
    isHydrated,
    isProfileComplete,
    onboardingStep,
    biometricSetupDone,
    hydrateAuth,
  } = useAuthStore();

  // Navigation ref is passed only to the main AppNavigator container (step 5).
  // Pre-auth containers (auth, biometric, under-review) don't need tap-navigation.
  const navigationRef = useNavigationContainerRef<WorkerTabParamList>();

  usePushToken(isProfileComplete === true);
  useNotificationHandlers(navigationRef);

  useEffect(() => {
    const hydrate = async () => {
      try {
        const [access, refresh, user, step, biometricDone] = await Promise.all([
          authStorage.getAccessToken(),
          authStorage.getRefreshToken(),
          authStorage.getUser() as Promise<MobileUser | null>,
          authStorage.getOnboardingStep(),
          authStorage.getBiometricSetupDone(),
        ]);
        hydrateAuth({
          accessToken:        access,
          refreshToken:       refresh,
          user,
          onboardingStep:     step,
          biometricSetupDone: biometricDone,
          isProfileComplete:  false, // always false on cold launch; biometric check sets it true
        });
      } catch {
        hydrateAuth({ accessToken: null, refreshToken: null, user: null });
      }
    };
    hydrate();
  }, [hydrateAuth]);

  if (!isHydrated) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#f8f6f0' }}>
        <ActivityIndicator size="large" color="#203428" />
      </View>
    );
  }

  // Routing order:
  // 1. Not authenticated                       -> AuthNavigator
  // 2. profile_submitted                       -> UnderReviewScreen (waiting for admin)
  // 3. approved + no biometric setup           -> BiometricSetupScreen (one-time)
  // 4. approved + biometric set + not checked  -> BiometricCheckScreen (per session)
  // 5. approved + biometric set + checked      -> AppNavigator

  if (!accessToken) {
    return (
      <NavigationContainer>
        <AuthNavigator />
      </NavigationContainer>
    );
  }

  let authenticatedNavigator;
  if (onboardingStep === 'profile_submitted') {
    authenticatedNavigator = <NavigationContainer><UnderReviewScreen /></NavigationContainer>;
  } else if (onboardingStep === 'approved' && !biometricSetupDone) {
    authenticatedNavigator = <NavigationContainer><BiometricSetupScreen /></NavigationContainer>;
  } else if (onboardingStep === 'approved' && biometricSetupDone && !isProfileComplete) {
    authenticatedNavigator = <NavigationContainer><BiometricCheckScreen /></NavigationContainer>;
  } else {
    const onboardingRoute = onboardingStep === 'identity_uploaded' ? 'BuildProfile' : 'VerifyIdentity';
    authenticatedNavigator = (
      <NavigationContainer ref={navigationRef}>
        {isProfileComplete === true ? <AppNavigator /> : <AuthNavigator initialRouteName={onboardingRoute} />}
      </NavigationContainer>
    );
  }

  return <LegalAcceptanceGate source="worker_mobile">{authenticatedNavigator}</LegalAcceptanceGate>;
}
