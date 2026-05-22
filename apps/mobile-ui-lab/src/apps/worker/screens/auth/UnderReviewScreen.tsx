import { useEffect, useRef } from 'react';
import { AppState, AppStateStatus, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Clock, UserRound } from 'lucide-react-native';
import { authStorage } from '../../../../shared/lib/auth-storage';
import { useAuthStore } from '../../../../shared/store/auth.store';
import { pushTokenService } from '../../../../shared/services/push-token.service';
import { workerOnboardingService } from '../../../../shared/services/worker-onboarding.service';
import { C, authStyles as baseStyles } from './styles';

const STEPS = [
  'We review your govt ID and selfie match',
  'We verify your skills and availability',
  'You get a push notification once approved',
];

const POLL_INTERVAL_MS = 30_000;

export default function UnderReviewScreen() {
  const { clearAuth, setOnboardingStep } = useAuthStore();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function checkApproval() {
    try {
      const status = await workerOnboardingService.getStatus();
      if (status.onboarding_step === 'approved') {
        await authStorage.setOnboardingStep('approved');
        setOnboardingStep('approved');
      }
    } catch {
      // silently ignore — polling, not critical
    }
  }

  useEffect(() => {
    // Check immediately when screen mounts
    checkApproval();

    // Then poll every 30 seconds
    intervalRef.current = setInterval(checkApproval, POLL_INTERVAL_MS);

    // Also check whenever the app comes back to the foreground
    const subscription = AppState.addEventListener('change', (state: AppStateStatus) => {
      if (state === 'active') {
        checkApproval();
      }
    });

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      subscription.remove();
    };
  }, []);

  const handleLogout = async () => {
    await pushTokenService.deactivate().catch(() => undefined);
    await authStorage.clear();
    clearAuth();
  };

  return (
    <SafeAreaView style={baseStyles.root} edges={['top', 'bottom']}>
      <ScrollView
        contentContainerStyle={local.scroll}
        showsVerticalScrollIndicator={false}
      >
        {/* Avatar icon with dashed ring */}
        <View style={local.avatarOuter}>
          <View style={local.avatarInner}>
            <UserRound size={36} color={C.muted} strokeWidth={1.5} />
            {/* Small checkmark badge */}
            <View style={local.checkBadge}>
              <Text style={local.checkBadgeText}>✓</Text>
            </View>
          </View>
        </View>

        {/* Under review pill */}
        <View style={local.pill}>
          <View style={local.pillDot} />
          <Text style={local.pillText}>Under review</Text>
        </View>

        {/* Heading */}
        <Text style={local.heading}>
          {"We're reviewing\nyour "}
          <Text style={local.headingAccent}>profile</Text>
        </Text>

        <Text style={local.subheading}>
          Our team is verifying your documents and details. This usually takes up to 24 hours.
        </Text>

        {/* What happens next card */}
        <View style={local.card}>
          <View style={local.cardHeader}>
            <Clock size={16} color={C.muted} strokeWidth={1.8} />
            <Text style={local.cardHeaderText}>What happens next?</Text>
          </View>
          {STEPS.map((step, i) => (
            <View key={step} style={local.stepRow}>
              <View style={local.stepNum}>
                <Text style={local.stepNumText}>{i + 1}</Text>
              </View>
              <Text style={local.stepText}>{step}</Text>
            </View>
          ))}
        </View>

        {/* Estimated wait row */}
        <View style={local.waitRow}>
          <Clock size={15} color={C.accent} strokeWidth={1.8} />
          <Text style={local.waitText}>
            Estimated wait: <Text style={local.waitBold}>up to 24 hours</Text>
          </Text>
        </View>

        {/* Contact */}
        <Text style={local.contactText}>
          Questions?{' '}
          <Text style={local.contactLink}>support@annaiillam.in</Text>
        </Text>

        <View style={{ flex: 1, minHeight: 32 }} />

        {/* Log out */}
        <Pressable
          style={({ pressed }) => [local.logoutBtn, pressed && { opacity: 0.6 }]}
          onPress={handleLogout}
        >
          <Text style={local.logoutText}>Log out</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const local = StyleSheet.create({
  scroll: {
    flexGrow: 1,
    paddingHorizontal: 28,
    paddingTop: 48,
    paddingBottom: 36,
    alignItems: 'center',
  },
  avatarOuter: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 1.5,
    borderColor: C.border,
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 28,
  },
  avatarInner: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: C.surfaceAlt,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkBadge: {
    position: 'absolute',
    bottom: 4,
    right: 4,
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: C.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
    lineHeight: 14,
  },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    borderRadius: 100,
    borderWidth: 1,
    borderColor: C.accent,
    paddingHorizontal: 14,
    paddingVertical: 6,
    marginBottom: 24,
  },
  pillDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: C.accent,
  },
  pillText: {
    color: C.ink,
    fontSize: 13,
    fontWeight: '600',
  },
  heading: {
    fontSize: 28,
    fontWeight: '800',
    color: C.ink,
    textAlign: 'center',
    lineHeight: 36,
    marginBottom: 12,
  },
  headingAccent: {
    color: C.accent,
    fontStyle: 'italic',
  },
  subheading: {
    fontSize: 14,
    color: C.muted,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 28,
  },
  card: {
    width: '100%',
    backgroundColor: C.surface,
    borderRadius: 16,
    padding: 18,
    gap: 14,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.04,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 2,
  },
  cardHeaderText: {
    fontSize: 14,
    fontWeight: '700',
    color: C.ink,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  stepNum: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: C.surfaceAlt,
    borderWidth: 1,
    borderColor: C.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  stepNumText: {
    fontSize: 11,
    fontWeight: '700',
    color: C.muted,
  },
  stepText: {
    flex: 1,
    fontSize: 13,
    color: C.muted,
    lineHeight: 20,
  },
  waitRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 16,
    marginBottom: 4,
  },
  waitText: {
    fontSize: 13,
    color: '#687267',
    lineHeight: 20,
    flex: 1,
  },
  waitBold: {
    fontWeight: '700',
    color: '#17211a',
  },
  contactText: {
    fontSize: 13,
    color: '#687267',
    textAlign: 'center',
    marginTop: 20,
    lineHeight: 20,
  },
  contactLink: {
    color: '#203428',
    fontWeight: '700',
  },
  logoutBtn: {
    marginTop: 24,
    alignSelf: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  logoutText: {
    fontSize: 13,
    color: '#687267',
    fontWeight: '600',
  },
});
