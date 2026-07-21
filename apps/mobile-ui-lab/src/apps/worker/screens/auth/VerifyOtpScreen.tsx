import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { getApiError } from '../../../../shared/lib/get-api-error';
import { authStorage } from '../../../../shared/lib/auth-storage';
import { authService } from '../../../../shared/services/auth.service';
import { workerOnboardingService } from '../../../../shared/services/worker-onboarding.service';
import { useAuthStore } from '../../../../shared/store/auth.store';
import type { WorkerAuthStackParamList } from '../../navigation/types';
import { C, authStyles as baseStyles } from './styles';

const OTP_LENGTH = 6;
type Props = NativeStackScreenProps<WorkerAuthStackParamList, 'VerifyOtp'>;

export default function VerifyOtpScreen({ route }: Props) {
  const { phone, devOtp } = route.params;
  const { setAuth } = useAuthStore();
  const inputRef = useRef<TextInput>(null);
  const [code, setCode] = useState('');
  const [displayOtp, setDisplayOtp] = useState(devOtp);
  const [isPending, setIsPending] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [cooldown, setCooldown] = useState(30);
  const digits = Array.from({ length: OTP_LENGTH }, (_, i) => code[i] ?? '');
  const isValid = code.length === OTP_LENGTH;
  const maskedPhone = phone.length > 4
    ? `${phone.slice(0, 4)} ${phone.slice(4, 6)} ****${phone.slice(-3)}`
    : phone;

  // Start cooldown on mount so the first resend is not immediately available.
  useEffect(() => {
    if (cooldown <= 0) return;
    const id = setInterval(() => setCooldown((s) => (s <= 1 ? 0 : s - 1)), 1000);
    return () => clearInterval(id);
  }, [cooldown]);

  useEffect(() => {
    const t = setTimeout(() => inputRef.current?.focus(), 250);
    return () => clearTimeout(t);
  }, []);

  const handleVerify = async () => {
    if (!isValid) {
      Alert.alert('Invalid code', 'Please enter the 6-digit code sent to your phone.');
      return;
    }
    Keyboard.dismiss();
    setIsPending(true);
    try {
      const tokens = await authService.verifyOtp({ phone, code, role: 'worker' });
      await authStorage.setTokens(tokens.access_token, tokens.refresh_token);
      const user = {
        id:    tokens.user.id,
        phone: tokens.user.phone,
        email: tokens.user.email,
        name:  tokens.user.name ?? null,
        role:  tokens.user.role,
      };
      await authStorage.setUser(user);

      let onboardingStep: string | null = null;
      try {
        const status = await workerOnboardingService.getStatus();
        onboardingStep = status.onboarding_step;
      } catch {
        // status check failed — treat as fresh onboarding
      }
      await authStorage.setOnboardingStep(onboardingStep);

      const biometricSetupDone = await authStorage.getBiometricSetupDone();

      setAuth({
        accessToken:  tokens.access_token,
        refreshToken: tokens.refresh_token,
        user,
        isProfileComplete: false, // RootNavigator biometric gate sets this to true
        onboardingStep,
        biometricSetupDone: biometricSetupDone ?? false,
      });

      // RootNavigator now gates the current legal version, then resumes the
      // correct onboarding, review, biometric, or application route.
    } catch (err) {
      Alert.alert('Error', getApiError(err, 'Invalid code. Please try again.'));
    } finally {
      setIsPending(false);
    }
  };

  const handleResend = async () => {
    if (isResending || cooldown > 0) return;
    setIsResending(true);
    try {
      const result = await authService.requestOtp({ phone, role: 'worker' });
      const newOtp = result?.otp ?? '';
      setDisplayOtp(newOtp);
      setCode('');
      setCooldown(30);
      Alert.alert('Code sent', 'A new verification code has been sent.');
    } catch (err) {
      Alert.alert('Error', getApiError(err, 'Failed to resend code.'));
    } finally {
      setIsResending(false);
    }
  };

  return (
    <SafeAreaView style={baseStyles.root} edges={['top', 'bottom']}>
      <KeyboardAvoidingView style={baseStyles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={baseStyles.page}>

          <Text style={baseStyles.heading}>Check your SMS</Text>
          <Text style={baseStyles.subheading}>6-digit code sent to +91 {maskedPhone}</Text>

          {__DEV__ && !!displayOtp && (
            <Pressable style={local.devBanner} onPress={() => setCode(displayOtp.slice(0, OTP_LENGTH))}>
              <Text style={local.devBannerText}>Dev OTP: {displayOtp} (tap to fill)</Text>
            </Pressable>
          )}

          <Pressable style={local.boxesRow} onPress={() => inputRef.current?.focus()}>
            {digits.map((digit, index) => {
              const filled = digit !== '';
              return (
                <View key={index} style={[local.box, filled && local.boxFilled]}>
                  <Text style={[local.dot, filled && local.dotFilled]}>{filled ? '*' : ''}</Text>
                </View>
              );
            })}
          </Pressable>

          <TextInput
            ref={inputRef}
            style={local.hiddenInput}
            value={code}
            onChangeText={(v) => setCode(v.replace(/\D/g, '').slice(0, OTP_LENGTH))}
            keyboardType="number-pad"
            maxLength={OTP_LENGTH}
            caretHidden
          />

          <View style={baseStyles.spacer} />

          <Pressable
            style={({ pressed }) => [
              baseStyles.button,
              isValid && baseStyles.buttonPrimary,
              (!isValid || isPending) && baseStyles.buttonDisabled,
              pressed && isValid && baseStyles.buttonPressed,
            ]}
            onPress={handleVerify}
            disabled={!isValid || isPending}
          >
            {isPending ? (
              <ActivityIndicator size="small" color={C.btnText} />
            ) : (
              <Text style={[baseStyles.buttonText, isValid && baseStyles.buttonTextPrimary]}>
                Verify
              </Text>
            )}
          </Pressable>

          <View style={local.resendRow}>
            <Text style={local.resendText}>Did not get it? </Text>
            <Pressable onPress={handleResend} disabled={isResending || cooldown > 0}>
              <Text style={[local.resendLink, (isResending || cooldown > 0) && local.resendLinkDisabled]}>
                {isResending ? 'Sending...' : cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend'}
              </Text>
            </Pressable>
          </View>

        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const local = StyleSheet.create({
  boxesRow: {
    flexDirection: 'row',
    gap: 10,
  },
  box: {
    flex: 1,
    maxWidth: 54,
    height: 52,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: C.border,
    backgroundColor: C.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  boxFilled: {
    borderColor: C.brand,
    backgroundColor: C.surfaceAlt,
  },
  dot: {
    color: C.muted,
    fontSize: 22,
    fontWeight: '900',
  },
  dotFilled: {
    color: C.brand,
  },
  hiddenInput: {
    position: 'absolute',
    width: 0,
    height: 0,
    opacity: 0,
  },
  resendRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 12,
  },
  resendText: {
    color: C.muted,
    fontSize: 13,
  },
  resendLink: {
    color: C.brand,
    fontSize: 13,
    fontWeight: '800',
    textDecorationLine: 'underline',
  },
  resendLinkDisabled: {
    color: C.muted,
    textDecorationLine: 'none',
    fontWeight: '500',
  },
  devBanner: {
    borderWidth: 1,
    borderColor: C.accent,
    backgroundColor: C.accentSoft,
    borderRadius: 10,
    padding: 10,
    marginBottom: 16,
  },
  devBannerText: {
    color: C.ink,
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center',
  },
});
