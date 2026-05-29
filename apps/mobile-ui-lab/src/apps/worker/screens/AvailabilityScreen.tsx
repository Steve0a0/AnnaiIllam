import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Alert, RefreshControl } from 'react-native';
import { ChevronLeft, ChevronRight, Moon } from 'lucide-react-native';
import { Button, Card, ScrollView, Text, View, XStack, YStack } from 'tamagui';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { workerProfileService, type WorkerProfileSummary } from '../../../shared/services/worker-profile.service';
import {
  workerAvailabilityService,
  type WorkerAvailabilityRecord,
  type WorkerAvailabilityStatus,
} from '../../../shared/services/worker-availability.service';

const C = {
  page: '#F5F5F4',
  card: '#FFFFFF',
  brand900: '#0D2E1E',
  brand600: '#1A6640',
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
};

const dayOptions = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const shiftOptions = ['Morning', 'General', 'Evening', 'Night'];

export default function AvailabilityScreen() {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const [profile, setProfile] = useState<WorkerProfileSummary | null>(null);
  const [records, setRecords] = useState<WorkerAvailabilityRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingRecords, setIsLoadingRecords] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [savingDate, setSavingDate] = useState<string | null>(null);
  const [visibleStartDate, setVisibleStartDate] = useState(() => startOfToday());
  const loadedRangeRef = useRef<string | null>(null);

  const weekRange = useMemo(() => getSevenDays(visibleStartDate), [visibleStartDate]);
  const rangeKey = `${weekRange[0].key}:${weekRange[weekRange.length - 1].key}`;

  const loadProfile = useCallback(async () => {
    const profileData = await workerProfileService.getProfile();
    setProfile(profileData);
  }, []);

  const loadRecords = useCallback(async (showInlineLoader = false) => {
    if (showInlineLoader) setIsLoadingRecords(true);
    const recordData = await workerAvailabilityService.list(
      weekRange[0].key,
      weekRange[weekRange.length - 1].key,
    );
    setRecords(recordData);
    loadedRangeRef.current = rangeKey;
    setIsLoadingRecords(false);
  }, [rangeKey, weekRange]);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);
      Promise.all([loadProfile(), loadRecords(false)])
        .catch(() => {
          if (active) Alert.alert('Could not load availability', 'Pull down to refresh.');
        })
        .finally(() => active && setIsLoading(false));
      return () => {
        active = false;
      };
    }, [loadProfile]),
  );

  useEffect(() => {
    if (isLoading) return;
    if (loadedRangeRef.current === rangeKey) return;
    loadRecords(true).catch(() => {
      Alert.alert('Could not load dates', 'Please try again.');
      setIsLoadingRecords(false);
    });
  }, [isLoading, loadRecords, rangeKey]);

  const refresh = async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([loadProfile(), loadRecords(false)]);
    } finally {
      setIsRefreshing(false);
    }
  };

  const selectedDays = csvToSet(profile?.available_days);
  const selectedShifts = csvToSet(profile?.available_shifts);
  const recordsByDate = new Map(records.map((record) => [record.availability_date, record]));

  const patchProfile = async (patch: { is_available?: boolean; available_days?: string[] | null; available_shifts?: string[] | null }) => {
    if (!profile) return;
    setIsSavingProfile(true);
    try {
      const nextProfile = await workerProfileService.patch(patch);
      setProfile({ ...profile, ...nextProfile });
    } catch {
      Alert.alert('Could not update availability', 'Please try again.');
    } finally {
      setIsSavingProfile(false);
    }
  };

  const toggleDayPreference = async (day: string) => {
    const next = new Set(selectedDays);
    if (next.has(day)) next.delete(day);
    else next.add(day);
    const arr = Array.from(next);
    await patchProfile({ available_days: arr.length ? arr : null });
  };

  const toggleShiftPreference = async (shift: string) => {
    const next = new Set(selectedShifts);
    if (next.has(shift)) next.delete(shift);
    else next.add(shift);
    const arr = Array.from(next);
    await patchProfile({ available_shifts: arr.length ? arr : null });
  };

  const setDateStatus = async (dateKey: string, status: WorkerAvailabilityStatus) => {
    setSavingDate(dateKey);
    try {
      const record = await workerAvailabilityService.setDay(dateKey, status);
      setRecords((current) => {
        const without = current.filter((item) => item.availability_date !== dateKey);
        return [...without, record].sort((a, b) => a.availability_date.localeCompare(b.availability_date));
      });
    } catch {
      Alert.alert('Could not update day', 'Please try again.');
    } finally {
      setSavingDate(null);
    }
  };

  return (
    <View flex={1} backgroundColor={C.page} paddingTop={insets.top}>
      <XStack height={56} paddingHorizontal={20} alignItems="center" justifyContent="space-between">
        <Button
          width={44}
          height={44}
          padding={0}
          borderRadius={22}
          backgroundColor={C.card}
          borderWidth={1}
          borderColor={C.neutral200}
          onPress={() => navigation.goBack()}
        >
          <ChevronLeft size={20} color={C.neutral700} />
        </Button>
        <YStack alignItems="center">
          <Text fontSize={17} fontWeight="600" color={C.neutral900}>
            Availability
          </Text>
          <Text fontSize={13} color={C.neutral500}>
            Keep it current
          </Text>
        </YStack>
        <View width={44} />
      </XStack>

      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={refresh} />}
      >
        <YStack paddingHorizontal={16} paddingBottom={insets.bottom + 28} gap={16}>
          {isLoading ? (
            <Card bordered borderRadius={16} padding={28} alignItems="center" backgroundColor={C.card}>
              <ActivityIndicator color={C.brand600} />
              <Text marginTop={12} color={C.neutral500} fontSize={14}>
                Loading availability...
              </Text>
            </Card>
          ) : !profile ? (
            <Card bordered borderRadius={16} padding={20} backgroundColor={C.card}>
              <Text fontSize={15} color={C.neutral900} fontWeight="600">
                Profile unavailable
              </Text>
              <Text marginTop={6} fontSize={13} color={C.neutral500}>
                Pull down to refresh and try again.
              </Text>
            </Card>
          ) : (
            <>
              <PreferenceCard title="Preferred Days" detail="Used by admin matching. Choose the days you normally work.">
                <XStack flexWrap="wrap" gap={8}>
                  {dayOptions.map((day) => (
                    <Chip
                      key={day}
                      label={day}
                      selected={selectedDays.has(day)}
                      disabled={isSavingProfile}
                      onPress={() => toggleDayPreference(day)}
                    />
                  ))}
                </XStack>
              </PreferenceCard>

              <PreferenceCard title="Preferred Shifts" detail="Choose when you normally want assignments.">
                <XStack flexWrap="wrap" gap={8}>
                  {shiftOptions.map((shift) => (
                    <Chip
                      key={shift}
                      label={shift}
                      selected={selectedShifts.has(shift)}
                      disabled={isSavingProfile}
                      onPress={() => toggleShiftPreference(shift)}
                    />
                  ))}
                </XStack>
              </PreferenceCard>

              <PreferenceCard
                title="Next 7 Days"
                detail="Mark days you cannot work. This overrides your normal preferences."
                action={
                  <XStack gap={6}>
                    <DateNavButton
                      label="Previous 7 days"
                      onPress={() => setVisibleStartDate((current) => addDays(current, -7))}
                    >
                      <ChevronLeft size={16} color={C.neutral700} />
                    </DateNavButton>
                    <Button
                      height={34}
                      paddingHorizontal={12}
                      borderRadius={10}
                      backgroundColor={C.card}
                      borderWidth={1}
                      borderColor={C.neutral200}
                      pressStyle={{ backgroundColor: '#FAFAF9', scale: 0.98 }}
                      onPress={() => setVisibleStartDate(startOfToday())}
                    >
                      <Text fontSize={12} fontWeight="600" color={C.brand600}>
                        Today
                      </Text>
                    </Button>
                    <DateNavButton
                      label="Next 7 days"
                      onPress={() => setVisibleStartDate((current) => addDays(current, 7))}
                    >
                      <ChevronRight size={16} color={C.neutral700} />
                    </DateNavButton>
                  </XStack>
                }
              >
                <Text marginBottom={12} fontSize={12} color={C.neutral500} fontFamily="$mono">
                  {formatRange(weekRange[0].dateValue, weekRange[weekRange.length - 1].dateValue)}
                </Text>
                {isLoadingRecords ? (
                  <YStack paddingVertical={20} alignItems="center">
                    <ActivityIndicator color={C.brand600} />
                    <Text marginTop={10} fontSize={13} color={C.neutral500}>
                      Loading dates...
                    </Text>
                  </YStack>
                ) : (
                <YStack gap={10}>
                  {weekRange.map((day) => {
                    const record = recordsByDate.get(day.key);
                    const status = record?.status ?? 'available';
                    return (
                      <XStack key={day.key} alignItems="center" gap={10}>
                        <YStack width={54}>
                          <Text fontSize={13} fontWeight="600" color={C.neutral900}>
                            {day.label}
                          </Text>
                          <Text fontSize={13} color={C.neutral500} fontFamily="$mono">
                            {day.date}
                          </Text>
                        </YStack>
                        <XStack flex={1} gap={6}>
                          {(['available', 'unavailable', 'leave'] as WorkerAvailabilityStatus[]).map((option) => (
                            <StatusChip
                              key={option}
                              label={option === 'available' ? 'Free' : option === 'unavailable' ? 'Busy' : 'Leave'}
                              selected={status === option}
                              status={option}
                              disabled={savingDate === day.key}
                              onPress={() => setDateStatus(day.key, option)}
                            />
                          ))}
                        </XStack>
                      </XStack>
                    );
                  })}
                </YStack>
                )}
              </PreferenceCard>

              <XStack borderLeftWidth={3} borderLeftColor={C.brand600} borderRadius={8} backgroundColor="#EDFAF3" padding={14} gap={10}>
                <Moon size={18} color={C.brand600} />
                <Text flex={1} fontSize={13} lineHeight={20} color={C.neutral700}>
                  Keep this simple. Update only when your usual days, shifts, or next week availability changes.
                </Text>
              </XStack>
            </>
          )}
        </YStack>
      </ScrollView>
    </View>
  );
}

