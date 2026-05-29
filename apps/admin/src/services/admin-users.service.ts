import { http } from "@/lib/http";

export type PermissionGroup = "super_admin" | "ops_admin" | "finance_admin" | "viewer";

export const PERMISSION_GROUP_LABELS: Record<PermissionGroup, string> = {
  super_admin: "Super Admin",
  ops_admin: "Ops Admin",
  finance_admin: "Finance Admin",
  viewer: "Viewer",
};

export type AdminUserRecord = {
  id: number;
  email: string;
  name: string | null;
  is_active: boolean;
  created_at: string;
  permission_group: PermissionGroup | null;
};

export type CreateAdminUserPayload = {
  email: string;
  name: string;
  password: string;
  permission_group: PermissionGroup;
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
