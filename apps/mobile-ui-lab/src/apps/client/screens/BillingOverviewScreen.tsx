import React from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { ChevronRight } from 'lucide-react-native';
import type { HomeStackParamList } from '../navigation/types';
import { C } from './clientStyles';

type Navigation = NativeStackNavigationProp<HomeStackParamList>;

type InvoiceStatus = 'paid' | 'partial' | 'pending' | 'overdue';

type MockInvoice = {
  id: number;
  jobName: string;
  location: string;
  workerCount: number;
  durationDays: number;
  totalAmount: number;
  paid: number;
  status: InvoiceStatus;
  utrRef?: string;
};

const MOCK_INVOICES: MockInvoice[] = [
  {
    id: 1,
    jobName: 'Cook',
    location: 'Velachery, Chennai',
    workerCount: 2,
    durationDays: 30,
    totalAmount: 15000,
    paid: 15000,
    status: 'paid',
    utrRef: 'UPI20240512A1B2C3',
  },
  {
    id: 2,
    jobName: 'Housekeeping',
    location: 'Adyar, Chennai',
    workerCount: 3,
    durationDays: 15,
    totalAmount: 15000,
    paid: 13000,
    status: 'partial',
  },
  {
    id: 3,
    jobName: 'Elder Care',
    location: 'Mylapore, Chennai',
    workerCount: 1,
    durationDays: 60,
    totalAmount: 18000,
    paid: 0,
    status: 'pending',
  },
  {
    id: 4,
    jobName: 'Night Nursing',
    location: 'T. Nagar, Chennai',
    workerCount: 2,
    durationDays: 7,
    totalAmount: 7000,
    paid: 0,
    status: 'overdue',
  },
];

const TOTAL_BILLED = MOCK_INVOICES.reduce((s, i) => s + i.totalAmount, 0);
const TOTAL_PAID = MOCK_INVOICES.reduce((s, i) => s + i.paid, 0);
const TOTAL_DUE = TOTAL_BILLED - TOTAL_PAID;

function fmt(n: number) {
  return `₹${n.toLocaleString('en-IN')}`;
}

const STATUS_META: Record<InvoiceStatus, { label: string; bg: string; color: string }> = {
  paid:    { label: 'Paid',             bg: C.successBg,  color: C.successText  },
  partial: { label: 'Partially paid',   bg: C.warningBg,  color: C.warningText  },
  pending: { label: 'Pending',          bg: C.infoBg,     color: C.infoText     },
  overdue: { label: 'Overdue',          bg: C.dangerBg,   color: C.dangerText   },
};

