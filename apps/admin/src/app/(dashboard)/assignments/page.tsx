"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ArrowRight, Search } from "lucide-react";
import { useAllAssignments } from "@/features/assignments/use-all-assignments";
import PageHeader from "@/components/shared/page-header";
import LoadingState from "@/components/shared/loading-state";
import EmptyState from "@/components/shared/empty-state";
import ErrorState from "@/components/shared/error-state";
import StatusBadge from "@/components/shared/status-badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { GlobalAssignmentItem } from "@/types/assignment";

const STATUS_FILTERS = [
  { label: "All", value: "all" },
  { label: "Assigned", value: "assigned" },
  { label: "Accepted", value: "accepted" },
  { label: "Active", value: "active" },
  { label: "Completed", value: "completed" },
  { label: "Declined", value: "declined" },
  { label: "Cancelled", value: "cancelled" },
];

export default function AssignmentsPage() {
  const { data, isLoading, isError, error, refetch } = useAllAssignments();
  const [activeStatus, setActiveStatus] = useState("all");
  const [query, setQuery] = useState("");

  const assignments = useMemo(() => data?.data?.items ?? [], [data?.data?.items]);

  const normalizedQuery = query.trim().toLowerCase();
  const filtered = assignments.filter((item) => {
    const matchesStatus = activeStatus === "all" || item.status === activeStatus;
    const matchesQuery =
      normalizedQuery.length === 0 ||
      [
        String(item.id),
        item.worker_name,
        item.worker_city ?? "",
        item.requirement_category ?? "",
        item.requirement_city ?? "",
        item.assigned_role ?? "",
        item.status,
      ].some((v) => v.toLowerCase().includes(normalizedQuery));
    return matchesStatus && matchesQuery;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Assignments"
        description="All worker assignments across every requirement."
      />

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState
          title="Could not load assignments"
          description={(error as Error)?.message ?? "Unknown error"}
          onRetry={refetch}
        />
      ) : (
        <>
          {/* Stats strip */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {buildStats(assignments).map((stat) => (
              <Card key={stat.label} className="p-4">
                <p className="text-2xl font-bold text-foreground">{stat.value}</p>
                <p className="mt-1 text-xs text-muted-foreground">{stat.label}</p>
              </Card>
            ))}
          </div>

          {/* Search + status filter */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search worker, requirement, role…"
                className="pl-9"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <div className="flex flex-wrap gap-2">
              {STATUS_FILTERS.map((f) => (
                <button
                  key={f.value}
                  onClick={() => setActiveStatus(f.value)}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                    activeStatus === f.value
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* List */}
          {filtered.length === 0 ? (
            <EmptyState
              title="No assignments found"
              description={
                assignments.length === 0
                  ? "Assignments will appear here once workers are assigned to requirements."
                  : "No assignments match your current filter."
              }
            />
          ) : (
            <div className="space-y-2">
              {filtered.map((item) => (
                <AssignmentRow key={item.id} item={item} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function AssignmentRow({ item }: { item: GlobalAssignmentItem }) {
  return (
    <Card className="flex items-center gap-4 p-4 transition-colors hover:bg-muted/40">
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-foreground">{item.worker_name}</span>
          {item.worker_city && (
            <span className="text-xs text-muted-foreground">· {item.worker_city}</span>
          )}
          <StatusBadge value={item.status} />
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <span>
            Req #{item.requirement_id}
            {item.requirement_category ? ` · ${item.requirement_category}` : ""}
            {item.requirement_city ? `, ${item.requirement_city}` : ""}
          </span>
          {item.assigned_role && <span>Role: {item.assigned_role}</span>}
          {item.assigned_shift && <span>Shift: {item.assigned_shift}</span>}
          {item.salary_amount && (
            <span>₹{item.salary_amount.toLocaleString("en-IN")}/day</span>
          )}
        </div>
      </div>
      <Link
        href={`/requirements/${item.requirement_id}`}
        className="flex shrink-0 items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
      >
        View requirement
        <ArrowRight className="size-3" />
      </Link>
    </Card>
  );
}

function buildStats(items: GlobalAssignmentItem[]) {
  const active = items.filter((i) =>
    ["assigned", "accepted", "active"].includes(i.status)
  ).length;
  const completed = items.filter((i) => i.status === "completed").length;
  const declined = items.filter((i) => i.status === "declined").length;
  return [
    { label: "Total", value: items.length },
    { label: "Active / Assigned", value: active },
    { label: "Completed", value: completed },
    { label: "Declined", value: declined },
  ];
}

