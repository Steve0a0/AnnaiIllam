import { http } from "@/lib/http";
import type {
  BlacklistCreatePayload,
  BlacklistCreateResponse,
  BlacklistListResponse,
  BlacklistRemoveResponse,
} from "@/types/blacklist";

export const blacklistService = {
  getByClient: async (clientProfileId: number): Promise<BlacklistListResponse> => {
    const res = await http.get(`/admin/blacklist/client/${clientProfileId}`);
    return res.data;
  },

  blacklistWorker: async (
    payload: BlacklistCreatePayload
  ): Promise<BlacklistCreateResponse> => {
    const res = await http.post("/admin/blacklist", payload);
    return res.data;
  },

  removeFromBlacklist: async (
    blacklistId: number
  ): Promise<BlacklistRemoveResponse> => {
    const res = await http.delete(`/admin/blacklist/${blacklistId}`);
    return res.data;
  },
};
