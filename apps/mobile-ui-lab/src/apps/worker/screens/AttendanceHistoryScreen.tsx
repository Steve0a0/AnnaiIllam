import React, { useCallback, useState } from 'react';
import { ActivityIndicator } from 'react-native';
import {
  CalendarDays,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Clock,
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
  workerAttendanceService,
  type WorkerAttendanceRecord,
  type WorkerAttendanceStatus,
} from '../../../shared/services/worker-attendance.service';
import type { AttendanceStackParamList } from '../navigation/types';

type Navigation = NativeStackNavigationProp<AttendanceStackParamList>;

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

const statusMeta: Record<WorkerAttendanceStatus, { label: string; bg: string; color: string }> = {
  present: { label: 'Present', bg: C.success100, color: C.success700 },
  approved: { label: 'Verified', bg: C.success100, color: C.success700 },
  corrected: { label: 'Corrected', bg: C.info100, color: C.info700 },
  late: { label: 'Late', bg: C.warning100, color: C.warning700 },
  half_day: { label: 'Half Day', bg: C.warning100, color: C.warning700 },
  absent: { label: 'Absent', bg: C.danger100, color: C.danger700 },
};

const DAY_LABELS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];

export default function AttendanceHistoryScreen() {
  const navigation = useNavigation<Navigation>();
  const insets = useSafeAreaInsets();

  const [records, setRecords] = useState<WorkerAttendanceRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewDate, setViewDate] = useState(() => new Date());

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await workerAttendanceService.list();
      setRecords(data);
    } catch {
      setError('Could not load attendance. Pull down to retry.');
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);
      load().finally(() => active && setIsLoading(false));
      return () => { active = false; };
    }, [load]),
  );

  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();

  const moveMonth = (delta: number) => {
    setViewDate((d) => {
      const next = new Date(d);
      next.setDate(1);
      next.setMonth(next.getMonth() + delta);
      return next;
    });
  };

  const monthLabel = viewDate.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });
  const calDays = buildCalendar(year, month, records);

  // Records for this month, sorted newest first
  const monthRecords = records
    .filter((r) => {
      const d = parseApiDate(r.attendance_date);
      return d.getFullYear() === year && d.getMonth() === month;
    })
    .sort((a, b) => b.attendance_date.localeCompare(a.attendance_date));

  // Summary counts
  const presentCount = records.filter((r) => r.status === 'present' || r.status === 'approved').length;
  const lateCount = records.filter((r) => r.status === 'late').length;
  const absentCount = records.filter((r) => r.status === 'absent').length;

  return (
    <View flex={1} backgroundColor={C.page} paddingTop={insets.top}>
      {/* Header */}
      <XStack height={56} paddingHorizontal={20} alignItems="center">
        <Text fontSize={17} fontWeight="600" color={C.neutral900} flex={1}>
          Attendance History
        </Text>
      </XStack>

      {isLoading ? (
        <YStack flex={1} alignItems="center" justifyContent="center" gap={12}>
          <ActivityIndicator size="large" color={C.brand600} />
          <Text fontSize={14} color={C.neutral500}>Loading attendance...</Text>
        </YStack>
      ) : error ? (
        <YStack flex={1} alignItems="center" justifyContent="center" paddingHorizontal={32} gap={12}>
          <CalendarDays size={40} color={C.neutral300} />
          <Text fontSize={16} fontWeight="500" color={C.neutral900} textAlign="center">
            Could not load attendance
          </Text>
          <Text fontSize={13} color={C.neutral500} textAlign="center">{error}</Text>
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
      ) : (
        <ScrollView showsVerticalScrollIndicator={false}>
          <YStack paddingBottom={insets.bottom + 32}>

            {/* Streak counter */}
            {records.length > 0 ? (
              <StreakCard streak={calcStreak(records)} />
            ) : null}

            {/* Summary strip */}
            <XStack marginHorizontal={16} marginTop={8} gap={10}>
              <SummaryTile label="Present" count={presentCount} bg={C.success100} color={C.success700} />
              <SummaryTile label="Late" count={lateCount} bg={C.warning100} color={C.warning700} />
              <SummaryTile label="Absent" count={absentCount} bg={C.danger100} color={C.danger700} />
            </XStack>

            {/* Calendar card */}
            <YStack marginHorizontal={16} marginTop={16}>
              <Card
                bordered
                borderRadius={16}
                borderColor={C.neutral200}
                backgroundColor={C.card}
                padding={16}
              >
                {/* Month navigator */}
                <XStack alignItems="center" justifyContent="space-between" marginBottom={14}>
                  <Button
                    width={36}
                    height={36}
                    padding={0}
                    borderRadius={10}
                    backgroundColor={C.page}
                    borderWidth={1}
                    borderColor={C.neutral200}
                    pressStyle={{ scale: 0.96 }}
                    onPress={() => moveMonth(-1)}
                    aria-label="Previous month"
                  >
                    <ChevronLeft size={16} color={C.neutral700} />
                  </Button>
                  <Text fontSize={15} fontWeight="600" color={C.neutral900}>
                    {monthLabel}
                  </Text>
                  <Button
                    width={36}
                    height={36}
                    padding={0}
                    borderRadius={10}
                    backgroundColor={C.page}
                    borderWidth={1}
                    borderColor={C.neutral200}
                    pressStyle={{ scale: 0.96 }}
                    onPress={() => moveMonth(1)}
                    aria-label="Next month"
                  >
                    <ChevronRight size={16} color={C.neutral700} />
                  </Button>
                </XStack>

                {/* Day labels */}
                <XStack marginBottom={8}>
                  {DAY_LABELS.map((d) => (
                    <View key={d} flex={1} alignItems="center">
                      <Text fontSize={11} fontWeight="500" color={C.neutral500}>
                        {d}
                      </Text>
                    </View>
                  ))}
                </XStack>

                {/* Calendar grid */}
                <YStack gap={4}>
                  {calDays.map((week: (CalCellData | null)[], wi: number) => (
                    <XStack key={wi} gap={4}>
                      {week.map((cell: CalCellData | null, di: number) => (
                        <View key={di} flex={1} alignItems="center" justifyContent="center">
                          {cell ? (
                            <CalCell cell={cell} />
                          ) : (
                            <View width={36} height={36} />
                          )}
                        </View>
                      ))}
                    </XStack>
                  ))}
                </YStack>

                {/* Legend */}
                <XStack marginTop={14} gap={12} flexWrap="wrap">
                  <LegendItem color={C.success700} bg={C.success100} label="Present" />
                  <LegendItem color={C.warning700} bg={C.warning100} label="Late" />
                  <LegendItem color={C.danger700} bg={C.danger100} label="Absent" />
                  <LegendItem color={C.neutral500} bg={C.neutral200} label="No shift" />
                </XStack>
              </Card>
            </YStack>

            {/* Monthly records list */}
            <YStack marginHorizontal={16} marginTop={20} gap={12}>
              <Text fontSize={12} fontWeight="500" color={C.neutral500} letterSpacing={0.5}>
                {monthLabel.toUpperCase()} RECORDS
              </Text>

              {monthRecords.length === 0 ? (
                <Card
                  bordered
                  borderRadius={14}
                  borderColor={C.neutral200}
                  backgroundColor={C.card}
                  padding={20}
                >
                  <YStack alignItems="center" gap={8}>
                    <CalendarDays size={28} color={C.neutral300} />
                    <Text fontSize={14} fontWeight="500" color={C.neutral900}>
                      No records this month
                    </Text>
                    <Text fontSize={13} color={C.neutral500} textAlign="center">
                      Your attendance records for {monthLabel} will appear here.
                    </Text>
                  </YStack>
                </Card>
              ) : (
                monthRecords.map((record) => (
                  <AttendanceRow key={record.id} record={record} />
                ))
              )}
            </YStack>

          </YStack>
        </ScrollView>
      )}
    </View>
  );
}

