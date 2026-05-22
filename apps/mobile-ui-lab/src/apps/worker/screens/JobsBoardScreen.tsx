import React, { useCallback, useState } from 'react';
import { ActivityIndicator, Alert, RefreshControl } from 'react-native';
import {
  BriefcaseBusiness,
  CalendarDays,
  Check,
  ChevronDown,
  ChevronUp,
  MapPin,
  Star,
  Utensils,
  X,
} from 'lucide-react-native';
import {
  Button,
  Card,
  ScrollView,
  Text,
  View,
  XStack,
  YStack,
} from 'tamagui';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  workerJobsService,
  type OpenJob,
} from '../../../shared/services/worker-jobs.service';

const C = {
  page: '#F5F5F4',
  card: '#FFFFFF',
  brand900: '#0D2E1E',
  brand600: '#1A6640',
  brand400: '#25A263',
  brand100: '#D4F0E3',
  neutral900: '#1C1917',
  neutral700: '#44403C',
  neutral500: '#78716C',
  neutral300: '#D6D3D1',
  neutral200: '#E7E5E4',
  success100: '#DCFCE7',
  success700: '#15803D',
  warning100: '#FEF3C7',
  warning700: '#B45309',
  info100: '#DBEAFE',
  info700: '#1D4ED8',
};

type Props = Record<string, never>;

