import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Circle, Path, Ellipse, Rect } from 'react-native-svg';
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

// ─── Decorative illustration ──────────────────────────────────────────────────

function HeroIllustration() {
  return (
    <Svg width={280} height={280} viewBox="0 0 280 280">
      {/* Background circle */}
      <Circle cx="140" cy="140" r="120" fill={C.brand} opacity={0.08} />
      <Circle cx="140" cy="140" r="90" fill={C.brand} opacity={0.07} />

      {/* House body */}
      <Rect x="80" y="145" width="120" height="85" rx="6" fill={C.brand} />

      {/* Roof */}
      <Path d="M68 150 L140 90 L212 150 Z" fill={C.accent} />

      {/* Door */}
      <Rect x="121" y="185" width="38" height="45" rx="4" fill={C.accentSoft} />
      <Circle cx="153" cy="210" r="3" fill={C.accent} />

      {/* Left window */}
      <Rect x="90" y="160" width="28" height="22" rx="3" fill={C.accentSoft} />
      <Path d="M104 160 L104 182" stroke={C.accent} strokeWidth={1.5} />
      <Path d="M90 171 L118 171" stroke={C.accent} strokeWidth={1.5} />

      {/* Right window */}
      <Rect x="162" y="160" width="28" height="22" rx="3" fill={C.accentSoft} />
      <Path d="M176 160 L176 182" stroke={C.accent} strokeWidth={1.5} />
      <Path d="M162 171 L190 171" stroke={C.accent} strokeWidth={1.5} />

      {/* Ground */}
      <Ellipse cx="140" cy="232" rx="75" ry="8" fill={C.brand} opacity={0.1} />

      {/* Sparkles */}
      <Path d="M56 80 L58 86 L64 88 L58 90 L56 96 L54 90 L48 88 L54 86 Z" fill={C.accent} opacity={0.7} />
      <Path d="M218 100 L220 104 L224 106 L220 108 L218 112 L216 108 L212 106 L216 104 Z" fill={C.accent} opacity={0.5} />
      <Circle cx="68" cy="112" r="3" fill={C.accent} opacity={0.4} />
      <Circle cx="210" cy="78" r="4" fill={C.brand} opacity={0.2} />
      <Circle cx="224" cy="140" r="2.5" fill={C.accent} opacity={0.4} />
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

        <Text style={styles.heading}>Your home,{'\n'}your peace of mind.</Text>
        <Text style={styles.subheading}>
          Book trusted home care services, track your requests and stay connected — all in one place.
        </Text>
      </View>

      {/* Bottom CTA */}
      <View style={styles.footer}>
        <View style={styles.dotsRow}>
          <View style={[styles.dot, styles.dotActive]} />
          <View style={styles.dot} />
          <View style={styles.dot} />
        </View>

        <Pressable
          style={({ pressed }) => [styles.loginBtn, pressed && styles.loginBtnPressed]}
          onPress={() => navigation.navigate('Login')}
        >
          <Text style={styles.loginBtnText}>Log in</Text>
        </Pressable>

        <Text style={styles.footerNote}>
          By continuing you agree to our{' '}
          <Text style={styles.footerLink}>Terms &amp; Privacy Policy</Text>
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
  dotsRow: {
    flexDirection: 'row',
    gap: 6,
    marginBottom: 4,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: C.border,
  },
  dotActive: {
    width: 24,
    backgroundColor: C.accent,
  },
  loginBtn: {
    width: '100%',
    height: 56,
    borderRadius: 16,
    backgroundColor: C.brand,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: C.brand,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
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
