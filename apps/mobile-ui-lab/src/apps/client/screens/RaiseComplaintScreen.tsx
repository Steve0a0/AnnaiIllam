import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { clientComplaintsService, type ComplaintType, type ComplaintSeverity } from '../../../shared/services/client-complaints.service';
import { clientRequirementsService, type ClientRequirementListItem } from '../../../shared/services/client-requirements.service';
import type { ComplaintsStackParamList } from '../navigation/types';
import { ScreenHeader } from './components';
import { C, clientStyles } from './clientStyles';

type Navigation = NativeStackNavigationProp<ComplaintsStackParamList>;
type RouteProps = NativeStackScreenProps<ComplaintsStackParamList, 'RaiseComplaint'>['route'];

const COMPLAINT_TYPES: { value: ComplaintType; label: string }[] = [
  { value: 'absent', label: 'Worker Absent' },
  { value: 'behavior', label: 'Behavior Issue' },
  { value: 'performance', label: 'Poor Performance' },
  { value: 'payment', label: 'Payment Issue' },
  { value: 'replacement_request', label: 'Request Replacement' },
  { value: 'other', label: 'Other' },
];

const SEVERITY_OPTIONS: { value: ComplaintSeverity; label: string; color: string }[] = [
  { value: 'low', label: 'Low', color: '#059669' },
  { value: 'medium', label: 'Medium', color: C.warningText },
  { value: 'high', label: 'High', color: C.dangerText },
  { value: 'urgent', label: 'Urgent', color: '#7F1D1D' },
];

export default function RaiseComplaintScreen() {
  const navigation = useNavigation<Navigation>();
  const route = useRoute<RouteProps>();
  const insets = useSafeAreaInsets();

  const [requirements, setRequirements] = useState<ClientRequirementListItem[]>([]);
  const [requirementId, setRequirementId] = useState<number | null>(route.params?.requirementId ?? null);
  const [complaintType, setComplaintType] = useState<ComplaintType | null>(null);
  const [severity, setSeverity] = useState<ComplaintSeverity>('medium');
  const [description, setDescription] = useState('');
  const [isLoadingReqs, setIsLoadingReqs] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    clientRequirementsService
      .list()
      .then(setRequirements)
      .catch(() => {})
      .finally(() => setIsLoadingReqs(false));
  }, []);

  const submit = useCallback(async () => {
    if (!requirementId) { Alert.alert('Select a request', 'Please pick the job request this complaint is about.'); return; }
    if (!complaintType) { Alert.alert('Select type', 'Please choose a complaint type.'); return; }
    if (description.trim().length < 10) { Alert.alert('Add detail', 'Please describe the issue in at least 10 characters.'); return; }

    setIsSubmitting(true);
    try {
      await clientComplaintsService.create({
        requirement_id: requirementId,
        complaint_type: complaintType,
        severity,
        description: description.trim(),
      });
      Alert.alert('Complaint raised', 'Your complaint has been submitted and our team will review it shortly.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { message?: string } } })?.response?.data?.message ?? 'Failed to submit. Please try again.';
      Alert.alert('Error', msg);
    } finally {
      setIsSubmitting(false);
    }
  }, [requirementId, complaintType, severity, description, navigation]);

  return (
    <View style={[clientStyles.root, { paddingTop: insets.top }]}>
      <ScrollView contentContainerStyle={clientStyles.content} keyboardShouldPersistTaps="handled">
        <ScreenHeader title="Raise Complaint" subtitle="Tell us what went wrong and we'll look into it." onBack={() => navigation.goBack()} />

        {/* Requirement picker */}
        <View style={clientStyles.card}>
          <Text style={clientStyles.sectionLabel}>Job Request</Text>
          {isLoadingReqs ? (
            <ActivityIndicator color={C.brand} style={{ marginTop: 12 }} />
          ) : requirements.length === 0 ? (
            <Text style={[clientStyles.subtitle, { marginTop: 8 }]}>No active requests found.</Text>
          ) : (
            <View style={styles.optionList}>
              {requirements.map((req) => {
                const isSelected = requirementId === req.id;
                return (
                  <Pressable
                    key={req.id}
                    style={[styles.optionChip, isSelected && styles.optionChipSelected]}
                    onPress={() => setRequirementId(req.id)}
                  >
                    <Text style={[styles.optionChipText, isSelected && styles.optionChipTextSelected]}>
                      #{req.id} · {req.category} · {req.city}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          )}
        </View>

        {/* Complaint type */}
        <View style={clientStyles.card}>
          <Text style={clientStyles.sectionLabel}>Complaint Type</Text>
          <View style={styles.optionList}>
            {COMPLAINT_TYPES.map((t) => {
              const isSelected = complaintType === t.value;
              return (
                <Pressable
                  key={t.value}
                  style={[styles.optionChip, isSelected && styles.optionChipSelected]}
                  onPress={() => setComplaintType(t.value)}
                >
                  <Text style={[styles.optionChipText, isSelected && styles.optionChipTextSelected]}>{t.label}</Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        {/* Severity */}
        <View style={clientStyles.card}>
          <Text style={clientStyles.sectionLabel}>Severity</Text>
          <View style={styles.severityRow}>
            {SEVERITY_OPTIONS.map((s) => {
              const isSelected = severity === s.value;
              return (
                <Pressable
                  key={s.value}
                  style={[styles.severityChip, isSelected && { backgroundColor: s.color, borderColor: s.color }]}
                  onPress={() => setSeverity(s.value)}
                >
                  <Text style={[styles.severityChipText, isSelected && { color: '#FFFFFF' }]}>{s.label}</Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        {/* Description */}
        <View style={clientStyles.card}>
          <Text style={clientStyles.sectionLabel}>Description</Text>
          <TextInput
            style={[clientStyles.input, clientStyles.textArea, { marginTop: 8 }]}
            placeholder="Describe the issue in detail..."
            placeholderTextColor={C.muted}
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={5}
            maxLength={2000}
          />
          <Text style={styles.charCount}>{description.length}/2000</Text>
        </View>

        <Pressable
          style={[clientStyles.primaryButton, isSubmitting && { opacity: 0.6 }]}
          onPress={submit}
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <ActivityIndicator color="#FFFFFF" size="small" />
          ) : (
            <Text style={clientStyles.primaryButtonText}>Submit Complaint</Text>
          )}
        </Pressable>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  optionList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 10,
  },
  optionChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: C.border,
    backgroundColor: C.surfaceAlt,
  },
  optionChipSelected: {
    borderColor: C.brand,
    backgroundColor: C.brandSoft,
  },
  optionChipText: {
    fontSize: 13,
    color: C.body,
    fontWeight: '500',
  },
  optionChipTextSelected: {
    color: C.brand,
    fontWeight: '700',
  },
  severityRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 10,
  },
  severityChip: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: C.border,
    alignItems: 'center',
  },
  severityChipText: {
    fontSize: 13,
    fontWeight: '600',
    color: C.body,
  },
  charCount: {
    fontSize: 11,
    color: C.muted,
    textAlign: 'right',
    marginTop: 4,
  },
});
