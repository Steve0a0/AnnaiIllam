import React, { useCallback, useState } from 'react';
import { ActivityIndicator, Alert, Linking, Platform } from 'react-native';
import {
  BriefcaseBusiness,
  CalendarDays,
  Check,
  ChevronLeft,
  Clock3,
  MapPin,
  UtensilsCrossed,
  Home,
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
import { useFocusEffect, useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  workerAssignmentsService,
  type WorkerAssignment,
  type WorkerAssignmentStatus,
} from '../../../shared/services/worker-assignments.service';
import {
  workerAttendanceService,
  type WorkerAttendanceRecord,
} from '../../../shared/services/worker-attendance.service';
import { workerOnboardingService } from '../../../shared/services/worker-onboarding.service';
import type { HomeStackParamList } from '../navigation/types';
import * as Location from 'expo-location';
import * as ImagePicker from 'expo-image-picker';

type Navigation = NativeStackNavigationProp<HomeStackParamList>;
type RouteProps = NativeStackScreenProps<HomeStackParamList, 'JobDetail'>['route'];

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
  active: 'Checked In',
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

export default function JobDetailScreen() {
  const navigation = useNavigation<Navigation>();
  const route = useRoute<RouteProps>();
  const insets = useSafeAreaInsets();
  const { assignmentId } = route.params;

  const [assignment, setAssignment] = useState<WorkerAssignment | null>(null);
  const [attendance, setAttendance] = useState<WorkerAttendanceRecord | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    const [assignmentsResult, attendanceResult] = await Promise.allSettled([
      workerAssignmentsService.list(),
      workerAttendanceService.list(),
    ]);

    if (assignmentsResult.status === 'fulfilled') {
      const found = assignmentsResult.value.find(
        (a) => a.assignment_id === assignmentId,
      );
      setAssignment(found ?? null);

      if (attendanceResult.status === 'fulfilled' && found) {
        const today = toDateKey(new Date());
        const rec = attendanceResult.value.find(
          (r) =>
            r.assignment_id === found.assignment_id &&
            r.attendance_date === today,
        );
        setAttendance(rec ?? null);
      }
    } else {
      setError('Could not load job details. Pull down to retry.');
    }
  }, [assignmentId]);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);
      load().finally(() => active && setIsLoading(false));
      return () => { active = false; };
    }, [load]),
  );

  const handleDecide = (action: 'accept' | 'decline') => {
    if (!assignment) return;
    const title = action === 'accept' ? 'Accept this shift?' : 'Decline this shift?';
    const message =
      action === 'accept'
        ? 'This confirms you are available for the assigned job.'
        : 'Admin will be notified and may assign another worker.';

    Alert.alert(title, message, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: action === 'accept' ? 'Accept' : 'Decline',
        style: action === 'decline' ? 'destructive' : 'default',
        onPress: async () => {
          setIsBusy(true);
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
            setIsBusy(false);
          }
        },
      },
    ]);
  };

  const handleAttendance = (action: 'check_in' | 'check_out') => {
    if (!assignment) return;
    const title = action === 'check_in' ? 'Check in now?' : 'Check out now?';
    const message =
      action === 'check_in'
        ? 'Your GPS location and a selfie will be recorded for this check-in.'
        : 'Your current GPS location will be recorded for this check-out.';

    Alert.alert(title, message, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: action === 'check_in' ? 'Check In' : 'Check Out',
        onPress: async () => {
          setIsBusy(true);
          try {
            // 1. Location permission + position (both actions)
            const locPerm = await Location.requestForegroundPermissionsAsync();
            if (locPerm.status !== Location.PermissionStatus.GRANTED) {
              throw new Error('Location permission is required for attendance.');
            }
            const pos = await Location.getCurrentPositionAsync({
              accuracy: Location.Accuracy.Balanced,
            });

            const payload: {
              assignment_id: number;
              latitude: number;
              longitude: number;
              selfie_url?: string;
              selfie_token?: string;
            } = {
              assignment_id: assignment.assignment_id,
              latitude: pos.coords.latitude,
              longitude: pos.coords.longitude,
            };

            // 2. Selfie capture + upload (check-in only)
            if (action === 'check_in') {
              const camPerm = await ImagePicker.requestCameraPermissionsAsync();
              if (camPerm.status !== 'granted') {
                throw new Error(
                  'Camera permission is required to take a selfie for check-in. Please enable it in your device settings.',
                );
              }

              // Get a one-time selfie token before opening the camera
              const selfieToken = await workerAttendanceService.getSelfieToken();

              const photo = await ImagePicker.launchCameraAsync({
                mediaTypes: ['images'],
                allowsEditing: true,
                aspect: [1, 1],
                quality: 0.8,
              });
              if (photo.canceled) {
                setIsBusy(false);
                return;
              }

              const asset = photo.assets[0];
              const selfieSize = asset.fileSize
                ?? await workerOnboardingService.getLocalFileSize(asset.uri);
              const uploadInfo = await workerOnboardingService.getUploadUrl(
                'selfie',
                asset.mimeType ?? 'image/jpeg',
                selfieSize,
              );

              if (uploadInfo.upload_url) {
                await workerOnboardingService.uploadToStorage(
                  uploadInfo.upload_url,
                  asset.uri,
                  asset.mimeType ?? 'image/jpeg',
                  uploadInfo.upload_headers,
                );
                payload.selfie_url = uploadInfo.object_url ?? asset.uri;
              } else {
                // Dev / local: no storage configured — pass local URI
                payload.selfie_url = asset.uri;
              }

              payload.selfie_token = selfieToken;
            }

            if (action === 'check_in') {
              await workerAttendanceService.checkIn(payload);
            } else {
              await workerAttendanceService.checkOut(payload);
            }
            await load();
          } catch (err) {
            Alert.alert(
              action === 'check_in' ? 'Could not check in' : 'Could not check out',
              err instanceof Error ? err.message : 'Please try again.',
            );
          } finally {
            setIsBusy(false);
          }
        },
      },
    ]);
  };

  const req = assignment?.requirement;
  const tone = assignment ? statusTone[assignment.status] : null;
  const today = toDateKey(new Date());

  // Use assignment-specific window if set, otherwise fall back to full requirement range
  const rangeStart = assignment?.start_date ?? req?.start_date ?? null;
  const rangeEnd = assignment?.end_date ?? (
    req ? toDateKey(addDays(parseApiDate(req.start_date), req.duration_days - 1)) : null
  );
  const isWithinRange =
    rangeStart != null &&
    today >= rangeStart &&
    (rangeEnd == null || today <= rangeEnd);

  const hasCheckedIn = Boolean(attendance?.check_in_time);
  const hasCheckedOut = Boolean(attendance?.check_out_time);
  const canCheckIn = isWithinRange && ['assigned', 'accepted'].includes(assignment?.status ?? '') && !hasCheckedIn;
  const canCheckOut = isWithinRange && (assignment?.status === 'active' || hasCheckedIn) && !hasCheckedOut;

  return (
    <View flex={1} backgroundColor={C.page} paddingTop={insets.top}>
      {/* Header */}
      <XStack
        height={56}
        paddingHorizontal={16}
        alignItems="center"
        gap={12}
        backgroundColor={C.page}
      >
        <Button
          width={40}
          height={40}
          padding={0}
          borderRadius={20}
          backgroundColor={C.card}
          borderWidth={1}
          borderColor={C.neutral200}
          pressStyle={{ backgroundColor: '#FAFAF9', scale: 0.96 }}
          onPress={() => navigation.goBack()}
          aria-label="Go back"
        >
          <ChevronLeft size={20} color={C.neutral700} />
        </Button>
        <Text fontSize={17} fontWeight="600" color={C.neutral900} flex={1}>
          Job Detail
        </Text>
        {assignment && tone ? (
          <XStack
            height={26}
            borderRadius={999}
            paddingHorizontal={10}
            alignItems="center"
            backgroundColor={tone.bg}
            gap={6}
          >
            <View width={6} height={6} borderRadius={999} backgroundColor={tone.color} />
            <Text fontSize={12} fontWeight="500" color={tone.color}>
              {statusLabel[assignment.status]}
            </Text>
          </XStack>
        ) : null}
      </XStack>

      {isLoading ? (
        <YStack flex={1} alignItems="center" justifyContent="center" gap={12}>
          <ActivityIndicator size="large" color={C.brand600} />
          <Text fontSize={14} color={C.neutral500}>Loading job details...</Text>
        </YStack>
      ) : error ? (
        <YStack flex={1} alignItems="center" justifyContent="center" paddingHorizontal={32} gap={12}>
          <BriefcaseBusiness size={40} color={C.neutral300} />
          <Text fontSize={16} fontWeight="500" color={C.neutral900} textAlign="center">
            Could not load this job
          </Text>
          <Text fontSize={13} color={C.neutral500} textAlign="center" lineHeight={20}>
            {error}
          </Text>
          <Button
            height={44}
            borderRadius={12}
            backgroundColor={C.brand600}
            pressStyle={{ backgroundColor: C.brand900, scale: 0.98 }}
            onPress={() => { setIsLoading(true); load().finally(() => setIsLoading(false)); }}
          >
            <Text color="#FFFFFF" fontSize={14} fontWeight="500">Try Again</Text>
          </Button>
        </YStack>
      ) : !assignment || !req ? (
        <YStack flex={1} alignItems="center" justifyContent="center" paddingHorizontal={32} gap={12}>
          <BriefcaseBusiness size={40} color={C.neutral300} />
          <Text fontSize={16} fontWeight="500" color={C.neutral900}>Job not found</Text>
          <Text fontSize={13} color={C.neutral500} textAlign="center">
            This assignment may have been removed or updated.
          </Text>
        </YStack>
      ) : (
        <ScrollView showsVerticalScrollIndicator={false}>
          <YStack paddingBottom={insets.bottom + 32}>

            {/* Hero card */}
            <YStack
              marginHorizontal={16}
              marginTop={8}
              borderRadius={24}
              padding={24}
              backgroundColor={C.brand900}
              shadowColor="rgba(13,46,30,0.3)"
              shadowRadius={20}
              shadowOffset={{ width: 0, height: 10 }}
            >
              <Text fontSize={11} fontWeight="500" color="rgba(255,255,255,0.42)" letterSpacing={1}>
                {today === rangeStart ? "TODAY'S SHIFT" : rangeStart ? formatDate(rangeStart).toUpperCase() : formatDate(req.start_date).toUpperCase()}
              </Text>

              <Text marginTop={10} fontSize={22} fontWeight="500" color="#FFFFFF" lineHeight={28}>
                {req.category}
              </Text>
              {req.subcategory ? (
                <Text marginTop={2} fontSize={14} color="rgba(255,255,255,0.55)">
                  {req.subcategory}
                </Text>
              ) : null}

              <YStack gap={10} marginTop={16}>
                <DarkRow icon={<MapPin size={15} color="rgba(255,255,255,0.6)" />}>
                  {req.work_location}
                </DarkRow>
                <DarkRow icon={<Clock3 size={15} color="#FFFFFF" />}>
                  {assignment.assigned_shift ?? 'Shift time not yet specified'}
                </DarkRow>
                <DarkRow icon={<BriefcaseBusiness size={15} color="rgba(255,255,255,0.6)" />}>
                  {assignment.assigned_role ?? req.subcategory ?? 'Worker'}
                </DarkRow>
                <DarkRow icon={<CalendarDays size={15} color="rgba(255,255,255,0.6)" />}>
                  {assignment.start_date
                    ? `${formatDate(assignment.start_date)}${assignment.end_date ? ` → ${formatDate(assignment.end_date)}` : ''}`
                    : `${formatDate(req.start_date)}${req.duration_days > 1 ? ` · ${req.duration_days} days` : ''}`
                  }
                </DarkRow>
              </YStack>

              {/* Perks row */}
              {(req.food_required || req.accommodation_required) ? (
                <XStack marginTop={16} gap={8}>
                  {req.food_required ? (
                    <XStack
                      height={28}
                      borderRadius={999}
                      paddingHorizontal={10}
                      alignItems="center"
                      gap={6}
                      backgroundColor="rgba(255,255,255,0.10)"
                      borderWidth={1}
                      borderColor="rgba(255,255,255,0.15)"
                    >
                      <UtensilsCrossed size={12} color="rgba(255,255,255,0.75)" />
                      <Text fontSize={12} fontWeight="500" color="rgba(255,255,255,0.75)">Food</Text>
                    </XStack>
                  ) : null}
                  {req.accommodation_required ? (
                    <XStack
                      height={28}
                      borderRadius={999}
                      paddingHorizontal={10}
                      alignItems="center"
                      gap={6}
                      backgroundColor="rgba(255,255,255,0.10)"
                      borderWidth={1}
                      borderColor="rgba(255,255,255,0.15)"
                    >
                      <Home size={12} color="rgba(255,255,255,0.75)" />
                      <Text fontSize={12} fontWeight="500" color="rgba(255,255,255,0.75)">Stay</Text>
                    </XStack>
                  ) : null}
                </XStack>
              ) : null}

              <View height={1} backgroundColor="rgba(255,255,255,0.10)" marginVertical={20} />

              {/* Action area */}
              {assignment.status === 'assigned' ? (
                <YStack gap={10}>
                  <Button
                    height={56}
                    borderRadius={14}
                    backgroundColor={C.brand400}
                    pressStyle={{ backgroundColor: C.brand700, scale: 0.98 }}
                    disabled={isBusy}
                    onPress={() => handleDecide('accept')}
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
                    onPress={() => handleDecide('decline')}
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
                  onPress={() => handleAttendance('check_in')}
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
                    onPress={() => handleAttendance('check_out')}
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
                  <Text color="#FFFFFF" fontSize={14} fontWeight="500">
                    Shift complete · Checked out {attendance?.check_out_time ? formatTime(attendance.check_out_time) : ''}
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
                  <View width={8} height={8} borderRadius={999} backgroundColor={tone?.color ?? '#FFFFFF'} />
                  <Text color="#FFFFFF" fontSize={14} fontWeight="500">
                    {statusLabel[assignment.status]}
                  </Text>
                </XStack>
              )}
            </YStack>

            {/* Map strip — location context at a glance */}
            <Button
              unstyled
              marginHorizontal={16}
              marginTop={16}
              borderRadius={16}
              overflow="hidden"
              height={120}
              backgroundColor="#D1E8D0"
              borderWidth={1}
              borderColor={C.neutral200}
              pressStyle={{ opacity: 0.82 }}
              onPress={() => openMapsWithAddress(`${req.work_location}, ${req.city}, ${req.state}`)}
              accessibilityRole="button"
              accessibilityLabel={`Open ${req.work_location} in Maps`}
            >
              {/* Grid lines to suggest a map */}
              <YStack flex={1} position="relative">
                {[20, 45, 70, 95].map((pct) => (
                  <View
                    key={pct}
                    position="absolute"
                    top={`${pct}%` as never}
                    left={0}
                    right={0}
                    height={1}
                    backgroundColor="rgba(255,255,255,0.55)"
                  />
                ))}
                {[20, 40, 60, 80].map((pct) => (
                  <View
                    key={pct}
                    position="absolute"
                    left={`${pct}%` as never}
                    top={0}
                    bottom={0}
                    width={1}
                    backgroundColor="rgba(255,255,255,0.55)"
                  />
                ))}
                {/* Pin */}
                <View position="absolute" top="30%" left="50%" style={{ marginLeft: -12 }}>
                  <View
                    width={24}
                    height={24}
                    borderRadius={12}
                    backgroundColor={C.brand600}
                    alignItems="center"
                    justifyContent="center"
                    borderWidth={2}
                    borderColor="#FFFFFF"
                  >
                    <MapPin size={12} color="#FFFFFF" />
                  </View>
                </View>
              </YStack>
              {/* Location label bar */}
              <XStack
                paddingHorizontal={12}
                paddingVertical={8}
                backgroundColor="rgba(13,46,30,0.80)"
                alignItems="center"
                gap={6}
              >
                <MapPin size={12} color="rgba(255,255,255,0.8)" />
                <Text fontSize={12} fontWeight="500" color="#FFFFFF" numberOfLines={1} flex={1}>
                  {req.work_location}
                </Text>
                <Text fontSize={11} color="rgba(255,255,255,0.6)">
                  {req.city}, {req.state}
                </Text>
                <ExternalLinkIcon />
              </XStack>
            </Button>

            {/* Info section */}
            <YStack marginHorizontal={16} marginTop={20} gap={12}>
              <SectionLabel label="JOB INFORMATION" />

              <InfoCard>
                <InfoRow label="Location" value={req.work_location} />
                <Divider />
                <InfoRow label="City" value={`${req.city}, ${req.state}`} />
                <Divider />
                <InfoRow label="Job start date" value={formatDate(req.start_date)} mono />
                <Divider />
                <InfoRow label="Job duration" value={`${req.duration_days} ${req.duration_days === 1 ? 'day' : 'days'}`} />
                <Divider />
                <InfoRow label="Category" value={req.category} />
                {req.subcategory ? (
                  <>
                    <Divider />
                    <InfoRow label="Role" value={req.subcategory} />
                  </>
                ) : null}
              </InfoCard>
            </YStack>

            {/* Assignment section */}
            <YStack marginHorizontal={16} marginTop={20} gap={12}>
              <SectionLabel label="YOUR ASSIGNMENT" />

              <InfoCard>
                <InfoRow label="Your role" value={assignment.assigned_role ?? 'Not specified'} />
                <Divider />
                <InfoRow label="Shift" value={assignment.assigned_shift ?? 'Not specified'} mono />
                {assignment.start_date ? (
                  <>
                    <Divider />
                    <InfoRow
                      label="Your dates"
                      value={assignment.end_date
                        ? `${formatDate(assignment.start_date)} – ${formatDate(assignment.end_date)}`
                        : `From ${formatDate(assignment.start_date)}`}
                      mono
                    />
                  </>
                ) : null}
                {assignment.salary_amount ? (
                  <>
                    <Divider />
                    <InfoRow label="Pay" value={`₹${assignment.salary_amount.toLocaleString('en-IN')}`} mono />
                  </>
                ) : null}
                {assignment.notes ? (
                  <>
                    <Divider />
                    <InfoRow label="Notes" value={assignment.notes} />
                  </>
                ) : null}
                <Divider />
                <InfoRow
                  label="Food provided"
                  value={req.food_required ? 'Yes' : 'No'}
                />
                <Divider />
                <InfoRow
                  label="Accommodation"
                  value={req.accommodation_required ? 'Yes' : 'No'}
                />
              </InfoCard>
            </YStack>

            {/* Attendance summary if checked in/out */}
            {attendance ? (
              <YStack marginHorizontal={16} marginTop={20} gap={12}>
                <SectionLabel label="TODAY'S ATTENDANCE" />
                <InfoCard>
                  <InfoRow
                    label="Check-in"
                    value={attendance.check_in_time ? formatTime(attendance.check_in_time) : '—'}
                    mono
                  />
                  <Divider />
                  <InfoRow
                    label="Check-out"
                    value={attendance.check_out_time ? formatTime(attendance.check_out_time) : '—'}
                    mono
                  />
                  {attendance.notes ? (
                    <>
                      <Divider />
                      <InfoRow label="Admin note" value={attendance.notes} />
                    </>
                  ) : null}
                </InfoCard>
              </YStack>
            ) : null}

          </YStack>
        </ScrollView>
      )}
    </View>
  );
}

