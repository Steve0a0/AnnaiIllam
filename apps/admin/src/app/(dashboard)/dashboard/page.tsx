"use client";

import { useEffect } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import axios from "axios";
import {
  AlertTriangle,
  ArrowRight,
  BriefcaseBusiness,
  CalendarCheck,
  CheckCircle2,
  ClipboardList,
  MessageCircleWarning,
  Timer,
  UserCheck,
  Users,
} from "lucide-react";
import DashboardError from "@/features/dashboard/dashboard-error";
import DashboardLoading from "@/features/dashboard/dashboard-loading";
import DashboardStatCard from "@/features/dashboard/dashboard-stat-card";
import { useDashboardAlerts } from "@/features/dashboard/use-dashboard-alerts";
import { useDashboardSummary } from "@/features/dashboard/use-dashboard-summary";
import { getErrorMessage } from "@/lib/get-error-message";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import PageHeader from "@/components/shared/page-header";
import StatusBadge from "@/components/shared/status-badge";
import { authStorage } from "@/lib/auth-storage";
import { useAuthStore } from "@/store/auth-store";

type PriorityAction = {
  title: string;
  detail: string;
  status: string;
  href: string;
  tone: "info" | "warning" | "danger" | "teal";
  icon: ReactNode;
};

type ActivityItem = {
  title: string;
  detail: string;
  time: string;
  icon: ReactNode;
};

