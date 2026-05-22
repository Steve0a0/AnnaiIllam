export type ComplaintSlaPolicy = {
  id: number;
  severity: string;
  response_hours: number;
  resolution_hours: number;
};

export type ComplaintSlaPoliciesResponse = {
  success: boolean;
  message: string;
  data: ComplaintSlaPolicy[];
};

export type ComplaintSlaPolicyUpdate = {
  severity: string;
  response_hours: number;
  resolution_hours: number;
};
