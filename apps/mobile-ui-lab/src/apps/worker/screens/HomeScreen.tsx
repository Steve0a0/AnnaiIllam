import React, { useCallback, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, Image, Linking, Modal, RefreshControl } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { pushTokenService } from '../../../shared/services/push-token.service';
import * as Location from 'expo-location';
import * as LocalAuthentication from 'expo-local-authentication';
import {
  Bell,
  BriefcaseBusiness,
  CalendarDays,
  Check,
  ChevronLeft,
  ChevronRight,
  Clock3,
  ClipboardList,
  LogOut,
  MapPin,
  MessageCircleWarning,
  WifiOff,
  X,
} from 'lucide-react-native';
import {
  View,
  YStack,
  XStack,
  Text,
  Card,
  Button,
  ScrollView,
} from 'tamagui';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuthStore } from '../../../shared/store/auth.store';
import { authStorage } from '../../../shared/lib/auth-storage';
import { useNetworkStatus } from '../../../shared/hooks/use-network-status';
import {
  workerAssignmentsService,
  type WorkerAssignment,
  type WorkerAssignmentStatus,
} from '../../../shared/services/worker-assignments.service';
import {
  workerAttendanceService,
  type WorkerAttendanceRecord,
} from '../../../shared/services/worker-attendance.service';
import { workerProfileService } from '../../../shared/services/worker-profile.service';

type Props = Record<string, never>;

const CACHE_KEY = 'worker_home_cache_v1';

interface HomeCache {
  assignments: WorkerAssignment[];
  attendance: WorkerAttendanceRecord[];
  isAvailable: boolean | null;
  cachedAt: number;
}

