import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Keyboard,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { getApiError } from '../../../../shared/lib/get-api-error';
import { authStorage } from '../../../../shared/lib/auth-storage';
import { workerOnboardingService } from '../../../../shared/services/worker-onboarding.service';
import { useAuthStore } from '../../../../shared/store/auth.store';
import type { WorkerAuthStackParamList } from '../../navigation/types';
import { C, authStyles as baseStyles } from './styles';

type Props = NativeStackScreenProps<WorkerAuthStackParamList, 'BuildProfile'>;

const SKILLS = [
  'Cleaning', 'Cooking', 'Plumbing', 'Electrical',
  'Carpentry', 'Painting', 'Laundry / Ironing', 'Pest Control',
  'Gardening', 'Babysitting', 'Elder Care', 'Driver',
];

const EXPERIENCE_OPTIONS = ['< 1 year', '1\u20132 years', '3\u20135 years', '5+ years'];

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const SHIFTS = ['Morning', 'Afternoon', 'Evening', 'Full Day'];

export default function BuildProfileScreen({ navigation }: Props) {
  const { setOnboardingStep } = useAuthStore();
  const [fullName, setFullName] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [experience, setExperience] = useState('');
  const [availableDays, setAvailableDays] = useState<string[]>([]);
  const [availableShifts, setAvailableShifts] = useState<string[]>([]);
  const [upiId, setUpiId] = useState('');
  const [accountNo, setAccountNo] = useState('');
  const [ifsc, setIfsc] = useState('');
  const [showBankFields, setShowBankFields] = useState(false);
  const [focused, setFocused] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const toggleItem = (list: string[], set: (v: string[]) => void, item: string) =>
    set(list.includes(item) ? list.filter((x) => x !== item) : [...list, item]);

  const canSubmit =
    fullName.trim().length > 1 &&
    city.trim().length > 1 &&
    state.trim().length > 1 &&
    selectedSkills.length > 0 &&
    experience !== '' &&
    availableDays.length > 0 &&
    availableShifts.length > 0;

  const handleSubmit = async () => {
    if (!canSubmit) {
      Alert.alert('Profile incomplete', 'Please fill in all required fields.');
      return;
    }
    Keyboard.dismiss();
    setIsSubmitting(true);
    try {
      await workerOnboardingService.submitProfile({
        full_name:        fullName.trim(),
        skills:           selectedSkills,
        experience_years: experience,
        available_days:   availableDays,
        available_shifts: availableShifts,
        city:             city.trim(),
        state:            state.trim(),
        payment: {
          upi_id:              upiId.trim() || null,
          bank_account_number: accountNo.trim() || null,
          bank_ifsc:           ifsc.trim() || null,
          bank_holder_name:    null,
        },
      });
      await authStorage.setOnboardingStep('profile_submitted');
      setOnboardingStep('profile_submitted');
      navigation.navigate('ProfileSubmitted');
    } catch (err) {
      Alert.alert('Submission failed', getApiError(err, 'Could not submit profile. Please try again.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={baseStyles.root} edges={['top', 'bottom']}>
      <ScrollView
        style={baseStyles.flex}
        contentContainerStyle={local.scroll}
        keyboardShouldPersistTaps="handled"
        onScrollBeginDrag={Keyboard.dismiss}
        showsVerticalScrollIndicator={false}
      >
        <View style={baseStyles.progressTrack}>
          <View style={[baseStyles.progressFill, { width: '66%' }]} />
        </View>

        <Text style={baseStyles.heading}>Build your profile</Text>
        <Text style={baseStyles.subheading}>
          What clients and admins will see when you are assigned.
        </Text>

        {/* Full name */}
        <Text style={local.label}>Full name <Text style={local.required}>*</Text></Text>
        <View style={[baseStyles.inputShell, focused === 'name' && baseStyles.inputFocused]}>
          <TextInput
            style={baseStyles.input}
            placeholder="e.g. Meenakshi Devi"
            placeholderTextColor={C.muted}
            value={fullName}
            onChangeText={setFullName}
            onFocus={() => setFocused('name')}
            onBlur={() => setFocused(null)}
          />
        </View>

        {/* City */}
        <Text style={local.label}>City <Text style={local.required}>*</Text></Text>
        <View style={[baseStyles.inputShell, focused === 'city' && baseStyles.inputFocused]}>
          <TextInput
            style={baseStyles.input}
            placeholder="e.g. Chennai, Mumbai, Bangalore"
            placeholderTextColor={C.muted}
            value={city}
            onChangeText={setCity}
            onFocus={() => setFocused('city')}
            onBlur={() => setFocused(null)}
          />
        </View>

        {/* State */}
        <Text style={local.label}>State <Text style={local.required}>*</Text></Text>
        <View style={[baseStyles.inputShell, focused === 'state' && baseStyles.inputFocused]}>
          <TextInput
            style={baseStyles.input}
            placeholder="e.g. Tamil Nadu, Maharashtra, Karnataka"
            placeholderTextColor={C.muted}
            value={state}
            onChangeText={setState}
            onFocus={() => setFocused('state')}
            onBlur={() => setFocused(null)}
          />
        </View>

        {/* Skills */}
        <Text style={local.label}>
          Skills <Text style={local.required}>*</Text>
          <Text style={local.labelMuted}> (select all that apply)</Text>
        </Text>
        <View style={local.chipWrap}>
          {SKILLS.map((skill) => {
            const active = selectedSkills.includes(skill);
            return (
              <Pressable
                key={skill}
                style={[local.chip, active && local.chipActive]}
                onPress={() => toggleItem(selectedSkills, setSelectedSkills, skill)}
              >
                <Text style={[local.chipText, active && local.chipTextActive]}>{skill}</Text>
              </Pressable>
            );
          })}
        </View>

        {/* Experience */}
        <Text style={local.label}>Years of experience <Text style={local.required}>*</Text></Text>
        <View style={local.chipWrap}>
          {EXPERIENCE_OPTIONS.map((opt) => {
            const active = experience === opt;
            return (
              <Pressable
                key={opt}
                style={[local.chip, active && local.chipActive]}
                onPress={() => setExperience(opt)}
              >
                <Text style={[local.chipText, active && local.chipTextActive]}>{opt}</Text>
              </Pressable>
            );
          })}
        </View>

        {/* Available days */}
        <Text style={local.label}>Available days <Text style={local.required}>*</Text></Text>
        <View style={local.chipWrap}>
          {DAYS.map((day) => {
            const active = availableDays.includes(day);
            return (
              <Pressable
                key={day}
                style={[local.chip, active && local.chipActive]}
                onPress={() => toggleItem(availableDays, setAvailableDays, day)}
              >
                <Text style={[local.chipText, active && local.chipTextActive]}>{day}</Text>
              </Pressable>
            );
          })}
        </View>

        {/* Preferred shift */}
        <Text style={local.label}>Preferred shift <Text style={local.required}>*</Text></Text>
        <View style={local.chipWrap}>
          {SHIFTS.map((shift) => {
            const active = availableShifts.includes(shift);
            return (
              <Pressable
                key={shift}
                style={[local.chip, active && local.chipActive]}
                onPress={() => toggleItem(availableShifts, setAvailableShifts, shift)}
              >
                <Text style={[local.chipText, active && local.chipTextActive]}>{shift}</Text>
              </Pressable>
            );
          })}
        </View>

        {/* Payment details */}
        <Text style={[local.label, local.sectionLabel]}>Payment details</Text>
        <Text style={local.hint}>Your salary will be transferred to this account.</Text>

        <Text style={local.subLabel}>UPI ID</Text>
        <View style={[baseStyles.inputShell, focused === 'upi' && baseStyles.inputFocused]}>
          <TextInput
            style={baseStyles.input}
            placeholder="yourname@upi  (e.g. PhonePe, GPay, Paytm)"
            placeholderTextColor={C.muted}
            value={upiId}
            onChangeText={setUpiId}
            autoCapitalize="none"
            keyboardType="email-address"
            onFocus={() => setFocused('upi')}
            onBlur={() => setFocused(null)}
          />
        </View>

        <Pressable style={local.toggleBank} onPress={() => setShowBankFields((v) => !v)}>
          <Text style={local.toggleBankText}>
            {showBankFields ? 'Hide bank account' : '+ Add bank account (Account No. & IFSC)'}
          </Text>
        </Pressable>

        {showBankFields && (
          <>
            <Text style={local.subLabel}>Account number</Text>
            <View style={[baseStyles.inputShell, focused === 'acc' && baseStyles.inputFocused]}>
              <TextInput
                style={baseStyles.input}
                placeholder="e.g. 1234567890"
                placeholderTextColor={C.muted}
                value={accountNo}
                onChangeText={setAccountNo}
                keyboardType="numeric"
                onFocus={() => setFocused('acc')}
                onBlur={() => setFocused(null)}
              />
            </View>

            <Text style={local.subLabel}>IFSC code</Text>
            <View style={[baseStyles.inputShell, focused === 'ifsc' && baseStyles.inputFocused]}>
              <TextInput
                style={baseStyles.input}
                placeholder="e.g. SBIN0001234"
                placeholderTextColor={C.muted}
                value={ifsc}
                onChangeText={(t) => setIfsc(t.toUpperCase())}
                autoCapitalize="characters"
                onFocus={() => setFocused('ifsc')}
                onBlur={() => setFocused(null)}
              />
            </View>
          </>
        )}

        <View style={local.spacerBottom} />

        <Pressable
          style={({ pressed }) => [
            baseStyles.button,
            canSubmit && baseStyles.buttonPrimary,
            (!canSubmit || isSubmitting) && baseStyles.buttonDisabled,
            pressed && canSubmit && baseStyles.buttonPressed,
          ]}
          onPress={handleSubmit}
          disabled={!canSubmit || isSubmitting}
        >
          {isSubmitting ? (
            <ActivityIndicator size="small" color={C.btnText} />
          ) : (
            <Text style={[baseStyles.buttonText, canSubmit && baseStyles.buttonTextPrimary]}>
              Submit profile
            </Text>
          )}
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const local = StyleSheet.create({
  scroll: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 40,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: C.ink,
    marginTop: 20,
    marginBottom: 8,
  },
  sectionLabel: {
    marginTop: 28,
    fontSize: 15,
  },
  labelMuted: {
    fontWeight: '400',
    color: C.muted,
    fontSize: 12,
  },
  required: {
    color: C.accent,
  },
  subLabel: {
    fontSize: 12,
    fontWeight: '500',
    color: C.muted,
    marginTop: 10,
    marginBottom: 6,
  },
  hint: {
    fontSize: 13,
    color: C.muted,
    marginBottom: 4,
  },
  chipWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 4,
  },
  chip: {
    backgroundColor: '#e8f5e9',
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  chipText: {
    fontSize: 13,
    color: '#2e7d32',
    fontWeight: '600',
  },
  chipActive: {
    backgroundColor: '#203428',
  },
  chipTextActive: {
    color: '#fffdf8',
  },
  toggleBank: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 10,
  },
  toggleBankText: {
    fontSize: 13,
    color: '#203428',
    fontWeight: '600',
  },
  spacerBottom: {
    height: 32,
  },
});
