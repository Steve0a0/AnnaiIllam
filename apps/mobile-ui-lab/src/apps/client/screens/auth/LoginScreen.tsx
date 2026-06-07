import { useState } from 'react';
import {
  Alert,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
  ActivityIndicator,
  TextInput,
  KeyboardAvoidingView,
  ScrollView,
  Keyboard,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Path } from 'react-native-svg';
import * as AppleAuthentication from 'expo-apple-authentication';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import { getApiError } from '../../../../shared/lib/get-api-error';
import { authService } from '../../../../shared/services/auth.service';
import { authStorage } from '../../../../shared/lib/auth-storage';
import { useAuthStore } from '../../../../shared/store/auth.store';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { ClientAuthStackParamList } from '../../navigation/types';
import type { SocialAuthTokens } from '../../../../shared/types/auth';

WebBrowser.maybeCompleteAuthSession();

// ─── Admin brand palette ─────────────────────────────────────────────────────
const C = {
  bg: '#f4f1e8',
  surface: '#fffaf0',
  brand: '#203428',
  ink: '#17211a',
  muted: '#687267',
  border: '#ddd3be',
  accent: '#c96f3c',
  accentSoft: '#f1c8a8',
  btnText: '#fffaf0',
  socialBg: '#fffaf0',
  socialBorder: '#ddd3be',
  socialText: '#17211a',
} as const;

// ─── SVG icons ───────────────────────────────────────────────────────────────

function GoogleIcon({ size = 20 }: { size?: number }) {
  return (
    <Svg width={size} height={size} viewBox="-3 0 262 262">
      <Path d="M255.878 133.451c0-10.734-.871-18.567-2.756-26.69H130.55v48.448h71.947c-1.45 12.04-9.283 30.172-26.69 42.356l-.244 1.622 38.755 30.023 2.685.268c24.659-22.774 38.875-56.282 38.875-96.027" fill="#4285F4" />
      <Path d="M130.55 261.1c35.248 0 64.839-11.605 86.453-31.622l-41.196-31.913c-11.024 7.688-25.82 13.055-45.257 13.055-34.523 0-63.824-22.773-74.269-54.25l-1.531.13-40.298 31.187-.527 1.465C35.393 231.798 79.49 261.1 130.55 261.1" fill="#34A853" />
      <Path d="M56.281 156.37c-2.756-8.123-4.351-16.827-4.351-25.82 0-8.994 1.595-17.697 4.206-25.82l-.073-1.73L15.26 71.312l-1.335.635C5.077 89.644 0 109.517 0 130.55s5.077 40.905 13.925 58.602l42.356-32.782" fill="#FBBC05" />
      <Path d="M130.55 50.479c24.514 0 41.05 10.589 50.479 19.438l36.844-35.974C195.245 12.91 165.798 0 130.55 0 79.49 0 35.393 29.301 13.925 71.947l42.211 32.783c10.59-31.477 39.891-54.251 74.414-54.251" fill="#EB4335" />
    </Svg>
  );
}

function AppleIcon({ size = 20, color = '#17211a' }: { size?: number; color?: string }) {
  return (
    <Svg width={size} height={size} viewBox="-52.01 0 560.035 560.035">
      <Path d="M380.844 297.529c.787 84.752 74.349 112.955 75.164 113.314-.622 1.988-11.754 40.191-38.756 79.652-23.343 34.117-47.568 68.107-85.731 68.811-37.499.691-49.557-22.236-92.429-22.236-42.859 0-56.256 21.533-91.753 22.928-36.837 1.395-64.889-36.891-88.424-70.883-48.093-69.53-84.846-196.475-35.496-282.165 24.516-42.554 68.328-69.501 115.882-70.192 36.173-.69 70.315 24.336 92.429 24.336 22.1 0 63.59-30.096 107.208-25.676 18.26.76 69.517 7.376 102.429 55.552-2.652 1.644-61.159 35.704-60.523 106.559M310.369 89.418C329.926 65.745 343.089 32.79 339.498 0 311.308 1.133 277.22 18.785 257 42.445c-18.121 20.952-33.991 54.487-29.709 86.628 31.421 2.431 63.52-15.967 83.078-39.655" fill={color} />
    </Svg>
  );
}

// ─── Google button ────────────────────────────────────────────────────────────

const toUndef = (v: string | undefined) => (v?.length ? v : undefined);
const GOOGLE_WEB_ID = toUndef(process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID);
const GOOGLE_IOS_ID = toUndef(process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID);
const GOOGLE_ANDROID_ID = toUndef(process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID);
const GOOGLE_CONFIGURED = !!(GOOGLE_IOS_ID || GOOGLE_ANDROID_ID || GOOGLE_WEB_ID);

type GoogleBtnProps = { onSignIn: (result: SocialAuthTokens) => Promise<void> };

