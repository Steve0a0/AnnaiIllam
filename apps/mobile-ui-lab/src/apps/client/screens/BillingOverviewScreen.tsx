import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { ChevronLeft, ReceiptText } from 'lucide-react-native';
import type { ProfileStackParamList } from '../navigation/types';
import { C } from './clientStyles';
import { clientPaymentsService, type ClientPaymentSummary } from '../../../shared/services/client-payments.service';

type Navigation = NativeStackNavigationProp<ProfileStackParamList>;

function fmtDate(iso: string) {
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(iso));
}

function invoiceNumber(id: number) {
  return `INV-${String(id).padStart(5, '0')}`;
}

export default function BillingOverviewScreen() {
  const navigation = useNavigation<Navigation>();
  const insets = useSafeAreaInsets();
  const [payments, setPayments] = useState<ClientPaymentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const data = await clientPaymentsService.listAll();
      // Only show paid payments — these are the ones an invoice was sent for
      setPayments(data.filter(p => p.payment_status === 'paid'));
    } catch {
      // silently fail — empty state shown
    } finally {
      if (isRefresh) setRefreshing(false); else setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <View style={s.root}>
      {/* ── Header ── */}
      <View style={[s.header, { paddingTop: insets.top + 12 }]}>
        <Pressable style={s.backRow} onPress={() => navigation.goBack()}>
          <ChevronLeft size={18} color={C.ink} />
          <Text style={s.backText}>Back</Text>
        </Pressable>
        <Text style={s.title}>My Invoices</Text>
        <Text style={s.subtitle}>Invoices emailed to you after each confirmed payment</Text>
      </View>

      {loading ? (
        <ActivityIndicator style={{ marginTop: 48 }} color={C.brand} />
      ) : (
        <ScrollView
          contentContainerStyle={s.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={C.brand} />}
        >
          {payments.length === 0 ? (
            <View style={s.empty}>
              <ReceiptText size={44} color={C.muted} />
              <Text style={s.emptyTitle}>No invoices yet</Text>
              <Text style={s.emptyBody}>Invoices appear here once a payment is confirmed</Text>
            </View>
          ) : (
            payments.map((p) => (
              <Pressable
                key={p.id}
                style={s.card}
                onPress={() => navigation.navigate('InvoiceViewer', {
                  paymentId: p.id,
                  invoiceNumber: invoiceNumber(p.id),
                })}
              >
                <View style={s.cardIcon}>
                  <ReceiptText size={20} color={C.brand} />
                </View>
                <View style={s.cardBody}>
                  <Text style={s.invoiceNum}>{invoiceNumber(p.id)}</Text>
                  <Text style={s.jobName}>{p.job_name ?? `Requirement #${p.requirement_id}`}</Text>
                  {p.location ? <Text style={s.meta}>{p.location}</Text> : null}
                  <Text style={s.meta}>
                    {p.paid_at ? `Sent on ${fmtDate(p.paid_at)}` : 'Confirmed'}
                  </Text>
                </View>
                <View style={s.sentBadge}>
                  <Text style={s.sentText}>View →</Text>
                </View>
              </Pressable>
            ))
          )}
        </ScrollView>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.page },

  header: {
    backgroundColor: C.surface,
    paddingHorizontal: 20,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  },
  backRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 14 },
  backText: { color: C.body, fontSize: 14 },
  title: { color: C.ink, fontSize: 22, fontWeight: '700', marginBottom: 4 },
  subtitle: { color: C.muted, fontSize: 13, lineHeight: 18 },

  list: { padding: 16, gap: 12 },

  empty: { alignItems: 'center', paddingTop: 72, gap: 10, paddingHorizontal: 32 },
  emptyTitle: { color: C.ink, fontSize: 16, fontWeight: '600' },
  emptyBody: { color: C.muted, fontSize: 13, textAlign: 'center', lineHeight: 19 },

  card: {
    backgroundColor: C.surface,
    borderColor: C.border,
    borderWidth: 1,
    borderRadius: 14,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  cardIcon: {
    width: 44,
    height: 44,
    borderRadius: 10,
    backgroundColor: `${C.brand}15`,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardBody: { flex: 1, gap: 2 },
  invoiceNum: { color: C.ink, fontSize: 14, fontWeight: '700', letterSpacing: 0.3 },
  jobName: { color: C.body, fontSize: 13 },
  meta: { color: C.muted, fontSize: 12 },

  sentBadge: {
    backgroundColor: C.successBg,
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  sentText: { color: C.successText, fontSize: 12, fontWeight: '600' },
});

type PaymentStatus = ClientPaymentSummary['payment_status'];

const STATUS_META: Record<PaymentStatus, { label: string; bg: string; color: string }> = {
  paid:                 { label: 'Paid',                bg: C.successBg,  color: C.successText  },
  pending:              { label: 'Pending',             bg: C.infoBg,     color: C.infoText     },
  pending_verification: { label: 'Verifying',           bg: C.warningBg,  color: C.warningText  },
  failed:               { label: 'Failed',              bg: C.dangerBg,   color: C.dangerText   },
  refunded:             { label: 'Refunded',            bg: C.neutralBg,   color: C.muted        },
};
