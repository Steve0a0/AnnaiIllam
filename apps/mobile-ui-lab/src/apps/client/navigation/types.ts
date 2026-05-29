export type ClientAuthStackParamList = {
  Welcome: undefined;
  Login: undefined;
  VerifyOtp: { phone: string; devOtp?: string };
  ProfileSetup: undefined;
};

// Bottom tab navigator
export type ClientTabParamList = {
  HomeTab: undefined;
  JobsTab: undefined;
  ComplaintsTab: undefined;
  ProfileTab: undefined;
};

// Per-tab stack param lists
export type HomeStackParamList = {
  Home: undefined;
  CreateRequest: undefined;
  RequestDetail: { requirementId: number };
  AssignedWorkers: { requirementId: number };
  RaiseComplaint: { requirementId: number };
  InvoiceDetail: {
    invoiceId: number;
    invoiceTotal: number;
    advanceAmount: number | null;
    jobName: string;
    location: string;
    workerCount: number;
    durationDays: number;
    paymentMode: 'advance' | 'full';
  };
  PaymentConfirm: { invoiceId: number; utrRef: string; amount: number; isGatewayPayment?: boolean };
  RateRequirement: { requirementId: number; category: string };
  RaiseDispute: { requirementId: number };
};

export type JobsStackParamList = {
  Requests: undefined;
  CreateRequest: undefined;
  RequestDetail: { requirementId: number };
  AssignedWorkers: { requirementId: number };
  RaiseComplaint: { requirementId: number };
  InvoiceDetail: {
    invoiceId: number;
    invoiceTotal: number;
    advanceAmount: number | null;
    jobName: string;
    location: string;
    workerCount: number;
    durationDays: number;
    paymentMode: 'advance' | 'full';
  };
  PaymentConfirm: { invoiceId: number; utrRef: string; amount: number; isGatewayPayment?: boolean };
  RateRequirement: { requirementId: number; category: string };
  RaiseDispute: { requirementId: number };
};

export type ComplaintsStackParamList = {
  Complaints: undefined;
  RaiseComplaint: { requirementId?: number } | undefined;
  ComplaintDetail: { complaintId: number };
};

export type ProfileStackParamList = {
  ClientProfile: undefined;
};

// Backward-compat alias
export type ClientAppStackParamList = HomeStackParamList;

