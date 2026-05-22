import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  BadgeCheck,
  CreditCard,
  Database,
  Eye,
  KeyRound,
  Lock,
  ScanFace,
  ShieldCheck,
  Trash2,
  User,
} from 'lucide-react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { WorkerAuthStackParamList } from '../../navigation/types';
import { C, authStyles as baseStyles } from './styles';

type Props = NativeStackScreenProps<WorkerAuthStackParamList, 'Consent'>;

const DATA_ITEMS = [
  {
    Icon: BadgeCheck,
    title: 'Government-issued ID',
    desc: 'Aadhaar, PAN, Driving Licence, or Passport — to verify your identity.',
  },
  {
    Icon: ScanFace,
    title: 'Selfie photo',
    desc: 'Matched against your ID to prevent fraud.',
  },
  {
    Icon: User,
    title: 'Personal & professional details',
    desc: 'Name, skills, experience and availability shown to clients and admins.',
  },
  {
    Icon: CreditCard,
    title: 'Payment details',
    desc: 'UPI ID or bank account for salary transfers. Stored encrypted (AES-256).',
  },
];

const PROTECTION_ITEMS = [
  { Icon: Lock,      text: 'All data is transmitted over HTTPS (TLS 1.3)' },
  { Icon: Database,  text: 'ID documents stored in encrypted cloud storage (India region)' },
  { Icon: KeyRound,  text: 'Payment details encrypted with AES-256 before saving to database' },
  { Icon: Eye,       text: 'ID images accessible to authorised admins only, with audit logging' },
  { Icon: Trash2,    text: 'Documents deleted after verification + 90-day retention window' },
];

const RIGHTS = [
  'Request a copy of your data at any time',
  'Correct or update inaccurate information',
  'Request deletion when your account is closed',
  'Raise a grievance with our Data Officer',
];

export default function ConsentScreen({ navigation }: Props) {
  const [agreed, setAgreed] = useState(false);

  return (
    <SafeAreaView style={baseStyles.root} edges={['top', 'bottom']}>
      <ScrollView
        style={baseStyles.flex}
        contentContainerStyle={local.scroll}
        showsVerticalScrollIndicator={false}
      >
        <View style={baseStyles.progressTrack}>
          <View style={[baseStyles.progressFill, { width: '16%' }]} />
        </View>

        <Text style={baseStyles.heading}>Your data is safe with us</Text>
        <Text style={baseStyles.subheading}>
          Under the Digital Personal Data Protection Act, 2023 (DPDPA), we are required to
          tell you exactly what we collect and why.
        </Text>

        {/* What we collect */}
        <Text style={local.sectionTitle}>What we collect</Text>
        {DATA_ITEMS.map((item) => (
          <View key={item.title} style={local.dataCard}>
            <View style={local.iconWrap}>
              <item.Icon size={18} color={C.brand} strokeWidth={1.8} />
            </View>
            <View style={local.dataText}>
              <Text style={local.dataTitle}>{item.title}</Text>
              <Text style={local.dataDesc}>{item.desc}</Text>
            </View>
          </View>
        ))}

        {/* How we protect it */}
        <Text style={local.sectionTitle}>How we protect it</Text>
        <View style={local.infoBox}>
          {PROTECTION_ITEMS.map((item) => (
            <View key={item.text} style={local.infoRow}>
              <item.Icon size={14} color={C.brand} strokeWidth={2} style={{ marginTop: 2 }} />
              <Text style={local.infoLine}>{item.text}</Text>
            </View>
          ))}
        </View>

        {/* Your rights */}
        <Text style={local.sectionTitle}>Your rights (DPDPA 2023)</Text>
        {RIGHTS.map((right) => (
          <View key={right} style={local.rightRow}>
            <ShieldCheck size={14} color={C.accent} strokeWidth={2} style={{ marginTop: 2 }} />
            <Text style={local.rightText}>{right}</Text>
          </View>
        ))}
        <Text style={local.grievance}>
          Grievance Officer: <Text style={local.grievanceLink}>privacy@annaiillam.in</Text>
        </Text>

        <View style={{ height: 28 }} />

        {/* Consent checkbox */}
        <Pressable style={local.checkRow} onPress={() => setAgreed((v) => !v)}>
          <View style={[local.checkbox, agreed && local.checkboxChecked]}>
            {agreed && <Text style={local.checkmark}>✓</Text>}
          </View>
          <Text style={local.checkLabel}>
            I have read and understood how my data will be collected, used, and protected.
          </Text>
        </Pressable>

        <View style={{ height: 20 }} />

        <Pressable
          style={({ pressed }) => [
            baseStyles.button,
            agreed && baseStyles.buttonPrimary,
            !agreed && baseStyles.buttonDisabled,
            pressed && agreed && baseStyles.buttonPressed,
          ]}
          onPress={() => agreed && navigation.navigate('VerifyIdentity')}
          disabled={!agreed}
        >
          <Text style={[baseStyles.buttonText, agreed && baseStyles.buttonTextPrimary]}>
            I agree &amp; continue
          </Text>
        </Pressable>

        <Text style={[baseStyles.terms, { marginTop: 16 }]}>
          By continuing you also accept our{' '}
          <Text style={{ color: C.accent }}>Privacy Policy</Text>
          {' '}and{' '}
          <Text style={{ color: C.accent }}>Terms of Use</Text>.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const local = StyleSheet.create({
  scroll: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 40,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: C.brand,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginTop: 24,
    marginBottom: 10,
  },
  dataCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    backgroundColor: C.surface,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.border,
    padding: 12,
    marginBottom: 8,
  },
  iconWrap: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: C.surfaceAlt,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dataText: {
    flex: 1,
  },
  dataTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: C.ink,
    marginBottom: 2,
  },
  dataDesc: {
    fontSize: 12,
    color: C.muted,
    lineHeight: 18,
  },
  infoBox: {
    backgroundColor: C.surface,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.border,
    padding: 14,
    gap: 10,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  infoLine: {
    fontSize: 12,
    color: C.ink,
    lineHeight: 18,
    flex: 1,
  },
  rightRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginBottom: 6,
  },
  rightText: {
    flex: 1,
    fontSize: 13,
    color: C.ink,
    lineHeight: 20,
  },
  grievance: {
    fontSize: 12,
    color: C.muted,
    marginTop: 10,
  },
  grievanceLink: {
    color: C.accent,
  },
  checkRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: C.border,
    backgroundColor: C.surface,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
    flexShrink: 0,
  },
  checkboxChecked: {
    backgroundColor: C.brand,
    borderColor: C.brand,
  },
  checkmark: {
    color: C.btnText,
    fontSize: 13,
    fontWeight: '700',
    lineHeight: 16,
  },
  checkLabel: {
    flex: 1,
    fontSize: 13,
    color: C.ink,
    lineHeight: 20,
  },
});
