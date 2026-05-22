"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  ArrowRight,
  CalendarDays,
  ClipboardList,
  FileCheck2,
  Search,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useRequirements } from "@/features/requirements/use-requirements";
import PageHeader from "@/components/shared/page-header";
import LoadingState from "@/components/shared/loading-state";
import EmptyState from "@/components/shared/empty-state";
import ErrorState from "@/components/shared/error-state";
import StatusBadge from "@/components/shared/status-badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { AdminRequirementListItem } from "@/types/requirement";

type StatusFilter = { label: string; value: string };

const STATUS_FILTERS: StatusFilter[] = [
  { label: "All", value: "all" },
  { label: "Submitted", value: "submitted" },
  { label: "Under review", value: "under_review" },
  { label: "Quoted", value: "quoted" },
  { label: "Approved", value: "approved" },
  { label: "Assigned", value: "workers_assigned" },
  { label: "In progress", value: "in_progress" },
  { label: "Rejected", value: "rejected" },
  { label: "Completed", value: "completed" },
];

const REVIEW_STATUSES = new Set(["submitted", "under_review"]);
const ACTIVE_STATUSES = new Set([
  "approved",
  "workers_assigned",
  "assigned",
  "accepted",
  "in_progress",
]);

export default function RequirementsPage() {
  const { data, isLoading, isError, error, refetch } = useRequirements();
  const [activeStatus, setActiveStatus] = useState("all");
  const [query, setQuery] = useState("");

  const requirements = useMemo(() => data?.data?.items || [], [data?.data?.items]);
  const stats = useMemo(() => buildStats(requirements), [requirements]);

  const normalizedQuery = query.trim().toLowerCase();
  const filteredRequirements = requirements.filter((item) => {
    const matchesStatus = activeStatus === "all" || item.status === activeStatus;
    const matchesQuery =
      normalizedQuery.length === 0 ||
      [
        `req-${item.id}`,
        String(item.id),
        item.category,
        item.city,
        item.status.replaceAll("_", " "),
        item.start_date,
      ]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(normalizedQuery));
    return matchesStatus && matchesQuery;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Requests"
        description="Review, quote, approve, and assign workers for client manpower requests."
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <RequirementStatCard
          label="Total requests"
          value={stats.total}
          helper="Across every client status"
          icon={ClipboardList}
          tone="brand"
        />
        <RequirementStatCard
          label="Needs review"
          value={stats.needsReview}
          helper="Submitted or under review"
          icon={FileCheck2}
          tone="purple"
        />
        <RequirementStatCard
          label="Ready to assign"
          value={stats.readyToAssign}
          helper="Approved by client"
          icon={Users}
          tone="success"
        />
        <RequirementStatCard
          label="Active jobs"
          value={stats.active}
          helper="Assigned or in progress"
          icon={CalendarDays}
          tone="teal"
        />
      </section>

      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="relative max-w-xl flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            aria-label="Search requirements"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by request ID, category, city, or status"
            className="pl-9"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {STATUS_FILTERS.map((filter) => (
            <button
              key={filter.value}
              type="button"
              onClick={() => setActiveStatus(filter.value)}
              className={
                activeStatus === filter.value
                  ? "h-9 rounded-full border border-primary bg-primary px-3 text-xs font-medium text-primary-foreground shadow-sm transition"
                  : "h-9 rounded-full border border-border bg-white px-3 text-xs font-medium text-muted-foreground transition hover:border-input hover:bg-muted/30 hover:text-foreground"
              }
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      <Card className="overflow-hidden">
        {isLoading ? (
          <div className="p-6">
            <LoadingState title="Loading requests" description="Fetching client requirement profiles…" />
          </div>
        ) : isError ? (
          <div className="p-6">
            <ErrorState
              title="Could not load requests"
              description={error?.message ?? "Check your connection and try again."}
              onRetry={() => refetch()}
            />
          </div>
        ) : requirements.length === 0 ? (
          <div className="p-6">
            <EmptyState
              title="No requests yet"
              description="Client requirement requests will appear here once clients create them."
            />
          </div>
        ) : filteredRequirements.length === 0 ? (
          <div className="p-6">
            <EmptyState
              title="No matching requests"
              description="Try a different search term or select a different status filter."
            />
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-muted/40">
                  <tr>
                    {["Request", "Status", "Category", "Location", "Workers", "Start date", ""].map(
                      (heading) => (
                        <th
                          key={heading}
                          className={`px-4 py-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground ${
                            heading === "" ? "text-right" : "text-left"
                          }`}
                        >
                          {heading}
                        </th>
                      ),
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredRequirements.map((item) => (
                    <RequirementRow key={item.id} item={item} />
                  ))}
                </tbody>
              </table>
            </div>
            <div className="border-t border-border px-4 py-3">
              <p className="text-xs text-muted-foreground">
                {filteredRequirements.length === requirements.length
                  ? `${requirements.length} request${requirements.length !== 1 ? "s" : ""}`
                  : `Showing ${filteredRequirements.length} of ${requirements.length} requests`}
              </p>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}

function RequirementRow({ item }: { item: AdminRequirementListItem }) {
  const action = getRequirementAction(item.status);

  return (
    <tr className="transition-colors hover:bg-muted/30">
      <td className="whitespace-nowrap px-4 py-3">
        <div className="font-mono text-sm font-medium text-foreground">REQ-{item.id}</div>
        <div className="mt-1 text-xs text-muted-foreground">Client request</div>
      </td>
      <td className="px-4 py-3">
        <StatusBadge value={item.status} />
      </td>
      <td className="px-4 py-3">
        <div className="text-sm font-medium text-foreground">{formatLabel(item.category)}</div>
      </td>
      <td className="px-4 py-3">
        <div className="text-sm text-muted-foreground">{item.city}</div>
      </td>
      <td className="whitespace-nowrap px-4 py-3 font-mono text-sm text-muted-foreground">
        {item.number_of_workers}
      </td>
      <td className="whitespace-nowrap px-4 py-3 font-mono text-sm text-muted-foreground">
        {formatDate(item.start_date)}
      </td>
      <td className="px-4 py-3 text-right">
        <Link
          href={`/requirements/${item.id}`}
          className="inline-flex h-8 items-center justify-center gap-1 rounded-full px-3 text-xs font-medium text-primary transition-colors hover:bg-(--color-brand-50)"
        >
          {action}
          <ArrowRight className="size-3.5" />
        </Link>
      </td>
    </tr>
  );
}

function RequirementStatCard({
  label,
  value,
  helper,
  icon: Icon,
  tone,
}: {
  label: string;
  value: number;
  helper: string;
  icon: LucideIcon;
  tone: "brand" | "purple" | "success" | "teal";
}) {
  const toneClass = {
    brand: "bg-[var(--color-brand-50)] text-primary",
    purple: "bg-purple-50 text-purple-700",
    success: "bg-green-50 text-green-700",
    teal: "bg-cyan-50 text-cyan-700",
  }[tone];

  return (
    <Card className="p-5">
      <div className={`flex size-10 items-center justify-center rounded-lg ${toneClass}`}>
        <Icon className="size-5" />
      </div>
      <p className="mt-5 font-display text-4xl font-semibold leading-none tracking-tight text-foreground">
        {value}
      </p>
      <div className="mt-3">
        <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">{label}</p>
        <p className="mt-1 text-sm text-muted-foreground">{helper}</p>
      </div>
    </Card>
  );
}

function buildStats(requirements: AdminRequirementListItem[]) {
  return requirements.reduce(
    (acc, item) => {
      acc.total += 1;
      if (REVIEW_STATUSES.has(item.status)) acc.needsReview += 1;
      if (item.status === "approved") acc.readyToAssign += 1;
      if (ACTIVE_STATUSES.has(item.status)) acc.active += 1;
      return acc;
    },
    { total: 0, needsReview: 0, readyToAssign: 0, active: 0 },
  );
}

function getRequirementAction(status: string) {
  switch (status) {
    case "submitted": return "Review";
    case "under_review": return "Create quote";
    case "quoted": return "View quote";
    case "approved": return "Assign workers";
    case "workers_assigned":
    case "assigned":
    case "accepted": return "Track assignment";
    case "in_progress": return "View attendance";
    default: return "View";
  }
}

function formatLabel(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

function formatDate(value: string) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}
