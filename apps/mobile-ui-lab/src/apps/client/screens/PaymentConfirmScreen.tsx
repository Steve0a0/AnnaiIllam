import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';
import { CheckCircle } from 'lucide-react-native';
import type { HomeStackParamList } from '../navigation/types';
import { C } from './clientStyles';

type Navigation = NativeStackNavigationProp<HomeStackParamList>;
type Route = RouteProp<HomeStackParamList, 'PaymentConfirm'>;

function fmt(n: number) {
  return `₹${n.toLocaleString('en-IN')}`;
}

export default function PaymentConfirmScreen() {
  const navigation = useNavigation<Navigation>();
  const route = useRoute<Route>();
  const insets = useSafeAreaInsets();
  const { utrRef, amount, isGatewayPayment } = route.params;

  return (
    <View
      style={[
        s.root,
        { paddingTop: insets.top + 32, paddingBottom: insets.bottom + 24 },
      ]}
    >
      {/* Green check circle */}
      <View style={s.iconWrap}>
        <CheckCircle size={72} color={C.successText} strokeWidth={1.5} />
      </View>

      <Text style={s.heading}>
        {isGatewayPayment ? 'Payment successful!' : 'Payment recorded'}
      </Text>

      <Text style={s.subtext}>
        {isGatewayPayment
          ? 'Your payment has been confirmed. The invoice will be updated shortly.'
          : 'Admin will verify your payment and close the invoice — usually within a few hours.'}
      </Text>

      {/* Monospace reference box — screenshot-friendly */}
      <View style={s.refBox}>
        <View style={s.refRow}>
          <Text style={s.refKey}>{isGatewayPayment ? 'Payment ID' : 'UPI Ref  '} </Text>
          <Text style={s.refVal}>{utrRef}</Text>
        </View>
        <View style={s.refSep} />
        <View style={s.refRow}>
          <Text style={s.refKey}>Amount    </Text>
          <Text style={s.refVal}>{fmt(amount)}</Text>
        </View>
      </View>

      <Text style={s.screenshotNote}>Screenshot this screen for your records.</Text>

      {/* Back to request */}
      <View style={s.btnWrap}>
        <Pressable
          style={({ pressed }) => [s.btn, pressed && { opacity: 0.85 }]}
          onPress={() => navigation.popTo('RequestDetail', { requirementId: route.params.invoiceId })}
        >
          <Text style={s.btnText}>Back to request</Text>
        </Pressable>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: C.page,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 28,
  },
  iconWrap: { marginBottom: 20 },
  heading: {
    color: C.ink,
    fontSize: 26,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 10,
  },
  subtext: {
    color: C.muted,
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 28,
  },

  // Dark monospace box
  refBox: {
    backgroundColor: C.brandDark,
    borderRadius: 14,
    padding: 20,
    width: '100%',
    gap: 10,
  },
  refRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  refKey: {
    color: 'rgba(255,255,255,0.45)',
    fontFamily: 'monospace',
    fontSize: 13,
    width: 88,
  },
  refVal: {
    color: '#FFFFFF',
    fontFamily: 'monospace',
    fontSize: 13,
    fontWeight: '700',
    flex: 1,
  },
  refSep: {
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.12)',
  },

  screenshotNote: { color: C.muted, fontSize: 12, marginTop: 14, marginBottom: 36 },

  btnWrap: { width: '100%' },
  btn: {
    minHeight: 52,
    borderRadius: 12,
    backgroundColor: C.brand,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnText: { color: '#FFFFFF', fontSize: 15, fontWeight: '700' },
});
