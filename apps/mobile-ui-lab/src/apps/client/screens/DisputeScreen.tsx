import React, { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';
import { CheckCircle } from 'lucide-react-native';
import {
  clientDisputesService,
  type DisputeType,
} from '../../../shared/services/client-disputes.service';
import type { HomeStackParamList } from '../navigation/types';
import { ScreenHeader } from './components';
import { C, clientStyles } from './clientStyles';

type Props = NativeStackScreenProps<HomeStackParamList, 'RaiseDispute'>;
type Navigation = NativeStackNavigationProp<HomeStackParamList>;

const DISPUTE_TYPES: { value: DisputeType; label: string; description: string }[] = [
  { value: 'attendance', label: 'Attendance', description: 'Worker attendance records are incorrect' },
  { value: 'quality', label: 'Quality', description: 'Work quality did not meet expectations' },
  { value: 'billing', label: 'Billing', description: 'Invoice or charges are incorrect' },
  { value: 'other', label: 'Other', description: 'Other issue not listed above' },
];

export default function DisputeScreen({ route }: Props) {
  const { requirementId } = route.params;
  const navigation = useNavigation<Navigation>();
  const insets = useSafeAreaInsets();

  const [selectedType, setSelectedType] = useState<DisputeType | null>(null);
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (!selectedType) {
      setError('Please select a dispute type.');
      return;
    }
    if (description.trim().length < 20) {
      setError('Description must be at least 20 characters.');
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await clientDisputesService.raise({
        requirement_id: requirementId,
        dispute_type: selectedType,
        description: description.trim(),
      });
      setSubmitted(true);
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        'Failed to raise dispute. Please try again.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <View style={[clientStyles.root, { paddingTop: insets.top }]}>
      <ScreenHeader title="Raise a Dispute" onBack={() => navigation.goBack()} />

      {submitted ? (
        <View style={s.successContainer}>
          <View style={s.successIcon}>
            <CheckCircle size={40} color={C.brand} />
          </View>
          <Text style={s.successTitle}>Dispute Raised</Text>
          <Text style={s.successBody}>
            Your dispute has been submitted. Our team will review it and get back to you shortly.
          </Text>
          <Pressable
            style={({ pressed }) => [clientStyles.primaryButton, pressed && { opacity: 0.85 }, s.doneBtn]}
            onPress={() => navigation.goBack()}
          >
            <Text style={clientStyles.primaryButtonText}>Done</Text>
          </Pressable>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={[clientStyles.content, { paddingBottom: insets.bottom + 24 }]}
          keyboardShouldPersistTaps="handled"
        >
          <View>
            <Text style={s.heading}>What would you like to dispute?</Text>
            <Text style={s.subHeading}>
              Disputes can only be raised on completed requirements. Our team will review your case
              within 2 business days.
            </Text>
          </View>

          {/* Dispute type selection */}
          <View style={s.section}>
            <Text style={clientStyles.fieldLabel}>Dispute type <Text style={s.required}>*</Text></Text>
            {DISPUTE_TYPES.map((t) => (
              <Pressable
                key={t.value}
                style={({ pressed }) => [
                  s.typeCard,
                  selectedType === t.value && s.typeCardSelected,
                  pressed && { opacity: 0.85 },
                ]}
                onPress={() => {
                  setSelectedType(t.value);
                  setError(null);
                }}
              >
                <View style={s.typeCardInner}>
                  <View style={[s.radio, selectedType === t.value && s.radioSelected]} />
                  <View style={{ flex: 1 }}>
                    <Text style={[s.typeLabel, selectedType === t.value && s.typeLabelSelected]}>
                      {t.label}
                    </Text>
                    <Text style={s.typeDesc}>{t.description}</Text>
                  </View>
                </View>
              </Pressable>
            ))}
          </View>

          {/* Description */}
          <View style={s.section}>
            <Text style={clientStyles.fieldLabel}>
              Description <Text style={s.required}>*</Text>
            </Text>
            <TextInput
              style={[clientStyles.input, clientStyles.textArea]}
              value={description}
              onChangeText={(t) => { setDescription(t); setError(null); }}
              placeholder="Describe the issue in detail (min. 20 characters)…"
              placeholderTextColor={C.muted}
              multiline
              textAlignVertical="top"
            />
            <Text style={s.charCount}>{description.trim().length} / 20 min</Text>
          </View>

          {error && (
            <View style={s.errorBox}>
              <Text style={s.errorText}>{error}</Text>
            </View>
          )}

          <Pressable
            style={({ pressed }) => [
              clientStyles.primaryButton,
              (pressed || submitting) && { opacity: 0.75 },
            ]}
            disabled={submitting}
            onPress={handleSubmit}
          >
            {submitting
              ? <ActivityIndicator size="small" color="#fff" />
              : <Text style={clientStyles.primaryButtonText}>Submit Dispute</Text>
            }
          </Pressable>
        </ScrollView>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  heading: {
    fontSize: 20,
    fontWeight: '700',
    color: C.ink,
    marginBottom: 6,
  },
  subHeading: {
    fontSize: 13,
    color: C.muted,
    lineHeight: 20,
  },
  section: {
    gap: 8,
  },
  required: {
    color: C.dangerText,
  },
  typeCard: {
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 10,
    padding: 12,
    backgroundColor: C.surface,
  },
  typeCardSelected: {
    borderColor: C.brand,
    backgroundColor: C.brandSoft,
  },
  typeCardInner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  radio: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: C.border,
    marginTop: 2,
  },
  radioSelected: {
    borderColor: C.brand,
    backgroundColor: C.brand,
  },
  typeLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: C.ink,
  },
  typeLabelSelected: {
    color: C.brand,
  },
  typeDesc: {
    fontSize: 12,
    color: C.muted,
    marginTop: 2,
  },
  charCount: {
    fontSize: 11,
    color: C.muted,
    textAlign: 'right',
  },
  errorBox: {
    backgroundColor: C.dangerBg,
    borderRadius: 10,
    padding: 12,
  },
  errorText: {
    color: C.dangerText,
    fontSize: 13,
  },
  successContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    gap: 16,
  },
  successIcon: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: C.brandSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  successTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: C.ink,
    textAlign: 'center',
  },
  successBody: {
    fontSize: 14,
    color: C.muted,
    textAlign: 'center',
    lineHeight: 22,
  },
  doneBtn: {
    marginTop: 8,
    alignSelf: 'stretch',
  },
});
