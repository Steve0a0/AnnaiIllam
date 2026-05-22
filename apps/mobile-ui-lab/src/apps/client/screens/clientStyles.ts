import { StyleSheet } from 'react-native';

export const C = {
  page: '#F5F5F4',
  surface: '#FFFFFF',
  surfaceAlt: '#FAFAF9',
  ink: '#1C1917',
  body: '#44403C',
  muted: '#78716C',
  border: '#E7E5E4',
  brand: '#1A6640',
  brandDark: '#0D2E1E',
  brandSoft: '#EDFAF3',
  successBg: '#DCFCE7',
  successText: '#15803D',
  warningBg: '#FEF3C7',
  warningText: '#B45309',
  dangerBg: '#FEE2E2',
  dangerText: '#B91C1C',
  infoBg: '#DBEAFE',
  infoText: '#1D4ED8',
  purpleBg: '#EDE9FE',
  purpleText: '#6D28D9',
  tealBg: '#CFFAFE',
  tealText: '#0E7490',
};

export const clientStyles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: C.page,
  },
  content: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 28,
    gap: 16,
  },
  header: {
    minHeight: 56,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  eyebrow: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.2,
    color: C.muted,
    textTransform: 'uppercase',
  },
  title: {
    color: C.ink,
    fontSize: 24,
    lineHeight: 30,
    fontWeight: '600',
  },
  subtitle: {
    color: C.muted,
    fontSize: 13,
    lineHeight: 20,
  },
  card: {
    backgroundColor: C.surface,
    borderColor: C.border,
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
  },
  primaryButton: {
    minHeight: 52,
    borderRadius: 12,
    backgroundColor: C.brand,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 18,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  ghostButton: {
    minHeight: 44,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 12,
  },
  ghostButtonText: {
    color: C.brand,
    fontSize: 14,
    fontWeight: '600',
  },
  sectionLabel: {
    color: C.muted,
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },
  input: {
    minHeight: 52,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surface,
    paddingHorizontal: 14,
    color: C.ink,
    fontSize: 14,
  },
  textArea: {
    minHeight: 96,
    paddingTop: 12,
    textAlignVertical: 'top',
  },
  fieldLabel: {
    color: C.body,
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 6,
  },
});

export function getStatusColors(status: string) {
  switch (status) {
    case 'submitted':
      return { bg: C.infoBg, text: C.infoText };
    case 'under_review':
    case 'quoted':
      return { bg: C.purpleBg, text: C.purpleText };
    case 'approved':
    case 'completed':
    case 'accepted':
    case 'present':
      return { bg: C.successBg, text: C.successText };
    case 'assigned':
      return { bg: '#D1FAE5', text: '#065F46' };
    case 'in_progress':
    case 'active':
      return { bg: C.tealBg, text: C.tealText };
    case 'rejected':
    case 'cancelled':
    case 'declined':
    case 'absent':
      return { bg: C.dangerBg, text: C.dangerText };
    case 'late':
    case 'half_day':
      return { bg: C.warningBg, text: C.warningText };
    default:
      return { bg: '#F5F5F4', text: C.muted };
  }
}
