import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type OnboardingStatus = {
  onboarding_step: string | null;
  has_profile: boolean;
  verification_status: string | null;
};

export type UploadUrlResult = {
  upload_url: string | null;
  s3_key: string | null;
  expires_in_seconds?: number;
  dev_mode: boolean;
};

export type ProfileSubmitPayload = {
  full_name: string;
  skills: string[];
  experience_years: string;
  available_days: string[];
  available_shifts: string[];
  city: string;
  state: string;
  payment: {
    upi_id?: string | null;
    bank_account_number?: string | null;
    bank_ifsc?: string | null;
    bank_holder_name?: string | null;
  };
};

export const workerOnboardingService = {
  getStatus: async (): Promise<OnboardingStatus> => {
    const res = await http.get<Envelope<OnboardingStatus>>('/worker/onboarding/status');
    return res.data.data;
  },

  getUploadUrl: async (
    document_type: 'govt_id' | 'selfie',
    content_type: string,
  ): Promise<UploadUrlResult> => {
    const res = await http.post<Envelope<UploadUrlResult>>('/worker/onboarding/upload-url', {
      document_type,
      content_type,
    });
    return res.data.data;
  },

  uploadToStorage: async (presignedUrl: string, uri: string, contentType: string) => {
    const response = await fetch(uri);
    const blob = await response.blob();
    const uploadResponse = await fetch(presignedUrl, {
      method: 'PUT',
      headers: { 'Content-Type': contentType },
      body: blob,
    });
    if (!uploadResponse.ok) {
      const detail = await uploadResponse.text().catch(() => '');
      throw new Error(`Document upload failed (${uploadResponse.status}). ${detail}`);
    }
  },

  uploadLocalDocument: async (
    document_type: 'govt_id' | 'selfie',
    uri: string,
    name: string,
    contentType: string,
  ): Promise<string> => {
    const formData = new FormData();
    formData.append('file', {
      uri,
      name,
      type: contentType,
    } as unknown as Blob);
    const res = await http.post<Envelope<{ local_key: string }>>(
      `/worker/onboarding/local-upload?document_type=${document_type}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    return res.data.data.local_key;
  },

  submitProfile: async (payload: ProfileSubmitPayload): Promise<void> => {
    await http.post('/worker/onboarding/profile', payload);
  },

  submitIdentity: async (
    govt_id_key: string,
    selfie_key: string,
  ): Promise<void> => {
    await http.post('/worker/onboarding/identity', {
      govt_id_key,
      selfie_key,
    });
  },
};
