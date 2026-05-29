export type BlacklistEntry = {
  id: number;
  worker_profile_id: number;
  reason: string;
  blacklisted_by_user_id: number | null;
  created_at: string;
};

export type BlacklistListResponse = {
  success: boolean;
  message: string;
  data: {
    items: BlacklistEntry[];
    total: number;
  };
};

export type BlacklistCreatePayload = {
  client_profile_id: number;
  worker_profile_id: number;
  reason: string;
};

export type BlacklistCreateResponse = {
  success: boolean;
  message: string;
  data: BlacklistEntry & { client_profile_id: number };
};

export type BlacklistRemoveResponse = {
  success: boolean;
  message: string;
  data: { id: number };
};
