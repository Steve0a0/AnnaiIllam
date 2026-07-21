import { http } from "@/lib/http";
import type {
  GenerateInvoicePayload,
  InvoiceListResponse,
  InvoiceResponse,
} from "@/types/invoice";

export const invoicesService = {
  getByRequirement: async (requirementId: number): Promise<InvoiceListResponse> => {
    const res = await http.get(`/admin/invoices/requirement/${requirementId}`);
    return res.data;
  },

  generate: async (payload: GenerateInvoicePayload): Promise<InvoiceResponse> => {
    const res = await http.post("/admin/invoices/generate", payload);
    return res.data;
  },

  issue: async (invoiceId: number): Promise<InvoiceResponse> => {
    const res = await http.post(`/admin/invoices/${invoiceId}/issue`);
    return res.data;
  },

  getDocument: async (invoiceId: number): Promise<Blob> => {
    const res = await http.get<Blob>(`/admin/invoices/${invoiceId}/document.html`, {
      responseType: "blob",
    });
    return res.data;
  },
};
