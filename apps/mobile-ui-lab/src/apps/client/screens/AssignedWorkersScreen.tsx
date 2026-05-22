import { useCallback, useState } from 'react';
import {
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useFocusEffect, useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';
import { AlertCircle, CalendarDays, ChevronLeft, CheckCircle2, MapPin, Users, XCircle } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { clientRequirementsService, type ClientRequirementDetail } from '../../../shared/services/client-requirements.service';
import type { HomeStackParamList } from '../navigation/types';
import { EmptyBlock, LoadingBlock, StatusBadge } from './components';
import { C, getStatusColors } from './clientStyles';

type Navigation = NativeStackNavigationProp<HomeStackParamList>;
type Route = NativeStackScreenProps<HomeStackParamList, 'AssignedWorkers'>['route'];
type Assignment = ClientRequirementDetail['assignments'][number];
type AttRecord = Assignment['attendance'][number];

type FilterKey = 'all' | 'in' | 'out' | 'absent' | 'pending';

export default function AssignedWorkersScreen() {
  const navigation = useNavigation<Navigation>();
  const route = useRoute<Route>();
  const insets = useSafeAreaInsets();
  const { requirementId } = route.params;

  const [detail, setDetail] = useState<ClientRequirementDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterKey>('all');

  const load = useCallback(async () => {
    setError(null);
    setDetail(await clientRequirementsService.getDetail(requirementId));
  }, [requirementId]);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);
      load()
        .catch(() => active && setError('Could not load workers. Pull down to retry.'))
        .finally(() => active && setIsLoading(false));
      return () => { active = false; };
    }, [load]),
  );

  const refresh = async () => {
    setIsRefreshing(true);
    try {
      await load();
    } catch {
      setError('Could not load workers. Pull down to retry.');
    } finally {
      setIsRefreshing(false);
    }
  };

  const todayStr = new Date().toISOString().split('T')[0];
  const getTodayRec = (att: AttRecord[]) => att.find((a) => a.attendance_date.startsWith(todayStr)) ?? null;

  const checkedIn  = detail?.assignments.filter((a) => { const r = getTodayRec(a.attendance); return !!(r?.check_in_time && !r?.check_out_time); }).length ?? 0;
  const checkedOut = detail?.assignments.filter((a) => { const r = getTodayRec(a.attendance); return !!r?.check_out_time; }).length ?? 0;
  const absent     = detail?.assignments.filter((a) => getTodayRec(a.attendance)?.status === 'absent').length ?? 0;

  const filtered = (detail?.assignments ?? []).filter((a) => {
    if (filter === 'all') return true;
    const r = getTodayRec(a.attendance);
    if (filter === 'in')     return !!(r?.check_in_time && !r?.check_out_time);
    if (filter === 'out')    return !!r?.check_out_time;
    if (filter === 'absent') return r?.status === 'absent';
    if (filter === 'pending') return !r;
    return true;
  });

  const isMultiDay = (detail?.duration_days ?? 1) > 1;

  return (
    <View style={{ flex: 1, backgroundColor: '#F5F5F4' }}>
      {/* Dark hero header */}
      <View style={[s.hero, { paddingTop: insets.top + 4 }]}>
        <Pressable style={s.backBtn} onPress={() => navigation.goBack()}>
          <ChevronLeft size={20} color="rgba(255,255,255,0.9)" />
        </Pressable>

        <View style={s.heroBody}>
          <View style={{ flex: 1 }}>
            <Text style={s.heroEyebrow}>ASSIGNED WORKERS</Text>
            <Text style={s.heroTitle} numberOfLines={2}>
              {detail ? detail.category : 'Loading...'}
            </Text>
            {detail ? (
              <View style={s.heroMeta}>
                <MapPin size={11} color="rgba(255,255,255,0.45)" />
                <Text style={s.heroMetaText}>{detail.city}, {detail.state}</Text>
                <View style={s.heroDot} />
                <CalendarDays size={11} color="rgba(255,255,255,0.45)" />
                <Text style={s.heroMetaText}>{formatDate(detail.start_date)}</Text>
                {detail.duration_days > 1 ? <Text style={s.heroMetaText}>· {detail.duration_days}d</Text> : null}
              </View>
            ) : null}
          </View>
          {detail ? <StatusBadge value={detail.status} /> : null}
        </View>

        {/* Stat chips */}
        {detail && detail.assignments.length > 0 ? (
          <View style={s.statRow}>
            <StatChip label="Assigned" value={detail.assignments.length} color="rgba(255,255,255,0.9)" />
            <StatChip label="Checked in" value={checkedIn} color="#6ee7b7" />
            <StatChip label="Checked out" value={checkedOut} color="#93c5fd" />
            <StatChip label="Absent" value={absent} color="#fca5a5" />
          </View>
        ) : null}
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={refresh} tintColor={C.brand} />}
      >
        {isLoading ? (
          <View style={{ margin: 16 }}><LoadingBlock label="Loading workers..." /></View>
        ) : error || !detail ? (
          <View style={{ margin: 16 }}>
            <EmptyBlock
              title="Could not load workers"
              detail={error ?? 'No data found.'}
              action={{ label: 'Retry', onPress: () => { setIsLoading(true); load().catch(() => setError('Could not load workers. Pull down to retry.')).finally(() => setIsLoading(false)); } }}
            />
          </View>
        ) : detail.assignments.length === 0 ? (
          <View style={{ margin: 16 }}>
            <EmptyBlock
              title="No workers assigned yet"
              detail={`Workers will be assigned by admin. Expected start: ${formatDate(detail.start_date)}.`}
            />
          </View>
        ) : (
          <>
            {/* Filter chips */}
            <ScrollView horizontal showsHorizontalScrollIndicator={false}
              contentContainerStyle={s.filterRow}>
              {([
                { key: 'all' as FilterKey, label: `All (${detail.assignments.length})` },
                { key: 'in' as FilterKey, label: `Checked in (${checkedIn})` },
                { key: 'out' as FilterKey, label: `Checked out (${checkedOut})` },
                { key: 'absent' as FilterKey, label: `Absent (${absent})` },
                { key: 'pending' as FilterKey, label: 'No record' },
              ]).map(({ key, label }) => (
                <Pressable key={key} style={[s.filterChip, filter === key && s.filterChipActive]}
                  onPress={() => setFilter(key)}>
                  <Text style={[s.filterChipText, filter === key && s.filterChipTextActive]}>{label}</Text>
                </Pressable>
              ))}
            </ScrollView>

            <View style={{ paddingHorizontal: 16, paddingBottom: 32, gap: 10 }}>
              {filtered.length === 0 ? (
                <EmptyBlock title="No workers match this filter" detail="Try a different filter above." />
              ) : (
                filtered.map((assignment) => (
                  <WorkerCard
                    key={assignment.id}
                    assignment={assignment}
                    todayRecord={getTodayRec(assignment.attendance)}
                    isMultiDay={isMultiDay}
                    durationDays={detail.duration_days}
                    startDate={detail.start_date}
                    onRaiseComplaint={() => navigation.navigate('RaiseComplaint', { requirementId })}
                  />
                ))
              )}
            </View>
          </>
        )}
      </ScrollView>
    </View>
  );
}