/* ── Calendar cell ─────────────────────────────────────── */

type CalCellData = {
  day: number;
  isToday: boolean;
  status: WorkerAttendanceStatus | null;
};

function CalCell({ cell }: { cell: CalCellData }) {
  const { day, isToday, status } = cell;
  let bg = 'transparent';
  let color = C.neutral500;
  let borderColor = 'transparent';

  if (isToday && !status) {
    bg = C.brand100;
    color = C.brand700;
    borderColor = C.brand600;
  } else if (status) {
    const meta = statusMeta[status];
    bg = meta.bg;
    color = meta.color;
  }

  return (
    <View
      width={36}
      height={36}
      borderRadius={10}
      alignItems="center"
      justifyContent="center"
      backgroundColor={bg}
      borderWidth={isToday ? 1.5 : 0}
      borderColor={borderColor}
    >
      <Text fontSize={13} fontWeight={isToday ? '600' : '400'} color={color} fontFamily="$mono">
        {String(day).padStart(2, '0')}
      </Text>
    </View>
  );
}

/* ── Attendance row ─────────────────────────────────────── */

function AttendanceRow({ record }: { record: WorkerAttendanceRecord }) {
  const meta = statusMeta[record.status] ?? { label: record.status, bg: C.neutral200, color: C.neutral500 };
  const date = parseApiDate(record.attendance_date);
  const dateLabel = isNaN(date.getTime())
    ? record.attendance_date ?? '—'
    : date.toLocaleDateString('en-IN', {
        weekday: 'short',
        day: '2-digit',
        month: 'short',
      });

  return (
    <Card
      bordered
      borderRadius={14}
      borderColor={C.neutral200}
      backgroundColor={C.card}
      padding={14}
    >
      <XStack alignItems="center" gap={12}>
        {/* Status icon */}
        <View
          width={40}
          height={40}
          borderRadius={20}
          backgroundColor={meta.bg}
          alignItems="center"
          justifyContent="center"
        >
          {record.status === 'absent' ? (
            <XCircle size={18} color={meta.color} />
          ) : record.status === 'late' ? (
            <Clock size={18} color={meta.color} />
          ) : (
            <CheckCircle size={18} color={meta.color} />
          )}
        </View>

        <YStack flex={1}>
          <Text fontSize={14} fontWeight="500" color={C.neutral900}>
            {dateLabel}
          </Text>
          {record.check_in_time || record.check_out_time ? (
            <Text fontSize={12} color={C.neutral500} fontFamily="$mono" marginTop={2}>
              {record.check_in_time ? formatTime(record.check_in_time) : '--:--'}
              {' → '}
              {record.check_out_time ? formatTime(record.check_out_time) : '--:--'}
            </Text>
          ) : null}
          {record.notes ? (
            <Text fontSize={12} color={C.neutral500} marginTop={2} numberOfLines={1}>
              {record.notes}
            </Text>
          ) : null}
        </YStack>

        <XStack
          height={24}
          borderRadius={999}
          paddingHorizontal={10}
          alignItems="center"
          backgroundColor={meta.bg}
        >
          <Text fontSize={12} fontWeight="500" color={meta.color}>
            {meta.label}
          </Text>
        </XStack>
      </XStack>
    </Card>
  );
}

