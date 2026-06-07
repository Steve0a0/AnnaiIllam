import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Linking,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';
import { CheckCircle2, ChevronLeft, Clock, X } from 'lucide-react-native';
import WebView from 'react-native-webview';
import type { WebViewMessageEvent } from 'react-native-webview';
import type { HomeStackParamList } from '../navigation/types';
import { C } from './clientStyles';
import {
  clientPaymentsService,
  type ClientPaymentRecord,
  type CreateOrderResponse,
} from '../../../shared/services/client-payments.service';

type Navigation = NativeStackNavigationProp<HomeStackParamList>;
type Route = RouteProp<HomeStackParamList, 'InvoiceDetail'>;

function fmt(n: number) {
  return `₹${n.toLocaleString('en-IN')}`;
}

function fmtDate(iso: string) {
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(iso));
}

function buildCheckoutHtml(order: CreateOrderResponse, jobName: string): string {
  return `<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <style>
    body { margin: 0; background: #f8f6f0; display: flex; align-items: center;
           justify-content: center; height: 100vh; font-family: sans-serif; }
    p { color: #203428; font-size: 16px; }
  </style>
</head>
<body>
  <p>Opening payment...</p>
  <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
  <script>
    var rzp = new Razorpay({
      key: ${JSON.stringify(order.razorpay_key_id)},
      amount: ${order.amount_paise},
      currency: ${JSON.stringify(order.currency)},
      name: 'Annai Illam',
      description: ${JSON.stringify(jobName)},
      order_id: ${JSON.stringify(order.gateway_order_id)},
      theme: { color: '#203428' },
      handler: function(r) {
        window.ReactNativeWebView.postMessage(JSON.stringify({
          status: 'success',
          razorpay_payment_id: r.razorpay_payment_id,
          razorpay_order_id: r.razorpay_order_id,
          razorpay_signature: r.razorpay_signature,
        }));
      },
      modal: {
        escape: false,
        ondismiss: function() {
          window.ReactNativeWebView.postMessage(JSON.stringify({ status: 'dismissed' }));
        }
      },
    });
    rzp.on('payment.failed', function(e) {
      window.ReactNativeWebView.postMessage(JSON.stringify({
        status: 'failed',
        error: (e.error && e.error.description) || 'Payment failed',
      }));
    });
    rzp.open();
  </script>
</body>
</html>`;
}

