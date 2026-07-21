import { useEffect } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { NavigationContainer, useNavigationContainerRef } from '@react-navigation/native';
import { useAuthStore } from '../../../shared/store/auth.store';
import { authStorage } from '../../../shared/lib/auth-storage';
import { usePushToken } from '../../../shared/hooks/use-push-token';
import { useNotificationHandlers } from '../../../shared/hooks/use-notification-handlers';
import type { MobileUser } from '../../../shared/types/auth';
import type { ClientTabParamList } from './types';
import AuthNavigator from './AuthNavigator';
import AppNavigator from './AppNavigator';
import LegalAcceptanceGate from '../../../shared/screens/LegalAcceptanceGate';

type Props = {
  isDark: boolean;
  onToggleDark: () => void;
};

export default function RootNavigator({ isDark, onToggleDark }: Props) {
  const { accessToken, isProfileComplete, isHydrated, hydrateAuth } = useAuthStore();
  const navigationRef = useNavigationContainerRef<ClientTabParamList>();

  usePushToken(!!accessToken && isProfileComplete === true);
  useNotificationHandlers(navigationRef);

  useEffect(() => {
    const hydrate = async () => {
      try {
        const [access, refresh, user, profileComplete] = await Promise.all([
          authStorage.getAccessToken(),
          authStorage.getRefreshToken(),
          authStorage.getUser() as Promise<MobileUser | null>,
          authStorage.getIsProfileComplete(),
        ]);
        hydrateAuth({ accessToken: access, refreshToken: refresh, user, isProfileComplete: profileComplete });
      } catch {
        // Storage unavailable — boot unauthenticated
        hydrateAuth({ accessToken: null, refreshToken: null, user: null });
      }
    };
    hydrate();
  }, [hydrateAuth]);

  if (!isHydrated) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#fdf9f5' }}>
        <ActivityIndicator size="large" color="#203428" />
      </View>
    );
  }

  const isAuthenticated = !!accessToken;
  const showApp = isAuthenticated && isProfileComplete === true;

  if (!isAuthenticated) {
    return <NavigationContainer><AuthNavigator /></NavigationContainer>;
  }

  return (
    <LegalAcceptanceGate source="client_mobile">
      <NavigationContainer ref={navigationRef}>
        {showApp ? <AppNavigator /> : <AuthNavigator initialRouteName="ProfileSetup" />}
      </NavigationContainer>
    </LegalAcceptanceGate>
  );
}