const C = {
  page: '#F5F5F4',
  card: '#FFFFFF',
  brand900: '#0D2E1E',
  brand700: '#165233',
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
  assigned: 'Assigned',
  accepted: 'Accepted',
  declined: 'Declined',
  active: 'Checked in',
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

export default function WorkerHomeScreen(_props: Props) {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<any>();
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const networkStatus = useNetworkStatus();
  const [assignments, setAssignments] = useState<WorkerAssignment[]>([]);
  const [attendance, setAttendance] = useState<WorkerAttendanceRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isStale, setIsStale] = useState(false);
  const [actionId, setActionId] = useState<number | null>(null);
  const [isAvailable, setIsAvailable] = useState<boolean | null>(null);
  const [visibleWeekDate, setVisibleWeekDate] = useState(() => new Date());
  const [selectedDateKey, setSelectedDateKey] = useState(() => toDateKey(new Date()));
  const [checkInPreview, setCheckInPreview] = useState<{
    assignment: WorkerAssignment;
    latitude: number;
    longitude: number;
  } | null>(null);
  const [isConfirmingCheckIn, setIsConfirmingCheckIn] = useState(false);

  /** Restore cached data so the screen isn't blank while loading. */
  const loadCache = useCallback(async () => {
    try {
      const raw = await AsyncStorage.getItem(CACHE_KEY);
      if (!raw) return;
      const cached: HomeCache = JSON.parse(raw);
      setAssignments(cached.assignments);
      setAttendance(cached.attendance);
      setIsAvailable(cached.isAvailable);
      setIsStale(true);
    } catch {
      // Corrupt cache — ignore
    }
  }, []);

  const saveCache = useCallback(
    async (a: WorkerAssignment[], att: WorkerAttendanceRecord[], avail: boolean | null) => {
      try {
        const payload: HomeCache = { assignments: a, attendance: att, isAvailable: avail, cachedAt: Date.now() };
        await AsyncStorage.setItem(CACHE_KEY, JSON.stringify(payload));
      } catch {
        // Non-fatal
      }
    },
    [],
  );

  const load = useCallback(async () => {
    const [profileResult, assignmentsResult, attendanceResult] = await Promise.allSettled([
      workerProfileService.getProfile(),
      workerAssignmentsService.list(),
      workerAttendanceService.list(),
    ]);
    if (profileResult.status === 'fulfilled') {
      setIsAvailable(profileResult.value.is_available);
    }
    if (assignmentsResult.status === 'fulfilled') {
      setAssignments(assignmentsResult.value);
    }
    if (attendanceResult.status === 'fulfilled') {
      setAttendance(attendanceResult.value);
    }
    if (
      assignmentsResult.status === 'fulfilled' &&
      attendanceResult.status === 'fulfilled'
    ) {
      setIsStale(false);
      await saveCache(
        assignmentsResult.value,
        attendanceResult.value,
        profileResult.status === 'fulfilled' ? profileResult.value.is_available : null,
      );
    }
  }, [saveCache]);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);

      // Show cached data immediately while the network request is in-flight.
      loadCache().finally(() => {
        if (!active) return;
        load()
          .catch(() => {
            if (active) {
              // If we have cached data, don't show an intrusive alert — the
              // stale banner is sufficient.
              if (assignments.length === 0) {
                Alert.alert('Could not load jobs', 'Pull down to refresh and try again.');
              }
            }
          })
          .finally(() => active && setIsLoading(false));
      });

      return () => {
        active = false;
      };
    }, [load, loadCache, assignments.length]),
  );

  const refresh = async () => {
    setIsRefreshing(true);
    try {
      await load();
    } catch {
      Alert.alert('Could not refresh', 'Check your connection and try again.');
    } finally {
      setIsRefreshing(false);
    }
  };

  const decideAssignment = async (assignment: WorkerAssignment, action: 'accept' | 'decline') => {
    const title = action === 'accept' ? 'Accept this shift?' : 'Decline this shift?';
    const message =
      action === 'accept'
        ? 'This confirms you are available for the assigned job.'
        : 'Admin will be told to assign another worker.';

    Alert.alert(title, message, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: action === 'accept' ? 'Accept' : 'Decline',
        style: action === 'decline' ? 'destructive' : 'default',
        onPress: async () => {
          setActionId(assignment.assignment_id);
          try {
            if (action === 'accept') {
              await workerAssignmentsService.accept(assignment.assignment_id);
            } else {
              await workerAssignmentsService.decline(assignment.assignment_id);
            }
            await load();
          } catch {
            Alert.alert('Could not update job', 'Please try again.');
          } finally {
            setActionId(null);
          }
        },
      },
    ]);
  };

  const markAttendance = async (assignment: WorkerAssignment, action: 'check_in' | 'check_out') => {
    if (action === 'check_in') {
      // Get GPS first, then show map preview modal
      setActionId(assignment.assignment_id);
      try {
        const position = await getCurrentLocation();
        setCheckInPreview({
          assignment,
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      } catch (error) {
        const code = (error as any)?.code;
        if (code === 'PERMISSION_DENIED') {
          Alert.alert(
            'Location Required',
            'Enable location permission in Settings to check in.',
            [
              { text: 'Cancel', style: 'cancel' },
              { text: 'Open Settings', onPress: () => Linking.openSettings() },
            ],
          );
        } else {
          Alert.alert('Location error', error instanceof Error ? error.message : 'Could not get your location.');
        }
      } finally {
        setActionId(null);
      }
      return;
    }

    // check_out: keep existing Alert flow
    Alert.alert('Check out now?', 'Your current location will be attached to this check-out.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Check Out',
        onPress: async () => {
          // Biometric gate before submitting check-out
          const bio = await LocalAuthentication.authenticateAsync({
            promptMessage: 'Confirm check-out',
            cancelLabel: 'Cancel',
            fallbackLabel: 'Use device passcode',
            disableDeviceFallback: false,
          });
          if (!bio.success) return;

          setActionId(assignment.assignment_id);
          try {
            const position = await getCurrentLocation();
            await workerAttendanceService.checkOut({
              assignment_id: assignment.assignment_id,
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
            });
            await load();
          } catch (error) {
            const code = (error as any)?.code;
            if (code === 'PERMISSION_DENIED') {
              Alert.alert(
                'Location Required',
                'Enable location permission in Settings to check out.',
                [
                  { text: 'Cancel', style: 'cancel' },
                  { text: 'Open Settings', onPress: () => Linking.openSettings() },
                ],
              );
            } else {
              Alert.alert('Could not check out', error instanceof Error ? error.message : 'Please try again.');
            }
          } finally {
            setActionId(null);
          }
        },
      },
    ]);
  };

  const handleConfirmCheckIn = async () => {
    if (!checkInPreview) return;

    // Biometric gate before submitting check-in
    const bio = await LocalAuthentication.authenticateAsync({
      promptMessage: 'Confirm check-in',
      cancelLabel: 'Cancel',
      fallbackLabel: 'Use device passcode',
      disableDeviceFallback: false,
    });
    if (!bio.success) return;

    setIsConfirmingCheckIn(true);
    try {
      await workerAttendanceService.checkIn({
        assignment_id: checkInPreview.assignment.assignment_id,
        latitude: checkInPreview.latitude,
        longitude: checkInPreview.longitude,
      });
      setCheckInPreview(null);
      await load();
    } catch (error) {
      Alert.alert('Could not check in', error instanceof Error ? error.message : 'Please try again.');
    } finally {
      setIsConfirmingCheckIn(false);
    }
  };

  const heroAssignment = useMemo(
    () => pickHeroAssignment(assignments, selectedDateKey),
    [assignments, selectedDateKey],
  );
  const heroAttendance = useMemo(
    () =>
      heroAssignment
        ? attendance.find(
            (item) =>
              item.assignment_id === heroAssignment.assignment_id &&
              item.attendance_date === selectedDateKey,
          ) ?? null
        : null,
    [attendance, heroAssignment, selectedDateKey],
  );
  const otherAssignments = assignments.filter(
    (item) => item.assignment_id !== heroAssignment?.assignment_id,
  );
  const pendingCount = assignments.filter((item) => item.status === 'assigned').length;
  const moveVisibleWeek = (days: number) => {
    setVisibleWeekDate((current) => addDays(current, days));
    setSelectedDateKey((current) => toDateKey(addDays(parseApiDate(current), days)));
  };

  const onLogout = async () => {
    await pushTokenService.deactivate().catch(() => undefined);
    await authStorage.clear();
    clearAuth();
  };

  const monthPct = calcMonthAttendancePct(attendance);

  return (
    <View flex={1} backgroundColor={C.page}>
      {/* Offline / stale-data banner */}
      {(networkStatus === 'offline' || isStale) && (
        <View
          backgroundColor={isStale ? '#f59e0b' : '#ef4444'}
          paddingTop={insets.top > 0 ? 4 : 6}
          paddingBottom={6}
          alignItems="center"
        >
          <Text color="white" fontSize={12} fontWeight="600">
            {networkStatus === 'offline'
              ? 'No internet connection — showing cached data'
              : 'Showing cached data — pull to refresh'}
          </Text>
        </View>
      )}
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={refresh} />}
      >
        <YStack paddingBottom={insets.bottom + 24}>
          {/* Full-bleed dark green header — greeting row + hero shift card */}
          <YStack backgroundColor={C.brand900} paddingTop={insets.top} paddingBottom={24}>
            <GreetingBar
              pendingCount={pendingCount}
              isAvailable={isAvailable}
              onLogout={onLogout}
              onProfile={() => navigation.getParent()?.navigate('ProfileTab')}
            />

            {isLoading ? (
              <LoadingHero />
            ) : (
              <HeroJobCard
                assignment={heroAssignment}
                selectedDateKey={selectedDateKey}
                attendance={heroAttendance}
                isBusy={heroAssignment ? actionId === heroAssignment.assignment_id : false}
                onAccept={heroAssignment ? () => decideAssignment(heroAssignment, 'accept') : undefined}
                onDecline={heroAssignment ? () => decideAssignment(heroAssignment, 'decline') : undefined}
                onCheckIn={heroAssignment ? () => markAttendance(heroAssignment, 'check_in') : undefined}
                onCheckOut={heroAssignment ? () => markAttendance(heroAssignment, 'check_out') : undefined}
              />
            )}
          </YStack>

          <WeekStrip
            assignments={assignments}
            visibleDate={visibleWeekDate}
            selectedDateKey={selectedDateKey}
            onSelectDate={setSelectedDateKey}
            onMoveWeek={moveVisibleWeek}
            onToday={() => {
              const today = new Date();
              setVisibleWeekDate(today);
              setSelectedDateKey(toDateKey(today));
            }}
          />

          {/* 2×2 Quick action grid */}
          <YStack marginHorizontal={16} marginTop={16} gap={10}>
            <XStack gap={10}>
              <QuickActionTile
                icon={<BriefcaseBusiness size={22} color={C.brand600} />}
                label="Open Jobs"
                stat={pendingCount > 0 ? `${pendingCount} pending` : 'Browse available'}
                statColor={pendingCount > 0 ? C.brand600 : C.neutral500}
                bgColor={C.brand100}
                onPress={() => (navigation as any).getParent()?.navigate('JobsTab')}
              />
              <QuickActionTile
                icon={<ClipboardList size={22} color={C.info700} />}
                label="Attendance"
                stat={attendance.length > 0 ? `${monthPct}% this month` : 'No records yet'}
                statColor={
                  attendance.length === 0 ? C.neutral500
                  : monthPct >= 80 ? C.success700
                  : monthPct >= 50 ? C.warning700
                  : C.danger700
                }
                bgColor={C.info100}
                onPress={() => (navigation as any).getParent()?.navigate('AttendanceTab')}
              />
            </XStack>
            <XStack gap={10}>
              <QuickActionTile
                icon={<MessageCircleWarning size={22} color={C.warning700} />}
                label="My Issues"
                stat="Raise a complaint"
                statColor={C.neutral500}
                bgColor={C.warning100}
                onPress={() => navigation.navigate('Issues' as never)}
              />
              <QuickActionTile
                icon={isAvailable
                  ? <Check size={22} color={C.success700} />
                  : <WifiOff size={22} color={C.warning700} />}
                label="Availability"
                stat={isAvailable === null ? '...' : isAvailable ? 'Available' : 'Paused'}
                statColor={isAvailable ? C.success700 : C.warning700}
                onPress={() => (navigation as any).getParent()?.navigate('ProfileTab')}
              />
            </XStack>
          </YStack>

          <YStack marginHorizontal={16} marginTop={20} gap={12}>
            <SectionLabel label="UPCOMING JOBS" />
            {isLoading ? (
              <CompactCard>
                <ActivityIndicator color={C.brand600} />
                <Text marginTop={12} color={C.neutral500} fontSize={14}>
                  Loading jobs...
                </Text>
              </CompactCard>
            ) : otherAssignments.length === 0 ? (
              <EmptyUpcoming hasHero={!!heroAssignment} />
            ) : (
              otherAssignments.slice(0, 4).map((assignment) => (
                <UpcomingJobCard
                  key={assignment.assignment_id}
                  assignment={assignment}
                  onPress={() =>
                    (navigation as any).getParent()?.navigate('JobsTab', {
                      screen: 'JobDetail',
                      params: { assignmentId: assignment.assignment_id },
                    })
                  }
                />
              ))
            )}
          </YStack>

          <YStack marginHorizontal={16} marginTop={20}>
            <NoticeCard />
          </YStack>
        </YStack>
      </ScrollView>

      {/* Check-in location preview modal */}
      <Modal
        visible={checkInPreview != null}
        transparent
        animationType="slide"
        onRequestClose={() => setCheckInPreview(null)}
      >
        <View style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.45)' }}>
          <View style={{ backgroundColor: '#FFFFFF', borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 24, gap: 16 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <MapPin size={20} color={C.brand600} />
              <Text style={{ fontSize: 17, fontWeight: '700', color: C.neutral900 }}>
                Confirm check-in location
              </Text>
            </View>

            {checkInPreview && (() => {
              const { latitude, longitude } = checkInPreview;
              const mapsKey = process.env.EXPO_PUBLIC_GOOGLE_MAPS_API_KEY ?? '';
              const staticMapUrl = mapsKey
                ? `https://maps.googleapis.com/maps/api/staticmap?center=${latitude},${longitude}&zoom=16&size=320x200&markers=color:green%7C${latitude},${longitude}&key=${mapsKey}`
                : null;
              return (
                <>
                  {staticMapUrl ? (
                    <Image
                      source={{ uri: staticMapUrl }}
                      style={{ width: '100%', height: 180, borderRadius: 10, backgroundColor: C.neutral200 }}
                      resizeMode="cover"
                    />
                  ) : (
                    <View style={{ height: 80, borderRadius: 10, backgroundColor: C.neutral200, alignItems: 'center', justifyContent: 'center' }}>
                      <MapPin size={28} color={C.neutral500} />
                    </View>
                  )}
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <MapPin size={13} color={C.neutral500} />
                    <Text style={{ color: C.neutral700, fontSize: 13 }}>
                      {latitude.toFixed(5)}, {longitude.toFixed(5)}
                    </Text>
                  </View>
                </>
              );
            })()}

            <View style={{ gap: 10 }}>
              <Button
                size="$4"
                backgroundColor={C.brand600}
                color="#FFFFFF"
                fontWeight="700"
                borderRadius={10}
                disabled={isConfirmingCheckIn}
                opacity={isConfirmingCheckIn ? 0.6 : 1}
                onPress={handleConfirmCheckIn}
                icon={isConfirmingCheckIn ? <ActivityIndicator size="small" color="#FFFFFF" /> : undefined}
              >
                {isConfirmingCheckIn ? 'Checking in…' : 'Check In from here'}
              </Button>
              <Button
                size="$4"
                chromeless
                color={C.neutral700}
                onPress={() => setCheckInPreview(null)}
                disabled={isConfirmingCheckIn}
              >
                Not my location
              </Button>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

function GreetingBar({
  pendingCount,
  isAvailable,
  onLogout,
  onProfile,
}: {
  pendingCount: number;
  isAvailable: boolean | null;
  onLogout: () => void | Promise<void>;
  onProfile: () => void;
}) {
  return (
    <XStack
      paddingHorizontal={20}
      paddingTop={8}
      paddingBottom={12}
      alignItems="center"
      justifyContent="space-between"
    >
      <YStack>
        <Text fontSize={12} fontWeight="500" color="rgba(255,255,255,0.5)">
          TODAY
        </Text>
        <Text fontSize={13} color="rgba(255,255,255,0.85)" fontFamily="$mono">
          {formatToday()}
        </Text>
        {isAvailable !== null && (
          <XStack
            marginTop={6}
            alignItems="center"
            gap={5}
            backgroundColor={isAvailable ? 'rgba(37,162,99,0.2)' : 'rgba(245,158,11,0.2)'}
            borderRadius={999}
            paddingHorizontal={8}
            paddingVertical={3}
            alignSelf="flex-start"
            pressStyle={{ opacity: 0.75 }}
            onPress={onProfile}
          >
            <View
              width={6}
              height={6}
              borderRadius={999}
              backgroundColor={isAvailable ? C.brand400 : C.warning700}
            />
            <Text fontSize={11} fontWeight="500" color={isAvailable ? '#a7f3d0' : '#FCD34D'}>
              {isAvailable ? 'Available' : 'Paused'}
            </Text>
          </XStack>
        )}
      </YStack>
      <XStack gap={8}>
        <DarkIconButton aria-label="Notifications">
          <Bell size={18} color="rgba(255,255,255,0.8)" />
          {pendingCount > 0 ? (
            <View
              position="absolute"
              top={7}
              right={7}
              width={8}
              height={8}
              borderRadius={999}
              backgroundColor={C.warning700}
            />
          ) : null}
        </DarkIconButton>
        <DarkIconButton onPress={onLogout} aria-label="Log out">
          <LogOut size={18} color="rgba(255,255,255,0.8)" />
        </DarkIconButton>
      </XStack>
    </XStack>
  );
}

function HeroJobCard({
  assignment,
  selectedDateKey,
  attendance,
  isBusy,
  onAccept,
  onDecline,
  onCheckIn,
  onCheckOut,
}: {
  assignment: WorkerAssignment | null;
  selectedDateKey: string;
  attendance: WorkerAttendanceRecord | null;
  isBusy: boolean;
  onAccept?: () => void;
  onDecline?: () => void;
  onCheckIn?: () => void;
  onCheckOut?: () => void;
}) {
  const selectedDate = parseApiDate(selectedDateKey);
  const isToday = selectedDateKey === toDateKey(new Date());
  const selectedLabel = formatSelectedDate(selectedDate);

  if (!assignment || !assignment.requirement) {
    return (
      <YStack
        marginHorizontal={16}
        marginTop={12}
        borderRadius={24}
        padding={24}
        minHeight={252}
        backgroundColor={C.brand900}
        justifyContent="center"
      >
        <YStack alignItems="center" gap={10}>
          <CalendarDays size={34} color="rgba(255,255,255,0.28)" />
          <Text fontSize={12} fontWeight="500" color="rgba(255,255,255,0.42)">
            {isToday ? 'TODAY' : selectedLabel.toUpperCase()}
          </Text>
          <Text fontSize={16} fontWeight="500" color="rgba(255,255,255,0.72)">
            No shift on this date
          </Text>
          <Text fontSize={13} color="rgba(255,255,255,0.42)" textAlign="center">
            Choose another date or browse open jobs for available work.
          </Text>
        </YStack>
      </YStack>
    );
  }

  const requirement = assignment.requirement;
  const tone = statusTone[assignment.status];
  const hasCheckedIn = Boolean(attendance?.check_in_time);
  const hasCheckedOut = Boolean(attendance?.check_out_time);
  const canCheckIn = isToday && assignment.status === 'accepted' && !hasCheckedIn;
  const canCheckOut = isToday && (assignment.status === 'active' || hasCheckedIn) && !hasCheckedOut;

  return (
    <YStack
      marginHorizontal={16}
      marginTop={12}
      borderRadius={24}
      padding={24}
      backgroundColor={C.brand900}
      shadowColor="rgba(13,46,30,0.28)"
      shadowRadius={18}
      shadowOffset={{ width: 0, height: 10 }}
    >
      <XStack justifyContent="space-between" alignItems="center">
        <Text fontSize={12} fontWeight="500" color="rgba(255,255,255,0.45)">
          {isToday ? "TODAY'S SHIFT" : `${selectedLabel.toUpperCase()} SHIFT`}
        </Text>
        <StatusPill status={assignment.status} dark />
      </XStack>

      <Text marginTop={14} fontSize={20} lineHeight={26} fontWeight="500" color="#FFFFFF">
        {requirement.category}
      </Text>

      <YStack gap={9} marginTop={14}>
        <DarkMeta icon={<MapPin size={14} color="rgba(255,255,255,0.64)" />}>
          {requirement.work_location}
        </DarkMeta>
        <DarkMeta icon={<Clock3 size={14} color="#FFFFFF" />}>
          {assignment.assigned_shift ?? 'Shift not specified'}
        </DarkMeta>
        <DarkMeta icon={<BriefcaseBusiness size={14} color="rgba(255,255,255,0.64)" />}>
          {assignment.assigned_role ?? requirement.subcategory ?? 'Worker'}
        </DarkMeta>
      </YStack>

      <View height={1} backgroundColor="rgba(255,255,255,0.10)" marginVertical={18} />

      {assignment.status === 'assigned' ? (
        <YStack gap={10}>
          <Button
            height={56}
            borderRadius={14}
            backgroundColor={C.brand400}
            pressStyle={{ backgroundColor: C.brand700, scale: 0.98 }}
            disabled={isBusy}
            onPress={onAccept}
            icon={isBusy ? undefined : <Check size={18} color="#FFFFFF" />}
          >
            <Text color="#FFFFFF" fontSize={16} fontWeight="500">
              {isBusy ? 'Updating...' : 'Accept Shift'}
            </Text>
          </Button>
          <Button
            height={48}
            borderRadius={12}
            backgroundColor="rgba(255,255,255,0.08)"
            borderColor="rgba(255,255,255,0.14)"
            borderWidth={1}
            pressStyle={{ backgroundColor: 'rgba(255,255,255,0.14)', scale: 0.98 }}
            disabled={isBusy}
            onPress={onDecline}
            icon={isBusy ? undefined : <X size={16} color="rgba(255,255,255,0.84)" />}
          >
            <Text color="rgba(255,255,255,0.84)" fontSize={14} fontWeight="500">
              Decline
            </Text>
          </Button>
        </YStack>
      ) : canCheckIn ? (
        <Button
          height={56}
          borderRadius={14}
          backgroundColor={C.brand400}
          pressStyle={{ backgroundColor: C.brand700, scale: 0.98 }}
          disabled={isBusy}
          onPress={onCheckIn}
          icon={isBusy ? undefined : <MapPin size={18} color="#FFFFFF" />}
        >
          <Text color="#FFFFFF" fontSize={16} fontWeight="500">
            {isBusy ? 'Checking in...' : 'Check In'}
          </Text>
        </Button>
      ) : canCheckOut ? (
        <XStack
          minHeight={56}
          borderRadius={14}
          paddingHorizontal={14}
          alignItems="center"
          backgroundColor="rgba(255,255,255,0.10)"
          borderWidth={1}
          borderColor="rgba(255,255,255,0.15)"
          gap={10}
        >
          <View width={8} height={8} borderRadius={999} backgroundColor={C.brand400} />
          <Text color="#FFFFFF" fontSize={14} fontWeight="500" flex={1}>
            Checked in {attendance?.check_in_time ? formatTime(attendance.check_in_time) : 'today'}
          </Text>
          <Button
            height={40}
            borderRadius={12}
            backgroundColor="rgba(255,255,255,0.12)"
            pressStyle={{ backgroundColor: 'rgba(255,255,255,0.18)', scale: 0.98 }}
            disabled={isBusy}
            onPress={onCheckOut}
          >
            <Text color="#FFFFFF" fontSize={13} fontWeight="500">
              {isBusy ? 'Saving...' : 'Check Out'}
            </Text>
          </Button>
        </XStack>
      ) : hasCheckedOut ? (
        <XStack
          minHeight={56}
          borderRadius={14}
          paddingHorizontal={16}
          alignItems="center"
          backgroundColor="rgba(255,255,255,0.10)"
          borderWidth={1}
          borderColor="rgba(255,255,255,0.15)"
          gap={10}
        >
          <View width={8} height={8} borderRadius={999} backgroundColor={C.success700} />
          <Text color="#FFFFFF" fontSize={14} fontWeight="500" flex={1}>
            Checked out {attendance?.check_out_time ? formatTime(attendance.check_out_time) : 'today'}
          </Text>
        </XStack>
      ) : (
        <XStack
          minHeight={56}
          borderRadius={14}
          paddingHorizontal={16}
          alignItems="center"
          backgroundColor="rgba(255,255,255,0.10)"
          borderWidth={1}
          borderColor="rgba(255,255,255,0.15)"
          gap={10}
        >
          <View width={8} height={8} borderRadius={999} backgroundColor={tone.color} />
          <Text color="#FFFFFF" fontSize={14} fontWeight="500" flex={1}>
            {assignment.status === 'accepted'
              ? isToday
                ? 'Accepted. Check-in is ready.'
                : 'Accepted. Check-in opens on shift day.'
              : statusLabel[assignment.status]}
          </Text>
        </XStack>
      )}
    </YStack>
  );
}

function WeekStrip({
  assignments,
  visibleDate,
  selectedDateKey,
  onSelectDate,
  onMoveWeek,
  onToday,
}: {
  assignments: WorkerAssignment[];
  visibleDate: Date;
  selectedDateKey: string;
  onSelectDate: (dateKey: string) => void;
  onMoveWeek: (days: number) => void;
  onToday: () => void;
}) {
  const days = buildWeek(assignments, visibleDate, selectedDateKey);
  const rangeLabel = formatWeekRange(days[0].dateValue, days[days.length - 1].dateValue);
  const title = isCurrentWeek(visibleDate) ? 'THIS WEEK' : 'SELECTED WEEK';

  return (
    <YStack marginTop={20}>
      <XStack marginHorizontal={16} marginBottom={10} alignItems="center" justifyContent="space-between">
        <YStack>
          <SectionLabel label={title} />
          <Text marginTop={2} fontSize={12} color={C.neutral500}>
            {rangeLabel}
          </Text>
        </YStack>
        <XStack gap={6}>
          <WeekNavButton label="Previous week" onPress={() => onMoveWeek(-7)}>
            <ChevronLeft size={16} color={C.neutral700} />
          </WeekNavButton>
          <Button
            height={34}
            paddingHorizontal={12}
            borderRadius={10}
            backgroundColor={C.card}
            borderWidth={1}
            borderColor={C.neutral200}
            pressStyle={{ backgroundColor: '#FAFAF9', scale: 0.98 }}
            onPress={onToday}
          >
            <Text fontSize={12} fontWeight="600" color={C.brand600}>
              Today
            </Text>
          </Button>
          <WeekNavButton label="Next week" onPress={() => onMoveWeek(7)}>
            <ChevronRight size={16} color={C.neutral700} />
          </WeekNavButton>
        </XStack>
      </XStack>
      <XStack marginHorizontal={16} gap={8}>
        {days.map((day) => (
          <Button
            key={day.key}
            flex={1}
            height={60}
            padding={0}
            borderRadius={10}
            backgroundColor={day.bg}
            borderWidth={day.isSelected ? 2 : 1}
            borderColor={day.isSelected ? C.brand700 : 'transparent'}
            pressStyle={{ scale: 0.97 }}
            onPress={() => onSelectDate(day.key)}
          >
            <YStack alignItems="center" justifyContent="center">
              <Text fontSize={13} fontWeight="500" color={day.color}>
                {day.label}
              </Text>
              <Text fontSize={16} fontWeight="500" color={day.color} fontFamily="$mono">
                {day.date}
              </Text>
            </YStack>
          </Button>
        ))}
      </XStack>
    </YStack>
  );
}

function WeekNavButton({
  label,
  children,
  onPress,
}: {
  label: string;
  children: React.ReactNode;
  onPress: () => void;
}) {
  return (
    <Button
      width={34}
      height={34}
      padding={0}
      borderRadius={10}
      backgroundColor={C.card}
      borderWidth={1}
      borderColor={C.neutral200}
      aria-label={label}
      pressStyle={{ backgroundColor: '#FAFAF9', scale: 0.96 }}
      onPress={onPress}
    >
      {children}
    </Button>
  );
}

function UpcomingJobCard({
  assignment,
  onPress,
}: {
  assignment: WorkerAssignment;
  onPress: () => void;
}) {
  const requirement = assignment.requirement;

  return (
    <Button
      unstyled
      onPress={onPress}
      pressStyle={{ opacity: 0.85, scale: 0.99 }}
    >
      <CompactCard>
        <XStack alignItems="flex-start" justifyContent="space-between" gap={12}>
          <YStack flex={1}>
            <Text fontSize={15} fontWeight="500" color={C.neutral900}>
              {requirement?.category ?? 'Assigned job'}
            </Text>
            <Text marginTop={4} fontSize={13} color={C.neutral500}>
              {requirement ? `${requirement.city}, ${requirement.state}` : 'Location not available'}
            </Text>
            <Text marginTop={8} fontSize={13} color={C.neutral700} fontFamily="$mono">
              {assignment.start_date ? formatDate(assignment.start_date) : requirement ? formatDate(requirement.start_date) : 'Date not available'}
            </Text>
          </YStack>
          <StatusPill status={assignment.status} />
        </XStack>
      </CompactCard>
    </Button>
  );
}


function NoticeCard() {
  return (
    <XStack
      borderLeftWidth={3}
      borderLeftColor={C.brand600}
      borderRadius={8}
      backgroundColor="#EDFAF3"
      padding={14}
      gap={10}
      alignItems="flex-start"
    >
      <MapPin size={18} color={C.brand600} />
      <Text flex={1} fontSize={13} lineHeight={20} color={C.neutral700}>
        Keep location access enabled before your shift. Check-in will use your job site location.
      </Text>
    </XStack>
  );
}

function EmptyUpcoming({ hasHero }: { hasHero: boolean }) {
  return (
    <CompactCard>
      <Text fontSize={15} fontWeight="500" color={C.neutral900}>
        {hasHero ? 'No more jobs' : 'No jobs yet'}
      </Text>
      <Text marginTop={6} fontSize={13} lineHeight={20} color={C.neutral500}>
        {hasHero
          ? 'Your next assigned job will appear here.'
          : 'Assignments from admin will appear here.'}
      </Text>
    </CompactCard>
  );
}

function LoadingHero() {
  return (
    <YStack marginHorizontal={16} marginTop={12} borderRadius={24} padding={24} minHeight={252} backgroundColor={C.brand900}>
      <ActivityIndicator color="#FFFFFF" />
      <Text marginTop={16} textAlign="center" color="rgba(255,255,255,0.62)" fontSize={14}>
        Loading today's shift...
      </Text>
    </YStack>
  );
}

function CompactCard({ children }: { children: React.ReactNode }) {
  return (
    <Card
      bordered
      borderRadius={12}
      borderColor={C.neutral200}
      backgroundColor={C.card}
      padding={16}
    >
      {children}
    </Card>
  );
}

function DarkIconButton({ children, onPress, 'aria-label': ariaLabel }: { children: React.ReactNode; onPress?: () => void; 'aria-label'?: string }) {
  return (
    <Button
      width={40}
      height={40}
      padding={0}
      borderRadius={20}
      backgroundColor="rgba(255,255,255,0.10)"
      borderWidth={1}
      borderColor="rgba(255,255,255,0.15)"
      pressStyle={{ backgroundColor: 'rgba(255,255,255,0.18)', scale: 0.98 }}
      onPress={onPress}
      aria-label={ariaLabel}
    >
      {children}
    </Button>
  );
}

function QuickActionTile({
  icon,
  label,
  stat,
  statColor,
  bgColor,
  onPress,
}: {
  icon: React.ReactNode;
  label: string;
  stat: string;
  statColor?: string;
  bgColor?: string;
  onPress: () => void;
}) {
  return (
    <Button
      unstyled
      flex={1}
      onPress={onPress}
      pressStyle={{ opacity: 0.82, scale: 0.97 }}
    >
      <YStack
        flex={1}
        borderRadius={16}
        padding={16}
        backgroundColor={bgColor ?? C.card}
        borderWidth={1}
        borderColor={C.neutral200}
        gap={10}
      >
        {icon}
        <YStack gap={3}>
          <Text fontSize={13} fontWeight="600" color={C.neutral900}>
            {label}
          </Text>
          <Text fontSize={12} color={statColor ?? C.neutral500}>
            {stat}
          </Text>
        </YStack>
      </YStack>
    </Button>
  );
}

function SectionLabel({ label }: { label: string }) {
  return (
    <Text fontSize={12} fontWeight="500" color={C.neutral500}>
      {label}
    </Text>
  );
}

function StatusPill({ status, dark = false }: { status: WorkerAssignmentStatus; dark?: boolean }) {
  const tone = statusTone[status];
  return (
    <XStack
      height={24}
      borderRadius={999}
      paddingHorizontal={10}
      alignItems="center"
      backgroundColor={dark ? 'rgba(255,255,255,0.12)' : tone.bg}
      gap={6}
    >
      <View width={6} height={6} borderRadius={999} backgroundColor={dark ? '#FFFFFF' : tone.color} />
      <Text fontSize={13} fontWeight="500" color={dark ? '#FFFFFF' : tone.color}>
        {statusLabel[status]}
      </Text>
    </XStack>
  );
}

function DarkMeta({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <XStack gap={8} alignItems="center">
      {icon}
      <Text flex={1} fontSize={13} lineHeight={20} color="rgba(255,255,255,0.66)">
        {children}
      </Text>
    </XStack>
  );
}

async function getCurrentLocation() {
  const permission = await Location.requestForegroundPermissionsAsync();
  if (permission.status !== Location.PermissionStatus.GRANTED) {
    throw Object.assign(new Error('Location permission denied.'), { code: 'PERMISSION_DENIED' });
  }

  const GPS_TIMEOUT_MS = 10_000;
  const MAX_ACCURACY_METERS = 100;

  const timeoutPromise = new Promise<never>((_, reject) =>
    setTimeout(
      () =>
        reject(
          Object.assign(new Error('GPS timed out. Move to an open area and retry.'), {
            code: 'GPS_TIMEOUT',
          }),
        ),
      GPS_TIMEOUT_MS,
    ),
  );

  const locationPromise = Location.getCurrentPositionAsync({
    accuracy: Location.Accuracy.Balanced,
  });

  const position = await Promise.race([locationPromise, timeoutPromise]);

  const accuracy = position.coords.accuracy ?? 0;
  if (accuracy > MAX_ACCURACY_METERS) {
    throw Object.assign(
      new Error(`GPS accuracy is low (${Math.round(accuracy)} m). Move outdoors and retry.`),
      { code: 'LOW_ACCURACY', position },
    );
  }

  return position;
}

function assignmentCoversDate(assignment: WorkerAssignment, dateKey: string): boolean {
  if (!assignment.start_date) return false;
  const start = assignment.start_date;
  const end = assignment.end_date ?? assignment.start_date;
  return start <= dateKey && dateKey <= end;
}

function pickHeroAssignment(assignments: WorkerAssignment[], selectedDateKey: string) {
  const selectedAssignments = assignments.filter((item) =>
    assignmentCoversDate(item, selectedDateKey),
  );

  return (
    selectedAssignments.find((item) => item.status === 'active') ||
    selectedAssignments.find((item) => item.status === 'accepted') ||
    selectedAssignments.find((item) => item.status === 'assigned') ||
    selectedAssignments[0] ||
    null
  );
}

function buildWeek(assignments: WorkerAssignment[], visibleDate: Date, selectedDateKey: string) {
  const today = new Date();
  const start = startOfWeek(visibleDate);

  // Collect every individual date covered by any assignment (handles multi-day ranges).
  const jobDates = new Set<string>();
  for (const item of assignments) {
    if (!item.start_date) continue;
    const assignEnd = item.end_date ?? item.start_date;
    let cur = parseApiDate(item.start_date);
    const endDate = parseApiDate(assignEnd);
    while (cur <= endDate) {
      jobDates.add(toDateKey(cur));
      cur = addDays(cur, 1);
    }
  }

  return Array.from({ length: 7 }).map((_, index) => {
    const date = addDays(start, index);
    const key = toDateKey(date);
    const isToday = key === toDateKey(today);
    const hasJob = jobDates.has(key);
    const isSelected = key === selectedDateKey;

    return {
      key,
      dateValue: date,
      isSelected,
      label: date.toLocaleDateString('en-IN', { weekday: 'short' }).slice(0, 1),
      date: String(date.getDate()).padStart(2, '0'),
      bg: isSelected ? C.brand600 : isToday ? C.brand100 : hasJob ? C.brand100 : C.neutral200,
      color: isSelected ? '#FFFFFF' : isToday || hasJob ? C.brand700 : C.neutral500,
    };
  });
}

function toDateKey(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function parseApiDate(value: string) {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, month - 1, day);
}

function formatTime(value: string | null | undefined) {
  if (!value) return '—';
  const d = new Date(value.replace(' ', 'T'));
  if (isNaN(d.getTime())) return '—';
  return new Intl.DateTimeFormat('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(d);
}

function addDays(date: Date, days: number) {
  const next = new Date(date);
  next.setDate(date.getDate() + days);
  return next;
}

function startOfWeek(date: Date) {
  const start = new Date(date);
  const day = start.getDay();
  const mondayOffset = day === 0 ? -6 : 1 - day;
  start.setDate(start.getDate() + mondayOffset);
  start.setHours(0, 0, 0, 0);
  return start;
}

function isCurrentWeek(date: Date) {
  return toDateKey(startOfWeek(date)) === toDateKey(startOfWeek(new Date()));
}

function calcMonthAttendancePct(records: import('../../../shared/services/worker-attendance.service').WorkerAttendanceRecord[]) {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const daysSoFar = Math.min(now.getDate(), daysInMonth);
  const thisMonth = records.filter((r) => {
    const d = parseApiDate(r.attendance_date);
    return d.getFullYear() === year && d.getMonth() === month;
  });
  const present = thisMonth.filter((r) =>
    r.status === 'present' || r.status === 'approved' || r.status === 'corrected' || r.check_in_time !== null,
  ).length;
  return daysSoFar === 0 ? 0 : Math.round((present / daysSoFar) * 100);
}

function formatToday() {
  return new Intl.DateTimeFormat('en-IN', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date());
}

function formatSelectedDate(date: Date) {
  const today = new Date();
  const isToday = toDateKey(date) === toDateKey(today);
  const tomorrow = addDays(today, 1);
  const isTomorrow = toDateKey(date) === toDateKey(tomorrow);
  if (isToday) return 'Today';
  if (isTomorrow) return 'Tomorrow';
  return new Intl.DateTimeFormat('en-IN', { weekday: 'short', day: 'numeric', month: 'short' }).format(date);
}

function formatWeekRange(from: Date, to: Date) {
  const sameMonth = from.getMonth() === to.getMonth();
  const dayFrom = from.getDate();
  const dayTo = to.getDate();
  const month = new Intl.DateTimeFormat('en-IN', { month: 'short' }).format(from);
  const monthTo = new Intl.DateTimeFormat('en-IN', { month: 'short' }).format(to);
  if (sameMonth) return `${month} ${dayFrom}–${dayTo}`;
  return `${month} ${dayFrom} – ${monthTo} ${dayTo}`;
}

function formatDate(value: string | null | undefined) {
  if (!value) return '—';
  const d = parseApiDate(value);
  if (isNaN(d.getTime())) return '—';
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(d);
}