export default function InvoiceDetailScreen() {
  const navigation = useNavigation<Navigation>();
  const route = useRoute<Route>();
  const insets = useSafeAreaInsets();

  const {
    invoiceId: requirementId,
    invoiceTotal,
    advanceAmount,
    jobName,
    location,
    workerCount,
    durationDays,
    paymentMode,
  } = route.params;

  const [payments, setPayments] = useState<ClientPaymentRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreatingOrder, setIsCreatingOrder] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [checkoutOrder, setCheckoutOrder] = useState<CreateOrderResponse | null>(null);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await clientPaymentsService.listForRequirement(requirementId);
      setPayments(data);
    } catch {
      // leave empty
    } finally {
      setIsLoading(false);
    }
  }, [requirementId]);

  useEffect(() => { load(); }, [load]);

  const paidRecords = payments.filter((p) => p.payment_status === 'paid');
  const pendingRecords = payments.filter(
    (p) => p.payment_status === 'pending_verification',
  );
  const totalPaid = paidRecords.reduce((s, p) => s + p.amount, 0);
  const outstanding = Math.max(0, invoiceTotal - totalPaid);
  const amountDueNow = paymentMode === 'advance'
    ? Math.max(0, (advanceAmount ?? 0) - totalPaid)
    : outstanding;
  const isFullyPaid = outstanding === 0;
  const hasPendingVerification = pendingRecords.length > 0;

  const closeCheckout = () => {
    setIsCheckoutOpen(false);
    setCheckoutOrder(null);
  };

  const handlePayNow = async () => {
    setIsCreatingOrder(true);
    try {
      const order = await clientPaymentsService.createOrder({
        requirement_id: requirementId,
        amount: amountDueNow,
        payment_model: 'client_pays_company',
      });
      setCheckoutOrder(order);
      setIsCheckoutOpen(true);
    } catch {
      Alert.alert('Payment unavailable', 'Could not connect to the payment gateway. Please try again.');
    } finally {
      setIsCreatingOrder(false);
    }
  };

  const handleWebViewMessage = async (event: WebViewMessageEvent) => {
    let msg: {
      status: string;
      razorpay_payment_id?: string;
      razorpay_order_id?: string;
      razorpay_signature?: string;
      error?: string;
    };
    try {
      msg = JSON.parse(event.nativeEvent.data);
    } catch {
      return;
    }

    if (msg.status === 'dismissed') {
      closeCheckout();
      return;
    }

    if (msg.status === 'failed') {
      closeCheckout();
      Alert.alert('Payment failed', msg.error ?? 'Your payment could not be processed. Please try again.');
      return;
    }

    if (
      msg.status === 'success' &&
      msg.razorpay_payment_id &&
      msg.razorpay_order_id &&
      msg.razorpay_signature
    ) {
      setIsVerifying(true);
      try {
        await clientPaymentsService.verifyPayment({
          razorpay_order_id: msg.razorpay_order_id,
          razorpay_payment_id: msg.razorpay_payment_id,
          razorpay_signature: msg.razorpay_signature,
        });
        closeCheckout();
        navigation.navigate('PaymentConfirm', {
          invoiceId: requirementId,
          utrRef: msg.razorpay_payment_id,
          amount: amountDueNow,
          isGatewayPayment: true,
        });
      } catch {
        Alert.alert(
          'Verification failed',
          `Your payment was received but could not be verified automatically. Contact support with Payment ID: ${msg.razorpay_payment_id}`,
        );
      } finally {
        setIsVerifying(false);
      }
    }
  };

  // Open UPI app deep links (PhonePe, GPay, etc.) outside the WebView
  const handleShouldStartLoad = (req: { url: string }) => {
    const { url } = req;
    if (!url.startsWith('http') && !url.startsWith('about:')) {
      Linking.openURL(url).catch(() => {});
      return false;
    }
    return true;
  };

  return (
    <View style={s.root}>
      {/* ── Dark green hero ── */}
      <View style={[s.hero, { paddingTop: insets.top + 12 }]}>
        <Pressable style={s.backBtn} onPress={() => navigation.goBack()}>
          <ChevronLeft size={18} color="rgba(255,255,255,0.7)" />
          <Text style={s.backText}>Back</Text>
        </Pressable>

        <Text style={s.heroJobName}>{jobName}</Text>
        <Text style={s.heroMeta}>
          {workerCount} workers · {durationDays} days · {location}
        </Text>

        <Text style={s.heroAmount}>{fmt(isFullyPaid ? totalPaid : amountDueNow)}</Text>
        <Text style={s.heroLabel}>
          {isFullyPaid ? 'Total paid' : 'Amount due'}
        </Text>

        {isFullyPaid && (
          <View style={s.paidBadge}>
            <CheckCircle2 size={14} color={C.successText} />
            <Text style={s.paidBadgeText}>Fully paid</Text>
          </View>
        )}
      </View>

      {isLoading ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
          <ActivityIndicator color={C.brand} size="large" />
        </View>
      ) : (
        <ScrollView contentContainerStyle={s.body}>

          {/* ── Pending verification banner ── */}
          {hasPendingVerification && (
            <View style={s.pendingBanner}>
              <Clock size={16} color={C.warningText} />
              <Text style={s.pendingBannerText}>
                Payment reference submitted — admin is verifying your payment.
              </Text>
            </View>
          )}

          {/* ── Invoice breakdown card ── */}
          <View style={s.card}>
            <Text style={s.cardTitle}>Invoice breakdown</Text>

            <View style={s.breakRow}>
              <Text style={s.breakLabel}>Quote total</Text>
              <Text style={s.breakValue}>{fmt(invoiceTotal)}</Text>
            </View>

            {/* Advance-mode: show two-stage payment structure clearly */}
            {paymentMode === 'advance' && advanceAmount != null && paidRecords.length === 0 && (
              <>
                <View style={s.breakDivider} />
                <View style={s.breakRow}>
                  <Text style={[s.breakLabel, { color: C.brand, fontWeight: '600' }]}>Advance due now</Text>
                  <Text style={[s.breakValue, { color: C.brand, fontWeight: '700' }]}>{fmt(advanceAmount)}</Text>
                </View>
                <View style={s.breakRow}>
                  <Text style={[s.breakLabel, s.breakLabelSub]}>Balance after advance</Text>
                  <Text style={[s.breakValue, { color: C.muted }]}>{fmt(Math.max(0, invoiceTotal - advanceAmount))}</Text>
                </View>
              </>
            )}

            {/* Normal mode: show each paid record as a deduction */}
            {paidRecords.map((p) => (
              <View key={p.id} style={s.breakRow}>
                <View>
                  <Text style={[s.breakLabel, s.breakLabelSub]}>Paid on {fmtDate(p.paid_at ?? p.created_at)}</Text>
                  {p.reference_note ? (
                    <Text style={s.breakRef}>{p.reference_note}</Text>
                  ) : null}
                </View>
                <Text style={[s.breakValue, s.breakPaid]}>−{fmt(p.amount)}</Text>
              </View>
            ))}

            {pendingRecords.map((p) => (
              <View key={p.id} style={s.breakRow}>
                <Text style={[s.breakLabel, s.breakLabelSub]}>Awaiting admin verification</Text>
                <Text style={[s.breakValue, s.breakPending]}>−{fmt(p.amount)}</Text>
              </View>
            ))}

            {/* Only show outstanding divider/row when there are paid records (not in fresh-advance mode) */}
            {(paidRecords.length > 0 || paymentMode !== 'advance') && (
              <>
                <View style={s.breakDivider} />
                <View style={s.breakRow}>
                  <Text style={s.breakDueLabel}>Outstanding</Text>
                  <Text style={s.breakDueValue}>{fmt(outstanding)}</Text>
                </View>
              </>
            )}
          </View>

          {/* ── Pay button ── */}
          {!isFullyPaid && !hasPendingVerification && (
            <>
              <Pressable
                style={({ pressed }) => [
                  s.payBtn,
                  (isCreatingOrder || isVerifying) && s.payBtnDisabled,
                  pressed && { opacity: 0.85 },
                ]}
                onPress={handlePayNow}
                disabled={isCreatingOrder || isVerifying}
              >
                {isCreatingOrder || isVerifying ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={s.payBtnText}>Pay {fmt(amountDueNow)}</Text>
                )}
              </Pressable>
              <Text style={s.payNote}>Secured by Razorpay · UPI · Cards · Net Banking</Text>
            </>
          )}

          <View style={{ height: insets.bottom + 20 }} />
        </ScrollView>
      )}

      {/* ── Razorpay Checkout Modal ── */}
      <Modal
        visible={isCheckoutOpen}
        animationType="slide"
        onRequestClose={closeCheckout}
      >
        <View style={[s.modalRoot, { paddingTop: insets.top }]}>
          <View style={s.modalHeader}>
            <Text style={s.modalTitle}>Complete Payment</Text>
            <Pressable style={s.modalClose} onPress={closeCheckout}>
              <X size={20} color={C.ink} />
            </Pressable>
          </View>

          {checkoutOrder && (
            <WebView
              source={{ html: buildCheckoutHtml(checkoutOrder, jobName) }}
              style={{ flex: 1 }}
              javaScriptEnabled
              domStorageEnabled
              originWhitelist={['*']}
              mixedContentMode="always"
              onMessage={handleWebViewMessage}
              onShouldStartLoadWithRequest={handleShouldStartLoad}
            />
          )}

          {isVerifying && (
            <View style={s.verifyingOverlay}>
              <ActivityIndicator size="large" color={C.brand} />
              <Text style={s.verifyingText}>Confirming payment...</Text>
            </View>
          )}
        </View>
      </Modal>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.page },

  hero: {
    backgroundColor: C.brandDark,
    paddingHorizontal: 20,
    paddingBottom: 28,
  },
  backBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 16,
    alignSelf: 'flex-start',
  },
  backText: { color: 'rgba(255,255,255,0.7)', fontSize: 14, fontWeight: '500' },
  heroJobName: {
    color: '#FFFFFF',
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 4,
  },
  heroMeta: {
    color: 'rgba(255,255,255,0.6)',
    fontSize: 13,
    marginBottom: 12,
  },
  heroAmount: {
    color: '#FFFFFF',
    fontSize: 44,
    fontWeight: '800',
    letterSpacing: -1,
  },
  heroLabel: {
    color: 'rgba(255,255,255,0.65)',
    fontSize: 14,
    fontWeight: '500',
    marginTop: 2,
  },
  paidBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 10,
    alignSelf: 'flex-start',
    backgroundColor: C.successBg,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  paidBadgeText: { color: C.successText, fontWeight: '600', fontSize: 14 },

  body: { paddingHorizontal: 16, paddingTop: 20, paddingBottom: 16, gap: 14 },

  card: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 14,
    padding: 16,
    gap: 8,
  },

  pendingBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: C.warningBg,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  pendingBannerText: { color: C.warningText, fontSize: 13, fontWeight: '500', flex: 1 },

  cardTitle: { color: C.ink, fontSize: 15, fontWeight: '600', marginBottom: 4 },

  breakRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingVertical: 3,
    gap: 8,
  },
  breakLabel: { color: C.body, fontSize: 14 },
  breakLabelSub: { color: C.muted, fontSize: 13 },
  breakRef: { color: C.muted, fontSize: 11, fontFamily: 'monospace', marginTop: 1 },
  breakValue: { color: C.body, fontSize: 14, fontWeight: '600' },
  breakPaid: { color: C.successText },
  breakPending: { color: C.warningText },
  breakDivider: { height: 1, backgroundColor: C.border, marginVertical: 4 },
  breakDueLabel: { color: C.dangerText, fontWeight: '700', fontSize: 15 },
  breakDueValue: { color: C.dangerText, fontWeight: '700', fontSize: 15 },

  payBtn: {
    minHeight: 56,
    borderRadius: 14,
    backgroundColor: C.brand,
    alignItems: 'center',
    justifyContent: 'center',
  },
  payBtnDisabled: { opacity: 0.4 },
  payBtnText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
  payNote: {
    color: C.muted,
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },

  // Modal
  modalRoot: { flex: 1, backgroundColor: C.page },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  },
  modalTitle: { color: C.ink, fontSize: 16, fontWeight: '700' },
  modalClose: { padding: 4 },

  verifyingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255,255,255,0.92)',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  verifyingText: { color: C.ink, fontSize: 15, fontWeight: '600' },
});
