export type ClientAuthStackParamList = {
  Welcome: undefined;
  Login: undefined;
  VerifyOtp: { phone: string; devOtp?: string };
  ProfileSetup: undefined;
};

// Bottom tab navigator
export type ClientTabParamList = {
  HomeTab: undefined;
  ComplaintsTab: undefined;
  ProfileTab: undefined;
};

// Per-tab stack param lists
export type HomeStackParamList = {
  Home: undefined;
  AllRequests: undefined;
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
  BillingOverview: undefined;
  InvoiceViewer: { invoiceId: number; invoiceNumber: string };
};

// Backward-compat alias
export type ClientAppStackParamList = HomeStackParamList;

