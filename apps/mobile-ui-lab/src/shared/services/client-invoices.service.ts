import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type ClientInvoiceSummary = {
  id: number;
  invoice_number: string;
  requirement_id: number;
  invoice_date: string;
  subtotal: number;
  gst_amount: number;
  total_amount: number;
  place_of_supply: string;
  status: 'issued';
  issued_at: string;
  due_date: string | null;
  content_sha256: string;
};

type InvoicePage = {
  invoices: ClientInvoiceSummary[];
  meta: { page: number; page_size: number; total: number; total_pages: number };
};

export const clientInvoicesService = {
  async listAll(): Promise<ClientInvoiceSummary[]> {
    const res = await http.get<Envelope<InvoicePage>>('/client/invoices');
    return res.data.data.invoices;
  },

  async fetchDocumentHtml(invoiceId: number): Promise<string> {
    const res = await http.get<string>(`/client/invoices/${invoiceId}/document.html`, {
      responseType: 'text',
    });
    return res.data;
  },
};