export default function DashboardPage() {
  const router = useRouter();
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const { data, isLoading, isError, error } = useDashboardSummary();
  const { data: alertsData } = useDashboardAlerts();

  useEffect(() => {
    if (!isError || !error) return;
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      if (status === 401 || status === 403) {
        authStorage.clear();
        clearAuth();
        router.replace("/login");
      }
    }
  }, [isError, error, clearAuth, router]);

  if (isLoading) return <DashboardLoading />;

  if (isError || !data?.data) {
    return <DashboardError message={getErrorMessage(error)} />;
  }

  const summary = data.data;
  const alerts = alertsData?.data;
  const missingAttendanceCount = alerts?.missing_attendance?.length ?? 0;
  const pendingRequests = summary.requirements?.open ?? 0;
  const activeJobs = summary.assignments?.active ?? 0;
  const workersOnShift = summary.attendance?.present ?? 0;
  const openComplaints = summary.complaints?.open ?? 0;

  const priorityActions: PriorityAction[] = [
    {
      title: "Review submitted worker requests",
      detail: `${pendingRequests} requests are waiting for approval or rejection.`,
      status: "submitted",
      href: "/requirements",
      tone: "info",
      icon: <ClipboardList className="h-4 w-4" />,
    },
    {
      title: "Assign workers to approved jobs",
      detail: `${activeJobs} active assignments need daily monitoring.`,
      status: "workers_assigned",
      href: "/assignments",
      tone: "teal",
      icon: <UserCheck className="h-4 w-4" />,
    },
    {
      title: "Verify attendance records",
      detail: `${missingAttendanceCount} records need admin follow-up today.`,
      status: missingAttendanceCount > 0 ? "not_started" : "verified",
      href: "/attendance",
      tone: missingAttendanceCount > 0 ? "warning" : "teal",
      icon: <CalendarCheck className="h-4 w-4" />,
    },
    {
      title: "Resolve open complaints",
      detail: `${openComplaints} complaints are still open.`,
      status: openComplaints > 0 ? "open" : "resolved",
      href: "/complaints",
      tone: openComplaints > 0 ? "danger" : "teal",
      icon: <MessageCircleWarning className="h-4 w-4" />,
    },
  ];

  const activityItems: ActivityItem[] = [
    {
      title: "Workers on site",
      detail: `${workersOnShift} workers marked present today.`,
      time: "Today",
      icon: <Users className="h-4 w-4" />,
    },
    {
      title: "Attendance exceptions",
      detail: `${summary.attendance?.absent ?? 0} absent records in the current view.`,
      time: "Today",
      icon: <AlertTriangle className="h-4 w-4" />,
    },
    {
      title: "Complaint queue",
      detail: `${summary.complaints?.total ?? 0} total complaints tracked.`,
      time: "Live",
      icon: <MessageCircleWarning className="h-4 w-4" />,
    },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Dashboard"
        description="Review worker requests, assign staff, verify attendance, and resolve complaints from one focused workspace."
        action={
          <Button asChild>
            <Link href="/requirements">
              Review requests
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        }
      />

      <section className="grid gap-4 grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        <DashboardStatCard
          title="Pending Requests"
          value={pendingRequests}
          subtitle="needs review"
          trend="Action"
          tone="info"
          icon={<ClipboardList className="h-5 w-5" />}
        />
        <DashboardStatCard
          title="Active Jobs"
          value={activeJobs}
          subtitle="in operation"
          trend="Live"
          tone="teal"
          icon={<BriefcaseBusiness className="h-5 w-5" />}
        />
        <DashboardStatCard
          title="Workers on Shift"
          value={workersOnShift}
          subtitle={`of ${summary.workers?.total ?? 0} workers`}
          tone="brand"
          icon={<Users className="h-5 w-5" />}
        />
        <DashboardStatCard
          title="Attendance to Verify"
          value={missingAttendanceCount}
          subtitle="needs follow-up"
          tone={missingAttendanceCount > 0 ? "warning" : "brand"}
          icon={<CalendarCheck className="h-5 w-5" />}
        />
        <DashboardStatCard
          title="Open Complaints"
          value={openComplaints}
          subtitle={`of ${summary.complaints?.total ?? 0} total`}
          tone={openComplaints > 0 ? "danger" : "brand"}
          icon={<MessageCircleWarning className="h-5 w-5" />}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <Card className="border-border bg-white shadow-sm">
          <CardHeader className="border-b border-border">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                  Priority actions
                </p>
                <CardTitle className="mt-2 font-display text-xl font-semibold">
                  Work that needs admin attention
                </CardTitle>
              </div>
              <span className="inline-flex items-center rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {priorityActions.length} queues
              </span>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {priorityActions.map((item) => (
                <Link
                  key={item.title}
                  href={item.href}
                  className="grid gap-4 p-5 transition-colors hover:bg-muted/30 md:grid-cols-[auto_minmax(0,1fr)_auto] md:items-center"
                >
                  <div className={getActionIconClass(item.tone)}>{item.icon}</div>
                  <div className="min-w-0">
                    <div className="mb-2">
                      <StatusBadge value={item.status} />
                    </div>
                    <p className="font-medium text-foreground">{item.title}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{item.detail}</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-white shadow-sm">
          <CardHeader className="border-b border-border">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Recent activity
            </p>
            <CardTitle className="mt-2 font-display text-xl font-semibold">Live operation signals</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {activityItems.map((item) => (
                <div key={item.title} className="flex gap-3 p-5">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-(--color-brand-50) text-(--color-brand-600)">
                    {item.icon}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-3">
                      <p className="font-medium text-foreground">{item.title}</p>
                      <span className="font-mono text-xs text-muted-foreground">{item.time}</span>
                    </div>
                    <p className="mt-1 text-sm leading-5 text-muted-foreground">{item.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <MiniPanel
          title="Available workers"
          value={summary.workers?.available ?? 0}
          detail="Ready for assignment"
          icon={<UserCheck className="h-4 w-4" />}
        />
        <MiniPanel
          title="Attendance present"
          value={summary.attendance?.present ?? 0}
          detail={`${summary.attendance?.total_records ?? 0} total records`}
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <MiniPanel
          title="Missing attendance"
          value={missingAttendanceCount}
          detail="From operational alerts"
          icon={<Timer className="h-4 w-4" />}
        />
      </section>
    </div>
  );
}

function getActionIconClass(tone: PriorityAction["tone"]) {
  const classes = {
    info: "bg-blue-50 text-blue-700",
    warning: "bg-amber-50 text-amber-700",
    danger: "bg-red-50 text-red-700",
    teal: "bg-cyan-50 text-cyan-700",
  };
  return `flex h-10 w-10 items-center justify-center rounded-md ${classes[tone]}`;
}

function MiniPanel({
  title,
  value,
  detail,
  icon,
}: {
  title: string;
  value: number;
  detail: string;
  icon: ReactNode;
}) {
  return (
    <Card className="border-border bg-white shadow-sm">
      <CardContent className="flex items-center gap-4 p-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-(--color-brand-50) text-(--color-brand-600)">
          {icon}
        </div>
        <div>
          <p className="text-sm font-medium text-foreground">{title}</p>
          <p className="mt-1 font-mono text-sm text-muted-foreground">
            {value} {detail}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
