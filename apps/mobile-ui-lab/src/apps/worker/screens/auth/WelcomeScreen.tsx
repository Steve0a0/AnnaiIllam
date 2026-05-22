import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Circle, Path, Rect, Ellipse } from 'react-native-svg';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { WorkerAuthStackParamList } from '../../navigation/types';
import { C } from './styles';

// ─── Illustration ─────────────────────────────────────────────────────────────
// Clean toolbox SVG — no decorative blobs around it.

function HeroIllustration() {
  return (
    <Svg width={220} height={220} viewBox="0 0 280 280">
      {/* Toolbox body */}
      <Rect x="75" y="148" width="130" height="82" rx="10" fill={C.brand} />

      {/* Toolbox lid */}
      <Rect x="75" y="132" width="130" height="26" rx="8" fill={C.accent} />

      {/* Handle */}
      <Path
        d="M115 132 C115 112 165 112 165 132"
        stroke={C.accent}
        strokeWidth={7}
        fill="none"
        strokeLinecap="round"
      />

      {/* Latch */}
      <Rect x="128" y="140" width="24" height="14" rx="4" fill={C.accentSoft} />

      {/* Tools sticking out */}
      <Rect x="100" y="108" width="8" height="44" rx="4" fill={C.accentSoft} />
      <Rect x="117" y="100" width="6" height="48" rx="3" fill={C.accentSoft} />
      <Rect x="157" y="106" width="8" height="46" rx="4" fill={C.accentSoft} />
      <Rect x="152" y="100" width="18" height="14" rx="4" fill={C.accentSoft} />

      {/* Ground shadow */}
      <Ellipse cx="140" cy="234" rx="70" ry="7" fill={C.brand} opacity={0.1} />
    </Svg>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

type Props = {
  navigation: NativeStackNavigationProp<WorkerAuthStackParamList, 'Welcome'>;
};

export default function WelcomeScreen({ navigation }: Props) {
  return (
    <SafeAreaView style={styles.root} edges={['top', 'bottom']}>

      {/* Main content */}
      <View style={styles.body}>
        <View style={styles.illustrationWrap}>
          <HeroIllustration />
        </View>

        <Text style={styles.heading}>Work shifts.{'\n'}Get paid. Grow.</Text>
        <Text style={styles.subheading}>
          Find assignments at verified job sites, track your shifts, and receive payments — all in one place.
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
          <Text style={styles.loginBtnText}>Get started</Text>
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
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 6,
  },
  loginBtnPressed: {
    opacity: 0.85,
  },
  loginBtnText: {
    fontSize: 17,
    fontWeight: '700',
    color: '#fffdf8',
    letterSpacing: 0.2,
  },
  footerNote: {
    fontSize: 13,
    color: C.muted,
    textAlign: 'center',
    lineHeight: 18,
  },
  footerLink: {
    color: C.ink,
    fontWeight: '600',
  },
});
