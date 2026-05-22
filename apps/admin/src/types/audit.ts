export type AuditLogItem = {
  id: number;
  action: string;
  details: Record<string, unknown>;
  created_at: string;
};

export type AuditLogResponse = {
  success: boolean;
  message: string;
  data: AuditLogItem[];
};