function PreferenceCard({
  title,
  detail,
  action,
  children,
}: {
  title: string;
  detail: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Card bordered borderRadius={16} padding={18} backgroundColor={C.card} borderColor={C.neutral200}>
      <XStack alignItems="flex-start" justifyContent="space-between" gap={12}>
        <YStack flex={1}>
          <Text fontSize={16} fontWeight="600" color={C.neutral900}>
            {title}
          </Text>
          <Text marginTop={4} marginBottom={14} fontSize={13} lineHeight={19} color={C.neutral500}>
            {detail}
          </Text>
        </YStack>
        {action}
      </XStack>
      {children}
    </Card>
  );
}

function DateNavButton({
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
      accessibilityLabel={label}
      pressStyle={{ backgroundColor: '#FAFAF9', scale: 0.96 }}
      onPress={onPress}
    >
      {children}
    </Button>
  );
}

function Chip({ label, selected, disabled, onPress }: { label: string; selected: boolean; disabled: boolean; onPress: () => void }) {
  return (
    <Button
      minWidth={64}
      height={42}
      borderRadius={12}
      backgroundColor={selected ? C.brand600 : C.card}
      borderWidth={1}
      borderColor={selected ? C.brand600 : C.neutral200}
      disabled={disabled}
      onPress={onPress}
    >
      <Text fontSize={13} fontWeight="600" color={selected ? '#FFFFFF' : C.neutral700}>
        {label}
      </Text>
    </Button>
  );
}

