import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CheckCircle2 } from 'lucide-react-native';

import { authStorage } from '../../../../shared/lib/auth-storage';
import { useAuthStore } from '../../../../shared/store/auth.store';
import { C, authStyles as baseStyles } from './styles';

const REVIEW = {
  bg:     '#f5f3ff',
  border: '#c4b5fd',
  dot:    '#7c3aed',
  text:   '#5b21b6',
} as const;

export default function ProfileSubmittedScreen() {
  const { setOnboardingStep } = useAuthStore();

  const handleGotIt = async () => {
    await authStorage.setOnboardingStep('profile_submitted');
    setOnboardingStep('profile_submitted');
  };

  return (
    <SafeAreaView style={baseStyles.root} edges={['top', 'bottom']}>
      <View style={baseStyles.page}>

        <View style={local.iconRing}>
          <CheckCircle2 size={44} color={C.brand} strokeWidth={1.5} />
        </View>

        <View style={local.pill}>
          <View style={local.pillDot} />
          <Text style={local.pillText}>Under review</Text>
        </View>

        <Text style={[baseStyles.heading, baseStyles.centerHeading]}>Profile submitted</Text>
        <Text style={[baseStyles.subheading, baseStyles.centerText]}>
          Our team is reviewing your details. You will hear back within 24 hours.
        </Text>

        <View style={baseStyles.spacer} />

        <Pressable
          style={({ pressed }) => [baseStyles.button, baseStyles.buttonPrimary, pressed && baseStyles.buttonPressed]}
          onPress={handleGotIt}
        >
          <Text style={[baseStyles.buttonText, baseStyles.buttonTextPrimary]}>Got it</Text>
        </Pressable>

      </View>
    </SafeAreaView>
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
    marginBottom: 20,
  },
  pill: {
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    borderRadius: 100,
    backgroundColor: REVIEW.bg,
    borderWidth: 1,
    borderColor: REVIEW.border,
    paddingHorizontal: 12,
    paddingVertical: 5,
    marginBottom: 16,
  },
  pillDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: REVIEW.dot,
  },
  pillText: {
    color: REVIEW.text,
    fontSize: 13,
    fontWeight: '700',
  },
});