function InfoCard({ children }: { children: React.ReactNode }) {
  return (
    <YStack
      backgroundColor={C.card}
      borderRadius={14}
      borderWidth={1}
      borderColor={C.neutral200}
      overflow="hidden"
    >
      {children}
    </YStack>
  );
}

function InfoRow({
  label,
  value,
  icon,
  mono,
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <XStack paddingHorizontal={16} paddingVertical={13} alignItems="center" gap={10}>
      {icon ? <View width={20} alignItems="center">{icon}</View> : null}
      <Text fontSize={13} color={C.neutral500} flex={1}>{label}</Text>
      <Text
        fontSize={13}
        fontWeight="500"
        color={C.neutral900}
        fontFamily={mono ? '$mono' : undefined}
        textAlign="right"
        flex={1}
      >
        {value}
      </Text>
    </XStack>
  );
}

function Divider() {
  return <View height={1} backgroundColor={C.neutral200} />;
}

function SectionLabel({ label }: { label: string }) {
  return (
    <Text fontSize={11} fontWeight="600" color={C.neutral500} letterSpacing={1} marginBottom={8}>
      {label}
    </Text>
  );
}

function formatTime(value: string | null | undefined) {
  if (!value) return '—';
  // Backend returns full ISO timestamps (e.g. "2026-06-05T10:30:00").
  // Pass directly to Date — do NOT prepend "1970-01-01T".
  const d = new Date(value.replace(' ', 'T'));
  if (isNaN(d.getTime())) return '—';
  return new Intl.DateTimeFormat('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }).format(d);
}

function formatDate(value: string | null | undefined) {
  if (!value) return '—';
  const d = new Date(value.replace(' ', 'T'));
  if (isNaN(d.getTime())) return '—';
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(d);
}

function openMapsWithAddress(address: string) {
  const encoded = encodeURIComponent(address);
  const appleUrl = `maps:0,0?q=${encoded}`;
  const googleUrl = `https://www.google.com/maps/search/?api=1&query=${encoded}`;

  if (Platform.OS === 'ios') {
    Alert.alert('Open in Maps', address, [
      {
        text: 'Apple Maps',
        onPress: () =>
          Linking.openURL(appleUrl).catch(() =>
            Alert.alert('Could not open Apple Maps'),
          ),
      },
      {
        text: 'Google Maps',
        onPress: () =>
          Linking.openURL(googleUrl).catch(() =>
            Alert.alert('Could not open Google Maps'),
          ),
      },
      { text: 'Cancel', style: 'cancel' },
    ]);
  } else {
    Linking.openURL(googleUrl).catch(() =>
      Alert.alert('Could not open Maps', 'No maps app found on this device.'),
    );
  }
}

function ExternalLinkIcon() {
  return (
    <View
      width={20}
      height={20}
      borderRadius={10}
      backgroundColor="rgba(255,255,255,0.18)"
      alignItems="center"
      justifyContent="center"
    >
      <MapPin size={11} color="#FFFFFF" />
    </View>
  );
}

function DarkRow({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <XStack alignItems="center" gap={8}>
      <View width={18} alignItems="center">{icon}</View>
      <Text fontSize={13} color="rgba(255,255,255,0.75)" flex={1} numberOfLines={2}>
        {children as string}
      </Text>
    </XStack>
  );
}

function toDateKey(date: Date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function parseApiDate(value: string) {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, month - 1, day);
}

function addDays(date: Date, days: number) {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
}
