import { useCallback, useState } from 'react';
import { ActivityIndicator, Alert, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Clock, CheckCircle2, XCircle } from 'lucide-react-native';
import { clientRequirementsService, type ClientRequirementDetail } from '../../../shared/services/client-requirements.service';
import {
  clientPaymentsService,
  type ClientPaymentRecord,
} from '../../../shared/services/client-payments.service';
import type { HomeStackParamList } from '../navigation/types';
import { EmptyBlock, LoadingBlock, ScreenHeader, StatusBadge } from './components';
import { C, clientStyles } from './clientStyles';

type PayCardVariant = 'advance' | 'active' | null;

function resolvePayCard(
  status: string,
  quote: { quoted_amount: number; advance_amount: number | null; payment_model: string } | null,
): PayCardVariant {
  if (!quote) return null;
  if (quote.payment_model === 'client_pays_worker_directly') return null;
  if (status === 'approved' && (quote.advance_amount ?? 0) > 0) return 'advance';
  if (status === 'in_progress') return 'active';
  return null;
}

type Navigation = NativeStackNavigationProp<HomeStackParamList>;
type Route = RouteProp<HomeStackParamList, 'RequestDetail'>;

const timeline = ['submitted', 'under_review', 'quoted', 'approved', 'workers_assigned', 'in_progress', 'completed'];

