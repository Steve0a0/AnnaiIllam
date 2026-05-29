export type InvoiceItem = {
  id: number;
  invoice_number: string;
  requirement_id: number;
  client_id: number;
  quote_id: number | null;
  subtotal: number;
  gst_rate: number;
  gst_amount: number;
  total_amount: number;
  status: string;
  issued_at: string | null;
  due_date: string | null;
  pdf_url: string | null;
  created_by_user_id: number | null;
  created_at: string;
  updated_at: string;
};

export type InvoiceListResponse = {
  success: boolean;
  message: string;
  data: InvoiceItem[];
};

export type InvoiceResponse = {
  success: boolean;
  message: string;
  data: InvoiceItem;
};

export type GenerateInvoicePayload = {
  requirement_id: number;
  gst_rate?: number;
};
