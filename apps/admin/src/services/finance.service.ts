import { http } from "@/lib/http";
import type {
  AdminClientPaymentsListResponse,
  ManualClientPaymentPayload,
  ManualClientPaymentResponse,
  ClientPaymentsListResponse,
  UpdateClientPaymentStatusPayload,
  UpdateClientPaymentStatusResponse,
  WorkerPayoutCreatePayload,
  WorkerPayoutCreateResponse,
  WorkerPayoutListResponse,
  WorkerPayoutStatusUpdatePayload,
  WorkerPayoutStatusUpdateResponse,
  PayrollQueueResponse,
  MarkRunPaidPayload,
  MarkRunPaidResponse,
} from "@/types/finance";

export const financeService = {
  /** List all client payments across all requirements (admin view). GET /admin/finance/client-payments */
  listAllClientPayments: async (
    status?: string,
  ): Promise<AdminClientPaymentsListResponse> => {
    const params = status ? { status } : {};
    const res = await http.get("/admin/finance/client-payments", { params });
    return res.data;
  },

  /** Update a client payment's status (confirm / reject). PATCH /admin/finance/client-payments/{id}/status */
  updateClientPaymentStatus: async (
    paymentId: number,
    payload: UpdateClientPaymentStatusPayload,
  ): Promise<UpdateClientPaymentStatusResponse> => {
    const res = await http.patch(
      `/admin/finance/client-payments/${paymentId}/status`,
      payload,
    );
    return res.data;
  },

  recordManualClientPayment: async (
    payload: ManualClientPaymentPayload,
  ): Promise<ManualClientPaymentResponse> => {
    const res = await http.post("/admin/finance/client-payments/manual", payload);
    return res.data;
  },

  getClientPaymentsByRequirement: async (
    requirementId: number,
  ): Promise<ClientPaymentsListResponse> => {
    const res = await http.get(
      `/admin/finance/client-payments/requirement/${requirementId}`,
    );
    return res.data;
  },

  createWorkerPayout: async (
    payload: WorkerPayoutCreatePayload,
  ): Promise<WorkerPayoutCreateResponse> => {
    const res = await http.post("/admin/finance/worker-payouts", payload);
    return res.data;
  },

  getWorkerPayoutsByPayrollItem: async (
    payrollItemId: number,
  ): Promise<WorkerPayoutListResponse> => {
    const res = await http.get(
      `/admin/finance/worker-payouts/payroll-item/${payrollItemId}`,
    );
    return res.data;
  },

  updateWorkerPayoutStatus: async (
    payoutId: number,
    payload: WorkerPayoutStatusUpdatePayload,
  ): Promise<WorkerPayoutStatusUpdateResponse> => {
    const res = await http.patch(
      `/admin/finance/worker-payouts/${payoutId}/status`,
      payload,
    );
    return res.data;
  },

  /** GET /admin/finance/payroll-queue — all non-draft payroll runs with items + worker names */
  getPayrollQueue: async (): Promise<PayrollQueueResponse> => {
    const res = await http.get("/admin/finance/payroll-queue");
    return res.data;
  },

  /** POST /admin/finance/payroll-queue/{id}/mark-paid — bulk transfer all items in a run */
  markRunPaid: async (
    payrollRunId: number,
    payload: MarkRunPaidPayload,
  ): Promise<MarkRunPaidResponse> => {
    const res = await http.post(
      `/admin/finance/payroll-queue/${payrollRunId}/mark-paid`,
      payload,
    );
    return res.data;
  },
};