function StatusChip({
  label,
  selected,
  status,
  disabled,
  onPress,
}: {
  label: string;
  selected: boolean;
  status: WorkerAvailabilityStatus;
  disabled: boolean;
  onPress: () => void;
}) {
  const tone =
    status === 'available'
      ? { bg: C.success100, fg: C.success700 }
      : status === 'leave'
        ? { bg: C.warning100, fg: C.warning700 }
        : { bg: C.danger100, fg: C.danger700 };
  return (
    <Button
      flex={1}
      height={38}
      borderRadius={10}
      backgroundColor={selected ? tone.bg : '#FAFAF9'}
      borderWidth={1}
      borderColor={selected ? tone.fg : C.neutral200}
      disabled={disabled}
      onPress={onPress}
    >
      <Text fontSize={13} fontWeight="600" color={selected ? tone.fg : C.neutral500}>
        {label}
      </Text>
    </Button>
  );
}

function csvToSet(value?: string | string[] | null) {
  if (!value) return new Set<string>();
  if (Array.isArray(value)) return new Set(value.filter(Boolean));
  return new Set(value.split(',').map((item) => item.trim()).filter(Boolean));
}

function getSevenDays(startDate: Date) {
  return Array.from({ length: 7 }).map((_, index) => {
    const date = addDays(startDate, index);
    return {
      key: toApiDate(date),
      label: date.toLocaleDateString('en-IN', { weekday: 'short' }),
      date: date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }),
      dateValue: date,
    };
  });
}

function startOfToday() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return today;
}

function addDays(date: Date, days: number) {
  const next = new Date(date);
  next.setDate(date.getDate() + days);
  return next;
}

function formatRange(start: Date, end: Date) {
  return `${start.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
  })} - ${end.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })}`;
}

function toApiDate(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
