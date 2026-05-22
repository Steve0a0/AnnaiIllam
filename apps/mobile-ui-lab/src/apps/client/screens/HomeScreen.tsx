import { useCallback, useState } from 'react';
import type { ReactNode } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { AlertCircle, ArrowRight, Bell, BriefcaseBusiness, CheckCircle, ChevronRight, Clock, Users } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { clientRequirementsService, type ClientRequirementListItem, type ClientDashboardSummary } from '../../../shared/services/client-requirements.service';
import { useAuthStore } from '../../../shared/store/auth.store';
import type { ClientAppStackParamList, ClientTabParamList } from '../navigation/types';
import { EmptyBlock, LoadingBlock, StatusBadge } from './components';
import { C, clientStyles } from './clientStyles';

type Navigation = NativeStackNavigationProp<ClientAppStackParamList>;
type TabNavigation = BottomTabNavigationProp<ClientTabParamList>;

export default function HomeScreen() {
  const navigation = useNavigation<Navigation>();
  const tabNavigation = useNavigation<TabNavigation>();
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const [summary, setSummary] = useState<ClientDashboardSummary | null>(null);
  const [requirements, setRequirements] = useState<ClientRequirementListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    const [summaryData, listData] = await Promise.all([
      clientRequirementsService.getSummary(),
      clientRequirementsService.list(),
    ]);
    setSummary(summaryData);
    setRequirements(listData);
  }, []);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);
      load()
        .catch(() => active && setError('Could not load dashboard. Pull down to retry.'))
        .finally(() => active && setIsLoading(false));
      return () => {
        active = false;
      };
    }, [load]),
  );

  const refresh = async () => {
    setIsRefreshing(true);
    try {
      await load();
    } catch {
      setError('Could not load dashboard. Pull down to retry.');
    } finally {
      setIsRefreshing(false);
    }
  };

  const needsAttention = requirements.filter((r) => r.status === 'quoted').slice(0, 3);
  const activeNow = requirements.filter((r) => ['assigned', 'in_progress'].includes(r.status)).slice(0, 3);

  return (
    <View style={[clientStyles.root, { paddingTop: insets.top }]}>
      <ScrollView
        contentContainerStyle={clientStyles.content}
        refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={refresh} tintColor={C.brand} />}
      >
        <View style={clientStyles.header}>
          <View>
            <Text style={clientStyles.eyebrow}>Client dashboard</Text>
            <Text style={styles.greeting}>Good morning</Text>
            <Text style={clientStyles.subtitle}>{user?.phone ?? 'Annai Illam client'}</Text>
          </View>
          <View style={styles.headerActions}>
            <Pressable style={styles.iconButton} accessibilityLabel="Notifications">
              <Bell size={18} color={C.body} />
            </Pressable>
            <Pressable
              style={styles.avatarButton}
              accessibilityLabel="Profile"
              onPress={() => tabNavigation.navigate('ProfileTab')}
            >
              <Text style={styles.avatarText}>{user?.phone?.slice(-2) ?? 'Me'}</Text>
            </Pressable>
          </View>
        </View>

        {isLoading ? (
          <LoadingBlock label="Loading dashboard..." />
        ) : error ? (
          <EmptyBlock
            title="Could not load dashboard"
            detail={error}
            action={{
              label: 'Retry',
              onPress: () => {
                setIsLoading(true);
                load()
                  .catch(() => setError('Could not load dashboard. Pull down to retry.'))
                  .finally(() => setIsLoading(false));
              },
            }}
          />
        ) : (
          <>
            <View style={styles.statsRow}>
              <StatCard
                icon={<AlertCircle size={16} color={C.warningText} />}
                label="Quotes pending"
                value={summary?.pending_quotes ?? 0}
                accent={C.warningText}
                bg={C.warningBg}
              />
              <StatCard
                icon={<BriefcaseBusiness size={16} color={C.tealText} />}
                label="Active jobs"
                value={summary?.open_jobs ?? 0}
                accent={C.tealText}
                bg={C.tealBg}
              />
              <StatCard
                icon={<CheckCircle size={16} color={C.successText} />}
                label="Completed"
                value={summary?.completed_jobs ?? 0}
                accent={C.successText}
                bg={C.successBg}
              />
            </View>

            {needsAttention.length > 0 && (
              <>
                <View style={styles.sectionHeader}>
                  <View style={styles.sectionLabelRow}>
                    <AlertCircle size={13} color={C.warningText} />
                    <Text style={[clientStyles.sectionLabel, { color: C.warningText }]}>Needs attention</Text>
                  </View>
                </View>
                {needsAttention.map((item) => (
                  <Pressable
                    key={item.id}
                    style={[clientStyles.card, styles.attentionCard]}
                    onPress={() => navigation.navigate('RequestDetail', { requirementId: item.id })}
                  >
                    <View style={styles.attentionAccent} />
                    <View style={styles.cardInner}>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.requestTitle}>{item.category}</Text>
                        <Text style={clientStyles.subtitle}>{item.city} · Starts {formatDate(item.start_date)}</Text>
                        <Text style={styles.attentionHint}>Quote ready — tap to review & approve</Text>
                      </View>
                      <ChevronRight size={18} color={C.warningText} />
                    </View>
                  </Pressable>
                ))}
              </>
            )}

            {activeNow.length > 0 && (
              <>
                <View style={styles.sectionHeader}>
                  <View style={styles.sectionLabelRow}>
                    <Clock size={13} color={C.tealText} />
                    <Text style={[clientStyles.sectionLabel, { color: C.tealText }]}>Active now</Text>
                  </View>
                </View>
                {activeNow.map((item) => (
                  <Pressable
                    key={item.id}
                    style={[clientStyles.card, styles.activeCard]}
                    onPress={() => navigation.navigate('RequestDetail', { requirementId: item.id })}
                  >
                    <View style={styles.activeAccent} />
                    <View style={styles.cardInner}>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.requestTitle}>{item.category}</Text>
                        <Text style={clientStyles.subtitle}>{item.city} · Starts {formatDate(item.start_date)}</Text>
                      </View>
                      <View style={styles.rightCol}>
                        <StatusBadge value={item.status} />
                        <Pressable
                          style={styles.workersLink}
                          onPress={(e) => {
                            e.stopPropagation();
                            navigation.navigate('AssignedWorkers', { requirementId: item.id });
                          }}
                        >
                          <Users size={12} color={C.tealText} />
                          <Text style={styles.workersLinkText}>{item.number_of_workers} workers</Text>
                          <ChevronRight size={12} color={C.tealText} />
                        </Pressable>
                      </View>
                    </View>
                  </Pressable>
                ))}
              </>
            )}

            {needsAttention.length === 0 && activeNow.length === 0 && (
              <EmptyBlock
                title="All caught up"
                detail={
                  requirements.length === 0
                    ? 'No requests yet. Head to Jobs to create your first worker request.'
                    : 'No quotes pending or active jobs right now.'
                }
              />
            )}

            <Pressable style={styles.viewAllRow} onPress={() => tabNavigation.navigate('JobsTab')}>
              <Text style={clientStyles.ghostButtonText}>View all requests</Text>
              <ArrowRight size={15} color={C.brand} />
            </Pressable>
          </>
        )}
      </ScrollView>
    </View>
  );
}