export default function JobsBoardScreen(_props: Props) {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const [jobs, setJobs] = useState<OpenJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [actionId, setActionId] = useState<number | null>(null);
  const [showOther, setShowOther] = useState(false);

  const load = useCallback(async () => {
    const data = await workerJobsService.getOpenJobs();
    setJobs(data);
  }, []);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);
      load()
        .catch(() => {
          if (active) Alert.alert('Could not load jobs', 'Pull down to refresh.');
        })
        .finally(() => active && setIsLoading(false));
      return () => { active = false; };
    }, [load]),
  );

  const refresh = async () => {
    setIsRefreshing(true);
    try { await load(); } finally { setIsRefreshing(false); }
  };

  const toggleInterest = async (job: OpenJob) => {
    const isInterested = job.my_interest === 'interested';
    const title = isInterested ? 'Withdraw interest?' : 'Express interest?';
    const message = isInterested
      ? 'You will no longer appear as available for this job.'
      : 'This tells admin you are available. You are not assigned yet.';

    Alert.alert(title, message, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: isInterested ? 'Withdraw' : "I'm Available",
        style: isInterested ? 'destructive' : 'default',
        onPress: async () => {
          setActionId(job.requirement_id);
          try {
            if (isInterested) {
              await workerJobsService.withdrawInterest(job.requirement_id);
            } else {
              await workerJobsService.expressInterest(job.requirement_id);
            }
            await load();
          } catch {
            Alert.alert('Could not update', 'Please try again.');
          } finally {
            setActionId(null);
          }
        },
      },
    ]);
  };

  const bestJobs = jobs.filter((j) => j.match_tier === 'best');
  const nearbyJobs = jobs.filter((j) => j.match_tier === 'nearby');
  const otherJobs = jobs.filter((j) => j.match_tier === 'other');

  return (
    <View flex={1} backgroundColor={C.page} paddingTop={insets.top}>
      {/* Header */}
      <XStack
        height={56}
        paddingHorizontal={20}
        alignItems="center"
        justifyContent="space-between"
      >
        <YStack>
          <Text fontSize={18} fontWeight="600" color={C.neutral900}>
            Jobs for You
          </Text>
          <Text fontSize={12} color={C.neutral500}>
            Based on your profile
          </Text>
        </YStack>
      </XStack>

      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={refresh} />}
      >
        <YStack paddingBottom={insets.bottom + 32} paddingHorizontal={16} gap={20} marginTop={8}>
          {isLoading ? (
            <YStack alignItems="center" paddingTop={60} gap={12}>
              <ActivityIndicator color={C.brand600} />
              <Text color={C.neutral500} fontSize={14}>Loading jobs...</Text>
            </YStack>
          ) : jobs.length === 0 ? (
            <YStack
              borderRadius={16}
              backgroundColor={C.card}
              padding={32}
              alignItems="center"
              gap={12}
              borderWidth={1}
              borderColor={C.neutral200}
            >
              <BriefcaseBusiness size={36} color={C.neutral300} />
              <Text fontSize={16} fontWeight="500" color={C.neutral900}>No open jobs right now</Text>
              <Text fontSize={13} color={C.neutral500} textAlign="center">
                New jobs will appear here once admin approves a client request.
              </Text>
            </YStack>
          ) : (
            <>
              {/* ── Best Match section ── */}
              <SectionHeader
                label="BEST MATCH"
                subtitle="Matches your category and city"
                count={bestJobs.length}
                accentColor={C.brand600}
                icon={<Star size={14} color={C.brand600} />}
              />
              {bestJobs.length === 0 ? (
                <EmptySection message="No best-match jobs right now. Check nearby jobs below." />
              ) : (
                bestJobs.map((job) => (
                  <JobCard
                    key={job.requirement_id}
                    job={job}
                    isBusy={actionId === job.requirement_id}
                    onToggle={() => toggleInterest(job)}
                  />
                ))
              )}

              {/* ── Nearby section ── */}
              {nearbyJobs.length > 0 ? (
                <>
                  <SectionHeader
                    label="NEARBY JOBS"
                    subtitle="Same state, different category"
                    count={nearbyJobs.length}
                    accentColor={C.info700}
                    icon={<MapPin size={14} color={C.info700} />}
                  />
                  {nearbyJobs.map((job) => (
                    <JobCard
                      key={job.requirement_id}
                      job={job}
                      isBusy={actionId === job.requirement_id}
                      onToggle={() => toggleInterest(job)}
                    />
                  ))}
                </>
              ) : null}

              {/* ── Other jobs (collapsed) ── */}
              {otherJobs.length > 0 ? (
                <>
                  <Button
                    unstyled
                    onPress={() => setShowOther((s) => !s)}
                    borderRadius={12}
                    backgroundColor={C.neutral200}
                    padding={12}
                    pressStyle={{ backgroundColor: C.neutral300, scale: 0.98 }}
                  >
                    <XStack alignItems="center" justifyContent="space-between">
                      <Text fontSize={13} fontWeight="600" color={C.neutral700}>
                        {showOther ? 'Hide' : `Show ${otherJobs.length} more jobs`}
                      </Text>
                      {showOther ? (
                        <ChevronUp size={16} color={C.neutral500} />
                      ) : (
                        <ChevronDown size={16} color={C.neutral500} />
                      )}
                    </XStack>
                  </Button>
                  {showOther
                    ? otherJobs.map((job) => (
                        <JobCard
                          key={job.requirement_id}
                          job={job}
                          isBusy={actionId === job.requirement_id}
                          onToggle={() => toggleInterest(job)}
                        />
                      ))
                    : null}
                </>
              ) : null}
            </>
          )}
        </YStack>
      </ScrollView>
    </View>
  );
}

function SectionHeader({
  label,
  subtitle,
  count,
  accentColor,
  icon,
}: {
  label: string;
  subtitle: string;
  count: number;
  accentColor: string;
  icon: React.ReactNode;
}) {
  return (
    <XStack alignItems="center" justifyContent="space-between" marginTop={4}>
      <XStack alignItems="center" gap={6}>
        {icon}
        <YStack>
          <Text fontSize={11} fontWeight="700" color={accentColor} letterSpacing={1.2}>
            {label}
          </Text>
          <Text fontSize={11} color={C.neutral500}>{subtitle}</Text>
        </YStack>
      </XStack>
      <View
        borderRadius={999}
        paddingHorizontal={10}
        paddingVertical={3}
        backgroundColor={C.neutral200}
      >
        <Text fontSize={12} fontWeight="600" color={C.neutral700}>{count}</Text>
      </View>
    </XStack>
  );
}

