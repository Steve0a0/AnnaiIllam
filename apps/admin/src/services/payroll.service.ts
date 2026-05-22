import { http } from "@/lib/http";
import type {
  PayrollRunCreatePayload,
  PayrollRunCreateResponse,
  PayrollRunDetailResponse,
  PayrollDeductionCreatePayload,
  PayrollDeductionCreateResponse,
  PayrollRunStatusUpdatePayload,
  PayrollRunStatusUpdateResponse,
} from "@/types/payroll";

export const payrollService = {
  createPayrollRun: async (
    payload: PayrollRunCreatePayload
  ): Promise<PayrollRunCreateResponse> => {
    const res = await http.post("/admin/payroll/runs", payload);
    return res.data;
  },

  getPayrollRunDetail: async (
    payrollRunId: number
  ): Promise<PayrollRunDetailResponse> => {
    const res = await http.get(`/admin/payroll/runs/${payrollRunId}`);
    return res.data;
  },

  generatePayrollRun: async (payrollRunId: number) => {
    const res = await http.post(
      `/admin/payroll/runs/${payrollRunId}/generate`
    );
    return res.data;
  },

  getPayrollRunItems: async (payrollRunId: number) => {
    const res = await http.get(`/admin/payroll/runs/${payrollRunId}/items`);
    return res.data;
  },

  addDeduction: async (
    payload: PayrollDeductionCreatePayload
  ): Promise<PayrollDeductionCreateResponse> => {
    const res = await http.post("/admin/payroll/deductions", payload);
    return res.data;
  },

  updatePayrollRunStatus: async (
    payrollRunId: number,
    payload: PayrollRunStatusUpdatePayload
  ): Promise<PayrollRunStatusUpdateResponse> => {
    const res = await http.patch(
      `/admin/payroll/runs/${payrollRunId}/status`,
      payload
    );
    return res.data;
  },
};
