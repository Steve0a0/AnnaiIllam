import { useCallback, useMemo, useState } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { ArrowRight, ChevronRight, Plus, Users } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { clientRequirementsService, type ClientRequirementListItem, type RequirementStatus } from '../../../shared/services/client-requirements.service';
import type { JobsStackParamList } from '../navigation/types';
import { EmptyBlock, LoadingBlock, ScreenHeader, StatusBadge } from './components';
import { C, clientStyles } from './clientStyles';

type Navigation = NativeStackNavigationProp<JobsStackParamList>;

type FilterKey = 'all' | 'active' | 'pending' | 'completed';

const FILTERS: { key: FilterKey; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'active', label: 'Active' },
  { key: 'pending', label: 'Pending' },
  { key: 'completed', label: 'Completed' },
];

const FILTER_STATUSES: Record<FilterKey, RequirementStatus[] | null> = {
  all: null,
  active: ['assigned', 'in_progress'],
  pending: ['submitted', 'under_review', 'quoted', 'approved'],
  completed: ['completed', 'cancelled', 'rejected'],
};

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
      return () => {
        active = false;
      };
    }, [load]),
  );

  const refresh = async () => {
    setIsRefreshing(true);
    try {
      await load();
    } finally {
      setIsRefreshing(false);
    }
  };

  const filtered = useMemo(() => {
    const statuses = FILTER_STATUSES[filter];
    if (!statuses) return items;
    return items.filter((i) => statuses.includes(i.status));
  }, [items, filter]);

  return (
    <View style={[clientStyles.root, { paddingTop: insets.top }]}>
      <ScrollView
        contentContainerStyle={clientStyles.content}
        refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={refresh} tintColor={C.brand} />}
      >
        <ScreenHeader title="Jobs" subtitle="All your worker requests in one place." />

        <Pressable style={clientStyles.primaryButton} onPress={() => navigation.navigate('CreateRequest')}>
          <Plus size={18} color="#FFFFFF" />
          <Text style={clientStyles.primaryButtonText}>New request</Text>
        </Pressable>

        <View style={styles.filterRow}>
          {FILTERS.map((f) => (
            <Pressable
              key={f.key}
              style={[styles.chip, filter === f.key && styles.chipActive]}
              onPress={() => setFilter(f.key)}
            >
              <Text style={[styles.chipText, filter === f.key && styles.chipTextActive]}>{f.label}</Text>
            </Pressable>
          ))}
        </View>

        {isLoading ? (
          <LoadingBlock label="Loading requests..." />
        ) : filtered.length === 0 ? (
          <EmptyBlock
            title={filter === 'all' ? 'No requests yet' : `No ${filter} requests`}
            detail={
              filter === 'all'
                ? 'Create a worker request and it will appear here.'
                : 'Nothing in this category right now.'
            }
          />
        ) : (
          filtered.map((item) => (
            <Pressable
              key={item.id}
              style={clientStyles.card}
              onPress={() => navigation.navigate('RequestDetail', { requirementId: item.id })}
            >
              <View style={styles.row}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.title}>{item.category}</Text>
                  <Text style={clientStyles.subtitle}>{item.city} · {item.number_of_workers} workers</Text>
                  <Text style={styles.date}>Starts {formatDate(item.start_date)}</Text>
                </View>
                <View style={styles.right}>
                  <StatusBadge value={item.status} />
                  {['assigned', 'in_progress'].includes(item.status) ? (
                    <Pressable
                      style={styles.workersLink}
                      onPress={(e) => {
                        e.stopPropagation();
                        navigation.navigate('AssignedWorkers', { requirementId: item.id });
                      }}
                    >
                      <Users size={12} color={C.brand} />
                      <Text style={styles.workersLinkText}>Workers</Text>
                      <ChevronRight size={12} color={C.brand} />
                    </Pressable>
                  ) : (
                    <ArrowRight size={18} color={C.muted} />
                  )}
                </View>
              </View>
            </Pressable>
          ))
        )}
      </ScrollView>
    </View>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value));
}

const styles = StyleSheet.create({
  filterRow: {
    flexDirection: 'row',
    gap: 8,
  },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
  },
  chipActive: {
    backgroundColor: C.brand,
    borderColor: C.brand,
  },
  chipText: {
    fontSize: 13,
    fontWeight: '600',
    color: C.muted,
  },
  chipTextActive: {
    color: '#FFFFFF',
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  title: {
    color: C.ink,
    fontSize: 16,
    fontWeight: '600',
  },
  date: {
    color: C.muted,
    fontSize: 12,
    marginTop: 8,
  },
  right: {
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    gap: 12,
  },
  workersLink: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  workersLinkText: {
    color: C.brand,
    fontSize: 12,
    fontWeight: '600',
  },
});