/* Worker Card */
function WorkerCard({
  assignment, todayRecord, isMultiDay, durationDays, startDate, onRaiseComplaint,
}: {
  assignment: Assignment; todayRecord: AttRecord | null;
  isMultiDay: boolean; durationDays: number; startDate: string;
  onRaiseComplaint: () => void;
}) {
  const status = resolveStatus(todayRecord, assignment.status);
  const colors = getStatusColors(status === 'checked_in' ? 'active' : status === 'checked_out' ? 'approved' : status);
  const initials = assignment.worker_name.slice(0, 2).toUpperCase();

  return (
    <View style={s.workerCard}>
      {/* Top row — avatar + name + badge */}
      <View style={s.cardTop}>
        <View style={s.workerAvatar}>
          <Text style={s.workerAvatarText}>{initials}</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={s.workerName}>{assignment.worker_name}</Text>
          <Text style={s.workerMeta}>
            {[assignment.worker_city, assignment.worker_category].filter(Boolean).join(' · ') || '—'}
          </Text>
        </View>
        <View style={[s.statusBadge, { backgroundColor: colors.bg }]}>
          <Text style={[s.statusBadgeText, { color: colors.text }]}>{status.replace(/_/g, ' ')}</Text>
        </View>
      </View>

      {/* Role + shift chips */}
      <View style={s.chipRow}>
        <InfoChip label="Role" value={assignment.assigned_role ?? '—'} />
        <InfoChip label="Shift" value={assignment.assigned_shift ?? '—'} />
      </View>

      {/* Check-in / out times split row */}
      <View style={s.timeSplit}>
        <View style={s.timeCol}>
          <Text style={s.timeKey}>CHECK-IN</Text>
          <Text style={[s.timeVal, !todayRecord?.check_in_time && s.timeValMuted]}>
            {todayRecord?.check_in_time ? formatTime(todayRecord.check_in_time) : '—'}
          </Text>
        </View>
        <View style={s.timeDivider} />
        <View style={s.timeCol}>
          <Text style={s.timeKey}>CHECK-OUT</Text>
          <Text style={[s.timeVal, !todayRecord?.check_out_time && s.timeValMuted]}>
            {todayRecord?.check_out_time ? formatTime(todayRecord.check_out_time) : '—'}
          </Text>
        </View>
      </View>

      {/* Multi-day streak */}
      {isMultiDay ? (
        <AttendanceStreak attendance={assignment.attendance} startDate={startDate} durationDays={durationDays} />
      ) : null}

      {/* Complaint shortcut */}
      <Pressable style={s.complaintRow} onPress={onRaiseComplaint}>
        <AlertCircle size={13} color={C.warningText} />
        <Text style={s.complaintText}>Raise complaint about this worker</Text>
      </Pressable>
    </View>
  );
}