export default function RequestDetailScreen() {
  const navigation = useNavigation<Navigation>();
  const route = useRoute<Route>();
  const insets = useSafeAreaInsets();
  const [detail, setDetail] = useState<ClientRequirementDetail | null>(null);
  const [payments, setPayments] = useState<ClientPaymentRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [quoteAction, setQuoteAction] = useState<'approve' | 'reject' | null>(null);
  const [cancelling, setCancelling] = useState(false);

  const todayStr = new Date().toISOString().split('T')[0];

  const load = useCallback(async () => {
    const [d, pmts] = await Promise.all([
      clientRequirementsService.getDetail(route.params.requirementId),
      clientPaymentsService.listForRequirement(route.params.requirementId).catch(() => [] as ClientPaymentRecord[]),
    ]);
    setDetail(d);
    setPayments(pmts);
  }, [route.params.requirementId]);

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

  const cancelRequest = () => {
    if (!detail || cancelling) return;
    Alert.alert(
      'Cancel this request?',
      'Please provide a reason (min 10 characters). This cannot be undone.',
      [
        { text: 'Go back', style: 'cancel' },
        {
          text: 'Cancel request',
          style: 'destructive',
          onPress: () => {
            Alert.prompt(
              'Cancellation reason',
              'Briefly describe why you are cancelling.',
              async (reason) => {
                if (!reason || reason.trim().length < 10) {
                  Alert.alert('Too short', 'Please provide at least 10 characters.');
                  return;
                }
                setCancelling(true);
                try {
                  await clientRequirementsService.cancel(detail.id, reason.trim());
                  await load();
                } catch {
                  Alert.alert('Could not cancel', 'Please try again.');
                } finally {
                  setCancelling(false);
                }
              },
              'plain-text',
            );
          },
        },
      ],
    );
  };

  const decideQuote = async (action: 'approve' | 'reject') => {
    if (!detail?.quote || quoteAction) return;

    const title = action === 'approve' ? 'Approve quote?' : 'Reject quote?';
    const message = action === 'approve'
      ? 'After approval, admin can assign workers to this request.'
      : 'This will reject the quote and send the request back to admin for review.';

    Alert.alert(title, message, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: action === 'approve' ? 'Approve' : 'Reject',
        style: action === 'approve' ? 'default' : 'destructive',
        onPress: async () => {
          setQuoteAction(action);
          try {
            await clientRequirementsService.decideQuote(detail.id, action);
            await load();
            if (action === 'approve') {
              Alert.alert('Quote approved', 'Your request is now approved. Pay the advance to confirm worker deployment.');
            } else {
              Alert.alert('Quote rejected', 'Admin has been notified and will send a revised quote shortly.');
            }
          } catch {
            Alert.alert('Could not update quote', 'Please try again.');
          } finally {
            setQuoteAction(null);
          }
        },
      },
    ]);
  };

  return (
    <View style={[clientStyles.root, { paddingTop: insets.top }]}>
      <ScrollView
        contentContainerStyle={clientStyles.content}
        refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={refresh} tintColor={C.brand} />}
      >
        <ScreenHeader title="Request detail" subtitle="Status, assigned workers, and job information." onBack={() => navigation.goBack()} />

        {isLoading ? (
          <LoadingBlock label="Loading request..." />
        ) : !detail ? (
          <EmptyBlock title="Request unavailable" detail="We could not load this request." />
        ) : (
          <>
            <View style={clientStyles.card}>
              <View style={styles.topRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.title}>{detail.category}</Text>
                  <Text style={clientStyles.subtitle}>{detail.city}, {detail.state}</Text>
                </View>
                <StatusBadge value={detail.status} />
              </View>
              <View style={styles.grid}>
                <Info label="Workers" value={String(detail.number_of_workers)} />
                <Info label="Start" value={formatDate(detail.start_date)} />
                <Info label="Duration" value={`${detail.duration_days} days`} />
                <Info label="Shift" value={detail.shift_details ?? 'Not specified'} />
              </View>
            </View>

            {/* ── Rejection notice ── */}
            {detail.status === 'rejected' && (
              <View style={styles.rejectionBanner}>
                <View style={styles.rejectionIconRow}>
                  <View style={styles.rejectionIconBox}>
                    <XCircle size={18} color={C.dangerText} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.rejectionHeading}>Request not approved</Text>
                    <Text style={styles.rejectionSubtext}>Our team reviewed your request and was unable to proceed.</Text>
                  </View>
                </View>
                {detail.rejection_reason ? (
                  <View style={styles.rejectionReasonBox}>
                    <Text style={styles.rejectionReasonLabel}>Reason given</Text>
                    <Text style={styles.rejectionReasonText}>{detail.rejection_reason}</Text>
                  </View>
                ) : null}
                <Pressable
                  style={({ pressed }) => [styles.resubmitBtn, pressed && { opacity: 0.85 }]}
                  onPress={() => navigation.navigate('CreateRequest')}
                >
                  <Text style={styles.resubmitBtnText}>Submit a new request →</Text>
                </Pressable>
              </View>
            )}

            {/* ── Cancellation notice ── */}
            {detail.status === 'cancelled' && detail.cancellation_reason ? (
              <View style={styles.cancellationBanner}>
                <View style={styles.rejectionIconRow}>
                  <View style={styles.cancellationIconBox}>
                    <XCircle size={18} color={C.warningText} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.cancellationHeading}>Request cancelled</Text>
                    <Text style={styles.cancellationSubtext}>This request was cancelled before workers were assigned.</Text>
                  </View>
                </View>
                <View style={styles.cancellationReasonBox}>
                  <Text style={styles.cancellationReasonLabel}>Cancellation reason</Text>
                  <Text style={styles.cancellationReasonText}>{detail.cancellation_reason}</Text>
                </View>
              </View>
            ) : null}

            <View style={clientStyles.card}>
              <Text style={clientStyles.sectionLabel}>Status timeline</Text>
              <View style={styles.timeline}>
                {timeline.map((step) => {
                  const active = timeline.indexOf(step) <= Math.max(timeline.indexOf(detail.status), 0);
                  return (
                    <View key={step} style={styles.timelineRow}>
                      <View style={[styles.dot, active && styles.dotActive]} />
                      <Text style={[styles.timelineText, active && styles.timelineTextActive]}>{step.replace(/_/g, ' ')}</Text>
                    </View>
                  );
                })}
              </View>
            </View>

            {detail.quote ? (
              <View style={clientStyles.card}>
                <View style={styles.topRow}>
                  <View style={{ flex: 1 }}>
                    <Text style={clientStyles.sectionLabel}>Quote</Text>
                    <Text style={styles.quoteAmount}>Rs. {formatAmount(detail.quote.quoted_amount)}</Text>
                  </View>
                  <StatusBadge value={detail.quote.status} />
                </View>
                <View style={styles.grid}>
                  <Info label="Rate" value={detail.quote.rate_per_worker ? `Rs. ${formatAmount(detail.quote.rate_per_worker)} / worker / day` : 'Not specified'} />
                  <Info label="Worker days" value={detail.quote.total_worker_days ? String(detail.quote.total_worker_days) : 'Not specified'} />
                  <Info label="Advance" value={detail.quote.advance_amount ? `Rs. ${formatAmount(detail.quote.advance_amount)}` : 'Not required'} />
                  <Info label="Payment" value={formatPaymentModel(detail.quote.payment_model)} />
                  <Info label="Valid Until" value={detail.quote.valid_until ? formatDate(detail.quote.valid_until) : 'Not specified'} />
                </View>
                {detail.quote.terms_notes ? <Text style={styles.notes}>{detail.quote.terms_notes}</Text> : null}
                {detail.quote.status === 'sent' ? (
                  detail.quote.valid_until && detail.quote.valid_until < todayStr ? (
                    <View style={styles.expiredBanner}>
                      <Text style={styles.expiredText}>
                        This quote expired on {formatDate(detail.quote.valid_until)}. Admin will send a revised quote shortly.
                      </Text>
                    </View>
                  ) : (
                    <View style={styles.quoteActions}>
                      <Pressable
                        style={[styles.quoteButton, styles.rejectButton, quoteAction !== null && styles.disabledButton]}
                        onPress={() => decideQuote('reject')}
                        disabled={quoteAction !== null}
                      >
                        {quoteAction === 'reject' ? <ActivityIndicator size="small" color={C.ink} /> : <Text style={styles.rejectText}>Reject quote</Text>}
                      </Pressable>
                      <Pressable
                        style={[styles.quoteButton, styles.approveButton, quoteAction !== null && styles.disabledButton]}
                        onPress={() => decideQuote('approve')}
                        disabled={quoteAction !== null}
                      >
                        {quoteAction === 'approve' ? <ActivityIndicator size="small" color="#FFFFFF" /> : <Text style={styles.approveText}>Approve quote</Text>}
                      </Pressable>
                    </View>
                  )
                ) : null}
              </View>
            ) : (
              <View style={clientStyles.card}>
                <Text style={clientStyles.sectionLabel}>Quote</Text>
                <Text style={styles.body}>
                  Admin is reviewing this request. The quote and approval buttons will appear here after review.
                </Text>
              </View>
            )}

            <View style={clientStyles.card}>
              <Text style={clientStyles.sectionLabel}>Location and worker provisions</Text>
              <Text style={styles.body}>{detail.work_location}</Text>
              <Text style={styles.body}>Food at site: {detail.food_required ? 'Provided for workers' : 'Not provided'}</Text>
              <Text style={styles.body}>Accommodation: {detail.accommodation_required ? 'Provided for workers' : 'Not provided'}</Text>
              {detail.notes ? <Text style={styles.notes}>{detail.notes}</Text> : null}
            </View>

            <View style={clientStyles.card}>
              <View style={styles.sectionHeadRow}>
                <Text style={clientStyles.sectionLabel}>Assigned workers</Text>
                {detail.assignments.length > 0 ? (
                  <Pressable style={styles.viewAllBtn} onPress={() => navigation.navigate('AssignedWorkers', { requirementId: detail.id })}>
                    <Text style={styles.viewAllText}>View all workers →</Text>
                  </Pressable>
                ) : null}
              </View>
              {detail.assignments.length === 0 ? (
                <Text style={[clientStyles.subtitle, { marginTop: 10 }]}>Workers will appear here after admin assignment.</Text>
              ) : (
                detail.assignments.slice(0, 3).map((assignment) => (
                  <View key={assignment.id} style={styles.workerRow}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.workerName}>{assignment.worker_name}</Text>
                      <Text style={clientStyles.subtitle}>{assignment.assigned_shift ?? 'Shift not set'}</Text>
                    </View>
                    <StatusBadge value={assignment.status} />
                  </View>
                ))
              )}
              {detail.assignments.length > 3 ? (
                <Text style={[clientStyles.subtitle, { marginTop: 6 }]}>+{detail.assignments.length - 3} more workers</Text>
              ) : null}
            </View>

            <View style={clientStyles.card}>
              <Text style={clientStyles.sectionLabel}>Attendance status</Text>
              {detail.assignments.length === 0 ? (
                <Text style={[clientStyles.subtitle, { marginTop: 10 }]}>Attendance appears after workers are assigned.</Text>
              ) : (
                detail.assignments.map((assignment) => {
                  const latestAttendance = assignment.attendance[0] ?? null;
                  return (
                    <View key={`attendance-${assignment.id}`} style={styles.attendanceRow}>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.workerName}>{assignment.worker_name}</Text>
                        <Text style={clientStyles.subtitle}>
                          {latestAttendance
                            ? `${formatDate(latestAttendance.attendance_date)} · ${formatAttendanceLine(latestAttendance)}`
                            : 'No check-in yet'}
                        </Text>
                      </View>
                      <StatusBadge value={latestAttendance?.status ?? assignment.status} />
                    </View>
                  );
                })
              )}
            </View>

            {/* ── Assigned info card ── */}
            {detail.status === 'assigned' && (
              <View style={[clientStyles.card, styles.assignedCard]}>
                <CheckCircle2 size={18} color={C.successText} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.assignedTitle}>Advance confirmed — workers being arranged</Text>
                  <Text style={clientStyles.subtitle}>
                    Your advance payment was verified. Admin is finalising worker deployment.
                  </Text>
                </View>
              </View>
            )}

            {/* ── Payment card — context-aware per status ── */}
            {(() => {
              const variant = resolvePayCard(detail.status, detail.quote);
              if (!variant || !detail.quote) return null;

              const isAdvance = variant === 'advance';
              const totalPaid = payments
                .filter((p) => p.payment_status === 'paid')
                .reduce((s, p) => s + p.amount, 0);
              // For advance: show advance_amount. For active: show remaining balance.
              const displayAmount = isAdvance
                ? (detail.quote.advance_amount ?? 0)
                : Math.max(0, detail.quote.quoted_amount - totalPaid);

              // Full payment complete — all collected amounts cover the quoted total
              if (!isAdvance && totalPaid >= detail.quote.quoted_amount) {
                return (
                  <View style={[clientStyles.card, styles.advancePendingCard, { borderColor: C.successText }]}>
                    <View style={styles.advancePendingRow}>
                      <CheckCircle2 size={16} color={C.successText} />
                      <Text style={[styles.advancePendingTitle, { color: C.successText }]}>
                        Payment complete
                      </Text>
                    </View>
                    <Text style={clientStyles.subtitle}>
                      ₹{formatAmount(detail.quote.quoted_amount)} received. This request has been marked as completed.
                    </Text>
                  </View>
                );
              }

              // If advance is already submitted/paid, show verification banner instead of pay card
              if (isAdvance && payments.some((p) => p.payment_status === 'pending' || p.payment_status === 'paid')) {
                const hasPaid = payments.some((p) => p.payment_status === 'paid');
                return (
                  <View style={[clientStyles.card, styles.advancePendingCard]}>
                    <View style={styles.advancePendingRow}>
                      <Clock size={16} color={C.warningText} />
                      <Text style={styles.advancePendingTitle}>
                        {hasPaid ? 'Advance received — pending admin confirmation' : 'Advance submitted — awaiting verification'}
                      </Text>
                    </View>
                    <Text style={clientStyles.subtitle}>
                      ₹{formatAmount(displayAmount)} · Admin will verify your payment and move this request to
                      deployment. This usually takes a few hours.
                    </Text>
                  </View>
                );
              }

              const cardLabel = isAdvance ? 'Advance Payment' : 'Invoice & Payment';
              const subtitle = isAdvance
                ? 'Required to confirm worker deployment'
                : 'Workers are active — settle to stay on track';
              const btnLabel = isAdvance
                ? `Pay advance ₹${formatAmount(displayAmount)} →`
                : `Pay ₹${formatAmount(displayAmount)} →`;

              return (
                <View style={clientStyles.card}>
                  <Text style={clientStyles.sectionLabel}>{cardLabel}</Text>
                  <View style={styles.paymentRow}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.paymentAmount}>
                        ₹{formatAmount(displayAmount)}
                      </Text>
                      <Text style={clientStyles.subtitle}>{subtitle}</Text>
                    </View>
                    <StatusBadge value={isAdvance ? 'advance_due' : 'pending'} />
                  </View>
                  <Pressable
                    style={({ pressed }) => [styles.payButton, pressed && { opacity: 0.85 }]}
                    onPress={() =>
                      navigation.navigate('InvoiceDetail', {
                        invoiceId: detail.id,
                        invoiceTotal: detail.quote?.quoted_amount ?? 0,
                        advanceAmount: detail.quote?.advance_amount ?? null,
                        jobName: detail.category,
                        location: `${detail.city}, ${detail.state}`,
                        workerCount: detail.number_of_workers,
                        durationDays: detail.duration_days,
                        paymentMode: isAdvance ? 'advance' : 'full',
                      })
                    }
                  >
                    <Text style={styles.payButtonText}>{btnLabel}</Text>
                  </Pressable>
                </View>
              );
            })()}

            {/* ── Cancel request (submitted or quoted only) ── */}
            {(detail.status === 'submitted' || detail.status === 'quoted') && (
              <View style={clientStyles.card}>
                <Text style={clientStyles.sectionLabel}>Cancel this request</Text>
                <Text style={[styles.body, { marginTop: 4 }]}>
                  You can cancel this request while it is still under review or quoted.
                  Once workers are assigned, cancellation must go through admin.
                </Text>
                <Pressable
                  style={({ pressed }) => [styles.cancelBtn, pressed && { opacity: 0.75 }, cancelling && styles.disabledButton]}
                  onPress={cancelRequest}
                  disabled={cancelling}
                >
                  {cancelling
                    ? <ActivityIndicator size="small" color={C.ink} />
                    : <Text style={styles.cancelBtnText}>Cancel request</Text>
                  }
                </Pressable>
              </View>
            )}

            {/* ── Rate this job (completed only) ── */}
            {detail.status === 'completed' && (
              <View style={clientStyles.card}>
                <Text style={clientStyles.sectionLabel}>Rate this job</Text>
                <Text style={[styles.body, { marginTop: 4 }]}>
                  How was your overall experience? Your feedback helps us improve.
                </Text>
                <Pressable
                  style={({ pressed }) => [styles.rateBtn, pressed && { opacity: 0.85 }]}
                  onPress={() => navigation.navigate('RateRequirement', { requirementId: detail.id, category: detail.category })}
                >
                  <Text style={styles.rateBtnText}>Leave a rating →</Text>
                </Pressable>
              </View>
            )}

            {/* ── Raise a dispute (completed only) ── */}
            {detail.status === 'completed' && (
              <View style={clientStyles.card}>
                <Text style={clientStyles.sectionLabel}>Dispute</Text>
                <Text style={[styles.body, { marginTop: 4 }]}>
                  Have an issue with attendance, quality, or billing? Raise a formal dispute for review.
                </Text>
                <Pressable
                  style={({ pressed }) => [styles.disputeBtn, pressed && { opacity: 0.85 }]}
                  onPress={() => navigation.navigate('RaiseDispute', { requirementId: detail.id })}
                >
                  <Text style={styles.disputeBtnText}>Raise a dispute →</Text>
                </Pressable>
              </View>
            )}
          </>
        )}
      </ScrollView>
    </View>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.info}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value));
}