function GoogleSignInButton({ onSignIn }: GoogleBtnProps) {
  const [isPending, setIsPending] = useState(false);
  // Do NOT pass redirectUri — the Google provider derives the correct platform-specific
  // URI from iosClientId / androidClientId (reversed-client-ID scheme).
  // Overriding it with makeRedirectUri() breaks native builds.
  const [, , promptAsync] = Google.useAuthRequest({
    webClientId: GOOGLE_WEB_ID,
    iosClientId: GOOGLE_IOS_ID,
    androidClientId: GOOGLE_ANDROID_ID,
  });

  const handlePress = async () => {
    setIsPending(true);
    try {
      const response = await promptAsync();
      if (response?.type !== 'success') return;
      const idToken = response.authentication?.idToken;
      if (!idToken) {
        Alert.alert('Sign-in failed', 'Google did not return a token. Please try again.');
        return;
      }
      const result = await authService.socialAuth({ provider: 'google', id_token: idToken });
      await onSignIn(result);
    } catch {
      Alert.alert('Sign-in failed', 'Could not sign in with Google. Please try again.');
    } finally {
      setIsPending(false);
    }
  };

  return (
    <Pressable
      style={({ pressed }) => [styles.socialBtn, pressed && styles.socialBtnPressed]}
      onPress={handlePress}
      disabled={isPending}
    >
      {isPending ? (
        <ActivityIndicator size="small" color={C.socialText} />
      ) : (
        <>
          <GoogleIcon size={20} />
          <Text style={styles.socialBtnLabel}>Sign in with Google</Text>
        </>
      )}
    </Pressable>
  );
}

function GoogleSignInUnconfigured() {
  return (
    <Pressable style={[styles.socialBtn, { opacity: 0.45 }]} disabled>
      <GoogleIcon size={20} />
      <Text style={styles.socialBtnLabel}>Sign in with Google</Text>
    </Pressable>
  );
}

// ─── Main screen ──────────────────────────────────────────────────────────────

type Props = {
  navigation: NativeStackNavigationProp<ClientAuthStackParamList, 'Login'>;
};

