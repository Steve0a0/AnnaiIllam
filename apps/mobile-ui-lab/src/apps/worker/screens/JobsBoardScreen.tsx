import React, { useCallback, useState } from 'react';
import { ActivityIndicator, Alert, RefreshControl } from 'react-native';
import {
  BriefcaseBusiness,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Clock3,
  MapPin,
  Star,
  Utensils,
  X,
  XCircle,
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
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  workerJobsService,
  type OpenJob,
} from '../../../shared/services/worker-jobs.service';
import {
  workerAssignmentsService,
  type WorkerAssignment,
  type WorkerAssignmentStatus,
} from '../../../shared/services/worker-assignments.service';
import type { JobsStackParamList } from '../navigation/types';

type Navigation = NativeStackNavigationProp<JobsStackParamList>;

type Segment = 'shifts' | 'jobs';

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
  danger100: '#FEE2E2',
  danger700: '#B91C1C',
  info100: '#DBEAFE',
  info700: '#1D4ED8',
};

const statusLabel: Record<WorkerAssignmentStatus, string> = {
  assigned: 'Pending',
  accepted: 'Accepted',
  declined: 'Declined',
  active: 'Active',
  completed: 'Completed',
  cancelled: 'Cancelled',
  replaced: 'Replaced',
};

const statusTone: Record<WorkerAssignmentStatus, { bg: string; color: string }> = {
  assigned: { bg: C.info100, color: C.info700 },
  accepted: { bg: C.success100, color: C.success700 },
  declined: { bg: C.danger100, color: C.danger700 },
  active: { bg: '#CFFAFE', color: '#0E7490' },
  completed: { bg: C.success100, color: C.success700 },
  cancelled: { bg: C.danger100, color: C.danger700 },
  replaced: { bg: C.warning100, color: C.warning700 },
};

type Props = Record<string, never>;