function formatAmount(value: number) {
  return new Intl.NumberFormat('en-IN').format(value);
}

function formatPaymentModel(value: string) {
  return value.replace(/_/g, ' ');
}

function formatAttendanceLine(value: {
  check_in_time: string | null;
  check_out_time: string | null;
}) {
  if (value.check_in_time && value.check_out_time) {
    return `In ${formatTime(value.check_in_time)} · Out ${formatTime(value.check_out_time)}`;
  }

  if (value.check_in_time) {
    return `Checked in ${formatTime(value.check_in_time)}`;
  }

  return 'No check-in yet';
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('en-IN', { hour: '2-digit', minute: '2-digit' }).format(new Date(value));
}

const styles = StyleSheet.create({
  topRow: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'flex-start',
  },
  title: {
    color: C.ink,
    fontSize: 20,
    fontWeight: '600',
  },
  grid: {
    marginTop: 16,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  info: {
    width: '47%',
    backgroundColor: C.surfaceAlt,
    borderRadius: 10,
    padding: 12,
  },
  infoLabel: {
    color: C.muted,
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  infoValue: {
    color: C.ink,
    fontSize: 14,
    fontWeight: '600',
    marginTop: 6,
  },
  timeline: {
    marginTop: 14,
    gap: 12,
  },
  timelineRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  dot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: C.border,
  },
  dotActive: {
    backgroundColor: C.brand,
  },
  timelineText: {
    color: C.muted,
    fontSize: 14,
    textTransform: 'capitalize',
  },
  timelineTextActive: {
    color: C.ink,
    fontWeight: '600',
  },
  body: {
    color: C.body,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 10,
  },
  quoteAmount: {
    color: C.ink,
    fontSize: 24,
    fontWeight: '800',
    marginTop: 8,
  },
  quoteActions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 16,
  },
  quoteButton: {
    flex: 1,
    minHeight: 46,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 12,
  },
  approveButton: {
    backgroundColor: C.brand,
  },
  rejectButton: {
    backgroundColor: C.surfaceAlt,
    borderWidth: 1,
    borderColor: C.border,
  },
  disabledButton: {
    opacity: 0.65,
  },
  approveText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '800',
  },
  rejectText: {
    color: C.ink,
    fontSize: 14,
    fontWeight: '800',
  },
  notes: {
    color: C.muted,
    fontSize: 13,
    lineHeight: 20,
    marginTop: 10,
    fontStyle: 'italic',
  },
  sectionHeadRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  viewAllBtn: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  viewAllText: {
    color: C.brand,
    fontSize: 13,
    fontWeight: '600',
  },
  workerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: C.border,
    gap: 10,
  },
  attendanceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: C.border,
    gap: 10,
  },
  paymentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 14,
  },
  paymentAmount: {
    fontSize: 20,
    fontWeight: '700',
    color: C.ink,
    marginBottom: 2,
  },
  payButton: {
    backgroundColor: C.brand,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
  },
  payButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  workerName: {
    color: C.ink,
    fontSize: 14,
    fontWeight: '600',
  },
  // Advance pending banner
  advancePendingCard: {
    borderColor: C.warningText,
    borderWidth: 1,
    backgroundColor: C.warningBg,
    gap: 6,
  },
  advancePendingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  advancePendingTitle: {
    color: C.warningText,
    fontSize: 14,
    fontWeight: '700',
    flex: 1,
  },
  // Assigned info card
  assignedCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    borderColor: C.successText,
    borderWidth: 1,
    backgroundColor: C.successBg,
  },
  assignedTitle: {
    color: C.successText,
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 2,
  },
  rateBtn: {
    marginTop: 14,
    backgroundColor: C.brand,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center' as const,
  },
  rateBtnText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600' as const,
  },
  disputeBtn: {
    marginTop: 14,
    borderWidth: 1,
    borderColor: C.dangerText,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center' as const,
  },
  disputeBtnText: {
    color: C.dangerText,
    fontSize: 15,
    fontWeight: '600' as const,
  },  rejectionBanner: {
    backgroundColor: C.dangerBg,
    borderColor: '#FECACA',
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    gap: 14,
  },
  rejectionIconRow: {
    flexDirection: 'row' as const,
    alignItems: 'flex-start' as const,
    gap: 12,
  },
  rejectionIconBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#FEE2E2',
    alignItems: 'center' as const,
    justifyContent: 'center' as const,
  },
  rejectionHeading: {
    color: C.dangerText,
    fontSize: 15,
    fontWeight: '700' as const,
  },
  rejectionSubtext: {
    color: '#EF4444',
    fontSize: 13,
    marginTop: 2,
    lineHeight: 18,
  },
  rejectionReasonBox: {
    backgroundColor: '#FEF2F2',
    borderLeftWidth: 3,
    borderLeftColor: C.dangerText,
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  rejectionReasonLabel: {
    color: C.dangerText,
    fontSize: 10,
    fontWeight: '700' as const,
    textTransform: 'uppercase' as const,
    letterSpacing: 1,
    marginBottom: 4,
  },
  rejectionReasonText: {
    color: '#7F1D1D',
    fontSize: 14,
    lineHeight: 22,
    fontStyle: 'italic' as const,
  },
  resubmitBtn: {
    backgroundColor: C.dangerText,
    borderRadius: 10,
    paddingVertical: 11,
    paddingHorizontal: 16,
    alignItems: 'center' as const,
  },
  resubmitBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600' as const,
  },
  cancellationBanner: {
    backgroundColor: C.warningBg,
    borderColor: '#FDE68A',
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    gap: 14,
  },
  cancellationIconBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#FEF3C7',
    alignItems: 'center' as const,
    justifyContent: 'center' as const,
  },
  cancellationHeading: {
    color: C.warningText,
    fontSize: 15,
    fontWeight: '700' as const,
  },
  cancellationSubtext: {
    color: '#D97706',
    fontSize: 13,
    marginTop: 2,
    lineHeight: 18,
  },
  cancellationReasonBox: {
    backgroundColor: '#FFFBEB',
    borderLeftWidth: 3,
    borderLeftColor: C.warningText,
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  cancellationReasonLabel: {
    color: C.warningText,
    fontSize: 10,
    fontWeight: '700' as const,
    textTransform: 'uppercase' as const,
    letterSpacing: 1,
    marginBottom: 4,
  },
  cancellationReasonText: {
    color: '#78350F',
    fontSize: 14,
    lineHeight: 22,
    fontStyle: 'italic' as const,
  },  expiredBanner: {
    marginTop: 14,
    borderRadius: 10,
    padding: 14,
    backgroundColor: C.surfaceAlt,
    borderWidth: 1,
    borderColor: C.border,
  },
  expiredText: {
    color: C.muted,
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  cancelBtn: {
    marginTop: 14,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center' as const,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surfaceAlt,
  },
  cancelBtnText: {
    color: C.ink,
    fontSize: 15,
    fontWeight: '600' as const,
  },
});
