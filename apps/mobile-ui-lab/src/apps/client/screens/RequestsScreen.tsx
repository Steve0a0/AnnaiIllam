import { useCallback, useMemo, useState } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { ArrowLeft, BriefcaseBusiness, ChevronRight, Plus, Users } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  clientRequirementsService,
  type ClientRequirementListItem,
  type RequirementStatus,
} from '../../../shared/services/client-requirements.service';
import type { HomeStackParamList } from '../navigation/types';
import { LoadingBlock, StatusBadge } from './components';
import { C, clientStyles } from './clientStyles';

type Navigation = NativeStackNavigationProp<HomeStackParamList>;

// filter definitions
type FilterKey = 'all' | 'active' | 'pending' | 'done';

const FILTERS: { key: FilterKey; label: string }[] = [
  { key: 'all',     label: 'All' },
  { key: 'active',  label: 'Active' },
  { key: 'pending', label: 'Pending' },
  { key: 'done',    label: 'Done' },
];

const FILTER_STATUSES: Record<FilterKey, RequirementStatus[] | null> = {
  all:     null,
  active:  ['assigned', 'in_progress'],
  pending: ['submitted', 'under_review', 'quoted', 'approved'],
  done:    ['completed', 'cancelled', 'rejected'],
};

function statusAccent(status: RequirementStatus): string {
  switch (status) {
    case 'in_progress': return C.tealText;
    case 'assigned':    return C.tealText;
    case 'quoted':      return C.warningText;
    case 'approved':    return C.infoText;
    case 'completed':   return C.successText;
    case 'rejected':    return C.dangerText;
    case 'cancelled':   return C.muted;
    default:            return C.purpleText;
  }
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(
    new Date(value),
  );
}

function FilterChip({
  label,
  count,
  active,
  onPress,
}: {
  label: string;
  count: number;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      style={[styles.chip, active && styles.chipActive]}
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
    >
      <Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text>
      {count > 0 && (
        <View style={[styles.chipBadge, active && styles.chipBadgeActive]}>
          <Text style={[styles.chipBadgeText, active && styles.chipBadgeTextActive]}>{count}</Text>
        </View>
      )}
    </Pressable>
  );
}

function RequestCard({
  item,
  onPress,
  onWorkersPress,
}: {
  item: ClientRequirementListItem;
  onPress: () => void;
  onWorkersPress?: () => void;
}) {
  const accent = statusAccent(item.status as RequirementStatus);
  const isActive = ['assigned', 'in_progress'].includes(item.status);

  return (
    <Pressable
      style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
      onPress={onPress}
    >
      <View style={[styles.cardAccent, { backgroundColor: accent }]} />
      <View style={styles.cardBody}>
        <View style={styles.cardTop}>
          <View style={{ flex: 1, gap: 2 }}>
            <Text style={styles.cardTitle} numberOfLines={1}>{item.category}</Text>
            <Text style={styles.cardMeta}>
              {item.city} · {item.number_of_workers} {item.number_of_workers === 1 ? 'worker' : 'workers'}
            </Text>
          </View>
          <StatusBadge value={item.status} />
        </View>
        <View style={styles.cardBottom}>
          <Text style={styles.cardDate}>Starts {formatDate(item.start_date)}</Text>
          {isActive && onWorkersPress ? (
            <Pressable
              style={[styles.workersChip, { backgroundColor: C.tealBg }]}
              onPress={(e) => { e.stopPropagation(); onWorkersPress(); }}
              hitSlop={8}
            >
              <Users size={11} color={C.tealText} />
              <Text style={[styles.workersChipText, { color: C.tealText }]}>
                {item.number_of_workers} workers
              </Text>
              <ChevronRight size={11} color={C.tealText} />
            </Pressable>
          ) : (
            <ChevronRight size={14} color={C.border} />
          )}
        </View>
      </View>
    </Pressable>
  );
}

