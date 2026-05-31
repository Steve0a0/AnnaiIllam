import Link from "next/link";
import { ChevronRight, FileText, UserCheck, MessageSquareWarning } from "lucide-react";

const reports = [
  {
    href: "/reports/requirements",
    icon: FileText,
    title: "Requirements",
    description: "All service requests with status, category, city, and start date.",
  },
  {
    href: "/reports/assignments",
    icon: UserCheck,
    title: "Assignments",
    description: "Worker assignment records with role, shift, salary, and status.",
  },
  {
    href: "/reports/complaints",
    icon: MessageSquareWarning,
    title: "Complaints",
    description: "Complaint records with type, severity, and resolution status.",
  },
];

export default function ReportsPage() {
  return (
    <div className="space-y-8">
      <section className="border-b border-border pb-6">
        <p className="text-xs font-medium uppercase tracking-[0.22em] text-muted-foreground">
          Management
        </p>
        <h1 className="mt-2 font-display text-3xl font-semibold tracking-[-0.02em] text-foreground">
          Reports
        </h1>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          Filter, view, and export data across requirements, assignments, and complaints.
        </p>
      </section>

      <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
        {reports.map((report, i) => {
          const Icon = report.icon;
          return (
            <Link
              key={report.href}
              href={report.href}
              className={`group flex items-center gap-4 px-6 py-5 transition-colors hover:bg-muted/30 ${
                i < reports.length - 1 ? "border-b border-border" : ""
              }`}
            >
              <span
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
                style={{ background: "var(--color-brand-50)" }}
              >
                <Icon
                  className="h-5 w-5"
                  style={{ color: "var(--color-brand-600)" }}
                />
              </span>

              <div className="min-w-0 flex-1">
                <p className="font-semibold text-foreground">{report.title}</p>
                <p className="mt-0.5 text-sm text-muted-foreground">{report.description}</p>
              </div>

              <ChevronRight
                className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5"
              />
            </Link>
          );
        })}
      </div>
    </div>
  );
}
