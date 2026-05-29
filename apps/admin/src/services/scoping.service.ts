import { http } from "@/lib/http";

export type ScopingAssignment = {
  assignment_id: number;
  client_profile_id: number;
  client_name: string | null;
  created_at: string;
};

type Envelope<T> = { success: boolean; message: string; data: T };

export const scopingService = {
  getAssignedClients: async (adminUserId: number): Promise<ScopingAssignment[]> => {
    const res = await http.get<Envelope<{ admin_user_id: number; assigned_clients: ScopingAssignment[]; total: number }>>(
      `/admin/scoping/admin/${adminUserId}`
    );
    return res.data.data.assigned_clients;
  },

  assignClient: async (adminUserId: number, clientProfileId: number): Promise<void> => {
    await http.post("/admin/scoping/assign", {
      admin_user_id: adminUserId,
      client_profile_id: clientProfileId,
    });
  },

  removeAssignment: async (assignmentId: number): Promise<void> => {
    await http.delete(`/admin/scoping/assign/${assignmentId}`);
  },
};
