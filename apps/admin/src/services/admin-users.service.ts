import { http } from "@/lib/http";

export type AdminUserRecord = {
  id: number;
  email: string;
  name: string | null;
  is_active: boolean;
  created_at: string;
};

export type CreateAdminUserPayload = {
  email: string;
  name: string;
  password: string;
};

export const adminUsersService = {
  list: async (): Promise<{ data: AdminUserRecord[] }> => {
    const res = await http.get("/admin/people/admin-users");
    return res.data;
  },

  create: async (payload: CreateAdminUserPayload): Promise<{ data: AdminUserRecord }> => {
    const res = await http.post("/admin/people/admin-users", payload);
    return res.data;
  },
};
