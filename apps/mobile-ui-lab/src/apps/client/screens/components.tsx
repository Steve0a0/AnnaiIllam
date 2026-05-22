import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { ChevronLeft } from 'lucide-react-native';
import { C, clientStyles, getStatusColors } from './clientStyles';

export function StatusBadge({ value }: { value: string }) {
  const colors = getStatusColors(value);
  return (
    <View style={[styles.badge, { backgroundColor: colors.bg }]}>
      <Text style={[styles.badgeText, { color: colors.text }]}>{value.replace(/_/g, ' ')}</Text>
    </View>
  );
}

export function ScreenHeader({
  title,
  subtitle,
  onBack,
}: {
  title: string;
  subtitle?: string;
  onBack?: () => void;
}) {
  return (
    <View style={clientStyles.header}>
      <View style={{ flex: 1 }}>
        {onBack ? (
          <Pressable style={styles.backButton} onPress={onBack}>
            <ChevronLeft size={18} color={C.brand} />
            <Text style={clientStyles.ghostButtonText}>Back</Text>
          </Pressable>
        ) : null}
        <Text style={clientStyles.title}>{title}</Text>
        {subtitle ? <Text style={clientStyles.subtitle}>{subtitle}</Text> : null}
      </View>
    </View>
  );
}

export function LoadingBlock({ label = 'Loading...' }: { label?: string }) {
  return (
    <View style={[clientStyles.card, styles.centerBlock]}>
      <ActivityIndicator color={C.brand} />
      <Text style={clientStyles.subtitle}>{label}</Text>
    </View>
  );
}

export function EmptyBlock({ title, detail, action }: { title: string; detail: string; action?: { label: string; onPress: () => void } }) {
  return (
    <View style={[clientStyles.card, styles.centerBlock]}>
      <Text style={styles.emptyTitle}>{title}</Text>
      <Text style={[clientStyles.subtitle, { textAlign: 'center' }]}>{detail}</Text>
      {action ? (
        <Pressable
          style={({ pressed }) => [styles.actionBtn, pressed && { opacity: 0.7 }]}
          onPress={action.onPress}
          accessibilityLabel={action.label}
        >
          <Text style={styles.actionBtnText}>{action.label}</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 8,
  },
  centerBlock: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    minHeight: 160,
  },
  emptyTitle: {
    color: C.ink,
    fontSize: 16,
    fontWeight: '600',
  },
  actionBtn: {
    marginTop: 4,
    backgroundColor: '#203428',
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 24,
  },
  actionBtnText: {
    color: '#fffdf8',
    fontSize: 14,
    fontWeight: '600',
  },
});
