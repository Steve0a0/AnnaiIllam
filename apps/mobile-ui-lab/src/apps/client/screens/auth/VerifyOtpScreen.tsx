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
import { authService } from '../../../../shared/services/auth.service';
import { authStorage } from '../../../../shared/lib/auth-storage';
import { clientProfileService } from '../../../../shared/services/client-profile.service';
import { useAuthStore } from '../../../../shared/store/auth.store';
import { getApiError } from '../../../../shared/lib/get-api-error';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';
import type { ClientAuthStackParamList } from '../../navigation/types';

const C = {
  bg: '#f8f6f0',
  surface: '#fffdf8',
  surfaceAlt: '#f4f1e8',
  brand: '#203428',
  ink: '#17211a',
  muted: '#687267',
  border: '#ddd3be',
  accent: '#c96f3c',
  accentSoft: '#f0dfd3',
  btnText: '#fffdf8',
} as const;

const OTP_LENGTH = 6;

type Props = {
  navigation: NativeStackNavigationProp<ClientAuthStackParamList, 'VerifyOtp'>;
  route: RouteProp<ClientAuthStackParamList, 'VerifyOtp'>;
};

export default function VerifyOtpScreen({ route }: Props) {
  const { phone, devOtp } = route.params;
  const { setAuth } = useAuthStore();
  const inputRef = useRef<TextInput>(null);
  const [code, setCode] = useState('');
  const [displayOtp, setDisplayOtp] = useState(devOtp);
  const [isPending, setIsPending] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [cooldown, setCooldown] = useState(30);
  const digits = Array.from({ length: OTP_LENGTH }, (_, index) => code[index] ?? '');
  const isValid = code.length === OTP_LENGTH;
  const maskedPhone =
    phone.length > 4 ? `${phone.slice(0, 4)} ${phone.slice(4, 6)} ****${phone.slice(-3)}` : phone;

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
      const tokens = await authService.verifyOtp({ phone, code, role: 'client' });
      await authStorage.setTokens(tokens.access_token, tokens.refresh_token);
      const user = {
        id: tokens.user.id,
        phone: tokens.user.phone,
        email: tokens.user.email,
        name: tokens.user.name ?? null,
        role: tokens.user.role,
      };
      await authStorage.setUser(user);

      // Determine profile completion — the OTP token response does not include
      // is_profile_complete, so we probe the profile endpoint directly.
      let profileComplete = false;
      try {
        await clientProfileService.getProfile();
        profileComplete = true;
      } catch {
        // 404 or any error → profile not yet created
      }

      await authStorage.setIsProfileComplete(profileComplete);
      setAuth({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        user,
        isProfileComplete: profileComplete,
      });

      // RootNavigator now gates the current legal version before either the
      // profile setup or the authenticated app can be shown.
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
      const result = await authService.requestOtp({ phone, role: 'client' });
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
    <SafeAreaView style={styles.root} edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.page}>
            <Text style={styles.heading}>Enter your code</Text>
            <Text style={styles.subheading}>6-digit code sent to +91 {maskedPhone}</Text>

            {!!displayOtp && (
              <Pressable
                style={styles.devBanner}
                onPress={() => setCode(displayOtp.slice(0, OTP_LENGTH))}
              >
                <Text style={styles.devBannerText}>Dev OTP: {displayOtp}</Text>
              </Pressable>
            )}

            <Pressable style={styles.boxesRow} onPress={() => inputRef.current?.focus()}>
              {digits.map((digit, index) => {
                const filled = digit !== '';
                return (
                  <View key={index} style={[styles.box, filled && styles.boxFilled]}>
                    <Text style={[styles.dot, filled && styles.dotFilled]}>
                      {filled ? '*' : ''}
                    </Text>
                  </View>
                );
              })}
            </Pressable>

            <TextInput
              ref={inputRef}
              style={styles.hiddenInput}
              value={code}
              onChangeText={(value) => setCode(value.replace(/\D/g, '').slice(0, OTP_LENGTH))}
              keyboardType="number-pad"
              maxLength={OTP_LENGTH}
              caretHidden
            />

            <View style={styles.spacer} />

            <Pressable
              style={({ pressed }) => [
                styles.button,
                isValid && styles.buttonPrimary,
                (!isValid || isPending) && styles.buttonDisabled,
                pressed && isValid && styles.buttonPressed,
              ]}
              onPress={handleVerify}
              disabled={!isValid || isPending}
            >
              {isPending ? (
                <ActivityIndicator size="small" color={C.btnText} />
              ) : (
                <Text style={[styles.buttonText, isValid && styles.buttonTextPrimary]}>Verify</Text>
              )}
            </Pressable>

            <View style={styles.resendRow}>
              <Text style={styles.resendText}>Did not get it? </Text>
              <Pressable onPress={handleResend} disabled={isResending || cooldown > 0}>
                <Text style={[styles.resendLink, (isResending || cooldown > 0) && styles.resendLinkDisabled]}>
                  {isResending ? 'Sending...' : cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend'}
                </Text>
              </Pressable>
            </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  flex: { flex: 1 },
  page: {
    flex: 1,
    paddingHorizontal: 26,
    paddingTop: 18,
    paddingBottom: 24,
  },
  heading: {
    color: C.ink,
    fontSize: 22,
    fontWeight: '800',
    letterSpacing: 0,
    marginBottom: 8,
  },
  subheading: {
    color: C.muted,
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 28,
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
  spacer: { flex: 1 },
  button: {
    height: 38,
    borderRadius: 8,
    borderWidth: 1.2,
    borderColor: C.brand,
    backgroundColor: C.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonPrimary: {
    backgroundColor: C.brand,
  },
  buttonDisabled: {
    opacity: 0.45,
  },
  buttonPressed: {
    opacity: 0.82,
  },
  buttonText: {
    color: C.ink,
    fontSize: 14,
    fontWeight: '800',
  },
  buttonTextPrimary: {
    color: C.btnText,
  },
  resendRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 12,
  },
  resendText: {
    color: C.muted,
    fontSize: 12,
  },
  resendLink: {
    color: C.brand,
    fontSize: 12,
    fontWeight: '800',
    textDecorationLine: 'underline',
  },
  resendLinkDisabled: {
    color: C.muted,
    textDecorationLine: 'none',
    fontWeight: '500',
  },
});