function InfoChip({ label, value }: { label: string; value: string }) {
  return (
    <View style={s.infoChip}>
      <Text style={s.infoChipLabel}>{label}</Text>
      <Text style={s.infoChipValue} numberOfLines={1}>{value}</Text>
    </View>
  );
}

function StatChip({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View style={s.statChip}>
      <Text style={[s.statValue, { color }]}>{value}</Text>
      <Text style={s.statLabel}>{label}</Text>
    </View>
  );
}

/* Attendance streak with numbered dots */
function AttendanceStreak({ attendance, startDate, durationDays }: {
  attendance: AttRecord[]; startDate: string; durationDays: number;
}) {
  const start = new Date(startDate);
  const today = new Date().toISOString().split('T')[0];
  const days = Array.from({ length: Math.min(durationDays, 14) }, (_, i) => {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    const dateStr = d.toISOString().split('T')[0];
    const rec = attendance.find((a) => a.attendance_date.startsWith(dateStr));
    const isPast = dateStr <= today;
    let state: 'present' | 'absent' | 'future' | 'none' = 'future';
    if (isPast) {
      if (rec?.check_in_time || rec?.status === 'present') state = 'present';
      else if (rec?.status === 'absent') state = 'absent';
      else state = 'none';
    }
    return { day: d.getDate(), state };
  });

  return (
    <View style={s.streak}>
      <Text style={s.streakLabel}>Attendance · {durationDays} day{durationDays > 1 ? 's' : ''}</Text>
      <View style={s.streakDots}>
        {days.map(({ day, state }, idx) => (
          <View key={idx} style={[
            s.streakDot,
            state === 'present' ? s.dotPresent :
            state === 'absent'  ? s.dotAbsent  :
            state === 'none'    ? s.dotNone    : s.dotFuture,
          ]}>
            <Text style={[
              s.streakDotText,
              state === 'present' ? { color: '#065F46' } :
              state === 'absent'  ? { color: '#B91C1C' } :
              { color: '#A8A29E' },
            ]}>{day}</Text>
          </View>
        ))}
        {durationDays > 14 ? <Text style={{ fontSize: 11, color: C.muted, alignSelf: 'center' }}>+{durationDays - 14}</Text> : null}
      </View>
    </View>
  );
}

/* Helpers */
function resolveStatus(record: AttRecord | null, assignmentStatus: string): string {
  if (!record) return assignmentStatus;
  if (record.status === 'absent') return 'absent';
  if (record.check_out_time) return 'checked_out';
  if (record.check_in_time) return 'checked_in';
  return record.status;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short' }).format(new Date(value));
}

