export type WorkerAuthStackParamList = {
  Welcome: undefined;
  Login: undefined;
  VerifyOtp: { phone: string; devOtp?: string };
  Consent: undefined;
  VerifyIdentity: undefined;
  BuildProfile: undefined;
  ProfileSubmitted: undefined;
};

export type WorkerTabParamList = {
  HomeTab: undefined;
  JobsTab: undefined;
  AttendanceTab: undefined;
  EarningsTab: undefined;
  ProfileTab: undefined;
};

export type EarningsStackParamList = {
  Earnings: undefined;
};

export type HomeStackParamList = {
  Home: undefined;
  Issues: undefined;
  RaiseIssue: undefined;
  IssueDetail: { issueId: number };
  JobDetail: { assignmentId: number };
};

export type JobsStackParamList = {
  Jobs: undefined;
  JobDetail: { assignmentId: number };
};

export type AttendanceStackParamList = {
  AttendanceHistory: undefined;
};

export type ProfileStackParamList = {
  Profile: undefined;
  Availability: undefined;
};

// Backward-compat alias — screens that navigated via the old single stack
// now live in HomeStackParamList (Issues, IssueDetail, JobDetail, RaiseIssue).
export type WorkerAppStackParamList = HomeStackParamList;