/* ── Summary tile ──────────────────────────────────────── */

function SummaryTile({
  label,
  count,
  bg,
  color,
}: {
  label: string;
  count: number;
  bg: string;
  color: string;
}) {
  return (
    <YStack
      flex={1}
      borderRadius={14}
      padding={14}
      backgroundColor={bg}
      alignItems="center"
      gap={4}
    >
      <Text fontSize={22} fontWeight="600" color={color} fontFamily="$mono">
        {count}
      </Text>
      <Text fontSize={12} fontWeight="500" color={color}>
        {label}
      </Text>
    </YStack>
  );
}

/* ── Legend item ───────────────────────────────────────── */

function LegendItem({ color, bg, label }: { color: string; bg: string; label: string }) {
  return (
    <XStack alignItems="center" gap={5}>
      <View width={12} height={12} borderRadius={4} backgroundColor={bg} borderWidth={1} borderColor={color} />
      <Text fontSize={11} color={C.neutral500}>{label}</Text>
    </XStack>
  );
}

/* ── Streak card ───────────────────────────────────────── */

function StreakCard({ streak }: { streak: number }) {
  if (streak === 0) return null;
  const emoji = streak >= 14 ? '🔥' : streak >= 7 ? '⭐' : '✅';
  const message =
    streak >= 14 ? `${streak} day streak — incredible run!`
    : streak >= 7 ? `${streak} day streak — keep it going!`
    : `${streak} day streak — great start!`;
  return (
    <XStack
      marginHorizontal={16}
      marginBottom={12}
      borderRadius={14}
      padding={16}
      backgroundColor={C.brand100}
      borderWidth={1}
      borderColor={C.brand400}
      alignItems="center"
      gap={12}
    >
      <Text fontSize={28}>{emoji}</Text>
      <YStack flex={1}>
        <Text fontSize={14} fontWeight="600" color={C.brand700}>
          {message}
        </Text>
        <Text fontSize={12} color={C.brand600} marginTop={2}>
          Consecutive days present
        </Text>
      </YStack>
    </XStack>
  );
}