function JobCard({
  job,
  isBusy,
  onToggle,
}: {
  job: OpenJob;
  isBusy: boolean;
  onToggle: () => void;
}) {
  const isInterested = job.my_interest === 'interested';

  return (
    <Card
      bordered
      borderRadius={16}
      borderColor={isInterested ? '#86EFAC' : C.neutral200}
      backgroundColor={isInterested ? '#F0FDF4' : C.card}
      padding={16}
      elevation={isInterested ? 2 : 1}
    >
      {/* Top row: title + interest badge */}
      <XStack alignItems="flex-start" justifyContent="space-between" gap={10}>
        <YStack flex={1}>
          <Text fontSize={16} fontWeight="600" color={C.neutral900}>
            {job.category}
            {job.subcategory ? ` · ${job.subcategory}` : ''}
          </Text>
          <XStack alignItems="center" gap={4} marginTop={4}>
            <MapPin size={12} color={C.neutral500} />
            <Text fontSize={13} color={C.neutral500}>
              {job.work_location ? `${job.work_location}, ` : ''}{job.city}
            </Text>
          </XStack>
        </YStack>
        {isInterested ? (
          <View
            borderRadius={999}
            paddingHorizontal={10}
            paddingVertical={4}
            backgroundColor={C.success100}
          >
            <XStack alignItems="center" gap={4}>
              <Check size={12} color={C.success700} />
              <Text fontSize={12} fontWeight="600" color={C.success700}>
                Interested
              </Text>
            </XStack>
          </View>
        ) : null}
      </XStack>

      {/* Meta row */}
      <XStack flexWrap="wrap" gap={12} marginTop={12}>
        <MetaItem icon={<CalendarDays size={13} color={C.neutral500} />}>
          {formatDate(job.start_date)} · {job.duration_days}d
        </MetaItem>
        <MetaItem icon={<BriefcaseBusiness size={13} color={C.neutral500} />}>
          {job.number_of_workers} workers needed
        </MetaItem>
        {job.shift_details ? (
          <MetaItem icon={<CalendarDays size={13} color={C.neutral500} />}>
            {job.shift_details}
          </MetaItem>
        ) : null}
        {job.food_required ? (
          <MetaItem icon={<Utensils size={13} color={C.neutral500} />}>
            Meals provided
          </MetaItem>
        ) : null}
      </XStack>

      {/* Match reasons */}
      {job.match_reasons.length > 0 ? (
        <XStack flexWrap="wrap" gap={6} marginTop={10}>
          {job.match_reasons.map((reason) => (
            <View
              key={reason}
              borderRadius={999}
              paddingHorizontal={8}
              paddingVertical={3}
              backgroundColor={C.brand100}
            >
              <Text fontSize={11} fontWeight="500" color={C.brand600}>
                {reason}
              </Text>
            </View>
          ))}
        </XStack>
      ) : null}

      {/* Action buttons */}
      <XStack gap={8} marginTop={14}>
        {isInterested ? (
          <Button
            flex={1}
            height={42}
            borderRadius={12}
            backgroundColor="transparent"
            borderWidth={1}
            borderColor="#FCA5A5"
            pressStyle={{ backgroundColor: '#FEE2E2', scale: 0.97 }}
            disabled={isBusy}
            onPress={onToggle}
          >
            <Text fontSize={13} fontWeight="600" color="#B91C1C">
              {isBusy ? 'Updating...' : 'Withdraw'}
            </Text>
          </Button>
        ) : (
          <Button
            flex={1}
            height={42}
            borderRadius={12}
            backgroundColor={C.brand600}
            pressStyle={{ backgroundColor: C.brand900, scale: 0.97 }}
            disabled={isBusy}
            onPress={onToggle}
          >
            <Text fontSize={13} fontWeight="600" color="#FFFFFF">
              {isBusy ? 'Updating...' : "I'm Available"}
            </Text>
          </Button>
        )}
      </XStack>
    </Card>
  );
}

function MetaItem({
  icon,
  children,
}: {
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <XStack alignItems="center" gap={5}>
      {icon}
      <Text fontSize={13} color={C.neutral500}>{children}</Text>
    </XStack>
  );
}

function EmptySection({ message }: { message: string }) {
  return (
    <View
      borderRadius={12}
      borderWidth={1}
      borderColor={C.neutral200}
      borderStyle="dashed"
      padding={16}
      backgroundColor={C.card}
    >
      <Text fontSize={13} color={C.neutral500}>{message}</Text>
    </View>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
  }).format(new Date(value));
}
