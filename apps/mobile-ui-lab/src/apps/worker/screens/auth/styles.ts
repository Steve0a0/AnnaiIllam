import { StyleSheet } from 'react-native';

export const C = {
  bg: '#f8f6f0',
  surface: '#fffdf8',
  surfaceAlt: '#f4f1e8',
  brand: '#203428',
  ink: '#17211a',
  muted: '#687267',
  border: '#ddd3be',
  accent: '#c96f3c',
  accentSoft: '#f0dfd3',
  btnText: '#fffdf8',
  success: '#527c2f',
} as const;

export const authStyles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: C.bg,
  },
  flex: {
    flex: 1,
  },
  page: {
    flex: 1,
    paddingHorizontal: 26,
    paddingTop: 18,
    paddingBottom: 24,
  },
  topIcon: {
    width: 48,
    height: 48,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surfaceAlt,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 26,
  },
  topIconText: {
    color: C.brand,
    fontSize: 13,
    fontWeight: '800',
  },
  heroIcon: {
    width: 86,
    height: 86,
    borderRadius: 43,
    borderWidth: 2,
    borderColor: C.brand,
    backgroundColor: C.surfaceAlt,
    alignSelf: 'center',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 20,
    marginBottom: 18,
  },
  heroIconText: {
    color: C.brand,
    fontSize: 24,
    fontWeight: '800',
  },
  heading: {
    color: C.ink,
    fontSize: 22,
    fontWeight: '800',
    letterSpacing: 0,
    marginBottom: 8,
  },
  centerHeading: {
    textAlign: 'center',
  },
  subheading: {
    color: C.muted,
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 28,
  },
  centerText: {
    textAlign: 'center',
  },
  spacer: {
    flex: 1,
  },
  inputShell: {
    minHeight: 50,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: C.border,
    backgroundColor: C.surface,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    marginBottom: 12,
  },
  inputFocused: {
    borderColor: C.brand,
    backgroundColor: '#fafaf8',
  },
  input: {
    flex: 1,
    color: C.ink,
    fontSize: 14,
    paddingVertical: 0,
  },
  prefix: {
    color: C.brand,
    fontSize: 14,
    fontWeight: '700',
    marginRight: 12,
  },
  button: {
    height: 52,
    borderRadius: 14,
    borderWidth: 1.2,
    borderColor: C.brand,
    backgroundColor: C.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonPrimary: {
    backgroundColor: C.brand,
  },
  buttonDisabled: {
    opacity: 0.45,
  },
  buttonPressed: {
    opacity: 0.82,
  },
  buttonText: {
    color: C.ink,
    fontSize: 14,
    fontWeight: '800',
  },
  buttonTextPrimary: {
    color: C.btnText,
  },
  terms: {
    color: C.muted,
    fontSize: 13,
    textAlign: 'center',
    marginTop: 14,
  },
  progressTrack: {
    height: 3,
    borderRadius: 10,
    backgroundColor: C.border,
    marginBottom: 16,
  },
  progressFill: {
    height: 3,
    borderRadius: 10,
    backgroundColor: C.brand,
  },
});