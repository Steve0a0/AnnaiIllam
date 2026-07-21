import { useCallback, useEffect, useState, type ReactNode } from 'react';
import {
  ActivityIndicator,
  Alert,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Check, ExternalLink, FileCheck2, ShieldCheck } from 'lucide-react-native';

import { getApiError } from '../lib/get-api-error';
import { legalService, type LegalAcceptanceStatus } from '../services/legal.service';

type Props = {
  children: ReactNode;
  source: 'client_mobile' | 'worker_mobile';
};

const C = {
  page: '#F5F5F4', card: '#FFFFFF', ink: '#1C1917', muted: '#78716C', border: '#E7E5E4',
  brand: '#1A6640', brandDark: '#0D2E1E', brandSoft: '#D4F0E3', white: '#FFFFFF', danger: '#B91C1C',
};

export default function LegalAcceptanceGate({ children, source }: Props) {
  const [status, setStatus] = useState<LegalAcceptanceStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      setStatus(await legalService.status());
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  if (loading) {
    return <GateMessage><ActivityIndicator size="large" color={C.brand} /><Text style={styles.stateText}>Checking current legal documents...</Text></GateMessage>;
  }
  if (error || !status) {
    return (
      <GateMessage>
        <Text style={styles.stateTitle}>We could not load the legal documents</Text>
        <Text style={styles.stateText}>Check your connection and try again. Access stays paused until the current version can be confirmed.</Text>
        <Pressable accessibilityRole="button" style={styles.retryButton} onPress={load}><Text style={styles.retryText}>Try again</Text></Pressable>
      </GateMessage>
    );
  }
  if (status.is_current) return <>{children}</>;

  const accept = async () => {
    if (!agreed || submitting) return;
    setSubmitting(true);
    try {
      const next = await legalService.accept(status, source);
      setStatus(next);
    } catch (err) {
      Alert.alert('Could not record acceptance', getApiError(err, 'Please review the current documents and try again.'));
      await load();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.screen} edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.icon}><ShieldCheck size={28} color={C.brand} /></View>
        <Text style={styles.eyebrow}>Before you continue</Text>
        <Text style={styles.title}>Review our current terms</Text>
        <Text style={styles.body}>These documents explain how the service works and how your information is handled. Open each document before accepting.</Text>

        <View style={styles.versionRow}>
          <FileCheck2 size={18} color={C.brand} />
          <View><Text style={styles.versionTitle}>Version {status.version}</Text><Text style={styles.versionBody}>Effective {status.effective_date}</Text></View>
        </View>

        <View style={styles.documents}>
          {status.required_documents.map((document) => (
            <Pressable
              key={document.slug}
              accessibilityRole="link"
              accessibilityLabel={`Open ${document.title}`}
              style={({ pressed }) => [styles.documentRow, pressed && styles.pressed]}
              onPress={() => Linking.openURL(document.url)}
            >
              <Text style={styles.documentTitle}>{document.title}</Text>
              <ExternalLink size={20} color={C.brand} />
            </Pressable>
          ))}
        </View>

        <Pressable accessibilityRole="checkbox" accessibilityState={{ checked: agreed }} style={styles.checkRow} onPress={() => setAgreed((value) => !value)}>
          <View style={[styles.checkbox, agreed && styles.checkboxChecked]}>{agreed ? <Check size={17} color={C.white} strokeWidth={3} /> : null}</View>
          <Text style={styles.checkText}>I have read and accept all documents listed above for my {status.role} account.</Text>
        </Pressable>

        <Pressable accessibilityRole="button" disabled={!agreed || submitting} style={({ pressed }) => [styles.acceptButton, (!agreed || submitting) && styles.disabled, pressed && agreed && styles.pressed]} onPress={accept}>
          {submitting ? <ActivityIndicator color={C.white} /> : <Text style={styles.acceptText}>Accept and continue</Text>}
        </Pressable>
        <Text style={styles.auditCopy}>Your role, document version, and acceptance time will be recorded.</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function GateMessage({ children }: { children: ReactNode }) {
  return <SafeAreaView style={styles.screen}><View style={styles.state}>{children}</View></SafeAreaView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.page },
  content: { paddingHorizontal: 20, paddingTop: 28, paddingBottom: 36 },
  icon: { width: 56, height: 56, borderRadius: 18, backgroundColor: C.brandSoft, alignItems: 'center', justifyContent: 'center' },
  eyebrow: { marginTop: 24, color: C.brand, fontSize: 14, lineHeight: 20, fontWeight: '700' },
  title: { marginTop: 5, color: C.brandDark, fontSize: 28, lineHeight: 34, fontWeight: '700' },
  body: { marginTop: 12, color: C.muted, fontSize: 16, lineHeight: 24 },
  versionRow: { marginTop: 24, padding: 16, borderRadius: 14, backgroundColor: C.brandSoft, flexDirection: 'row', alignItems: 'center', gap: 12 },
  versionTitle: { color: C.brandDark, fontSize: 15, lineHeight: 21, fontWeight: '700' },
  versionBody: { marginTop: 2, color: C.brand, fontSize: 13, lineHeight: 18 },
  documents: { marginTop: 16, borderTopWidth: 1, borderTopColor: C.border },
  documentRow: { minHeight: 58, paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: C.border, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 16 },
  documentTitle: { flex: 1, color: C.ink, fontSize: 16, lineHeight: 22, fontWeight: '600' },
  checkRow: { marginTop: 26, flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  checkbox: { width: 24, height: 24, borderRadius: 6, borderWidth: 2, borderColor: C.muted, backgroundColor: C.card, alignItems: 'center', justifyContent: 'center' },
  checkboxChecked: { borderColor: C.brand, backgroundColor: C.brand },
  checkText: { flex: 1, color: C.ink, fontSize: 16, lineHeight: 24 },
  acceptButton: { minHeight: 56, marginTop: 24, borderRadius: 14, backgroundColor: C.brand, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 18 },
  acceptText: { color: C.white, fontSize: 16, fontWeight: '700' },
  auditCopy: { marginTop: 12, color: C.muted, textAlign: 'center', fontSize: 13, lineHeight: 19 },
  disabled: { opacity: 0.45 }, pressed: { opacity: 0.78 },
  state: { flex: 1, paddingHorizontal: 28, alignItems: 'center', justifyContent: 'center', gap: 14 },
  stateTitle: { color: C.brandDark, fontSize: 21, lineHeight: 28, fontWeight: '700', textAlign: 'center' },
  stateText: { color: C.muted, fontSize: 15, lineHeight: 23, textAlign: 'center' },
  retryButton: { minHeight: 52, minWidth: 150, marginTop: 8, borderRadius: 12, backgroundColor: C.brand, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 20 },
  retryText: { color: C.white, fontSize: 16, fontWeight: '700' },
});

