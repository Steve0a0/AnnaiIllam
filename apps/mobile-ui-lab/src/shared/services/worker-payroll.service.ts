import { http } from '../lib/http';
import { authStorage } from '../lib/auth-storage';

type Envelope<T> = { success: boolean; message: string; data: T };

export type WorkerPayrollItem = {
  id: number;
  payroll_run_id: number;
  assignment_id: number | null;
  gross_amount: number;
  total_deduction_amount: number;
  net_amount: number;
  attendance_days: number;
  half_days: number;
  absent_days: number;
  payment_status: string;
  period_start: string | null;
  period_end: string | null;
  run_status: string | null;
};

export type WorkerPayout = {
  id: number;
  payroll_item_id: number;
  amount: number;
  payout_mode: string;
  payout_status: string;
  transaction_reference: string | null;
  notes: string | null;
  paid_at: string | null;
  created_at: string;
};

export const workerPayrollService = {
  listPayroll: async (): Promise<WorkerPayrollItem[]> => {
    const res = await http.get<Envelope<WorkerPayrollItem[]>>('/worker/payroll');
    return res.data.data ?? [];
  },

  listPayouts: async (): Promise<WorkerPayout[]> => {
    const res = await http.get<Envelope<WorkerPayout[]>>('/worker/payroll/payouts');
    return res.data.data ?? [];
  },

  getPayslipText: async (payrollItemId: number): Promise<string> => {
    const res = await http.get<string>(`/worker/payroll/${payrollItemId}/payslip`, {
      responseType: 'text',
    });
    return res.data as unknown as string;
  },

  getPayslipPdfUrl: (payrollItemId: number): string => {
    // Returns the full URL for the PDF payslip so expo-file-system can download it.
    const base = (http.defaults.baseURL ?? '').replace(/\/$/, '');
    return `${base}/worker/payroll/${payrollItemId}/payslip.pdf`;
  },

  getAccessToken: (): Promise<string | null> => {
    // Read the token directly from SecureStore (same source as the axios interceptor).
    return authStorage.getAccessToken();
  },
};
