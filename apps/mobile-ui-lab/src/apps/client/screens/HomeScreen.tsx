import { useCallback, useState } from 'react';
import type { ReactNode } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { AlertCircle, ArrowRight, Bell, BriefcaseBusiness, CheckCircle, ChevronRight, Clock, CreditCard, Star, Users } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { clientRequirementsService, type ClientRequirementListItem, type ClientDashboardSummary } from '../../../shared/services/client-requirements.service';
import { useAuthStore } from '../../../shared/store/auth.store';
import type { ClientAppStackParamList, ClientTabParamList } from '../navigation/types';
import { EmptyBlock, LoadingBlock, StatusBadge } from './components';
import { C, clientStyles } from './clientStyles';
import { useNetworkStatus } from '../../../shared/hooks/use-network-status';

type Navigation = NativeStackNavigationProp<ClientAppStackParamList>;
type TabNavigation = BottomTabNavigationProp<ClientTabParamList>;

const CLIENT_CACHE_KEY = 'client_home_cache_v1';

interface ClientHomeCache {
  summary: ClientDashboardSummary | null;
  requirements: ClientRequirementListItem[];
  cachedAt: number;
}

export default function HomeScreen() {
  const navigation = useNavigation<Navigation>();
  const tabNavigation = useNavigation<TabNavigation>();
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const networkStatus = useNetworkStatus();
  const [summary, setSummary] = useState<ClientDashboardSummary | null>(null);
  const [requirements, setRequirements] = useState<ClientRequirementListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isStale, setIsStale] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCache = useCallback(async () => {
    try {
      const raw = await AsyncStorage.getItem(CLIENT_CACHE_KEY);
      if (!raw) return;
      const cached: ClientHomeCache = JSON.parse(raw);
      setSummary(cached.summary);
      setRequirements(cached.requirements);
      setIsStale(true);
    } catch {
      // Corrupt cache — ignore
    }
  }, []);

  const saveCache = useCallback(
    async (s: ClientDashboardSummary | null, r: ClientRequirementListItem[]) => {
      try {
        await AsyncStorage.setItem(
          CLIENT_CACHE_KEY,
          JSON.stringify({ summary: s, requirements: r, cachedAt: Date.now() }),
        );
      } catch {
        // Non-fatal
      }
    },
    [],
  );

  const load = useCallback(async () => {
    setError(null);
    const [summaryResult, listResult] = await Promise.allSettled([
      clientRequirementsService.getSummary(),
      clientRequirementsService.list(),
    ]);
    if (summaryResult.status === 'fulfilled') setSummary(summaryResult.value);
    if (listResult.status === 'fulfilled') setRequirements(listResult.value);
    if (summaryResult.status === 'fulfilled' && listResult.status === 'fulfilled') {
      setIsStale(false);
      await saveCache(summaryResult.value, listResult.value);
    } else {
      // Both failed
      throw new Error('Could not load dashboard.');
    }
  }, [saveCache]);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);
      loadCache().finally(() => {
        if (!active) return;
        load()
          .catch(() => active && setError('Could not load dashboard. Pull down to retry.'))
          .finally(() => active && setIsLoading(false));
      });
      return () => {
        active = false;
      };
    }, [load, loadCache]),
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

  const paymentDue = requirements.filter((r) => r.status === 'approved').slice(0, 3);
  const balanceDue = requirements.filter((r) => r.status === 'in_progress' && (r.pending_balance_amount ?? 0) > 0).slice(0, 3);
  const needsAttention = requirements.filter((r) => r.status === 'quoted').slice(0, 3);
  const activeNow = requirements.filter((r) => ['assigned', 'in_progress'].includes(r.status)).slice(0, 3);
  const unrated = requirements.filter((r) => r.status === 'completed' && !r.has_rated).slice(0, 3);

  return (
    <View style={[clientStyles.root, { paddingTop: insets.top }]}>
      {/* Offline / stale-data banner */}
      {(networkStatus === 'offline' || isStale) && (
        <View
          style={{
            backgroundColor: isStale ? '#f59e0b' : '#ef4444',
            paddingVertical: 6,
            alignItems: 'center',
          }}
        >
          <Text style={{ color: 'white', fontSize: 12, fontWeight: '600' }}>
            {networkStatus === 'offline'
              ? 'No internet connection \u2014 showing cached data'
              : 'Showing cached data \u2014 pull to refresh'}
          </Text>
        </View>
      )}
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
            {paymentDue.length > 0 && (
              <Pressable
                style={styles.paymentBanner}
                onPress={() => navigation.navigate('RequestDetail', { requirementId: paymentDue[0].id })}
              >
                <View style={styles.paymentBannerIcon}>
                  <CreditCard size={20} color="#FFFFFF" />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.paymentBannerEyebrow}>Action required</Text>
                  <Text style={styles.paymentBannerTitle}>
                    {paymentDue.length === 1
                      ? `${paymentDue[0].category} · ${paymentDue[0].city}`
                      : `${paymentDue.length} jobs awaiting advance payment`}
                  </Text>
                  <Text style={styles.paymentBannerSub}>
                    {paymentDue.length === 1
                      ? 'Pay the advance — workers are on hold'
                      : 'Workers cannot be deployed until payment is confirmed'}
                  </Text>
                </View>
                <View style={styles.paymentBannerCta}>
                  <Text style={styles.paymentBannerCtaText}>Pay now</Text>
                  <ArrowRight size={14} color="#B91C1C" />
                </View>
              </Pressable>
            )}

            {balanceDue.length > 0 && (
              <Pressable
                style={styles.balanceBanner}
                onPress={() => navigation.navigate('RequestDetail', { requirementId: balanceDue[0].id })}
              >
                <View style={styles.balanceBannerIcon}>
                  <CreditCard size={20} color="#FFFFFF" />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.balanceBannerEyebrow}>Payment due</Text>
                  <Text style={styles.balanceBannerTitle}>
                    {balanceDue.length === 1
                      ? `${balanceDue[0].category} · ${balanceDue[0].city}`
                      : `${balanceDue.length} jobs have an outstanding balance`}
                  </Text>
                  <Text style={styles.balanceBannerSub}>
                    {balanceDue.length === 1 && balanceDue[0].pending_balance_amount
                      ? `₹${formatAmount(balanceDue[0].pending_balance_amount)} remaining — workers are active`
                      : 'Settle the remaining balance to keep workers active'}
                  </Text>
                </View>
                <View style={styles.balanceBannerCta}>
                  <Text style={styles.balanceBannerCtaText}>Pay now</Text>
                  <ArrowRight size={14} color="#92400E" />
                </View>
              </Pressable>
            )}

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

            {unrated.length > 0 && (
              <>
                <View style={styles.sectionHeader}>
                  <View style={styles.sectionLabelRow}>
                    <Star size={13} color={C.brand} />
                    <Text style={[clientStyles.sectionLabel, { color: C.brand }]}>Rate your experience</Text>
                  </View>
                </View>
                {unrated.map((item) => (
                  <Pressable
                    key={item.id}
                    style={[clientStyles.card, styles.rateCard]}
                    onPress={() => navigation.navigate('RateRequirement', { requirementId: item.id, category: item.category })}
                  >
                    <View style={styles.rateAccent} />
                    <View style={styles.cardInner}>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.requestTitle}>{item.category}</Text>
                        <Text style={clientStyles.subtitle}>{item.city} · Completed</Text>
                        <Text style={styles.rateHint}>How was your experience? Tap to leave a rating</Text>
                      </View>
                      <ChevronRight size={18} color={C.brand} />
                    </View>
                  </Pressable>
                ))}
              </>
            )}

            {paymentDue.length === 0 && needsAttention.length === 0 && activeNow.length === 0 && (
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

function formatAmount(value: number) {
  return new Intl.NumberFormat('en-IN').format(value);
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
  paymentBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: C.dangerBg,
    borderWidth: 1,
    borderColor: C.dangerText + '50',
    borderRadius: 14,
    padding: 14,
  },
  paymentBannerIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: C.dangerText,
    alignItems: 'center',
    justifyContent: 'center',
  },
  paymentBannerEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
    color: C.dangerText,
    marginBottom: 2,
  },
  paymentBannerTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#7F1D1D',
    lineHeight: 19,
  },
  paymentBannerSub: {
    fontSize: 12,
    color: C.dangerText,
    marginTop: 2,
    lineHeight: 17,
  },
  paymentBannerCta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: C.dangerText + '40',
  },
  paymentBannerCtaText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#B91C1C',
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
  balanceBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#FFFBEB',
    borderWidth: 1,
    borderColor: '#D9770650',
    borderRadius: 14,
    padding: 14,
  },
  balanceBannerIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: '#D97706',
    alignItems: 'center',
    justifyContent: 'center',
  },
  balanceBannerEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
    color: '#B45309',
    marginBottom: 2,
  },
  balanceBannerTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#78350F',
    lineHeight: 19,
  },
  balanceBannerSub: {
    fontSize: 12,
    color: '#92400E',
    marginTop: 2,
    lineHeight: 17,
  },
  balanceBannerCta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: '#D9770640',
  },
  balanceBannerCtaText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#92400E',
  },
  rateCard: {
    flexDirection: 'row',
    alignItems: 'stretch',
    padding: 0,
    overflow: 'hidden',
    borderColor: C.brand + '40',
  },
  rateAccent: {
    width: 4,
    backgroundColor: C.brand,
  },
  rateHint: {
    color: C.brand,
    fontSize: 12,
    fontWeight: '500',
    marginTop: 4,
  },
});