/* ── Helpers ────────────────────────────────────────────── */

function calcStreak(records: WorkerAttendanceRecord[]): number {
  const presentDates = new Set(
    records
      .filter((r) => r.status === 'present' || r.status === 'approved')
      .map((r) => r.attendance_date),
  );
  let streak = 0;
  const cursor = new Date();
  // Walk backwards from yesterday (today may not have attendance yet)
  cursor.setDate(cursor.getDate() - 1);
  while (true) {
    const key = toDateKey(cursor);
    if (!presentDates.has(key)) break;
    streak++;
    cursor.setDate(cursor.getDate() - 1);
  }
  return streak;
}

function parseApiDate(value: string | null | undefined): Date {
  if (!value) return new Date(NaN);
  const parts = value.split('-').map(Number);
  if (parts.length !== 3 || parts.some(isNaN)) return new Date(NaN);
  return new Date(parts[0], parts[1] - 1, parts[2]);
}

function toDateKey(date: Date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function formatTime(value: string | null | undefined) {
  if (!value) return '—';
  const d = new Date(`1970-01-01T${value}`);
  if (isNaN(d.getTime())) return value;
  return new Intl.DateTimeFormat('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }).format(d);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-IN', { weekday: 'short', day: '2-digit', month: 'short' }).format(
    new Date(value),
  );
}

function buildCalendar(
  year: number,
  month: number,
  records: import('../../../shared/services/worker-attendance.service').WorkerAttendanceRecord[],
): (CalCellData | null)[][] {
  const firstDay = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const today = new Date();

  // Build a status map keyed by "YYYY-MM-DD"
  const statusMap: Record<string, WorkerAttendanceStatus> = {};
  records.forEach((r) => {
    const d = parseApiDate(r.attendance_date);
    if (d.getFullYear() === year && d.getMonth() === month) {
      statusMap[r.attendance_date] = r.status;
    }
  });

  // Start from Monday (0 = Mon ... 6 = Sun)
  const startDow = firstDay.getDay(); // 0=Sun,1=Mon,...
  const offset = startDow === 0 ? 6 : startDow - 1;

  const cells: (CalCellData | null)[] = Array(offset).fill(null);
  for (let d = 1; d <= daysInMonth; d++) {
    const date = new Date(year, month, d);
    const key = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    const isToday =
      date.getFullYear() === today.getFullYear() &&
      date.getMonth() === today.getMonth() &&
      date.getDate() === today.getDate();
    cells.push({ day: d, isToday, status: statusMap[key] ?? null });
  }

  // Pad to full weeks
  while (cells.length % 7 !== 0) cells.push(null);

  // Split into rows of 7
  const weeks: (CalCellData | null)[][] = [];
  for (let i = 0; i < cells.length; i += 7) {
    weeks.push(cells.slice(i, i + 7));
  }
  return weeks;
}