export default function BillingOverviewScreen() {
  const navigation = useNavigation<Navigation>();
  const insets = useSafeAreaInsets();

  return (
    <View style={s.root}>
      {/* ── Dark green hero ── */}
      <View style={[s.hero, { paddingTop: insets.top + 16 }]}>
        <Text style={s.heroEyebrow}>Billing Overview</Text>
        <Text style={s.heroLabel}>Outstanding Balance</Text>

        {/* Amber warning badge */}
        <View style={s.heroBadge}>
          <Text style={s.heroBadgeText}>{fmt(TOTAL_DUE)}</Text>
        </View>

        {/* Three stat chips */}
        <View style={s.statsRow}>
          <View style={s.statChip}>
            <Text style={s.statChipLabel}>Total billed</Text>
            <Text style={s.statChipValue}>{fmt(TOTAL_BILLED)}</Text>
          </View>
          <View style={s.statDivider} />
          <View style={s.statChip}>
            <Text style={s.statChipLabel}>Total paid</Text>
            <Text style={s.statChipValue}>{fmt(TOTAL_PAID)}</Text>
          </View>
          <View style={s.statDivider} />
          <View style={s.statChip}>
            <Text style={s.statChipLabel}>Due</Text>
            <Text style={[s.statChipValue, { color: C.warningBg }]}>{fmt(TOTAL_DUE)}</Text>
          </View>
        </View>
      </View>

      {/* ── Invoice list ── */}
      <ScrollView contentContainerStyle={s.list}>
        <Text style={s.sectionLabel}>Invoices</Text>

        {MOCK_INVOICES.map((invoice) => {
          const meta = STATUS_META[invoice.status];
          const due = invoice.totalAmount - invoice.paid;

          return (
            <Pressable
              key={invoice.id}
              style={({ pressed }) => [s.card, pressed && { opacity: 0.8 }]}
              onPress={() => navigation.navigate('InvoiceDetail', {
                invoiceId: invoice.id,
                invoiceTotal: invoice.totalAmount,
                advanceAmount: null,
                jobName: invoice.jobName,
                location: invoice.location,
                workerCount: invoice.workerCount,
                durationDays: invoice.durationDays,
                paymentMode: 'full',
              })}
            >
              {/* Top: job info + amount */}
              <View style={s.cardTop}>
                <View style={{ flex: 1 }}>
                  <Text style={s.cardTitle}>{invoice.jobName}</Text>
                  <Text style={s.cardMeta}>
                    {invoice.workerCount} workers · {invoice.durationDays} days · {invoice.location}
                  </Text>
                </View>
                <View style={s.cardAmountCol}>
                  <Text style={s.cardAmount}>{fmt(invoice.totalAmount)}</Text>
                  <ChevronRight size={14} color={C.muted} />
                </View>
              </View>

              {/* Bottom: status pill + references/actions */}
              <View style={s.cardBottom}>
                <View style={[s.pill, { backgroundColor: meta.bg }]}>
                  <Text style={[s.pillText, { color: meta.color }]}>{meta.label}</Text>
                </View>

                {/* Paid: show UTR reference */}
                {invoice.status === 'paid' && invoice.utrRef ? (
                  <Text style={s.utrText}>Ref: {invoice.utrRef}</Text>
                ) : null}

                {/* Partial: split pill + Pay now button */}
                {invoice.status === 'partial' ? (
                  <View style={s.splitRow}>
                    <View style={[s.pill, { backgroundColor: C.successBg }]}>
                      <Text style={[s.pillText, { color: C.successText }]}>
                        {fmt(invoice.paid)} paid · {fmt(due)} due
                      </Text>
                    </View>
                    <Pressable
                      style={({ pressed }) => [s.payNowBtn, pressed && { opacity: 0.8 }]}
                      onPress={() => navigation.navigate('InvoiceDetail', {
                        invoiceId: invoice.id,
                        invoiceTotal: invoice.totalAmount,
                        advanceAmount: null,
                        jobName: invoice.jobName,
                        location: invoice.location,
                        workerCount: invoice.workerCount,
                        durationDays: invoice.durationDays,
                        paymentMode: 'full',
                      })}
                    >
                      <Text style={s.payNowBtnText}>Pay now</Text>
                    </Pressable>
                  </View>
                ) : null}
              </View>
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.page },

  // Hero
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
    marginBottom: 4,
  },
  heroLabel: {
    color: 'rgba(255,255,255,0.75)',
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  heroBadge: {
    backgroundColor: C.warningBg,
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 10,
    alignSelf: 'flex-start',
    marginBottom: 20,
  },
  heroBadgeText: {
    color: C.warningText,
    fontSize: 30,
    fontWeight: '800',
  },

  // Stats row inside hero
  statsRow: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 12,
    paddingVertical: 12,
  },
  statChip: { flex: 1, alignItems: 'center', gap: 2 },
  statDivider: { width: 1, backgroundColor: 'rgba(255,255,255,0.15)' },
  statChipLabel: {
    color: 'rgba(255,255,255,0.55)',
    fontSize: 11,
    fontWeight: '500',
    textAlign: 'center',
  },
  statChipValue: { color: '#FFFFFF', fontSize: 14, fontWeight: '700' },

  // List
  list: { paddingHorizontal: 16, paddingTop: 16, paddingBottom: 28, gap: 12 },
  sectionLabel: {
    color: C.muted,
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 2,
  },

  // Invoice card
  card: {
    backgroundColor: C.surface,
    borderColor: C.border,
    borderWidth: 1,
    borderRadius: 14,
    padding: 16,
    gap: 12,
  },
  cardTop: { flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  cardTitle: { color: C.ink, fontSize: 15, fontWeight: '600' },
  cardMeta: { color: C.muted, fontSize: 12, marginTop: 2, lineHeight: 17 },
  cardAmountCol: { alignItems: 'flex-end', gap: 2 },
  cardAmount: { color: C.ink, fontSize: 17, fontWeight: '700' },

  cardBottom: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
  },

  pill: { borderRadius: 6, paddingHorizontal: 10, paddingVertical: 4 },
  pillText: { fontSize: 12, fontWeight: '600' },
  utrText: { color: C.muted, fontSize: 12, fontFamily: 'monospace' },

  splitRow: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  payNowBtn: {
    backgroundColor: C.brand,
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 7,
    marginLeft: 'auto',
  },
  payNowBtnText: { color: '#FFFFFF', fontSize: 13, fontWeight: '700' },
});