export default function JobsBoardScreen(_props: Props) {
  const navigation = useNavigation<Navigation>();
  const insets = useSafeAreaInsets();

  const [segment, setSegment] = useState<Segment>('shifts');

  // My Shifts state
  const [assignments, setAssignments] = useState<WorkerAssignment[]>([]);
  const [shiftsLoading, setShiftsLoading] = useState(true);
  const [showPast, setShowPast] = useState(false);

  // Open Jobs state
  const [jobs, setJobs] = useState<OpenJob[]>([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [actionId, setActionId] = useState<number | null>(null);
  const [showOther, setShowOther] = useState(false);

  const loadShifts = useCallback(async () => {
    const data = await workerAssignmentsService.list();
    setAssignments(data);
  }, []);

  const loadJobs = useCallback(async () => {
    const data = await workerJobsService.getOpenJobs();
    setJobs(data);
  }, []);

  const loadAll = useCallback(async () => {
    await Promise.allSettled([loadShifts(), loadJobs()]);
  }, [loadShifts, loadJobs]);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setShiftsLoading(true);
      setJobsLoading(true);
      loadShifts()
        .catch(() => { if (active) Alert.alert('Could not load shifts', 'Pull down to refresh.'); })
        .finally(() => active && setShiftsLoading(false));
      loadJobs()
        .catch(() => {})
        .finally(() => active && setJobsLoading(false));
      return () => { active = false; };
    }, [loadShifts, loadJobs]),
  );

  const refresh = async () => {
    setIsRefreshing(true);
    try { await loadAll(); } finally { setIsRefreshing(false); }
  };

  const toggleInterest = async (job: OpenJob) => {
    const isInterested = job.my_interest === 'interested';
    Alert.alert(
      isInterested ? 'Withdraw interest?' : 'Express interest?',
      isInterested
        ? 'You will no longer appear as available for this job.'
        : 'This tells admin you are available. You are not assigned yet.',
      [
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
              await loadJobs();
            } catch {
              Alert.alert('Could not update', 'Please try again.');
            } finally {
              setActionId(null);
            }
          },
        },
      ],
    );
  };

  // Grouped shifts
  const activeShifts = assignments.filter((a) => a.status === 'active');
  const upcomingShifts = assignments.filter((a) => a.status === 'assigned' || a.status === 'accepted');
  const pastShifts = assignments.filter((a) =>
    a.status === 'completed' || a.status === 'cancelled' || a.status === 'replaced' || a.status === 'declined',
  );

  // Open jobs tiers
  const bestJobs = jobs.filter((j) => j.match_tier === 'best');
  const nearbyJobs = jobs.filter((j) => j.match_tier === 'nearby');
  const otherJobs = jobs.filter((j) => j.match_tier === 'other');

  const pendingCount = upcomingShifts.filter((a) => a.status === 'assigned').length;

  return (
    <View flex={1} backgroundColor={C.page} paddingTop={insets.top}>
      {/* Header */}
      <YStack paddingHorizontal={20} paddingTop={12} paddingBottom={8}>
        <Text fontSize={20} fontWeight="700" color={C.neutral900}>Jobs</Text>
        {pendingCount > 0 && (
          <Text fontSize={12} color={C.warning700} marginTop={2}>
            {pendingCount} shift{pendingCount > 1 ? 's' : ''} waiting for your response
          </Text>
        )}
      </YStack>

      {/* Segment control */}
      <XStack marginHorizontal={16} marginBottom={12} borderRadius={12} backgroundColor={C.neutral200} padding={3}>
        <SegmentButton
          label="My Shifts"
          active={segment === 'shifts'}
          onPress={() => setSegment('shifts')}
          badge={pendingCount > 0 ? pendingCount : undefined}
        />
        <SegmentButton
          label="Open Jobs"
          active={segment === 'jobs'}
          onPress={() => setSegment('jobs')}
        />
      </XStack>

      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={refresh} />}
      >
        <YStack paddingBottom={insets.bottom + 32} paddingHorizontal={16} gap={12}>

          {/* ─── MY SHIFTS ─── */}
          {segment === 'shifts' && (
            <>
              {shiftsLoading ? (
                <YStack alignItems="center" paddingTop={60} gap={12}>
                  <ActivityIndicator color={C.brand600} />
                  <Text color={C.neutral500} fontSize={14}>Loading your shifts...</Text>
                </YStack>
              ) : assignments.length === 0 ? (
                <EmptyState
                  icon={<BriefcaseBusiness size={36} color={C.neutral300} />}
                  title="No shifts yet"
                  subtitle="When admin assigns you to a job it will appear here."
                />
              ) : (
                <>
                  {/* Active */}
                  {activeShifts.length > 0 && (
                    <>
                      <ShiftSectionLabel label="ACTIVE NOW" color="#0E7490" />
                      {activeShifts.map((a) => (
                        <ShiftCard
                          key={a.assignment_id}
                          assignment={a}
                          onPress={() => navigation.navigate('JobDetail', { assignmentId: a.assignment_id })}
                        />
                      ))}
                    </>
                  )}

                  {/* Upcoming */}
                  {upcomingShifts.length > 0 && (
                    <>
                      <ShiftSectionLabel label="UPCOMING" color={C.brand600} />
                      {upcomingShifts.map((a) => (
                        <ShiftCard
                          key={a.assignment_id}
                          assignment={a}
                          onPress={() => navigation.navigate('JobDetail', { assignmentId: a.assignment_id })}
                        />
                      ))}
                    </>
                  )}

                  {/* Past */}
                  {pastShifts.length > 0 && (
                    <>
                      <Button
                        unstyled
                        onPress={() => setShowPast((s) => !s)}
                        borderRadius={10}
                        backgroundColor={C.neutral200}
                        paddingHorizontal={14}
                        paddingVertical={10}
                        pressStyle={{ backgroundColor: C.neutral300, scale: 0.98 }}
                      >
                        <XStack alignItems="center" justifyContent="space-between">
                          <Text fontSize={12} fontWeight="600" color={C.neutral700} letterSpacing={0.8}>
                            HISTORY · {pastShifts.length} job{pastShifts.length > 1 ? 's' : ''}
                          </Text>
                          {showPast ? (
                            <ChevronUp size={15} color={C.neutral500} />
                          ) : (
                            <ChevronDown size={15} color={C.neutral500} />
                          )}
                        </XStack>
                      </Button>
                      {showPast && pastShifts.map((a) => (
                        <ShiftCard
                          key={a.assignment_id}
                          assignment={a}
                          onPress={() => navigation.navigate('JobDetail', { assignmentId: a.assignment_id })}
                          muted
                        />
                      ))}
                    </>
                  )}

                  {activeShifts.length === 0 && upcomingShifts.length === 0 && (
                    <EmptyState
                      icon={<CheckCircle2 size={36} color={C.neutral300} />}
                      title="All done!"
                      subtitle="No active or upcoming shifts. Check history below or browse open jobs."
                    />
                  )}
                </>
              )}
            </>
          )}

          {/* ─── OPEN JOBS ─── */}
          {segment === 'jobs' && (
            <>
              {jobsLoading ? (
                <YStack alignItems="center" paddingTop={60} gap={12}>
                  <ActivityIndicator color={C.brand600} />
                  <Text color={C.neutral500} fontSize={14}>Loading jobs...</Text>
                </YStack>
              ) : jobs.length === 0 ? (
                <EmptyState
                  icon={<BriefcaseBusiness size={36} color={C.neutral300} />}
                  title="No open jobs right now"
                  subtitle="New jobs will appear here once admin approves a client request."
                />
              ) : (
                <>
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

                  {nearbyJobs.length > 0 && (
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
                  )}

                  {otherJobs.length > 0 && (
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
                      {showOther && otherJobs.map((job) => (
                        <JobCard
                          key={job.requirement_id}
                          job={job}
                          isBusy={actionId === job.requirement_id}
                          onToggle={() => toggleInterest(job)}
                        />
                      ))}
                    </>
                  )}
                </>
              )}
            </>
          )}
        </YStack>
      </ScrollView>
    </View>
  );
}