function StatCard({
  icon,
  label,
  value,
  accent,
  bg,
}: {
  icon: ReactNode;
  label: string;
  value: number;
  accent: string;
  bg: string;
}) {
  return (
    <View style={[styles.statCard, { borderColor: accent + '33' }]}>
      <View style={[styles.statIcon, { backgroundColor: bg }]}>{icon}</View>
      <Text style={[styles.statValue, { color: accent }]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short' }).format(new Date(value));
}

const styles = StyleSheet.create({
  greeting: {
    color: C.ink,
    fontSize: 22,
    lineHeight: 28,
    fontWeight: '700',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  iconButton: {
    width: 38,
    height: 38,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  statCard: {
    flex: 1,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    gap: 4,
  },
  statIcon: {
    width: 32,
    height: 32,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 2,
  },
  statValue: {
    fontSize: 20,
    fontWeight: '700',
    lineHeight: 26,
  },
  statLabel: {
    color: C.muted,
    fontSize: 11,
    fontWeight: '500',
    textAlign: 'center',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  sectionLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  attentionCard: {
    flexDirection: 'row',
    alignItems: 'stretch',
    padding: 0,
    overflow: 'hidden',
    borderColor: C.warningText + '40',
  },
  attentionAccent: {
    width: 4,
    backgroundColor: C.warningText,
  },
  activeCard: {
    flexDirection: 'row',
    alignItems: 'stretch',
    padding: 0,
    overflow: 'hidden',
    borderColor: C.tealText + '40',
  },
  activeAccent: {
    width: 4,
    backgroundColor: C.tealText,
  },
  cardInner: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    gap: 10,
  },
  requestTitle: {
    color: C.ink,
    fontSize: 15,
    fontWeight: '600',
    lineHeight: 20,
  },
  attentionHint: {
    color: C.warningText,
    fontSize: 12,
    fontWeight: '500',
    marginTop: 4,
  },
  rightCol: {
    alignItems: 'flex-end',
    gap: 8,
  },
  workersLink: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: C.tealBg,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  workersLinkText: {
    color: C.tealText,
    fontSize: 12,
    fontWeight: '600',
  },
  avatarButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: C.brand,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  viewAllRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 4,
  },
});
