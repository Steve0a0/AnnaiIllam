import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { ChevronLeft, ReceiptText } from 'lucide-react-native';
import type { ProfileStackParamList } from '../navigation/types';
import { C } from './clientStyles';
import { clientInvoicesService, type ClientInvoiceSummary } from '../../../shared/services/client-invoices.service';

type Navigation = NativeStackNavigationProp<ProfileStackParamList>;

function fmtDate(iso: string) {
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(iso));
}

export default function BillingOverviewScreen() {
  const navigation = useNavigation<Navigation>();
  const insets = useSafeAreaInsets();
  const [invoices, setInvoices] = useState<ClientInvoiceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      setInvoices(await clientInvoicesService.listAll());
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
        <Text style={s.subtitle}>Issued GST tax invoices</Text>
      </View>

      {loading ? (
        <ActivityIndicator style={{ marginTop: 48 }} color={C.brand} />
      ) : (
        <ScrollView
          contentContainerStyle={s.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={C.brand} />}
        >
          {invoices.length === 0 ? (
            <View style={s.empty}>
              <ReceiptText size={44} color={C.muted} />
              <Text style={s.emptyTitle}>No invoices yet</Text>
              <Text style={s.emptyBody}>Invoices appear here after Finance issues them</Text>
            </View>
          ) : (
            invoices.map((invoice) => (
              <Pressable
                key={invoice.id}
                style={s.card}
                onPress={() => navigation.navigate('InvoiceViewer', {
                  invoiceId: invoice.id,
                  invoiceNumber: invoice.invoice_number,
                })}
              >
                <View style={s.cardIcon}>
                  <ReceiptText size={20} color={C.brand} />
                </View>
                <View style={s.cardBody}>
                  <Text style={s.invoiceNum}>{invoice.invoice_number}</Text>
                  <Text style={s.jobName}>Requirement #{invoice.requirement_id}</Text>
                  <Text style={s.meta}>Total: Rs. {invoice.total_amount.toLocaleString('en-IN')}</Text>
                  <Text style={s.meta}>
                    Issued on {fmtDate(invoice.invoice_date)}
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
