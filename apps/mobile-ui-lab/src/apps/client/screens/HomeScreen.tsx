import { useCallback, useMemo, useState } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { AlertCircle, ArrowRight, BriefcaseBusiness, CheckCircle, ChevronRight, Clock, CreditCard, Plus, Star, Users } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { clientRequirementsService, type ClientRequirementListItem, type ClientDashboardSummary, type RequirementStatus } from '../../../shared/services/client-requirements.service';
import { useAuthStore } from '../../../shared/store/auth.store';
import type { ClientAppStackParamList, ClientTabParamList } from '../navigation/types';
import { LoadingBlock, StatusBadge } from './components';
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

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

function getUserFirstName(name?: string | null, phone?: string): string {
  if (name?.trim()) return name.trim().split(' ')[0];
  return '';
}

function getInitials(name?: string | null, phone?: string): string {
  if (name?.trim()) return name.trim().split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2);
  return (phone ?? '').slice(-2) || 'Me';
}

function statusAccent(status: RequirementStatus): string {
  switch (status) {
    case 'in_progress': return C.tealText;
    case 'assigned':    return C.tealText;
    case 'quoted':      return C.warningText;
    case 'approved':    return C.infoText;
    case 'submitted':
    case 'under_review': return C.purpleText;
    case 'completed':   return C.successText;
    case 'rejected':    return C.dangerText;
    default:            return C.muted;
  }
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
      setRequirements(Array.isArray(cached.requirements) ? cached.requirements : []);
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

  // Derived
  const paymentDue = useMemo(() => requirements.filter((r) => r.status === 'approved'), [requirements]);
  const balanceDue = useMemo(
    () => requirements.filter((r) => r.status === 'in_progress' && (r.pending_balance_amount ?? 0) > 0),
    [requirements],
  );
  const needsAttention = useMemo(() => requirements.filter((r) => r.status === 'quoted'), [requirements]);
  const activeNow = useMemo(
    () => requirements.filter((r) => ['assigned', 'in_progress'].includes(r.status)),
    [requirements],
  );
  const unrated = useMemo(
    () => requirements.filter((r) => r.status === 'completed' && !r.has_rated),
    [requirements],
  );
  const recentRequests = useMemo(() => {
    // IDs already shown in contextual sections — exclude them from Recent
    const shownIds = new Set([
      ...needsAttention.map((r) => r.id),
      ...activeNow.map((r) => r.id),
      ...unrated.map((r) => r.id),
    ]);
    return requirements.filter((r) => !shownIds.has(r.id)).slice(0, 5);
  }, [requirements, needsAttention, activeNow, unrated]);

  const dashboardLine = (() => {
    const active = summary?.open_jobs ?? 0;
    if (active > 0) return `${active} active job${active !== 1 ? 's' : ''} in progress`;
    if (requirements.length > 0) return `${requirements.length} request${requirements.length !== 1 ? 's' : ''} total`;
    return 'Annai Illam staffing client';
  })();

  return (
    <View style={[clientStyles.root, { paddingTop: insets.top }]}>
      {/* Offline / stale banner */}
      {(networkStatus === 'offline' || isStale) && (
        <View style={[styles.statusBanner, { backgroundColor: networkStatus === 'offline' ? '#EF4444' : C.warningText }]}>
          <Text style={styles.statusBannerText}>
            {networkStatus === 'offline'
              ? 'No internet connection — showing cached data'
              : 'Showing cached data — pull to refresh'}
          </Text>
        </View>
      )}

      <ScrollView
        contentContainerStyle={clientStyles.content}
        refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={refresh} tintColor={C.brand} />}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Header ── */}
        <View style={styles.header}>
          <View style={{ flex: 1 }}>
            <Text style={styles.greetingLabel}>{getGreeting()}</Text>
            {!!getUserFirstName(user?.name, user?.phone) && (
              <Text style={styles.greeting}>{getUserFirstName(user?.name, user?.phone)}</Text>
            )}
            <Text style={clientStyles.subtitle}>{dashboardLine}</Text>
          </View>
          <View style={styles.headerActions}>
            <Pressable
              style={styles.avatarButton}
              accessibilityLabel="Profile"
              onPress={() => tabNavigation.navigate('ProfileTab')}
            >
              <Text style={styles.avatarText}>{getInitials(user?.name, user?.phone)}</Text>
            </Pressable>
          </View>
        </View>

        {/* ── New request CTA ── */}
        <Pressable
          style={({ pressed }) => [styles.newRequestBtn, pressed && { opacity: 0.88 }]}
          onPress={() => navigation.navigate('CreateRequest')}
          accessibilityRole="button"
          accessibilityLabel="Post a new worker request"
        >
          <View style={styles.newRequestIconBox}>
            <Plus size={15} color={C.brand} />
          </View>
          <Text style={styles.newRequestBtnText}>Post a new worker request</Text>
          <ArrowRight size={15} color={C.brand} />
        </Pressable>

        {isLoading ? (
          <LoadingBlock label="Loading dashboard..." />
        ) : error ? (
          <View style={styles.errorBlock}>
            <Text style={styles.errorTitle}>Could not load dashboard</Text>
            <Text style={styles.errorDetail}>{error}</Text>
            <Pressable
              style={styles.retryBtn}
              onPress={() => {
                setIsLoading(true);
                load()
                  .catch(() => setError('Could not load dashboard. Pull down to retry.'))
                  .finally(() => setIsLoading(false));
              }}
            >
              <Text style={styles.retryBtnText}>Retry</Text>
            </Pressable>
          </View>
        ) : (
          <>
            {/* ── Advance payment due ── */}
            {paymentDue.length > 0 && (
              <Pressable
                style={[styles.alertBanner, styles.alertBannerRed]}
                onPress={() => navigation.navigate('RequestDetail', { requirementId: paymentDue[0].id })}
              >
                <View style={[styles.alertIcon, { backgroundColor: C.dangerText }]}>
                  <CreditCard size={16} color="#FFF" />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.alertEyebrow, { color: C.dangerText }]}>Action required</Text>
                  <Text style={[styles.alertTitle, { color: '#7F1D1D' }]}>
                    Advance payment due{paymentDue.length > 1 ? ` · ${paymentDue.length} jobs` : ''}
                  </Text>
                  <Text style={[styles.alertSub, { color: C.dangerText }]}>
                    {paymentDue[0].category}, {paymentDue[0].city}
                  </Text>
                </View>
                <View style={[styles.alertCta, { borderColor: C.dangerText + '40' }]}>
                  <Text style={[styles.alertCtaText, { color: C.dangerText }]}>Pay now</Text>
                  <ChevronRight size={11} color={C.dangerText} />
                </View>
              </Pressable>
            )}

            {/* ── Balance due ── */}
            {balanceDue.length > 0 && (
              <Pressable
                style={[styles.alertBanner, styles.alertBannerAmber]}
                onPress={() => navigation.navigate('RequestDetail', { requirementId: balanceDue[0].id })}
              >
                <View style={[styles.alertIcon, { backgroundColor: C.warningText }]}>
                  <CreditCard size={16} color="#FFF" />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.alertEyebrow, { color: C.warningText }]}>Balance outstanding</Text>
                  <Text style={[styles.alertTitle, { color: '#78350F' }]}>
                    ₹{new Intl.NumberFormat('en-IN').format(balanceDue[0].pending_balance_amount ?? 0)} due
                  </Text>
                  <Text style={[styles.alertSub, { color: '#92400E' }]}>
                    {balanceDue[0].category}, {balanceDue[0].city}
                  </Text>
                </View>
                <View style={[styles.alertCta, { borderColor: C.warningText + '40' }]}>
                  <Text style={[styles.alertCtaText, { color: C.warningText }]}>Settle</Text>
                  <ChevronRight size={11} color={C.warningText} />
                </View>
              </Pressable>
            )}

            {/* ── Quote review needed ── */}
            {needsAttention.length > 0 && (
              <Pressable
                style={[styles.alertBanner, styles.alertBannerAmber]}
                onPress={() => navigation.navigate('RequestDetail', { requirementId: needsAttention[0].id })}
              >
                <View style={[styles.alertIcon, { backgroundColor: C.warningText }]}>
                  <AlertCircle size={16} color="#FFF" />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.alertEyebrow, { color: C.warningText }]}>Awaiting your response</Text>
                  <Text style={[styles.alertTitle, { color: '#78350F' }]}>
                    Quote ready to review{needsAttention.length > 1 ? ` · ${needsAttention.length} pending` : ''}
                  </Text>
                  <Text style={[styles.alertSub, { color: '#92400E' }]}>
                    {needsAttention[0].category}, {needsAttention[0].city}
                  </Text>
                </View>
                <View style={[styles.alertCta, { borderColor: C.warningText + '40' }]}>
                  <Text style={[styles.alertCtaText, { color: C.warningText }]}>Review</Text>
                  <ChevronRight size={11} color={C.warningText} />
                </View>
              </Pressable>
            )}

            {/* ── Stats strip ── */}
            <View style={styles.statsRow}>
              <StatTile
                label="Quotes"
                value={summary?.pending_quotes ?? 0}
                tint={needsAttention.length > 0 ? C.warningText : C.muted}
                bg={needsAttention.length > 0 ? C.warningBg : C.surface}
                borderColor={needsAttention.length > 0 ? C.warningText + '35' : C.border}
              />
              <StatTile
                label="Active"
                value={summary?.open_jobs ?? 0}
                tint={(summary?.open_jobs ?? 0) > 0 ? C.tealText : C.muted}
                bg={(summary?.open_jobs ?? 0) > 0 ? C.tealBg : C.surface}
                borderColor={(summary?.open_jobs ?? 0) > 0 ? C.tealText + '35' : C.border}
              />
              <StatTile
                label="Done"
                value={summary?.completed_jobs ?? 0}
                tint={(summary?.completed_jobs ?? 0) > 0 ? C.successText : C.muted}
                bg={(summary?.completed_jobs ?? 0) > 0 ? C.successBg : C.surface}
                borderColor={(summary?.completed_jobs ?? 0) > 0 ? C.successText + '35' : C.border}
              />
            </View>

            {/* ── Active now ── */}
            {activeNow.length > 0 && (
              <View style={styles.section}>
                <View style={styles.sectionHeader}>
                  <View style={styles.sectionTitleRow}>
                    <View style={[styles.sectionDot, { backgroundColor: C.tealText }]} />
                    <Text style={[styles.sectionTitle, { color: C.tealText }]}>Active now</Text>
                  </View>
                </View>
                {activeNow.map((item) => (
                  <RequestCard
                    key={item.id}
                    item={item}
                    onPress={() => navigation.navigate('RequestDetail', { requirementId: item.id })}
                    onWorkersPress={() => navigation.navigate('AssignedWorkers', { requirementId: item.id })}
                  />
                ))}
              </View>
            )}

            {/* ── Needs attention: quote review ── */}
            {needsAttention.length > 0 && (
              <View style={styles.section}>
                <View style={styles.sectionHeader}>
                  <View style={styles.sectionTitleRow}>
                    <View style={[styles.sectionDot, { backgroundColor: C.warningText }]} />
                    <Text style={[styles.sectionTitle, { color: C.warningText }]}>Needs attention</Text>
                  </View>
                </View>
                {needsAttention.map((item) => (
                  <RequestCard
                    key={item.id}
                    item={item}
                    onPress={() => navigation.navigate('RequestDetail', { requirementId: item.id })}
                  />
                ))}
              </View>
            )}

            {/* ── Rate your experience ── */}
            {unrated.length > 0 && (
              <View style={styles.section}>
                <View style={styles.sectionHeader}>
                  <View style={styles.sectionTitleRow}>
                    <Star size={11} color={C.brand} />
                    <Text style={[styles.sectionTitle, { color: C.brand }]}>Rate your experience</Text>
                  </View>
                </View>
                {unrated.map((item) => (
                  <RequestCard
                    key={item.id}
                    item={item}
                    onPress={() => navigation.navigate('RateRequirement', { requirementId: item.id, category: item.category })}
                  />
                ))}
              </View>
            )}

            {/* ── Recent requests (always visible) ── */}
            <View style={styles.section}>
              <View style={styles.sectionHeader}>
                <View style={styles.sectionTitleRow}>
                  <Text style={styles.sectionTitle}>Recent requests</Text>
                </View>
                <Pressable
                  style={styles.sectionLink}
                  onPress={() => navigation.navigate('AllRequests')}
                >
                  <Text style={styles.sectionLinkText}>View all</Text>
                  <ArrowRight size={12} color={C.brand} />
                </Pressable>
              </View>

              {recentRequests.length === 0 ? (
                <View style={styles.emptyState}>
                  <View style={styles.emptyStateIcon}>
                    <BriefcaseBusiness size={32} color={C.muted} />
                  </View>
                  <Text style={styles.emptyStateTitle}>No requests yet</Text>
                  <Text style={styles.emptyStateDetail}>
                    Post your first request above and we will handle the rest.
                  </Text>
                </View>
              ) : (
                recentRequests.map((item) => (
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
            </View>
          </>
        )}
      </ScrollView>
    </View>
  );
}