// ─── Segment control ────────────────────────────────────────────────────────

function SegmentButton({
  label,
  active,
  badge,
  onPress,
}: {
  label: string;
  active: boolean;
  badge?: number;
  onPress: () => void;
}) {
  return (
    <Button
      flex={1}
      height={36}
      borderRadius={10}
      backgroundColor={active ? C.card : 'transparent'}
      pressStyle={{ opacity: 0.8 }}
      onPress={onPress}
      shadowColor={active ? 'rgba(0,0,0,0.08)' : 'transparent'}
      shadowRadius={active ? 4 : 0}
      shadowOffset={{ width: 0, height: 1 }}
    >
      <XStack alignItems="center" gap={6}>
        <Text fontSize={13} fontWeight={active ? '700' : '500'} color={active ? C.neutral900 : C.neutral500}>
          {label}
        </Text>
        {badge !== undefined && badge > 0 && (
          <View
            borderRadius={999}
            minWidth={18}
            height={18}
            paddingHorizontal={5}
            backgroundColor={C.warning700}
            alignItems="center"
            justifyContent="center"
          >
            <Text fontSize={10} fontWeight="700" color="#FFFFFF">{badge}</Text>
          </View>
        )}
      </XStack>
    </Button>
  );
}

// ─── Shift card ─────────────────────────────────────────────────────────────