export default function LoginScreen({ navigation }: Props) {
  const { setAuth } = useAuthStore();
  const [appleIsPending, setAppleIsPending] = useState(false);
  const [phone, setPhone] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isPending, setIsPending] = useState(false);

  const isPhoneValid = /^\d{10,15}$/.test(phone.trim());

  const handleContinue = async () => {
    if (!isPhoneValid) {
      Alert.alert('Invalid number', 'Please enter a valid phone number (10–15 digits).');
      return;
    }
    Keyboard.dismiss();
    setIsPending(true);
    const phoneWithCode = '+91' + phone.trim();
    try {
      const result = await authService.requestOtp({ phone: phoneWithCode, role: 'client' });
      navigation.navigate('VerifyOtp', { phone: phoneWithCode, devOtp: result?.otp });
    } catch (err) {
      Alert.alert('Error', getApiError(err, 'Failed to send code. Please try again.'));
    } finally {
      setIsPending(false);
    }
  };

  const persistAndSetAuth = async (result: SocialAuthTokens) => {
    await authStorage.setTokens(result.access_token, result.refresh_token);
    const user = {
      id: result.user.id,
      email: result.user.email,
      name: result.user.name,
      role: result.user.role,
    };
    await authStorage.setUser(user);
    await authStorage.setIsProfileComplete(result.is_profile_complete ?? false);
    setAuth({
      accessToken: result.access_token,
      refreshToken: result.refresh_token,
      user,
      isProfileComplete: result.is_profile_complete,
    });
    if (!result.is_profile_complete) navigation.replace('ProfileSetup');
  };

  const handleAppleSignIn = async () => {
    setAppleIsPending(true);
    try {
      const credential = await AppleAuthentication.signInAsync({
        requestedScopes: [
          AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
          AppleAuthentication.AppleAuthenticationScope.EMAIL,
        ],
      });
      if (!credential.identityToken) {
        Alert.alert('Sign-in failed', 'Apple did not return a token. Please try again.');
        return;
      }
      const name = credential.fullName
        ? [credential.fullName.givenName, credential.fullName.familyName]
            .filter(Boolean).join(' ') || null
        : null;
      const result = await authService.socialAuth({
        provider: 'apple',
        id_token: credential.identityToken,
        name,
      });
      await persistAndSetAuth(result);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'code' in err &&
          (err as { code: string }).code === 'ERR_CANCELED') return;
      Alert.alert('Sign-in failed', 'Apple sign-in encountered an error. Please try again.');
    } finally {
      setAppleIsPending(false);
    }
  };

  return (
    <SafeAreaView style={styles.root} edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
          <ScrollView
            contentContainerStyle={styles.scrollContent}
            keyboardShouldPersistTaps="handled"
            onScrollBeginDrag={Keyboard.dismiss}
            showsVerticalScrollIndicator={false}
          >
            {/* ── Heading ── */}
            <Text style={styles.heading}>Log in</Text>
            <Text style={styles.subheading}>
              By logging in, you agree to our{' '}
              <Text style={styles.subheadingLink}>Terms of Use.</Text>
            </Text>

            {/* ── Phone number input ── */}
            <Text style={styles.inputLabel}>Phone number</Text>
            <View style={[styles.inputShell, isFocused && styles.inputShellFocused]}>
              <View style={styles.prefixPill}>
                <Text style={styles.prefixText}>+91</Text>
              </View>
              <View style={styles.inputDivider} />
              <TextInput
                style={styles.input}
                placeholder="Your phone number"
                placeholderTextColor={C.muted}
                keyboardType="phone-pad"
                value={phone}
                onChangeText={(v) => setPhone(v.replace(/\D/g, ''))}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                returnKeyType="done"
                onSubmitEditing={handleContinue}
              />
            </View>
            <Text style={styles.inputHint}>
              We will send you a one-time code to verify it is you.
            </Text>

            {/* ── Connect button ── */}
            <Pressable
              style={({ pressed }) => [
                styles.connectBtn,
                !isPhoneValid && styles.connectBtnDisabled,
                pressed && isPhoneValid && styles.connectBtnPressed,
              ]}
              onPress={handleContinue}
              disabled={!isPhoneValid || isPending}
            >
              {isPending ? (
                <ActivityIndicator size="small" color={C.btnText} />
              ) : (
                <Text style={styles.connectBtnText}>Connect</Text>
              )}
            </Pressable>

            {/* ── Divider ── */}
            <View style={styles.dividerRow}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>Or</Text>
              <View style={styles.dividerLine} />
            </View>

            {/* ── Social buttons (stacked) ── */}
            <View style={styles.socialStack}>
              {GOOGLE_CONFIGURED
                ? <GoogleSignInButton onSignIn={persistAndSetAuth} />
                : <GoogleSignInUnconfigured />
              }

              {Platform.OS === 'ios' && (
                appleIsPending ? (
                  <View style={[styles.socialBtn, { justifyContent: 'center' }]}>
                    <ActivityIndicator size="small" color={C.socialText} />
                  </View>
                ) : (
                  <Pressable
                    style={({ pressed }) => [styles.socialBtn, pressed && styles.socialBtnPressed]}
                    onPress={handleAppleSignIn}
                  >
                    <AppleIcon size={20} color={C.ink} />
                    <Text style={styles.socialBtnLabel}>Sign in with Apple</Text>
                  </Pressable>
                )
              )}
            </View>

            {/* ── Footer ── */}
            <Text style={styles.footer}>
              For more information, please see our{' '}
              <Text style={styles.footerLink}>Privacy policy.</Text>
            </Text>

          </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: C.bg,
  },
  flex: { flex: 1 },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 28,
    paddingTop: 40,
    paddingBottom: 40,
  },

  // ── Heading ──
  heading: {
    fontSize: 32,
    fontWeight: '800',
    color: C.ink,
    letterSpacing: -0.5,
    marginBottom: 8,
  },
  subheading: {
    fontSize: 14,
    color: C.muted,
    lineHeight: 20,
    marginBottom: 32,
  },
  subheadingLink: {
    color: C.ink,
    fontWeight: '700',
  },

  // ── Phone input ──
  inputLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: C.ink,
    marginBottom: 6,
    letterSpacing: 0.1,
  },
  inputShell: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 54,
    borderRadius: 14,
    backgroundColor: C.surface,
    borderWidth: 1.5,
    borderColor: C.border,
    paddingHorizontal: 14,
  },
  inputShellFocused: {
    borderColor: C.brand,
  },
  prefixPill: {
    paddingRight: 10,
  },
  prefixText: {
    fontSize: 15,
    fontWeight: '600',
    color: C.ink,
  },
  inputDivider: {
    width: 1,
    height: 20,
    backgroundColor: C.border,
    marginRight: 12,
  },
  input: {
    flex: 1,
    fontSize: 15,
    color: C.ink,
    paddingVertical: 0,
  },
  inputHint: {
    fontSize: 12,
    color: C.muted,
    marginTop: 6,
    marginBottom: 24,
    lineHeight: 18,
  },

  // ── Connect button ──
  connectBtn: {
    height: 54,
    borderRadius: 14,
    backgroundColor: C.brand,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 28,
    shadowColor: C.brand,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  connectBtnDisabled: {
    backgroundColor: C.brand,
    opacity: 0.45,
    shadowOpacity: 0,
    elevation: 0,
  },
  connectBtnPressed: {
    opacity: 0.85,
  },
  connectBtnText: {
    fontSize: 16,
    fontWeight: '700',
    color: C.btnText,
    letterSpacing: 0.2,
  },

  // ── Divider ──
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 20,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: C.border,
  },
  dividerText: {
    fontSize: 13,
    color: C.muted,
    fontWeight: '500',
  },

  // ── Social buttons ──
  socialStack: {
    gap: 12,
    marginBottom: 32,
  },
  socialBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 54,
    borderRadius: 14,
    backgroundColor: C.socialBg,
    borderWidth: 1.5,
    borderColor: C.socialBorder,
    gap: 10,
  },
  socialBtnPressed: {
    opacity: 0.7,
  },
  socialBtnLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: C.socialText,
  },

  // ── Footer ──
  footer: {
    fontSize: 12,
    color: C.muted,
    textAlign: 'center',
    lineHeight: 18,
  },
  footerLink: {
    color: C.ink,
    fontWeight: '700',
  },
});