// ── Sub-components ──────────────────────────────────────────────

function StatTile({
  label,
  value,
  tint,
  bg,
  borderColor,
}: {
  label: string;
  value: number;
  tint: string;
  bg: string;
  borderColor: string;
}) {
  return (
    <View style={[styles.statTile, { backgroundColor: bg, borderColor }]}>
      <Text style={[styles.statTileValue, { color: tint }]}>{value}</Text>
      <Text style={[styles.statTileLabel, { color: tint }]}>{label}</Text>
    </View>
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
  const accent = statusAccent(item.status);
  const isActive = ['assigned', 'in_progress'].includes(item.status);
  const isQuote = item.status === 'quoted';
  const isUnrated = item.status === 'completed' && !item.has_rated;

  return (
    <Pressable
      style={({ pressed }) => [styles.reqCard, pressed && styles.reqCardPressed]}
      onPress={onPress}
    >
      <View style={[styles.reqAccent, { backgroundColor: accent }]} />
      <View style={styles.reqBody}>
        <View style={styles.reqTopRow}>
          <View style={{ flex: 1, paddingRight: 8 }}>
            <Text style={styles.reqTitle} numberOfLines={1}>{item.category}</Text>
            <Text style={styles.reqSub} numberOfLines={1}>{item.city} · {formatDate(item.start_date)}</Text>
          </View>
          <StatusBadge value={item.status} />
        </View>
        <View style={styles.reqBottomRow}>
          {isActive && onWorkersPress ? (
            <Pressable style={styles.workersChip} onPress={onWorkersPress} hitSlop={6}>
              <Users size={11} color={C.tealText} />
              <Text style={styles.workersChipText}>{item.number_of_workers} workers</Text>
            </Pressable>
          ) : isQuote ? (
            <View style={styles.hintChip}>
              <AlertCircle size={11} color={C.warningText} />
              <Text style={[styles.hintChipText, { color: C.warningText }]}>Tap to review quote</Text>
            </View>
          ) : isUnrated ? (
            <View style={styles.hintChip}>
              <Star size={11} color={C.brand} />
              <Text style={[styles.hintChipText, { color: C.brand }]}>Tap to leave a rating</Text>
            </View>
          ) : (
            <Text style={styles.reqMeta}>
              {item.number_of_workers} worker{item.number_of_workers !== 1 ? 's' : ''} · {formatDate(item.start_date)}
            </Text>
          )}
          <ChevronRight size={15} color={C.muted} />
        </View>
      </View>
    </Pressable>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short' }).format(new Date(value));
}

function formatAmount(value: number) {
  return new Intl.NumberFormat('en-IN').format(value);
}

const styles = StyleSheet.create({
  statusBanner: {
    paddingVertical: 7,
    alignItems: 'center',
  },
  statusBannerText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    paddingBottom: 4,
  },
  greetingLabel: {
    fontSize: 13,
    color: C.muted,
    fontWeight: '500',
  },
  greeting: {
    fontSize: 24,
    fontWeight: '700',
    color: C.ink,
    lineHeight: 30,
    marginTop: 1,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingTop: 2,
  },
  avatarButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: C.brand,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },

  // New request CTA
  newRequestBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: C.brandSoft,
    borderWidth: 1.5,
    borderColor: C.brand + '50',
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  newRequestIconBox: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: C.brand + '18',
    alignItems: 'center',
    justifyContent: 'center',
  },
  newRequestBtnText: {
    flex: 1,
    color: C.brand,
    fontSize: 15,
    fontWeight: '600',
  },

  // Error block
  errorBlock: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    gap: 8,
  },
  errorTitle: {
    color: C.ink,
    fontSize: 15,
    fontWeight: '600',
  },
  errorDetail: {
    color: C.muted,
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 20,
  },
  retryBtn: {
    marginTop: 4,
    backgroundColor: C.brand,
    borderRadius: 10,
    paddingVertical: 9,
    paddingHorizontal: 20,
  },
  retryBtnText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },

  // Alert banners
  alertBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderWidth: 1,
    borderRadius: 14,
    padding: 14,
  },
  alertBannerRed: {
    backgroundColor: C.dangerBg,
    borderColor: C.dangerText + '30',
  },
  alertBannerAmber: {
    backgroundColor: C.warningBg,
    borderColor: C.warningText + '30',
  },
  alertIcon: {
    width: 38,
    height: 38,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  alertEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    marginBottom: 2,
  },
  alertTitle: {
    fontSize: 14,
    fontWeight: '700',
    lineHeight: 19,
  },
  alertSub: {
    fontSize: 12,
    marginTop: 2,
    lineHeight: 17,
  },
  alertCta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderWidth: 1,
  },
  alertCtaText: {
    fontSize: 12,
    fontWeight: '700',
  },

  // Stats
  statsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  statTile: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 10,
    alignItems: 'center',
    gap: 3,
  },
  statTileValue: {
    fontSize: 22,
    fontWeight: '700',
    lineHeight: 26,
  },
  statTileLabel: {
    fontSize: 11,
    fontWeight: '500',
    textAlign: 'center',
  },

  // Sections
  section: {
    gap: 10,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 2,
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  sectionDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    color: C.muted,
  },
  sectionLink: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  sectionLinkText: {
    color: C.brand,
    fontSize: 13,
    fontWeight: '600',
  },

  // Request cards
  reqCard: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'stretch',
    overflow: 'hidden',
  },
  reqCardPressed: {
    opacity: 0.92,
    borderColor: C.brand + '40',
  },
  reqAccent: {
    width: 4,
  },
  reqBody: {
    flex: 1,
    padding: 14,
    gap: 10,
  },
  reqTopRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  reqTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: C.ink,
    lineHeight: 20,
  },
  reqSub: {
    fontSize: 13,
    color: C.muted,
    marginTop: 2,
  },
  reqBottomRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  reqMeta: {
    fontSize: 13,
    color: C.muted,
  },
  workersChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: C.tealBg,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  workersChipText: {
    color: C.tealText,
    fontSize: 12,
    fontWeight: '600',
  },
  hintChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  hintChipText: {
    fontSize: 12,
    fontWeight: '500',
  },

  // Empty state
  emptyState: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 14,
    padding: 28,
    alignItems: 'center',
    gap: 8,
  },
  emptyStateIcon: {
    width: 64,
    height: 64,
    borderRadius: 16,
    backgroundColor: C.surfaceAlt,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  emptyStateTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: C.ink,
  },
  emptyStateDetail: {
    fontSize: 13,
    color: C.muted,
    textAlign: 'center',
    lineHeight: 20,
    maxWidth: 240,
  },
});
