export type MobileUser = {
  id: number;
  phone?: string;
  email?: string;
  name?: string | null;
  role: 'client' | 'worker' | 'admin';
};

export type AuthTokens = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: MobileUser;
};

export type SocialAuthTokens = AuthTokens & {
  is_profile_complete: boolean;
};

export type MeResponse = MobileUser & {
  is_active: boolean;
  is_email_verified: boolean;
};
