import React, { useCallback, useState } from 'react';
import { ActivityIndicator, RefreshControl, StyleSheet } from 'react-native';
import { AlertCircle, MessageCircleWarning, Plus } from 'lucide-react-native';
import { Button, Card, ScrollView, Text, View, XStack, YStack } from 'tamagui';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { workerIssuesService, type WorkerIssue } from '../../../shared/services/worker-issues.service';
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

function StatusBadge({ value }: { value: string }) {
  const colors = statusColors(value);
  return (
    <View style={[ss.badge, { backgroundColor: colors.bg }]}>
      <Text style={[ss.badgeText, { color: colors.text }]}>{value.replace(/_/g, ' ')}</Text>
    </View>
  );
}

export default function IssuesScreen() {
  const navigation = useNavigation<Navigation>();
  const insets = useSafeAreaInsets();
  const [items, setItems] = useState<WorkerIssue[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    const data = await workerIssuesService.list();
    setItems(data);
  }, []);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);
      load().catch((e) => active && setError(e?.response?.data?.message ?? 'Failed to load issues')).finally(() => active && setIsLoading(false));
      return () => { active = false; };
    }, [load]),
  );

  const refresh = async () => {
    setIsRefreshing(true);
    await load().catch(() => {});
    setIsRefreshing(false);
  };

  return (
    <View flex={1} backgroundColor={C.page} paddingTop={insets.top}>
      <ScrollView
        flex={1}
        contentContainerStyle={{ padding: 16, gap: 16 }}
        refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={refresh} tintColor={C.brand600} />}
      >
        {/* Header */}
        <YStack gap="$1" marginBottom="$2">
          <Text fontSize={24} fontWeight="700" color={C.neutral900}>My Issues</Text>
          <Text fontSize={13} color={C.neutral500}>Track issues you've reported about your assignments.</Text>
        </YStack>

        <Button
          backgroundColor={C.brand600}
          color="white"
          fontWeight="600"
          height={52}
          borderRadius={12}
          onPress={() => navigation.navigate('RaiseIssue')}
          icon={<Plus size={18} color="white" />}
        >
          Report an issue
        </Button>

        {isLoading ? (
          <Card backgroundColor={C.card} borderRadius={12} padding="$4" alignItems="center" justifyContent="center" minHeight={160}>
            <ActivityIndicator color={C.brand600} />
            <Text color={C.neutral500} marginTop="$2">Loading issues...</Text>
          </Card>
        ) : error ? (
          <Card backgroundColor={C.card} borderRadius={12} padding="$4" alignItems="center" justifyContent="center" minHeight={160} gap="$2">
            <AlertCircle size={24} color={C.danger700} />
            <Text color={C.neutral500} textAlign="center">{error}</Text>
          </Card>
        ) : items.length === 0 ? (
          <Card backgroundColor={C.card} borderRadius={12} padding="$5" alignItems="center" justifyContent="center" minHeight={160} gap="$2">
            <MessageCircleWarning size={28} color={C.neutral500} />
            <Text fontSize={15} fontWeight="600" color={C.neutral900}>No issues reported</Text>
            <Text color={C.neutral500} textAlign="center">Issues you report will appear here.</Text>
          </Card>
        ) : (
          items.map((item) => (
            <Card
              key={item.id}
              backgroundColor={C.card}
              borderRadius={12}
              padding="$4"
              borderWidth={1}
              borderColor={C.neutral200}
              pressStyle={{ opacity: 0.7 }}
              onPress={() => navigation.navigate('IssueDetail', { issueId: item.id })}
            >
              <XStack justifyContent="space-between" alignItems="center" marginBottom="$2">
                <StatusBadge value={item.status} />
                <Text fontSize={12} color={C.neutral500}>{new Date(item.created_at).toLocaleDateString()}</Text>
              </XStack>
              <Text fontSize={15} fontWeight="700" color={C.neutral900} textTransform="capitalize" marginBottom="$1">
                {item.issue_type.replace(/_/g, ' ')}
              </Text>
              <Text fontSize={13} color={C.neutral700} numberOfLines={2}>{item.description}</Text>
              {item.assignment_id ? (
                <Text fontSize={12} color={C.neutral500} marginTop="$2">Assignment #{item.assignment_id}</Text>
              ) : null}
            </Card>
          ))
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
