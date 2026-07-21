import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation, useRoute, type RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { WebView } from 'react-native-webview';
import { ChevronLeft } from 'lucide-react-native';
import type { ProfileStackParamList } from '../navigation/types';
import { C } from './clientStyles';
import { clientInvoicesService } from '../../../shared/services/client-invoices.service';

type Navigation = NativeStackNavigationProp<ProfileStackParamList>;
type Route = RouteProp<ProfileStackParamList, 'InvoiceViewer'>;

export default function InvoiceViewerScreen() {
  const navigation = useNavigation<Navigation>();
  const { params } = useRoute<Route>();
  const insets = useSafeAreaInsets();

  const [html, setHtml] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const content = await clientInvoicesService.fetchDocumentHtml(params.invoiceId);
      setHtml(content);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [params.invoiceId]);

  useEffect(() => { load(); }, [load]);

  return (
    <View style={[s.root, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={s.header}>
        <Pressable style={s.backRow} onPress={() => navigation.goBack()}>
          <ChevronLeft size={18} color={C.ink} />
          <Text style={s.backText}>Invoices</Text>
        </Pressable>
        <Text style={s.title}>{params.invoiceNumber}</Text>
      </View>

      {loading ? (
        <View style={s.center}>
          <ActivityIndicator color={C.brand} size="large" />
          <Text style={s.loadingText}>Loading invoice…</Text>
        </View>
      ) : error ? (
        <View style={s.center}>
          <Text style={s.errorTitle}>Could not load invoice</Text>
          <Text style={s.errorBody}>Check your connection and try again.</Text>
          <Pressable style={s.retryBtn} onPress={load}>
            <Text style={s.retryText}>Retry</Text>
          </Pressable>
        </View>
      ) : (
        <WebView
          style={s.webview}
          originWhitelist={['*']}
          source={{ html: html! }}
          // Disable navigation — this is a static HTML document
          onShouldStartLoadWithRequest={(req) => req.navigationType === 'other'}
          showsVerticalScrollIndicator={false}
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.surface },

  header: {
    backgroundColor: C.surface,
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  },
  backRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 10 },
  backText: { color: C.body, fontSize: 14 },
  title: { color: C.ink, fontSize: 18, fontWeight: '700', letterSpacing: 0.4 },

  webview: { flex: 1, backgroundColor: '#F5F5F4' },

  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10, padding: 32 },
  loadingText: { color: C.muted, fontSize: 13, marginTop: 8 },
  errorTitle: { color: C.ink, fontSize: 16, fontWeight: '600' },
  errorBody: { color: C.muted, fontSize: 13, textAlign: 'center', lineHeight: 19 },
  retryBtn: {
    marginTop: 8,
    backgroundColor: C.brand,
    borderRadius: 10,
    paddingHorizontal: 24,
    paddingVertical: 10,
  },
  retryText: { color: '#fff', fontSize: 14, fontWeight: '600' },
});