function ShiftCard({
  assignment,
  onPress,
  muted = false,
}: {
  assignment: WorkerAssignment;
  onPress: () => void;
  muted?: boolean;
}) {
  const req = assignment.requirement;
  const tone = statusTone[assignment.status];
  const isActive = assignment.status === 'active';
  const isPending = assignment.status === 'assigned';

  return (
    <Button
      unstyled
      onPress={onPress}
      pressStyle={{ opacity: 0.82, scale: 0.99 }}
    >
      <Card
        bordered
        borderRadius={14}
        borderColor={isActive ? '#A5F3FC' : isPending ? '#BFDBFE' : C.neutral200}
        backgroundColor={isActive ? '#F0FDFF' : isPending ? '#EFF6FF' : C.card}
        padding={14}
        opacity={muted ? 0.75 : 1}
      >
        <XStack alignItems="flex-start" justifyContent="space-between" gap={10}>
          <YStack flex={1} gap={4}>
            <Text fontSize={15} fontWeight="600" color={C.neutral900} numberOfLines={1}>
              {req?.category ?? 'Assigned job'}
              {req?.subcategory ? ` · ${req.subcategory}` : ''}
            </Text>
            {req && (
              <XStack alignItems="center" gap={4}>
                <MapPin size={12} color={C.neutral500} />
                <Text fontSize={13} color={C.neutral500} numberOfLines={1}>
                  {req.work_location}, {req.city}
                </Text>
              </XStack>
            )}
            <XStack gap={12} marginTop={4} flexWrap="wrap">
              {assignment.start_date && (
                <XStack alignItems="center" gap={4}>
                  <CalendarDays size={12} color={C.neutral500} />
                  <Text fontSize={12} color={C.neutral700} fontFamily="$mono">
                    {formatDate(assignment.start_date)}
                    {assignment.end_date && assignment.end_date !== assignment.start_date
                      ? ` – ${formatDate(assignment.end_date)}`
                      : ''}
                  </Text>
                </XStack>
              )}
              {assignment.assigned_shift && (
                <XStack alignItems="center" gap={4}>
                  <Clock3 size={12} color={C.neutral500} />
                  <Text fontSize={12} color={C.neutral700}>{assignment.assigned_shift}</Text>
                </XStack>
              )}
            </XStack>
          </YStack>

          <YStack alignItems="flex-end" gap={6}>
            {/* Status pill */}
            <XStack
              height={22}
              borderRadius={999}
              paddingHorizontal={9}
              alignItems="center"
              backgroundColor={tone.bg}
              gap={4}
            >
              <View width={5} height={5} borderRadius={999} backgroundColor={tone.color} />
              <Text fontSize={11} fontWeight="600" color={tone.color}>
                {statusLabel[assignment.status]}
              </Text>
            </XStack>

            {/* Status icon hint */}
            {assignment.status === 'completed' && <CheckCircle2 size={16} color={C.success700} />}
            {(assignment.status === 'cancelled' || assignment.status === 'declined') && (
              <XCircle size={16} color={C.danger700} />
            )}
            {(assignment.status === 'assigned' || assignment.status === 'accepted' || assignment.status === 'active') && (
              <ChevronRight size={16} color={C.neutral500} />
            )}
          </YStack>
        </XStack>

        {isPending && (
          <View
            marginTop={10}
            borderRadius={8}
            paddingHorizontal={10}
            paddingVertical={6}
            backgroundColor={C.info100}
          >
            <Text fontSize={12} color={C.info700} fontWeight="500">
              Tap to accept or decline this shift
            </Text>
          </View>
        )}
      </Card>
    </Button>
  );
}

// ─── Shared helpers ──────────────────────────────────────────────────────────

function ShiftSectionLabel({ label, color }: { label: string; color: string }) {
  return (
    <Text fontSize={11} fontWeight="700" color={color} letterSpacing={1.2} marginTop={4}>
      {label}
    </Text>
  );
}

