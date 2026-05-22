import { useCallback, useState } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { AlertCircle, Plus } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { clientComplaintsService, type ClientComplaint } from '../../../shared/services/client-complaints.service';
import type { ComplaintsStackParamList } from '../navigation/types';
import { EmptyBlock, LoadingBlock, ScreenHeader, StatusBadge } from './components';
import { C, clientStyles } from './clientStyles';

type Navigation = NativeStackNavigationProp<ComplaintsStackParamList>;

const SEVERITY_COLORS: Record<string, { bg: string; text: string }> = {
  low: { bg: '#D1FAE5', text: '#065F46' },
  medium: { bg: C.warningBg, text: C.warningText },
  high: { bg: C.dangerBg, text: C.dangerText },
  urgent: { bg: '#FEE2E2', text: '#7F1D1D' },
};

export default function ComplaintsScreen() {
  const navigation = useNavigation<Navigation>();
  const insets = useSafeAreaInsets();
  const [items, setItems] = useState<ClientComplaint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    const data = await clientComplaintsService.listAll();
    setItems(data);
  }, []);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);
      load().catch((e) => active && setError(e?.response?.data?.message ?? 'Failed to load complaints')).finally(() => active && setIsLoading(false));
      return () => { active = false; };
    }, [load]),
  );

  const refresh = async () => {
    setIsRefreshing(true);
    await load().catch(() => {});
    setIsRefreshing(false);
  };

  return (
    <View style={[clientStyles.root, { paddingTop: insets.top }]}>
      <ScrollView
        contentContainerStyle={clientStyles.content}
        refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={refresh} tintColor={C.brand} />}
      >
        <ScreenHeader
          title="Complaints"
          subtitle="Track complaints raised on your job requests."
          onBack={() => navigation.goBack()}
        />

        <Pressable style={clientStyles.primaryButton} onPress={() => navigation.navigate('RaiseComplaint')}>
          <Plus size={18} color="#FFFFFF" />
          <Text style={clientStyles.primaryButtonText}>Raise a complaint</Text>
        </Pressable>

        {isLoading ? (
          <LoadingBlock label="Loading complaints..." />
        ) : error ? (
          <View style={[clientStyles.card, styles.centerBlock]}>
            <AlertCircle size={24} color={C.dangerText} />
            <Text style={[clientStyles.subtitle, { textAlign: 'center' }]}>{error}</Text>
          </View>
        ) : items.length === 0 ? (
          <EmptyBlock title="No complaints" detail="Complaints you raise will appear here." />
        ) : (
          items.map((item) => {
            const sev = SEVERITY_COLORS[item.severity] ?? { bg: '#F5F5F4', text: C.muted };
            return (
              <Pressable
                key={item.id}
                style={({ pressed }) => [clientStyles.card, pressed && { opacity: 0.7 }]}
                onPress={() => navigation.navigate('ComplaintDetail', { complaintId: item.id })}
              >
                <View style={styles.rowTop}>
                  <View style={styles.badgeRow}>
                    <StatusBadge value={item.status} />
                    <View style={[styles.severityBadge, { backgroundColor: sev.bg }]}>
                      <Text style={[styles.severityText, { color: sev.text }]}>{item.severity}</Text>
                    </View>
                  </View>
                  <Text style={styles.dateText}>{new Date(item.created_at).toLocaleDateString()}</Text>
                </View>
                <Text style={styles.typeText}>{item.complaint_type.replace(/_/g, ' ')}</Text>
                <Text style={clientStyles.subtitle} numberOfLines={2}>{item.description}</Text>
                <Text style={styles.reqLabel}>Request #{item.requirement_id} · {item.requirement_category}</Text>
              </Pressable>
            );
          })
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  rowTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
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
  dateText: {
    fontSize: 12,
    color: C.muted,
  },
  typeText: {
    fontSize: 15,
    fontWeight: '600',
    color: C.ink,
    textTransform: 'capitalize',
    marginBottom: 4,
  },
  reqLabel: {
    fontSize: 12,
    color: C.muted,
    marginTop: 8,
  },
  centerBlock: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    minHeight: 160,
  },
});
