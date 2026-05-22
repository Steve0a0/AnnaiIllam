import React, { useCallback, useState } from 'react';
import { ActivityIndicator, StyleSheet } from 'react-native';
import { AlertCircle, CheckCircle, Clock, MessageSquare } from 'lucide-react-native';
import { Button, Card, ScrollView, Text, View, XStack, YStack } from 'tamagui';
import { useFocusEffect, useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';
import { ChevronLeft } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { workerIssuesService, type WorkerIssue } from '../../../shared/services/worker-issues.service';
import type { HomeStackParamList } from '../navigation/types';

type Navigation = NativeStackNavigationProp<HomeStackParamList>;
type RouteProps = NativeStackScreenProps<HomeStackParamList, 'IssueDetail'>['route'];

const C = {
  page: '#F5F5F4',
  card: '#FFFFFF',
  brand600: '#1A6640',
  neutral900: '#1C1917',
  neutral700: '#44403C',
  neutral500: '#78716C',
  neutral200: '#E7E5E4',
  success100: '#DCFCE7',
  success700: '#15803D',
  warning100: '#FEF3C7',
  warning700: '#B45309',
  danger100: '#FEE2E2',
  danger700: '#B91C1C',
  info100: '#DBEAFE',
  info700: '#1D4ED8',
};

function statusColors(status: string) {
  switch (status) {
    case 'resolved': return { bg: C.success100, text: C.success700 };
    case 'in_review': return { bg: C.info100, text: C.info700 };
    case 'closed': return { bg: '#F5F5F4', text: C.neutral500 };
    default: return { bg: C.warning100, text: C.warning700 };
  }
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'resolved') return <CheckCircle size={20} color={C.success700} />;
  if (status === 'in_review') return <Clock size={20} color={C.info700} />;
  if (status === 'open') return <AlertCircle size={20} color={C.warning700} />;
  return <MessageSquare size={20} color={C.neutral500} />;
}

export default function IssueDetailScreen() {
  const navigation = useNavigation<Navigation>();
  const route = useRoute<RouteProps>();
  const insets = useSafeAreaInsets();
  const { issueId } = route.params;

  const [issue, setIssue] = useState<WorkerIssue | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);
      setError(null);
      workerIssuesService
        .list()
        .then((all) => {
          if (!active) return;
          const found = all.find((i) => i.id === issueId) ?? null;
          setIssue(found);
          if (!found) setError('Issue not found.');
        })
        .catch(() => active && setError('Failed to load issue.'))
        .finally(() => active && setIsLoading(false));
      return () => { active = false; };
    }, [issueId]),
  );

  const statusCol = issue ? statusColors(issue.status) : null;

  return (
    <View flex={1} backgroundColor={C.page} paddingTop={insets.top}>
      <ScrollView flex={1} contentContainerStyle={{ padding: 16, gap: 16 }}>
        {/* Header */}
        <XStack alignItems="center" gap="$2" marginBottom="$1">
          <Button
            chromeless
            circular
            size="$3"
            icon={<ChevronLeft size={20} color={C.brand600} />}
            onPress={() => navigation.goBack()}
          />
          <Text fontSize={22} fontWeight="700" color={C.neutral900}>Issue Detail</Text>
        </XStack>

        {isLoading ? (
          <Card backgroundColor={C.card} borderRadius={12} padding="$5" alignItems="center" justifyContent="center" minHeight={160} gap="$2">
            <ActivityIndicator color={C.brand600} />
            <Text color={C.neutral500}>Loading issue...</Text>
          </Card>
        ) : error || !issue ? (
          <Card backgroundColor={C.card} borderRadius={12} padding="$5" alignItems="center" justifyContent="center" minHeight={160} gap="$2">
            <AlertCircle size={24} color={C.danger700} />
            <Text color={C.neutral500} textAlign="center">{error ?? 'Issue not found.'}</Text>
          </Card>
        ) : (
          <>
            {/* Status card */}
            <Card backgroundColor={C.card} borderRadius={12} padding="$4" borderWidth={1} borderColor={C.neutral200}>
              <XStack alignItems="flex-start" gap="$3">
                <StatusIcon status={issue.status} />
                <YStack flex={1} gap="$2">
                  <Text fontSize={16} fontWeight="700" color={C.neutral900} textTransform="capitalize">
                    {issue.issue_type.replace(/_/g, ' ')}
                  </Text>
                  <View style={[ss.badge, { backgroundColor: statusCol!.bg }]}>
                    <Text style={[ss.badgeText, { color: statusCol!.text }]}>{issue.status.replace(/_/g, ' ')}</Text>
                  </View>
                </YStack>
              </XStack>
            </Card>

            {/* Details */}
            <Card backgroundColor={C.card} borderRadius={12} padding="$4" borderWidth={1} borderColor={C.neutral200}>
              <Text fontSize={11} fontWeight="700" color={C.neutral500} textTransform="uppercase" letterSpacing={1} marginBottom="$3">
                Details
              </Text>
              <YStack gap="$2">
                {issue.assignment_id ? (
                  <XStack justifyContent="space-between">
                    <Text fontSize={13} color={C.neutral500}>Assignment</Text>
                    <Text fontSize={13} fontWeight="600" color={C.neutral900}>#{issue.assignment_id}</Text>
                  </XStack>
                ) : null}
                <XStack justifyContent="space-between">
                  <Text fontSize={13} color={C.neutral500}>Reported on</Text>
                  <Text fontSize={13} fontWeight="600" color={C.neutral900}>{new Date(issue.created_at).toLocaleString()}</Text>
                </XStack>
              </YStack>
            </Card>

            {/* Description */}
            <Card backgroundColor={C.card} borderRadius={12} padding="$4" borderWidth={1} borderColor={C.neutral200}>
              <Text fontSize={11} fontWeight="700" color={C.neutral500} textTransform="uppercase" letterSpacing={1} marginBottom="$2">
                Description
              </Text>
              <Text fontSize={14} color={C.neutral700} lineHeight={22}>{issue.description}</Text>
            </Card>

            {/* Resolution */}
            {issue.resolution_notes ? (
              <Card backgroundColor={C.success100} borderRadius={12} padding="$4" borderWidth={1} borderColor="#86EFAC">
                <Text fontSize={11} fontWeight="700" color={C.success700} textTransform="uppercase" letterSpacing={1} marginBottom="$2">
                  Resolution
                </Text>
                <Text fontSize={14} color={C.neutral700} lineHeight={22}>{issue.resolution_notes}</Text>
              </Card>
            ) : null}
          </>
        )}
      </ScrollView>
    </View>
  );
}

const ss = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
});
