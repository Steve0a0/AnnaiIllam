import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { FileDown } from 'lucide-react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as FileSystem from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import type { EarningsStackParamList } from '../navigation/types';
import {
  workerPayrollService,
  type WorkerPayrollItem,
  type WorkerPayout,
} from '../../../shared/services/worker-payroll.service';

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
  successBg: '#DCFCE7',
  successText: '#15803D',
  dangerText: '#B91C1C',
  warningText: '#B45309',
};

function fmt(n: number) {
  return `₹${n.toLocaleString('en-IN')}`;
}

function fmtPeriod(start: string | null, end: string | null): string {
  if (!start || !end) return '—';
  const opts: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short', year: 'numeric' };
  const s = new Intl.DateTimeFormat('en-IN', opts).format(new Date(start));
  const e = new Intl.DateTimeFormat('en-IN', opts).format(new Date(end));
  return `${s} – ${e}`;
}

function fmtDate(iso: string | null): string {
  if (!iso) return '—';
  return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(iso));
}

function statusLabel(status: string): string {
  switch (status) {
    case 'paid': return 'Paid';
    case 'pending': return 'Pending';
    case 'processing': return 'Processing';
    default: return status.charAt(0).toUpperCase() + status.slice(1);
  }
}

export default function EarningsScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<NativeStackNavigationProp<EarningsStackParamList>>();

  const [items, setItems] = useState<WorkerPayrollItem[]>([]);
  const [payouts, setPayouts] = useState<WorkerPayout[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const [itemData, payoutData] = await Promise.all([
        workerPayrollService.listPayroll(),
        workerPayrollService.listPayouts(),
      ]);
      // Most recent period first
      itemData.sort((a, b) =>
        (b.period_end ?? '').localeCompare(a.period_end ?? '')
      );
      setItems(itemData);
      setPayouts(payoutData);
    } catch {
      // leave state empty; user sees empty state
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const onRefresh = () => { setRefreshing(true); load(); };

  const handleDownloadPayslip = async (item: WorkerPayrollItem) => {
    if (downloadingId) return;
    setDownloadingId(item.id);
    try {
      const url = workerPayrollService.getPayslipPdfUrl(item.id);
      const token = await workerPayrollService.getAccessToken();
      const localUri = `${FileSystem.cacheDirectory}payslip-${item.id}.pdf`;

      const downloadResult = await FileSystem.downloadAsync(url, localUri, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (downloadResult.status !== 200) {
        throw new Error(`Server returned ${downloadResult.status}`);
      }

      const canShare = await Sharing.isAvailableAsync();
      if (!canShare) {
        Alert.alert('Sharing not available', 'Your device does not support file sharing.');
        return;
      }

      await Sharing.shareAsync(downloadResult.uri, {
        mimeType: 'application/pdf',
        dialogTitle: 'Save or share your payslip',
        UTI: 'com.adobe.pdf',
      });
    } catch {
      Alert.alert('Could not download payslip', 'Please try again.');
    } finally {
      setDownloadingId(null);
    }
  };

  // Build a map payroll_item_id → payout for quick lookup
  const payoutMap = new Map<number, WorkerPayout>();
  for (const p of payouts) {
    if (!payoutMap.has(p.payroll_item_id)) payoutMap.set(p.payroll_item_id, p);
  }

  const latest = items[0];
  const latestPayout = latest ? payoutMap.get(latest.id) : undefined;
  const totalEarned = items.reduce((s, i) => s + (i.payment_status === 'paid' ? i.net_amount : 0), 0);

  if (loading) {
    return (
      <View style={[s.root, s.center]}>
        <ActivityIndicator color={C.brand} size="large" />
      </View>
    );
  }

  return (
    <View style={s.root}>
      {/* ── Dark green hero extends behind status bar ── */}
      <View style={[s.hero, { paddingTop: insets.top + 16 }]}>
        <Text style={s.heroEyebrow}>My Earnings</Text>
        <Text style={s.heroAmount}>
          {latest ? fmt(latest.net_amount) : '₹0'}
        </Text>

        {latest?.payment_status === 'paid' && latestPayout?.paid_at ? (
          <View style={s.paidBadge}>
            <Text style={s.paidBadgeText}>Paid · {fmtDate(latestPayout.paid_at)}</Text>
          </View>
        ) : latest ? (
          <View style={[s.paidBadge, { backgroundColor: '#FEF3C7' }]}>
            <Text style={[s.paidBadgeText, { color: C.warningText }]}>
              {statusLabel(latest.payment_status)} · {fmtPeriod(latest.period_start, latest.period_end)}
            </Text>
          </View>
        ) : null}

        {/* Three stat chips */}
        <View style={s.chipsRow}>
          <View style={s.chip}>
            <Text style={s.chipValue}>{latest?.attendance_days ?? 0}</Text>
            <Text style={s.chipLabel}>Days worked</Text>
          </View>
          <View style={s.chipDivider} />
          <View style={s.chip}>
            <Text style={s.chipValue}>{fmt(latest?.gross_amount ?? 0)}</Text>
            <Text style={s.chipLabel}>Gross pay</Text>
          </View>
          <View style={s.chipDivider} />
          <View style={s.chip}>
            <Text style={s.chipValue}>{fmt(latest?.total_deduction_amount ?? 0)}</Text>
            <Text style={[s.chipLabel, (latest?.total_deduction_amount ?? 0) > 0 && s.chipLabelWarn]}>
              Deducted
            </Text>
          </View>
        </View>
      </View>

      {/* ── Payment history ── */}
      <ScrollView
        contentContainerStyle={s.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.brand} />}
      >
        <Text style={s.sectionLabel}>Payment history</Text>

        {items.length === 0 ? (
          <View style={s.emptyCard}>
            <Text style={s.emptyTitle}>No payroll records yet</Text>
            <Text style={s.emptySub}>
              Your payment records will appear here once admin processes your payroll.
            </Text>
          </View>
        ) : (
          items.map((item) => {
            const payout = payoutMap.get(item.id);
            const isPaid = item.payment_status === 'paid';

            return (
              <View key={item.id} style={s.card}>
                {/* Top row */}
                <View style={s.cardTop}>
                  <View style={{ flex: 1 }}>
                    <Text style={s.cardTitle}>{fmtPeriod(item.period_start, item.period_end)}</Text>
                    <Text style={s.cardMeta}>
                      {item.attendance_days} days worked
                      {item.half_days > 0 ? ` · ${item.half_days} half-days` : ''}
                    </Text>
                  </View>
                  <View style={s.cardRight}>
                    <Text style={s.cardNet}>{fmt(item.net_amount)}</Text>
                    <View style={[s.paidPill, !isPaid && s.pendingPill]}>
                      <Text style={[s.paidPillText, !isPaid && s.pendingPillText]}>
                        {statusLabel(item.payment_status)}
                      </Text>
                    </View>
                  </View>
                </View>

                {/* Gross → deductions → net */}
                <Text style={s.detailText}>
                  Gross: {fmt(item.gross_amount)}
                </Text>

                {item.total_deduction_amount > 0 && (
                  <View style={s.deductRow}>
                    <Text style={s.deductLabel}>Total deductions</Text>
                    <Text style={s.deductAmount}>−{fmt(item.total_deduction_amount)}</Text>
                  </View>
                )}

                {/* UPI / transaction ref if paid */}
                {payout?.transaction_reference ? (
                  <View style={s.refRow}>
                    <Text style={s.refLabel}>Ref</Text>
                    <Text style={s.refValue}>{payout.transaction_reference}</Text>
                  </View>
                ) : isPaid ? (
                  <View style={s.refRow}>
                    <Text style={s.refLabel}>Paid on</Text>
                    <Text style={s.refValue}>{fmtDate(payout?.paid_at ?? null)}</Text>
                  </View>
                ) : null}

                {/* Download payslip */}
                <Pressable
                  style={({ pressed }) => [s.downloadBtn, (pressed || downloadingId === item.id) && { opacity: 0.6 }]}
                  disabled={downloadingId !== null}
                  onPress={() => handleDownloadPayslip(item)}
                >
                  {downloadingId === item.id
                    ? <ActivityIndicator size="small" color={C.brand} />
                    : <FileDown size={15} color={C.brand} />
                  }
                  <Text style={s.downloadBtnText}>
                    {downloadingId === item.id ? 'Loading…' : 'Download payslip'}
                  </Text>
                </Pressable>
              </View>
            );
          })
        )}

        {items.length > 0 && (
          <View style={s.totalRow}>
            <Text style={s.totalLabel}>Total received</Text>
            <Text style={s.totalValue}>{fmt(totalEarned)}</Text>
          </View>
        )}

        <View style={{ height: insets.bottom + 20 }} />
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.page },
  center: { alignItems: 'center', justifyContent: 'center', flex: 1 },

  // Hero — no paddingTop here; computed dynamically with insets
  hero: {
    backgroundColor: C.brandDark,
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  heroEyebrow: {
    color: 'rgba(255,255,255,0.55)',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  heroAmount: {
    color: '#FFFFFF',
    fontSize: 44,
    fontWeight: '800',
    letterSpacing: -1,
    marginBottom: 10,
  },
  paidBadge: {
    backgroundColor: C.successBg,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 5,
    alignSelf: 'flex-start',
    marginBottom: 14,
  },
  paidBadgeText: { color: C.successText, fontSize: 12, fontWeight: '600' },

  chipsRow: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 12,
    padding: 12,
    gap: 0,
  },
  chip: { flex: 1, alignItems: 'center', gap: 3 },
  chipDivider: { width: 1, backgroundColor: 'rgba(255,255,255,0.15)', marginHorizontal: 4 },
  chipValue: { color: '#FFFFFF', fontSize: 15, fontWeight: '700' },
  chipLabel: { color: 'rgba(255,255,255,0.55)', fontSize: 11, textAlign: 'center' },
  chipLabelWarn: { color: '#FCD34D' },

  // List
  list: { paddingHorizontal: 16, paddingTop: 20, gap: 12, paddingBottom: 16 },

  sectionLabel: {
    color: C.muted,
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },

  // Cards
  card: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 14,
    padding: 16,
    gap: 8,
  },
  cardTop: { flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  cardTitle: { color: C.ink, fontSize: 15, fontWeight: '600' },
  cardMeta: { color: C.muted, fontSize: 12, marginTop: 2, lineHeight: 17 },
  cardRight: { alignItems: 'flex-end', gap: 5 },
  cardNet: { color: C.ink, fontSize: 17, fontWeight: '700' },
  paidPill: {
    backgroundColor: C.successBg,
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  paidPillText: { color: C.successText, fontSize: 11, fontWeight: '700' },
  pendingPill: { backgroundColor: '#FEF3C7' },
  pendingPillText: { color: C.warningText },

  detailText: { color: C.muted, fontSize: 13 },

  deductRow: { flexDirection: 'row', justifyContent: 'space-between' },
  deductLabel: { color: C.muted, fontSize: 13 },
  deductAmount: { color: C.dangerText, fontSize: 13, fontWeight: '600' },

  refRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: C.border,
    paddingTop: 8,
    marginTop: 2,
  },
  refLabel: { color: C.muted, fontSize: 12 },
  refValue: { color: C.body, fontSize: 12, fontFamily: 'monospace', fontWeight: '600' },

  // Download payslip button (inside each card)
  downloadBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderTopWidth: 1,
    borderTopColor: C.border,
    paddingTop: 10,
    marginTop: 2,
  },
  downloadBtnText: { color: C.brand, fontSize: 13, fontWeight: '600' },

  // Empty state
  emptyCard: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 14,
    padding: 24,
    alignItems: 'center',
    gap: 8,
  },
  emptyTitle: { color: C.ink, fontSize: 15, fontWeight: '600' },
  emptySub: { color: C.muted, fontSize: 13, textAlign: 'center', lineHeight: 19 },

  // Total row
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: C.brandSoft,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    marginTop: 4,
  },
  totalLabel: { color: C.brand, fontSize: 14, fontWeight: '600' },
  totalValue: { color: C.brand, fontSize: 18, fontWeight: '800' },
});

