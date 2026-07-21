import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Linking,
  Pressable,
  RefreshControl,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { ChevronLeft, Download, ExternalLink, ShieldCheck, Trash2 } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { getApiError } from '../lib/get-api-error';
import { LEGAL_DOCUMENTS, legalDocumentUrl } from '../constants/legal';
import {
  privacyService,
  type PrivacyRequest,
  type PrivacyRequestType,
} from '../services/privacy.service';

const C = {
  page: '#F5F5F4',
  card: '#FFFFFF',
  ink: '#1C1917',
  body: '#44403C',
  muted: '#78716C',
  border: '#E7E5E4',
  brand: '#1A6640',
  brandSoft: '#D4F0E3',
  warningSoft: '#FEF3C7',
  warning: '#B45309',
  dangerSoft: '#FEE2E2',
  danger: '#B91C1C',
};

export default function PrivacySettingsScreen() {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const [requests, setRequests] = useState<PrivacyRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [submitting, setSubmitting] = useState<PrivacyRequestType | null>(null);
  const [sharingId, setSharingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setRequests(await privacyService.list());
  }, []);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setLoading(true);
      load()
        .catch((error) => active && Alert.alert('Could not load requests', getApiError(error)))
        .finally(() => active && setLoading(false));
      return () => { active = false; };
    }, [load]),
  );

  const openRequest = (type: PrivacyRequestType) =>
    requests.find(
      (item) =>
        item.request_type === type &&
        (item.status === 'pending' || item.status === 'in_review'),
    );

  const createRequest = async (type: PrivacyRequestType) => {
    setSubmitting(type);
    try {
      await privacyService.create(type);
      await load();
      Alert.alert(
        'Request submitted',
        type === 'deletion'
          ? 'Your account stays active while our privacy team reviews the request.'
          : 'We will show the download option here after the export is approved.',
      );
    } catch (error) {
      Alert.alert('Could not submit request', getApiError(error));
    } finally {
      setSubmitting(null);
    }
  };

  const confirmDeletion = () => {
    Alert.alert(
      'Request account deletion?',
      'After approval, you will lose access and your personal profile and identity documents will be removed. Invoices and payroll records may be retained where legally required.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Request deletion',
          style: 'destructive',
          onPress: () => createRequest('deletion'),
        },
      ],
    );
  };

  const shareExport = async (request: PrivacyRequest) => {
    setSharingId(request.id);
    try {
      const data = await privacyService.exportData(request.id);
      await Share.share({
        title: 'Annai Illam data export',
        message: JSON.stringify(data, null, 2),
      });
    } catch (error) {
      Alert.alert('Could not prepare export', getApiError(error));
    } finally {
      setSharingId(null);
    }
  };

  const latestExport = requests.find(
    (item) => item.request_type === 'export' && item.status === 'completed',
  );
  const exportOpen = openRequest('export');
  const deletionOpen = openRequest('deletion');

  return (
    <View style={[styles.screen, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Go back"
          hitSlop={12}
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <ChevronLeft size={22} color={C.ink} />
        </Pressable>
        <Text style={styles.headerTitle}>Privacy and data</Text>
        <View style={styles.backButton} />
      </View>

      <ScrollView
        contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 32 }]}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            tintColor={C.brand}
            onRefresh={() => {
              setRefreshing(true);
              load().finally(() => setRefreshing(false));
            }}
          />
        }
      >
        <View style={styles.intro}>
          <View style={styles.introIcon}>
            <ShieldCheck size={22} color={C.brand} />
          </View>
          <Text style={styles.introTitle}>You control your account data</Text>
          <Text style={styles.introBody}>
            Ask for a copy of your information or request account deletion. Requests are reviewed by an authorized administrator.
          </Text>
        </View>

        <View style={styles.legalSection}>
          <View style={styles.legalHeadingRow}>
            <Text style={styles.legalTitle}>Legal documents</Text>
            <Text style={styles.legalVersion}>Current version</Text>
          </View>
          {LEGAL_DOCUMENTS.map((document) => (
            <Pressable
              key={document.slug}
              accessibilityRole="link"
              accessibilityLabel={`Open ${document.title}`}
              style={({ pressed }) => [styles.legalRow, pressed && { opacity: 0.65 }]}
              onPress={() => Linking.openURL(legalDocumentUrl(document.slug))}
            >
              <Text style={styles.legalRowText}>{document.title}</Text>
              <ExternalLink size={18} color={C.brand} />
            </Pressable>
          ))}
        </View>

        {loading ? (
          <View style={styles.loading}>
            <ActivityIndicator color={C.brand} />
            <Text style={styles.mutedText}>Loading request status...</Text>
          </View>
        ) : (
          <>
            <View style={styles.card}>
              <View style={[styles.iconBox, { backgroundColor: C.brandSoft }]}>
                <Download size={20} color={C.brand} />
              </View>
              <Text style={styles.cardTitle}>Download your data</Text>
              <Text style={styles.cardBody}>
                Receive a JSON copy of your account, profile, and relevant work or billing records.
              </Text>
              {exportOpen ? (
                <StatusLine request={exportOpen} />
              ) : latestExport ? (
                <Pressable
                  accessibilityRole="button"
                  style={styles.primaryButton}
                  disabled={sharingId === latestExport.id}
                  onPress={() => shareExport(latestExport)}
                >
                  {sharingId === latestExport.id ? (
                    <ActivityIndicator color="#FFFFFF" />
                  ) : (
                    <Text style={styles.primaryButtonText}>Share data export</Text>
                  )}
                </Pressable>
              ) : (
                <Pressable
                  accessibilityRole="button"
                  style={styles.primaryButton}
                  disabled={submitting !== null}
                  onPress={() => createRequest('export')}
                >
                  {submitting === 'export' ? (
                    <ActivityIndicator color="#FFFFFF" />
                  ) : (
                    <Text style={styles.primaryButtonText}>Request data export</Text>
                  )}
                </Pressable>
              )}
            </View>

            <View style={styles.card}>
              <View style={[styles.iconBox, { backgroundColor: C.dangerSoft }]}>
                <Trash2 size={20} color={C.danger} />
              </View>
              <Text style={styles.cardTitle}>Delete your account</Text>
              <Text style={styles.cardBody}>
                Approved deletion removes login details, personal profile data, sessions, and identity documents. Records required for finance, payroll, fraud prevention, or law are retained with your identity removed where possible.
              </Text>
              {deletionOpen ? (
                <StatusLine request={deletionOpen} />
              ) : (
                <Pressable
                  accessibilityRole="button"
                  style={styles.deletionButton}
                  disabled={submitting !== null}
                  onPress={confirmDeletion}
                >
                  {submitting === 'deletion' ? (
                    <ActivityIndicator color={C.danger} />
                  ) : (
                    <Text style={styles.deletionButtonText}>Request account deletion</Text>
                  )}
                </Pressable>
              )}
            </View>

            {requests.some((item) => item.status === 'rejected') ? (
              <View style={styles.history}>
                <Text style={styles.historyTitle}>Previous outcomes</Text>
                {requests
                  .filter((item) => item.status === 'rejected')
                  .map((item) => (
                    <View key={item.id} style={styles.historyRow}>
                      <Text style={styles.historyType}>
                        {item.request_type === 'deletion' ? 'Account deletion' : 'Data export'}
                      </Text>
                      <Text style={styles.historyNote}>
                        {item.resolution_notes ?? 'Request was not approved.'}
                      </Text>
                    </View>
                  ))}
              </View>
            ) : null}
          </>
        )}
      </ScrollView>
    </View>
  );
}

