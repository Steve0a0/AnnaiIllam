import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ArrowLeft } from 'lucide-react-native';
import { useNavigation } from '@react-navigation/native';
import {
  workerDisbursementsService,
  type WorkerDisbursement,
} from '../../../shared/services/worker-disbursements.service';

const C = {
  page: '#F5F5F4',
  surface: '#FFFFFF',
  ink: '#1C1917',
  body: '#44403C',
  muted: '#78716C',
  border: '#E7E5E4',
  brandDark: '#0D2E1E',
  brand: '#1A6640',
  brandSoft: '#EDFAF3',
  pendingBg: '#FEF3C7',
  pendingText: '#B45309',
  paidBg: '#DCFCE7',
  paidText: '#15803D',
  failedBg: '#FEE2E2',
  failedText: '#B91C1C',
  processingBg: '#DBEAFE',
  processingText: '#1D4ED8',
};

function fmt(paise: number) {
  return `₹${(paise / 100).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function fmtDate(iso: string) {
  return new Intl.DateTimeFormat('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(iso));
}

function statusStyle(status: WorkerDisbursement['disbursement_status']) {
  switch (status) {
    case 'paid':
      return { bg: C.paidBg, text: C.paidText };
    case 'failed':
      return { bg: C.failedBg, text: C.failedText };
    case 'processing':
      return { bg: C.processingBg, text: C.processingText };
    default:
      return { bg: C.pendingBg, text: C.pendingText };
  }
}

function statusLabel(status: WorkerDisbursement['disbursement_status']) {
  switch (status) {
    case 'paid': return 'Paid';
    case 'failed': return 'Failed';
    case 'processing': return 'Processing';
    default: return 'Pending';
  }
}

export default function PaymentScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation();

  const [items, setItems] = useState<WorkerDisbursement[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const page = await workerDisbursementsService.list(1, 50);
      setItems(page.items);
    } catch {
      // leave state empty; user sees empty state
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const onRefresh = () => {
    setRefreshing(true);
    void load();
  };

  return (
    <View style={[styles.root, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable onPress={() => navigation.goBack()} style={styles.backBtn} hitSlop={10}>
          <ArrowLeft size={20} color={C.ink} />
        </Pressable>
        <Text style={styles.headerTitle}>Salary Payments</Text>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={C.brand} />
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
          showsVerticalScrollIndicator={false}
        >
          {/* Summary card */}
          {items.length > 0 && (
            <View style={styles.summaryCard}>
              <SummaryItem
                label="Total"
                value={fmt(items.reduce((s, d) => s + d.amount, 0))}
              />
              <SummaryItem
                label="Paid"
                value={fmt(
                  items
                    .filter((d) => d.disbursement_status === 'paid')
                    .reduce((s, d) => s + d.amount, 0)
                )}
              />
              <SummaryItem
                label="Pending"
                value={fmt(
                  items
                    .filter((d) => d.disbursement_status === 'pending')
                    .reduce((s, d) => s + d.amount, 0)
                )}
              />
            </View>
          )}

          {items.length === 0 ? (
            <View style={styles.empty}>
              <Text style={styles.emptyTitle}>No payments yet</Text>
              <Text style={styles.emptyBody}>
                Salary disbursements will appear here once your assignments are
                completed and payments are created by the admin.
              </Text>
            </View>
          ) : (
            <View style={styles.listSection}>
              <Text style={styles.sectionTitle}>Payment history</Text>
              {items.map((item) => (
                <DisbursementCard key={item.id} item={item} />
              ))}
            </View>
          )}
        </ScrollView>
      )}
    </View>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.summaryItem}>
      <Text style={styles.summaryLabel}>{label}</Text>
      <Text style={styles.summaryValue}>{value}</Text>
    </View>
  );
}

function DisbursementCard({ item }: { item: WorkerDisbursement }) {
  const s = statusStyle(item.disbursement_status);
  return (
    <View style={styles.card}>
      <View style={styles.cardRow}>
        <View style={styles.cardLeft}>
          <Text style={styles.cardAmount}>{fmt(item.amount)}</Text>
          <Text style={styles.cardSub}>
            Assignment #{item.assignment_id}
          </Text>
          <Text style={styles.cardSub}>
            Scheduled {fmtDate(item.scheduled_date)}
          </Text>
          {item.paid_at && (
            <Text style={styles.cardSub}>Paid {fmtDate(item.paid_at)}</Text>
          )}
          {item.payment_reference && (
            <Text style={[styles.cardSub, styles.mono]}>
              Ref: {item.payment_reference}
            </Text>
          )}
          {item.notes && item.disbursement_status === 'failed' && (
            <Text style={[styles.cardSub, { color: C.failedText }]}>
              {item.notes}
            </Text>
          )}
        </View>
        <View style={[styles.badge, { backgroundColor: s.bg }]}>
          <Text style={[styles.badgeText, { color: s.text }]}>
            {statusLabel(item.disbursement_status)}
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: C.page,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 20,
    paddingVertical: 14,
    backgroundColor: C.surface,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: C.border,
  },
  backBtn: {
    padding: 2,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: C.ink,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scroll: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 32,
    gap: 16,
  },
  summaryCard: {
    backgroundColor: C.surface,
    borderRadius: 14,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: C.border,
    marginBottom: 4,
  },
  summaryItem: {
    alignItems: 'center',
    flex: 1,
  },
  summaryLabel: {
    fontSize: 11,
    fontWeight: '500',
    color: C.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 15,
    fontWeight: '700',
    color: C.ink,
  },
  listSection: {
    gap: 10,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: C.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  card: {
    backgroundColor: C.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: C.border,
  },
  cardRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 12,
  },
  cardLeft: {
    flex: 1,
    gap: 3,
  },
  cardAmount: {
    fontSize: 18,
    fontWeight: '700',
    color: C.ink,
    marginBottom: 2,
  },
  cardSub: {
    fontSize: 12,
    color: C.muted,
    lineHeight: 18,
  },
  mono: {
    fontFamily: 'monospace' as const,
  },
  badge: {
    borderRadius: 100,
    paddingHorizontal: 10,
    paddingVertical: 4,
    alignSelf: 'flex-start',
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  empty: {
    alignItems: 'center',
    paddingTop: 60,
    paddingHorizontal: 24,
    gap: 10,
  },
  emptyTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: C.ink,
    textAlign: 'center',
  },
  emptyBody: {
    fontSize: 14,
    color: C.muted,
    textAlign: 'center',
    lineHeight: 22,
  },
});
