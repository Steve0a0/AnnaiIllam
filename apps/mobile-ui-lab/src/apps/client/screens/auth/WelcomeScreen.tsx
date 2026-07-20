import {
  Alert,
  Linking,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Circle, Path, Rect } from 'react-native-svg';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { ClientAuthStackParamList } from '../../navigation/types';

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
} as const;

const TERMS_URL = 'https://annaiillam.in/terms';
const PRIVACY_URL = 'https://annaiillam.in/privacy';

async function openLegalUrl(url: string) {
  try {
    const canOpen = await Linking.canOpenURL(url);
    if (!canOpen) throw new Error('Cannot open URL');
    await Linking.openURL(url);
  } catch {
    Alert.alert('Could not open link', 'Please try again later.');
  }
}

// ─── Decorative illustration ──────────────────────────────────────────────────

function HeroIllustration() {
  return (
    <Svg width={280} height={280} viewBox="0 0 280 280">
      <Circle cx="140" cy="140" r="120" fill={C.brand} opacity={0.08} />
      <Circle cx="140" cy="140" r="90" fill={C.brand} opacity={0.07} />

      <Rect x="72" y="72" width="136" height="154" rx="18" fill={C.surface} />
      <Rect x="72" y="72" width="136" height="154" rx="18" stroke={C.border} strokeWidth={2} fill="none" />
      <Rect x="96" y="54" width="88" height="34" rx="12" fill={C.brand} />
      <Rect x="118" y="46" width="44" height="18" rx="9" fill={C.accent} />

      <Path d="M100 116 H180" stroke={C.brand} strokeWidth={8} strokeLinecap="round" opacity={0.9} />
      <Path d="M100 144 H166" stroke={C.brand} strokeWidth={8} strokeLinecap="round" opacity={0.45} />
      <Path d="M100 172 H152" stroke={C.brand} strokeWidth={8} strokeLinecap="round" opacity={0.3} />

      <Circle cx="86" cy="115" r="19" fill={C.brand} />
      <Circle cx="86" cy="106" r="7" fill={C.accentSoft} />
      <Path d="M72 130 C76 121 96 121 100 130" fill={C.accentSoft} />

      <Circle cx="86" cy="167" r="19" fill={C.accent} />
      <Circle cx="86" cy="158" r="7" fill={C.accentSoft} />
      <Path d="M72 182 C76 173 96 173 100 182" fill={C.accentSoft} />

      <Rect x="166" y="184" width="58" height="40" rx="12" fill={C.brand} />
      <Path d="M182 204 L192 213 L209 194" stroke={C.btnText} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" />

      <Rect x="174" y="80" width="54" height="54" rx="16" fill={C.accentSoft} />
      <Path d="M190 107 H213" stroke={C.accent} strokeWidth={5} strokeLinecap="round" />
      <Path d="M202 95 V119" stroke={C.accent} strokeWidth={5} strokeLinecap="round" />
    </Svg>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

type Props = {
  navigation: NativeStackNavigationProp<ClientAuthStackParamList, 'Welcome'>;
};

export default function WelcomeScreen({ navigation }: Props) {
  return (
    <SafeAreaView style={styles.root} edges={['top', 'bottom']}>
      {/* Decorative blobs */}
      <View style={styles.blobTopRight} />
      <View style={styles.blobBottomLeft} />

      {/* Main content */}
      <View style={styles.body}>
        <View style={styles.illustrationWrap}>
          <HeroIllustration />
        </View>

        <Text style={styles.heading}>Staff your site{'\n'}with confidence.</Text>
        <Text style={styles.subheading}>
          Raise worker requests, review quotes, and track assigned staff from one place.
        </Text>
      </View>

      {/* Bottom CTA */}
      <View style={styles.footer}>
        <Pressable
          style={({ pressed }) => [styles.loginBtn, pressed && styles.loginBtnPressed]}
          onPress={() => navigation.navigate('Login')}
        >
          <Text style={styles.loginBtnText}>Log in</Text>
        </Pressable>

        <Text style={styles.footerNote}>
          By continuing you agree to our{' '}
          <Text style={styles.footerLink} onPress={() => openLegalUrl(TERMS_URL)}>
            Terms
          </Text>
          {' '}and{' '}
          <Text style={styles.footerLink} onPress={() => openLegalUrl(PRIVACY_URL)}>
            Privacy Policy
          </Text>
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: C.bg,
  },

  // ── Background blobs ──
  blobTopRight: {
    position: 'absolute',
    top: -60,
    right: -60,
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: C.accentSoft,
    opacity: 0.35,
  },
  blobBottomLeft: {
    position: 'absolute',
    bottom: -80,
    left: -80,
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: C.brand,
    opacity: 0.06,
  },

  // ── Body ──
  body: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  illustrationWrap: {
    marginBottom: 36,
  },
  heading: {
    fontSize: 34,
    fontWeight: '800',
    color: C.ink,
    textAlign: 'center',
    lineHeight: 42,
    letterSpacing: -0.5,
    marginBottom: 16,
  },
  subheading: {
    fontSize: 15,
    color: C.muted,
    textAlign: 'center',
    lineHeight: 23,
    maxWidth: 300,
  },

  // ── Footer ──
  footer: {
    paddingHorizontal: 28,
    paddingBottom: 20,
    alignItems: 'center',
    gap: 16,
  },
  loginBtn: {
    width: '100%',
    height: 56,
    borderRadius: 16,
    backgroundColor: C.brand,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: C.brand,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.24,
    shadowRadius: 8,
    elevation: 4,
  },
  loginBtnPressed: {
    opacity: 0.85,
  },
  loginBtnText: {
    fontSize: 17,
    fontWeight: '700',
    color: C.btnText,
    letterSpacing: 0.2,
  },
  footerNote: {
    fontSize: 12,
    color: C.muted,
    textAlign: 'center',
    lineHeight: 18,
  },
  footerLink: {
    color: C.ink,
    fontWeight: '600',
  },
});