function StatusLine({ request }: { request: PrivacyRequest }) {
  const inReview = request.status === 'in_review';
  return (
    <View style={[styles.statusLine, { backgroundColor: inReview ? '#EDE9FE' : C.warningSoft }]}>
      <View style={[styles.statusDot, { backgroundColor: inReview ? '#6D28D9' : C.warning }]} />
      <Text style={[styles.statusText, { color: inReview ? '#6D28D9' : C.warning }]}>
        {inReview ? 'Request is being reviewed' : 'Request submitted'}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.page },
  header: { height: 56, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  backButton: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  headerTitle: { fontSize: 17, fontWeight: '600', color: C.ink },
  content: { paddingHorizontal: 16, gap: 16 },
  intro: { alignItems: 'center', paddingHorizontal: 12, paddingVertical: 18 },
  introIcon: { width: 48, height: 48, borderRadius: 24, backgroundColor: C.brandSoft, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  introTitle: { fontSize: 20, fontWeight: '600', color: C.ink, textAlign: 'center' },
  introBody: { marginTop: 8, fontSize: 14, lineHeight: 21, color: C.muted, textAlign: 'center' },
  loading: { minHeight: 180, alignItems: 'center', justifyContent: 'center', gap: 12 },
  mutedText: { color: C.muted, fontSize: 14 },
  card: { backgroundColor: C.card, borderRadius: 16, borderWidth: 1, borderColor: C.border, padding: 18 },
  legalSection: { backgroundColor: C.card, borderRadius: 16, borderWidth: 1, borderColor: C.border, paddingHorizontal: 18, paddingTop: 18 },
  legalHeadingRow: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between', gap: 12, paddingBottom: 10 },
  legalTitle: { fontSize: 16, fontWeight: '600', color: C.ink },
  legalVersion: { fontSize: 12, color: C.muted },
  legalRow: { minHeight: 54, borderTopWidth: 1, borderTopColor: C.border, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 14 },
  legalRowText: { flex: 1, fontSize: 15, lineHeight: 21, fontWeight: '500', color: C.body },
  iconBox: { width: 40, height: 40, borderRadius: 12, alignItems: 'center', justifyContent: 'center', marginBottom: 14 },
  cardTitle: { fontSize: 16, fontWeight: '600', color: C.ink },
  cardBody: { marginTop: 6, fontSize: 13, lineHeight: 20, color: C.muted },
  primaryButton: { minHeight: 48, borderRadius: 12, marginTop: 18, paddingHorizontal: 16, backgroundColor: C.brand, alignItems: 'center', justifyContent: 'center' },
  primaryButtonText: { fontSize: 14, fontWeight: '600', color: '#FFFFFF' },
  deletionButton: { minHeight: 48, borderRadius: 12, marginTop: 18, paddingHorizontal: 16, borderWidth: 1, borderColor: '#FCA5A5', backgroundColor: '#FFF7F7', alignItems: 'center', justifyContent: 'center' },
  deletionButtonText: { fontSize: 14, fontWeight: '600', color: C.danger },
  statusLine: { minHeight: 44, borderRadius: 10, marginTop: 18, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', gap: 8 },
  statusDot: { width: 7, height: 7, borderRadius: 4 },
  statusText: { fontSize: 13, fontWeight: '600' },
  history: { backgroundColor: C.card, borderRadius: 16, borderWidth: 1, borderColor: C.border, padding: 18 },
  historyTitle: { fontSize: 14, fontWeight: '600', color: C.ink, marginBottom: 6 },
  historyRow: { paddingVertical: 10, borderTopWidth: 1, borderTopColor: C.border },
  historyType: { fontSize: 13, fontWeight: '600', color: C.body },
  historyNote: { marginTop: 3, fontSize: 12, lineHeight: 18, color: C.muted },
});
