import { http } from "@/lib/http";
import type {
  AdminClientsResponse,
  AdminClientCreatePayload,
  AdminClientUpdatePayload,
  AdminClientMutationResponse,
  AdminClientDetailResponse,
  AdminWorkersResponse,
  AdminWorkerDetailResponse,
  AdminWorkerUpdatePayload,
  AdminWorkerUpdateResponse,
  WorkerAvailabilityToggleResponse,
  WorkerDocumentViewUrlResponse,
  WorkerReviewActionResponse,
  WorkerImportItem,
  WorkerImportResponse,
} from "@/types/people";

export const peopleService = {
  getClients: async (): Promise<AdminClientsResponse> => {
    const res = await http.get("/admin/people/clients");
    return res.data;
  },

  createClient: async (payload: AdminClientCreatePayload): Promise<AdminClientMutationResponse> => {
    const res = await http.post("/admin/people/clients", payload);
    return res.data;
  },

  updateClient: async (
    clientProfileId: number,
    payload: AdminClientUpdatePayload,
  ): Promise<AdminClientMutationResponse> => {
    const res = await http.patch(`/admin/people/clients/${clientProfileId}`, payload);
    return res.data;
  },

  deactivateClient: async (clientProfileId: number): Promise<{ success: boolean; message: string }> => {
    const res = await http.post(`/admin/people/clients/${clientProfileId}/deactivate`);
    return res.data;
  },

  getClientById: async (clientProfileId: number): Promise<AdminClientDetailResponse> => {
    const res = await http.get(`/admin/people/clients/${clientProfileId}`);
    return res.data;
  },

  getWorkers: async (): Promise<AdminWorkersResponse> => {
    const res = await http.get("/admin/people/workers");
    return res.data;
  },

  importWorkers: async (workers: WorkerImportItem[]): Promise<WorkerImportResponse> => {
    const res = await http.post("/admin/people/workers/import", { workers });
    return res.data;
  },

  approveWorker: async (userId: number): Promise<WorkerReviewActionResponse> => {
    const res = await http.post(`/admin/people/workers/${userId}/approve`);
    return res.data;
  },

  rejectWorker: async ({
    userId,
    reason,
  }: {
    userId: number;
    reason: string;
  }): Promise<WorkerReviewActionResponse> => {
    const res = await http.post(`/admin/people/workers/${userId}/reject`, { reason });
    return res.data;
  },

  getWorkerDocumentViewUrl: async (documentId: number): Promise<WorkerDocumentViewUrlResponse> => {
    const res = await http.get(`/admin/people/worker-documents/${documentId}/view-url`);
    return res.data;
  },

  getWorkerDocumentContent: async (documentId: number): Promise<Blob> => {
    const res = await http.get(`/admin/people/worker-documents/${documentId}/content`, {
      responseType: "blob",
    });
    return res.data;
  },

  setWorkerAvailability: async (
    userId: number,
    isAvailable: boolean,
  ): Promise<WorkerAvailabilityToggleResponse> => {
    const res = await http.patch(`/admin/people/workers/${userId}/availability`, {
      is_available: isAvailable,
    });
    return res.data;
  },

  getWorkerById: async (workerProfileId: number): Promise<AdminWorkerDetailResponse> => {
    const res = await http.get(`/admin/people/workers/${workerProfileId}`);
    return res.data;
  },

  updateWorker: async (
    workerProfileId: number,
    payload: AdminWorkerUpdatePayload,
  ): Promise<AdminWorkerUpdateResponse> => {
    const res = await http.patch(`/admin/people/workers/${workerProfileId}`, payload);
    return res.data;
  },
};
