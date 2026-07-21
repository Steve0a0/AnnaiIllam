export const LEGAL_VERSION = '2026-07-21';
export const LEGAL_EFFECTIVE_DATE = '21 July 2026';
export const GRIEVANCE_EMAIL = 'privacy@annaiillam.in';

const configuredLegalBaseUrl = process.env.EXPO_PUBLIC_LEGAL_BASE_URL?.trim();
if (process.env.EXPO_PUBLIC_APP_ENV === 'production' && !configuredLegalBaseUrl) {
  throw new Error('EXPO_PUBLIC_LEGAL_BASE_URL must be configured for production builds.');
}
const LEGAL_BASE_URL = (configuredLegalBaseUrl || 'https://annaiillam.in/legal').replace(/\/$/, '');

export const LEGAL_DOCUMENTS = [
  { slug: 'privacy', title: 'Privacy Notice' },
  { slug: 'client-terms', title: 'Client Terms' },
  { slug: 'worker-terms', title: 'Worker Terms' },
  { slug: 'refund-cancellation', title: 'Refund and Cancellation Policy' },
  { slug: 'grievance', title: 'Grievance Process' },
] as const;

export function legalDocumentUrl(slug: string, version?: string) {
  return version ? `${LEGAL_BASE_URL}/${slug}/${version}` : `${LEGAL_BASE_URL}/${slug}`;
}
