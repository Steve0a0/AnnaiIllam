import { useState } from 'react';
import { ActivityIndicator, Alert, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Fingerprint, ShieldCheck } from 'lucide-react-native';
import * as LocalAuthentication from 'expo-local-authentication';

import { authStorage } from '../../../../shared/lib/auth-storage';
import { useAuthStore } from '../../../../shared/store/auth.store';
import { C, authStyles as baseStyles } from './styles';

/**
 * Shown exactly ONCE after admin approves the worker for the first time.
 * Sets biometricSetupDone = true, then opens the dashboard by setting
 * isProfileComplete = true (RootNavigator switches to AppNavigator).
 *
 */
export default function BiometricSetupScreen() {
  const { setBiometricSetupDone, setProfileComplete } = useAuthStore();
  const [isPending, setIsPending] = useState(false);

  const handleEnable = async () => {
    setIsPending(true);
    try {
      const hasHardware = await LocalAuthentication.hasHardwareAsync();

      if (!hasHardware) {
        // Device has no biometric sensor — skip setup and proceed directly.
        await authStorage.setBiometricSetupDone(true);
        setBiometricSetupDone(true);
        setProfileComplete(true);
        return;
      }

      // Do NOT pre-check isEnrolledAsync. Calling authenticateAsync with
      // disableDeviceFallback: false lets iOS/Android present Face ID,
      // fingerprint, or device PIN as appropriate. A separate isEnrolled guard
      // blocks PIN-only devices and prevents Face ID from appearing on iOS.
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Set up biometric access',
        cancelLabel: 'Cancel',
        fallbackLabel: 'Use device passcode',
        disableDeviceFallback: false,
      });

      if (!result.success) {
        Alert.alert('Biometric setup cancelled', 'Biometric access was not enabled.');
        return;
      }

      await authStorage.setBiometricSetupDone(true);
      setBiometricSetupDone(true);
      setProfileComplete(true);
    } catch {
      Alert.alert('Biometric setup failed', 'Could not enable biometric access. Please try again.');
    } finally {
      setIsPending(false);
    }
  };

  return (
    <SafeAreaView style={baseStyles.root} edges={['top', 'bottom']}>
      <View style={baseStyles.page}>

        <View style={local.iconRing}>
          <Fingerprint size={40} color={C.brand} strokeWidth={1.5} />
        </View>

        <Text style={[baseStyles.heading, baseStyles.centerHeading]}>
          Set up biometrics
        </Text>
        <Text style={[baseStyles.subheading, baseStyles.centerText]}>
          Use Face ID or your fingerprint to sign in quickly and securely every time you open the app.
        </Text>

        <View style={local.featureList}>
          <FeatureRow text="Keeps your account secure" />
          <FeatureRow text="No password to remember" />
          <FeatureRow text="Works with Face ID and fingerprint" />
        </View>

        <View style={baseStyles.spacer} />

        <Pressable
          style={({ pressed }) => [
            baseStyles.button,
            baseStyles.buttonPrimary,
            isPending && baseStyles.buttonDisabled,
            pressed && baseStyles.buttonPressed,
          ]}
          onPress={handleEnable}
          disabled={isPending}
        >
          {isPending ? (
            <ActivityIndicator size="small" color={C.btnText} />
          ) : (
            <Text style={[baseStyles.buttonText, baseStyles.buttonTextPrimary]}>
              Enable biometrics
            </Text>
          )}
        </Pressable>

        <Text style={local.helperText}>
          This step is required after admin approval. Annai Illam never stores your fingerprint or face data.
        </Text>

      </View>
    </SafeAreaView>
  );
}

function FeatureRow({ text }: { text: string }) {
  return (
    <View style={local.featureRow}>
      <ShieldCheck size={16} color={C.success} strokeWidth={2} />
      <Text style={local.featureText}>{text}</Text>
    </View>
  );
}

const local = StyleSheet.create({
  iconRing: {
    width: 96,
    height: 96,
    borderRadius: 28,
    borderWidth: 1.5,
    borderColor: C.border,
    backgroundColor: C.surfaceAlt,
    alignSelf: 'center',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 20,
    marginBottom: 24,
  },
  featureList: {
    marginTop: 8,
    gap: 12,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  featureText: {
    fontSize: 14,
    fontWeight: '600',
    color: C.ink,
    flex: 1,
  },
  helperText: {
    fontSize: 12,
    color: C.muted,
    textAlign: 'center',
    lineHeight: 18,
    marginTop: 14,
  },
});
