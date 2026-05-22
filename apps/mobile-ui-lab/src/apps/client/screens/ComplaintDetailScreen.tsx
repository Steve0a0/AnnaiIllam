import { useCallback, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useRoute } from '@react-navigation/native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';
import { AlertCircle, CheckCircle, Clock, MessageSquare } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { clientComplaintsService, type ClientComplaint } from '../../../shared/services/client-complaints.service';
import type { ComplaintsStackParamList } from '../navigation/types';
import { LoadingBlock, ScreenHeader, StatusBadge } from './components';
import { C, clientStyles } from './clientStyles';

type Navigation = NativeStackNavigationProp<ComplaintsStackParamList>;
type RouteProps = NativeStackScreenProps<ComplaintsStackParamList, 'ComplaintDetail'>['route'];

const SEVERITY_COLORS: Record<string, { bg: string; text: string }> = {
  low: { bg: '#D1FAE5', text: '#065F46' },
  medium: { bg: C.warningBg, text: C.warningText },
  high: { bg: C.dangerBg, text: C.dangerText },
  urgent: { bg: '#FEE2E2', text: '#7F1D1D' },
};

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'resolved') return <CheckCircle size={20} color="#059669" />;
  if (status === 'open') return <AlertCircle size={20} color={C.warningText} />;
  if (status === 'under_review') return <Clock size={20} color={C.infoText} />;
  return <MessageSquare size={20} color={C.muted} />;
}

export default function ComplaintDetailScreen() {
  const navigation = useNavigation<Navigation>();
  const route = useRoute<RouteProps>();
  const insets = useSafeAreaInsets();
  const { complaintId } = route.params;

  const [complaint, setComplaint] = useState<ClientComplaint | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);
      setError(null);
      clientComplaintsService
        .listAll()
        .then((all) => {
          if (!active) return;
          const found = all.find((c) => c.id === complaintId) ?? null;
          setComplaint(found);
          if (!found) setError('Complaint not found.');
        })
        .catch(() => active && setError('Failed to load complaint.'))
        .finally(() => active && setIsLoading(false));
      return () => { active = false; };
    }, [complaintId]),
  );

  const sev = complaint ? (SEVERITY_COLORS[complaint.severity] ?? { bg: '#F5F5F4', text: C.muted }) : null;

  return (
    <View style={[clientStyles.root, { paddingTop: insets.top }]}>
      <ScrollView contentContainerStyle={clientStyles.content}>
        <ScreenHeader title="Complaint Detail" onBack={() => navigation.goBack()} />

        {isLoading ? (
          <LoadingBlock label="Loading complaint..." />
        ) : error || !complaint ? (
          <View style={[clientStyles.card, styles.centerBlock]}>
            <AlertCircle size={24} color={C.dangerText} />
            <Text style={[clientStyles.subtitle, { textAlign: 'center' }]}>{error ?? 'Complaint not found.'}</Text>
          </View>
        ) : (
          <>
            {/* Status card */}
            <View style={clientStyles.card}>
              <View style={styles.statusHeader}>
                <StatusIcon status={complaint.status} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.typeText}>{complaint.complaint_type.replace(/_/g, ' ')}</Text>
                  <View style={styles.badgeRow}>
                    <StatusBadge value={complaint.status} />
                    {sev && (
                      <View style={[styles.severityBadge, { backgroundColor: sev.bg }]}>
                        <Text style={[styles.severityText, { color: sev.text }]}>{complaint.severity}</Text>
                      </View>
                    )}
                  </View>
                </View>
              </View>
            </View>

            {/* Details */}
            <View style={clientStyles.card}>
              <Text style={clientStyles.sectionLabel}>Details</Text>
              <View style={{ gap: 8, marginTop: 10 }}>
                <InfoRow label="Request" value={`#${complaint.requirement_id} · ${complaint.requirement_category}`} />
                {complaint.assignment_id ? <InfoRow label="Assignment" value={`#${complaint.assignment_id}`} /> : null}
                <InfoRow label="Raised on" value={new Date(complaint.created_at).toLocaleString()} />
              </View>
            </View>

            {/* Description */}
            <View style={clientStyles.card}>
              <Text style={clientStyles.sectionLabel}>Description</Text>
              <Text style={[clientStyles.subtitle, { marginTop: 8 }]}>{complaint.description}</Text>
            </View>

            {/* Resolution */}
            {complaint.resolution_notes ? (
              <View style={[clientStyles.card, { borderColor: '#059669' }]}>
                <Text style={[clientStyles.sectionLabel, { color: '#059669' }]}>Resolution</Text>
                <Text style={[clientStyles.subtitle, { marginTop: 8 }]}>{complaint.resolution_notes}</Text>
              </View>
            ) : null}
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  statusHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  typeText: {
    fontSize: 16,
    fontWeight: '700',
    color: C.ink,
    textTransform: 'capitalize',
    marginBottom: 6,
  },
  badgeRow: {
    flexDirection: 'row',
    gap: 6,
    alignItems: 'center',
  },
  severityBadge: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  severityText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 12,
  },
  infoLabel: {
    fontSize: 13,
    color: C.muted,
    fontWeight: '500',
  },
  infoValue: {
    fontSize: 13,
    color: C.ink,
    fontWeight: '600',
    textAlign: 'right',
    flex: 1,
  },
  centerBlock: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    minHeight: 160,
  },
});
