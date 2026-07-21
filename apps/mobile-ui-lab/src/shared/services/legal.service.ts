import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type RequiredLegalDocument = {
  slug: string;
  title: string;
  url: string;
  accepted_at: string | null;
};

export type LegalAcceptanceStatus = {
  version: string;
  effective_date: string;
  role: 'client' | 'worker';
  is_current: boolean;
  required_documents: RequiredLegalDocument[];
};

export const legalService = {
  status: async (): Promise<LegalAcceptanceStatus> => {
    const response = await http.get<Envelope<LegalAcceptanceStatus>>('/me/legal-acceptances');
    return response.data.data;
  },

  accept: async (
    status: LegalAcceptanceStatus,
    source: 'client_mobile' | 'worker_mobile',
  ): Promise<LegalAcceptanceStatus> => {
    const response = await http.post<Envelope<LegalAcceptanceStatus>>('/me/legal-acceptances', {
      version: status.version,
      document_slugs: status.required_documents.map((document) => document.slug),
      source,
    });
    return response.data.data;
  },
};