export default function RequestsScreen() {
  const navigation = useNavigation<Navigation>();
  const insets = useSafeAreaInsets();
  const [items, setItems] = useState<ClientRequirementListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [filter, setFilter] = useState<FilterKey>('all');

  const load = useCallback(async () => {
    setItems(await clientRequirementsService.list());
  }, []);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);
      load().finally(() => active && setIsLoading(false));
      return () => { active = false; };
    }, [load]),
  );

  const refresh = async () => {
    setIsRefreshing(true);
    try { await load(); } finally { setIsRefreshing(false); }
  };

  const counts = useMemo<Record<FilterKey, number>>(() => ({
    all:     items.length,
    active:  items.filter((i) => FILTER_STATUSES.active!.includes(i.status as RequirementStatus)).length,
    pending: items.filter((i) => FILTER_STATUSES.pending!.includes(i.status as RequirementStatus)).length,
    done:    items.filter((i) => FILTER_STATUSES.done!.includes(i.status as RequirementStatus)).length,
  }), [items]);

  const filtered = useMemo(() => {
    const statuses = FILTER_STATUSES[filter];
    if (!statuses) return items;
    return items.filter((i) => statuses.includes(i.status as RequirementStatus));
  }, [items, filter]);

  return (
    <View style={[clientStyles.root, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Pressable
          style={styles.backBtn}
          onPress={() => navigation.goBack()}
          hitSlop={12}
          accessibilityLabel="Go back"
        >
          <ArrowLeft size={20} color={C.ink} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={styles.headerTitle}>All requests</Text>
          {items.length > 0 && (
            <Text style={styles.headerSub}>{items.length} {items.length === 1 ? 'request' : 'requests'} total</Text>
          )}
        </View>
        <Pressable
          style={styles.newBtn}
          onPress={() => navigation.navigate('CreateRequest')}
          accessibilityLabel="New request"
        >
          <Plus size={16} color="#FFFFFF" />
          <Text style={styles.newBtnText}>New</Text>
        </Pressable>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filterRow}
        style={styles.filterScroll}
      >
        {FILTERS.map((f) => (
          <FilterChip
            key={f.key}
            label={f.label}
            count={counts[f.key]}
            active={filter === f.key}
            onPress={() => setFilter(f.key)}
          />
        ))}
      </ScrollView>

      <ScrollView
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={refresh} tintColor={C.brand} />}
        showsVerticalScrollIndicator={false}
      >
        {isLoading ? (
          <LoadingBlock label="Loading requests..." />
        ) : filtered.length === 0 ? (
          <View style={styles.empty}>
            <View style={styles.emptyIcon}>
              <BriefcaseBusiness size={28} color={C.muted} />
            </View>
            <Text style={styles.emptyTitle}>
              {filter === 'all' ? 'No requests yet' : `No ${filter} requests`}
            </Text>
            <Text style={styles.emptyDetail}>
              {filter === 'all'
                ? 'Post your first worker request from the home screen.'
                : 'Nothing in this category right now.'}
            </Text>
          </View>
        ) : (
          filtered.map((item) => (
            <RequestCard
              key={item.id}
              item={item}
              onPress={() => navigation.navigate('RequestDetail', { requirementId: item.id })}
              onWorkersPress={
                ['assigned', 'in_progress'].includes(item.status)
                  ? () => navigation.navigate('AssignedWorkers', { requirementId: item.id })
                  : undefined
              }
            />
          ))
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
    backgroundColor: C.page,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: C.ink,
    lineHeight: 24,
  },
  headerSub: {
    fontSize: 12,
    color: C.muted,
    marginTop: 1,
  },
  newBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: C.brand,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 9,
  },
  newBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  filterScroll: {
    borderBottomWidth: 1,
    borderBottomColor: C.border,
    backgroundColor: C.page,
    flexGrow: 0,
  },
  filterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 999,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
  },
  chipActive: {
    backgroundColor: C.brandDark,
    borderColor: C.brandDark,
  },
  chipText: {
    fontSize: 13,
    fontWeight: '600',
    color: C.body,
  },
  chipTextActive: {
    color: '#FFFFFF',
  },
  chipBadge: {
    minWidth: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: C.surfaceAlt,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
  },
  chipBadgeActive: {
    backgroundColor: 'rgba(255,255,255,0.22)',
  },
  chipBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: C.muted,
  },
  chipBadgeTextActive: {
    color: '#FFFFFF',
  },
  list: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 32,
    gap: 10,
  },
  card: {
    flexDirection: 'row',
    backgroundColor: C.surface,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: C.border,
    overflow: 'hidden',
  },
  cardPressed: {
    borderColor: C.brand + '60',
    backgroundColor: C.brandSoft,
  },
  cardAccent: {
    width: 4,
  },
  cardBody: {
    flex: 1,
    padding: 14,
    gap: 10,
  },
  cardTop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: C.ink,
    lineHeight: 20,
  },
  cardMeta: {
    fontSize: 12,
    color: C.body,
    lineHeight: 17,
  },
  cardBottom: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  cardDate: {
    fontSize: 12,
    color: C.muted,
  },
  workersChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  workersChipText: {
    fontSize: 11,
    fontWeight: '600',
  },
  empty: {
    marginTop: 48,
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 32,
  },
  emptyIcon: {
    width: 64,
    height: 64,
    borderRadius: 18,
    backgroundColor: C.surfaceAlt,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: C.ink,
    textAlign: 'center',
  },
  emptyDetail: {
    fontSize: 13,
    color: C.muted,
    textAlign: 'center',
    lineHeight: 20,
  },
});