function EmptyState({
  icon,
  title,
  subtitle,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
}) {
  return (
    <YStack
      borderRadius={16}
      backgroundColor={C.card}
      padding={32}
      alignItems="center"
      gap={10}
      borderWidth={1}
      borderColor={C.neutral200}
      marginTop={8}
    >
      {icon}
      <Text fontSize={16} fontWeight="500" color={C.neutral900}>{title}</Text>
      <Text fontSize={13} color={C.neutral500} textAlign="center">{subtitle}</Text>
    </YStack>
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
      <XStack alignItems="flex-start" justifyContent="space-between" gap={10}>
        <YStack flex={1}>
          <Text fontSize={16} fontWeight="600" color={C.neutral900}>
            {job.category}{job.subcategory ? ` · ${job.subcategory}` : ''}
          </Text>
          <XStack alignItems="center" gap={4} marginTop={4}>
            <MapPin size={12} color={C.neutral500} />
            <Text fontSize={13} color={C.neutral500}>
              {job.work_location ? `${job.work_location}, ` : ''}{job.city}
            </Text>
          </XStack>
        </YStack>
        {isInterested && (
          <View borderRadius={999} paddingHorizontal={10} paddingVertical={4} backgroundColor={C.success100}>
            <XStack alignItems="center" gap={4}>
              <Check size={12} color={C.success700} />
              <Text fontSize={12} fontWeight="600" color={C.success700}>Interested</Text>
            </XStack>
          </View>
        )}
      </XStack>

      <XStack flexWrap="wrap" gap={12} marginTop={12}>
        <MetaItem icon={<CalendarDays size={13} color={C.neutral500} />}>
          {formatDate(job.start_date)} · {job.duration_days}d
        </MetaItem>
        <MetaItem icon={<BriefcaseBusiness size={13} color={C.neutral500} />}>
          {job.number_of_workers} workers needed
        </MetaItem>
        {job.shift_details && (
          <MetaItem icon={<CalendarDays size={13} color={C.neutral500} />}>
            {job.shift_details}
          </MetaItem>
        )}
        {job.food_required && (
          <MetaItem icon={<Utensils size={13} color={C.neutral500} />}>
            Meals provided
          </MetaItem>
        )}
      </XStack>

      {job.match_reasons.length > 0 && (
        <XStack flexWrap="wrap" gap={6} marginTop={10}>
          {job.match_reasons.map((reason) => (
            <View key={reason} borderRadius={999} paddingHorizontal={8} paddingVertical={3} backgroundColor={C.brand100}>
              <Text fontSize={11} fontWeight="500" color={C.brand600}>{reason}</Text>
            </View>
          ))}
        </XStack>
      )}

      <XStack gap={8} marginTop={14}>
        {isInterested ? (
          <Button
            flex={1} height={42} borderRadius={12}
            backgroundColor="transparent" borderWidth={1} borderColor="#FCA5A5"
            pressStyle={{ backgroundColor: '#FEE2E2', scale: 0.97 }}
            disabled={isBusy} onPress={onToggle}
          >
            <Text fontSize={13} fontWeight="600" color="#B91C1C">
              {isBusy ? 'Updating...' : 'Withdraw'}
            </Text>
          </Button>
        ) : (
          <Button
            flex={1} height={42} borderRadius={12}
            backgroundColor={C.brand600}
            pressStyle={{ backgroundColor: C.brand900, scale: 0.97 }}
            disabled={isBusy} onPress={onToggle}
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

function MetaItem({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <XStack alignItems="center" gap={5}>
      {icon}
      <Text fontSize={13} color={C.neutral500}>{children}</Text>
    </XStack>
  );
}

function EmptySection({ message }: { message: string }) {
  return (
    <View borderRadius={12} borderWidth={1} borderColor={C.neutral200} borderStyle="dashed" padding={16} backgroundColor={C.card}>
      <Text fontSize={13} color={C.neutral500}>{message}</Text>
    </View>
  );
}

function formatDate(value: string | null | undefined) {
  if (!value) return '—';
  const d = new Date(value.replace(' ', 'T'));
  if (isNaN(d.getTime())) return '—';
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short' }).format(d);
}
