import { useState } from 'react';
import { ActivityIndicator, Alert, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Fingerprint } from 'lucide-react-native';
import * as LocalAuthentication from 'expo-local-authentication';

import { authStorage } from '../../../../shared/lib/auth-storage';
import { useAuthStore } from '../../../../shared/store/auth.store';
import { C, authStyles as baseStyles } from './styles';

/**
 * Shown on every login session for approved workers who have completed
 * the one-time BiometricSetupScreen.
 *
 * Sets isProfileComplete = true for the current session so RootNavigator
 * transitions to AppNavigator. Does NOT mutate onboardingStep or storage.
 *
 * Fallback: if biometrics are unavailable or the worker dismisses them,
 * "Sign in with OTP" clears the session and returns to the Login screen.
 */
export default function BiometricCheckScreen() {
  const { setProfileComplete, clearAuth } = useAuthStore();
  const [isPending, setIsPending] = useState(false);

  const handleUnlock = async () => {
    // In Expo Go (dev) biometrics are unavailable — skip straight through.
    if (__DEV__) {
      setProfileComplete(true);
      return;
    }

    setIsPending(true);
    try {
      const hasHardware = await LocalAuthentication.hasHardwareAsync();
      const isEnrolled  = await LocalAuthentication.isEnrolledAsync();

      if (!hasHardware || !isEnrolled) {
        // Device has no enrolled biometrics — the worker already went through
        // BiometricSetupScreen which confirmed this. Just let them in silently.
        setProfileComplete(true);
        return;
      }

      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Unlock Annai Illam',
        cancelLabel: 'Cancel',
        fallbackLabel: 'Use device passcode',
        disableDeviceFallback: false,
      });

      if (result.success) {
        setProfileComplete(true);
      } else {
        // error codes: user_cancel, system_cancel, not_enrolled, lockout, etc.
        const reason = (result as any).error ?? '';
        const message = reason === 'not_enrolled'
          ? 'Face ID is not enrolled on this device. Go to iOS Settings → Face ID & Passcode to set it up.'
          : reason === 'lockout'
          ? 'Too many failed attempts. Please use your device passcode or try again later.'
          : 'Biometric verification was cancelled. You can try again or sign in with OTP.';

        Alert.alert('Unlock not completed', message, [
          { text: 'Try again', style: 'cancel' },
          { text: 'Use OTP instead', onPress: handleUseOtp },
        ]);
      }
    } catch {
      Alert.alert(
        'Unlock failed',
        'Could not verify your identity. Try again or sign in with OTP.',
        [
          { text: 'Try again', style: 'cancel' },
          { text: 'Use OTP instead', onPress: handleUseOtp },
        ],
      );
    } finally {
      setIsPending(false);
    }
  };

  const handleUseOtp = async () => {
    await authStorage.clear();
    clearAuth(); // RootNavigator sees accessToken = null → shows AuthNavigator
  };

  return (
    <SafeAreaView style={baseStyles.root} edges={['top', 'bottom']}>
      <View style={baseStyles.page}>

        <View style={local.iconRing}>
          <Fingerprint size={40} color={C.brand} strokeWidth={1.5} />
        </View>

        <Text style={[baseStyles.heading, baseStyles.centerHeading]}>
          Confirm it is you
        </Text>
        <Text style={[baseStyles.subheading, baseStyles.centerText]}>
          Use biometrics to securely access your shifts and assignments.
        </Text>

        <View style={local.spacer} />

        <Pressable
          style={({ pressed }) => [
            baseStyles.button,
            baseStyles.buttonPrimary,
            pressed && baseStyles.buttonPressed,
            isPending && baseStyles.buttonDisabled,
          ]}
          onPress={handleUnlock}
          disabled={isPending}
          accessibilityLabel="Unlock with biometrics"
        >
          {isPending ? (
            <ActivityIndicator color={C.btnText} />
          ) : (
            <Text style={[baseStyles.buttonText, baseStyles.buttonTextPrimary]}>
              Unlock with biometrics
            </Text>
          )}
        </Pressable>

        <Pressable
          style={({ pressed }) => [local.otpLink, pressed && { opacity: 0.5 }]}
          onPress={handleUseOtp}
          accessibilityLabel="Sign in with OTP instead"
        >
          <Text style={local.otpLinkText}>Sign in with OTP instead</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const local = StyleSheet.create({
  iconRing: {
    width: 86,
    height: 86,
    borderRadius: 43,
    borderWidth: 2,
    borderColor: C.brand,
    backgroundColor: '#f4f1e8',
    alignSelf: 'center',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 40,
    marginBottom: 24,
  },
  spacer: {
    flex: 1,
  },
  otpLink: {
    alignSelf: 'center',
    marginTop: 16,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  otpLinkText: {
    fontSize: 14,
    color: C.muted,
    textDecorationLine: 'underline',
  },
});
