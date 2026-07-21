export type AuthUser = {
  id: number;
  email: string;
  name: string | null;
  role: string;
  is_active?: boolean;
  permission_group?: string | null;
};

/** Backward-compat alias — prefer AuthUser in new code */
export type AdminUser = AuthUser;

export type AdminLoginPayload = {
  email: string;
  password: string;
};

export type AuthSuccessResponse = {
  success: boolean;
  message: string;
  data: {
    access_token: string;
    token_type: string;
    csrf_token: string;
    user: AuthUser;
  };
};

export type CsrfResponse = {
  success: boolean;
  message: string;
  data: { csrf_token: string };
};

export type MeResponse = {
  success: boolean;
  message: string;
  data: AuthUser;
};

/** Legacy alias kept for compatibility */
export type AuthTokenResponse = AuthSuccessResponse["data"];
