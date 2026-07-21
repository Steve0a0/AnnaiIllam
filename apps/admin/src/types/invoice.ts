export type InvoiceItem = {
  id: number;
  invoice_number: string;
  requirement_id: number;
  client_id: number;
  quote_id: number | null;
  financial_year: string | null;
  sequence_number: number | null;
  invoice_date: string | null;
  subtotal: number;
  gst_rate: number;
  gst_amount: number;
  total_amount: number;
  cgst_rate: number;
  cgst_amount: number;
  sgst_rate: number;
  sgst_amount: number;
  igst_rate: number;
  igst_amount: number;
  place_of_supply: string | null;
  place_of_supply_state_code: string | null;
  sac_code: string | null;
  recipient_gstin: string | null;
  status: string;
  issued_at: string | null;
  due_date: string | null;
  content_sha256: string | null;
  created_by_user_id: number;
  issued_by_user_id: number | null;
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
};
