import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, TextInput } from 'react-native';
import { Button, Card, ScrollView, Text, View, XStack, YStack } from 'tamagui';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { ChevronLeft } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { workerIssuesService } from '../../../shared/services/worker-issues.service';
import { workerAssignmentsService, type WorkerAssignment } from '../../../shared/services/worker-assignments.service';
import type { HomeStackParamList } from '../navigation/types';

type Navigation = NativeStackNavigationProp<HomeStackParamList>;

const C = {
  page: '#F5F5F4',
  card: '#FFFFFF',
  brand600: '#1A6640',
  brand100: '#D4F0E3',
  neutral900: '#1C1917',
  neutral700: '#44403C',
  neutral500: '#78716C',
  neutral200: '#E7E5E4',
  border: '#E7E5E4',
  danger700: '#B91C1C',
};

const ISSUE_TYPES = [
  { value: 'safety', label: 'Safety Concern' },
  { value: 'payment', label: 'Payment Issue' },
  { value: 'worksite', label: 'Worksite Problem' },
  { value: 'health', label: 'Health & Welfare' },
  { value: 'harassment', label: 'Harassment / Misconduct' },
  { value: 'other', label: 'Other' },
];

export default function RaiseIssueScreen() {
  const navigation = useNavigation<Navigation>();
  const insets = useSafeAreaInsets();

  const [assignments, setAssignments] = useState<WorkerAssignment[]>([]);
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<number | null>(null);
  const [issueType, setIssueType] = useState<string | null>(null);
  const [description, setDescription] = useState('');
  const [isLoadingAssignments, setIsLoadingAssignments] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    workerAssignmentsService
      .list()
      .then((data) => setAssignments(data.filter((a) => a.status === 'accepted' || a.status === 'active' || a.status === 'assigned')))
      .catch(() => {})
      .finally(() => setIsLoadingAssignments(false));
  }, []);

  const submit = useCallback(async () => {
    if (!issueType) { Alert.alert('Select issue type', 'Please choose the type of issue.'); return; }
    if (description.trim().length < 10) { Alert.alert('Add detail', 'Please describe the issue in at least 10 characters.'); return; }

    setIsSubmitting(true);
    try {
      await workerIssuesService.create({
        assignment_id: selectedAssignmentId ?? undefined,
        issue_type: issueType,
        description: description.trim(),
      });
      Alert.alert('Issue reported', 'Your issue has been submitted. We will look into it promptly.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { message?: string } } })?.response?.data?.message ?? 'Failed to submit. Please try again.';
      Alert.alert('Error', msg);
    } finally {
      setIsSubmitting(false);
    }
  }, [issueType, description, selectedAssignmentId, navigation]);

  return (
    <View flex={1} backgroundColor={C.page} paddingTop={insets.top}>
      <ScrollView flex={1} contentContainerStyle={{ padding: 16, gap: 16 }} keyboardShouldPersistTaps="handled">
        {/* Header */}
        <XStack alignItems="center" gap="$2" marginBottom="$1">
          <Button
            chromeless
            circular
            size="$3"
            icon={<ChevronLeft size={20} color={C.brand600} />}
            onPress={() => navigation.goBack()}
          />
          <YStack flex={1}>
            <Text fontSize={22} fontWeight="700" color={C.neutral900}>Report Issue</Text>
            <Text fontSize={13} color={C.neutral500}>Tell us what happened and we'll help resolve it.</Text>
          </YStack>
        </XStack>

        {/* Assignment (optional) */}
        <Card backgroundColor={C.card} borderRadius={12} padding="$4" borderWidth={1} borderColor={C.border}>
          <Text fontSize={11} fontWeight="700" color={C.neutral500} textTransform="uppercase" letterSpacing={1} marginBottom="$2">
            Related Assignment (optional)
          </Text>
          {isLoadingAssignments ? (
            <ActivityIndicator color={C.brand600} />
          ) : assignments.length === 0 ? (
            <Text fontSize={13} color={C.neutral500}>No active assignments found.</Text>
          ) : (
            <YStack gap="$2">
              <View
                style={[ss.chip, selectedAssignmentId === null && ss.chipSelected]}
                onTouchEnd={() => setSelectedAssignmentId(null)}
              >
                <Text style={[ss.chipText, selectedAssignmentId === null && ss.chipTextSelected]}>None</Text>
              </View>
              {assignments.map((a) => {
                const isSelected = selectedAssignmentId === a.assignment_id;
                return (
                  <View
                    key={a.assignment_id}
                    style={[ss.chip, isSelected && ss.chipSelected]}
                    onTouchEnd={() => setSelectedAssignmentId(a.assignment_id)}
                  >
                    <Text style={[ss.chipText, isSelected && ss.chipTextSelected]}>
                      #{a.assignment_id} · {a.requirement?.category ?? 'Assignment'} · {a.requirement?.city ?? ''}
                    </Text>
                  </View>
                );
              })}
            </YStack>
          )}
        </Card>

        {/* Issue type */}
        <Card backgroundColor={C.card} borderRadius={12} padding="$4" borderWidth={1} borderColor={C.border}>
          <Text fontSize={11} fontWeight="700" color={C.neutral500} textTransform="uppercase" letterSpacing={1} marginBottom="$2">
            Issue Type
          </Text>
          <YStack gap="$2">
            {ISSUE_TYPES.map((t) => {
              const isSelected = issueType === t.value;
              return (
                <View
                  key={t.value}
                  style={[ss.chip, isSelected && ss.chipSelected]}
                  onTouchEnd={() => setIssueType(t.value)}
                >
                  <Text style={[ss.chipText, isSelected && ss.chipTextSelected]}>{t.label}</Text>
                </View>
              );
            })}
          </YStack>
        </Card>

        {/* Description */}
        <Card backgroundColor={C.card} borderRadius={12} padding="$4" borderWidth={1} borderColor={C.border}>
          <Text fontSize={11} fontWeight="700" color={C.neutral500} textTransform="uppercase" letterSpacing={1} marginBottom="$2">
            Description
          </Text>
          <TextInput
            style={ss.textArea}
            placeholder="Describe the issue in detail..."
            placeholderTextColor={C.neutral500}
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={5}
            maxLength={2000}
          />
          <Text style={ss.charCount}>{description.length}/2000</Text>
        </Card>

        <Button
          backgroundColor={C.brand600}
          color="white"
          fontWeight="600"
          height={52}
          borderRadius={12}
          opacity={isSubmitting ? 0.6 : 1}
          onPress={submit}
          disabled={isSubmitting}
          icon={isSubmitting ? <ActivityIndicator color="white" size="small" /> : undefined}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Issue'}
        </Button>
      </ScrollView>
    </View>
  );
}

const ss = StyleSheet.create({
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: '#E7E5E4',
    backgroundColor: '#FAFAF9',
  },
  chipSelected: {
    borderColor: '#1A6640',
    backgroundColor: '#EDFAF3',
  },
  chipText: {
    fontSize: 14,
    color: '#44403C',
    fontWeight: '500',
  },
  chipTextSelected: {
    color: '#1A6640',
    fontWeight: '700',
  },
  textArea: {
    minHeight: 100,
    paddingTop: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E7E5E4',
    backgroundColor: '#FAFAF9',
    color: '#1C1917',
    fontSize: 14,
    textAlignVertical: 'top',
  },
  charCount: {
    fontSize: 11,
    color: '#78716C',
    textAlign: 'right',
    marginTop: 4,
  },
});