function formatTime(value: string | null): string {
  if (!value) return '—';
  try {
    return new Intl.DateTimeFormat('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }).format(new Date(value));
  } catch { return value; }
}

/* Styles */
const s = StyleSheet.create({
  hero: { backgroundColor: '#0D2E1E', paddingHorizontal: 16, paddingBottom: 16 },
  backBtn: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center', justifyContent: 'center',
    marginBottom: 12, alignSelf: 'flex-start',
  },
  heroBody: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 16 },
  heroEyebrow: { fontSize: 10, fontWeight: '600', color: 'rgba(255,255,255,0.4)', letterSpacing: 1, marginBottom: 4 },
  heroTitle: { fontSize: 20, fontWeight: '600', color: '#FFF', lineHeight: 26 },
  heroMeta: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 6, flexWrap: 'wrap' },
  heroMetaText: { fontSize: 12, color: 'rgba(255,255,255,0.5)' },
  heroDot: { width: 3, height: 3, borderRadius: 999, backgroundColor: 'rgba(255,255,255,0.3)' },
  statRow: { flexDirection: 'row', gap: 6 },
  statChip: {
    flex: 1, backgroundColor: 'rgba(255,255,255,0.08)',
    borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.1)',
    borderRadius: 10, paddingVertical: 10, alignItems: 'center', gap: 2,
  },
  statValue: { fontSize: 18, fontWeight: '600' },
  statLabel: { fontSize: 9, fontWeight: '600', color: 'rgba(255,255,255,0.4)', letterSpacing: 0.5 },
  filterRow: { paddingHorizontal: 16, paddingVertical: 12, gap: 6 },
  filterChip: {
    paddingHorizontal: 14, paddingVertical: 6, borderRadius: 999,
    borderWidth: 0.5, borderColor: C.border, backgroundColor: C.surface,
  },
  filterChipActive: { backgroundColor: '#0D2E1E', borderColor: '#0D2E1E' },
  filterChipText: { fontSize: 12, fontWeight: '500', color: C.muted },
  filterChipTextActive: { color: '#FFF' },
  workerCard: {
    backgroundColor: C.surface, borderRadius: 16,
    borderWidth: 0.5, borderColor: C.border, overflow: 'hidden',
  },
  cardTop: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 14 },
  workerAvatar: {
    width: 42, height: 42, borderRadius: 12,
    backgroundColor: '#EDFAF3', alignItems: 'center', justifyContent: 'center',
  },
  workerAvatarText: { fontSize: 14, fontWeight: '600', color: C.brand },
  workerName: { fontSize: 14, fontWeight: '600', color: C.ink, lineHeight: 20 },
  workerMeta: { fontSize: 12, color: C.muted, marginTop: 1 },
  statusBadge: { paddingHorizontal: 9, paddingVertical: 4, borderRadius: 999 },
  statusBadgeText: { fontSize: 11, fontWeight: '600', textTransform: 'capitalize' },
  chipRow: {
    flexDirection: 'row', gap: 8,
    paddingHorizontal: 14, paddingBottom: 12,
  },
  infoChip: {
    flex: 1, backgroundColor: '#F5F5F4', borderRadius: 8,
    paddingHorizontal: 10, paddingVertical: 8,
    borderWidth: 0.5, borderColor: C.border,
  },
  infoChipLabel: { fontSize: 9, fontWeight: '600', color: C.muted, letterSpacing: 0.5, textTransform: 'uppercase', marginBottom: 2 },
  infoChipValue: { fontSize: 13, fontWeight: '500', color: C.ink },
  timeSplit: { flexDirection: 'row', borderTopWidth: 0.5, borderTopColor: C.border },
  timeDivider: { width: 0.5, backgroundColor: C.border },
  timeCol: { flex: 1, padding: 12 },
  timeKey: { fontSize: 9, fontWeight: '600', color: '#A8A29E', letterSpacing: 0.5, marginBottom: 4 },
  timeVal: { fontSize: 14, fontWeight: '600', color: C.ink, fontVariant: ['tabular-nums'] },
  timeValMuted: { color: '#C4B5A5', fontWeight: '400' },
  streak: { borderTopWidth: 0.5, borderTopColor: C.border, padding: 12 },
  streakLabel: { fontSize: 9, fontWeight: '600', color: C.muted, letterSpacing: 0.5, textTransform: 'uppercase', marginBottom: 8 },
  streakDots: { flexDirection: 'row', flexWrap: 'wrap', gap: 5 },
  streakDot: { width: 26, height: 26, borderRadius: 7, alignItems: 'center', justifyContent: 'center' },
  streakDotText: { fontSize: 10, fontWeight: '600' },
  dotPresent: { backgroundColor: '#D1FAE5' },
  dotAbsent: { backgroundColor: '#FEE2E2' },
  dotNone: { backgroundColor: '#F5F5F4', borderWidth: 0.5, borderColor: C.border },
  dotFuture: { backgroundColor: '#F5F5F4' },
  complaintRow: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    borderTopWidth: 0.5, borderTopColor: C.border,
    paddingHorizontal: 14, paddingVertical: 11,
  },
  complaintText: { fontSize: 12, fontWeight: '500', color: C.warningText },
});
