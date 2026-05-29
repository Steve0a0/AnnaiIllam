"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import StatusBadge from "@/components/shared/status-badge";
import LoadingState from "@/components/shared/loading-state";
import ErrorState from "@/components/shared/error-state";
import { disputesService } from "@/services/disputes.service";

const STATUS_FILTERS = [
  { value: "", label: "All" },
  { value: "open", label: "Open" },
  { value: "under_review", label: "Under review" },
  { value: "resolved", label: "Resolved" },
  { value: "closed", label: "Closed" },
];

export default function DisputesPage() {
  const [statusFilter, setStatusFilter] = useState("");

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-disputes", statusFilter],
    queryFn: () => disputesService.list(statusFilter || undefined),
  });

  if (isLoading) return <LoadingState title="Loading disputes" description="Fetching dispute records…" />;
  if (isError) return <ErrorState title="Could not load disputes" description="Please try again." onRetry={() => refetch()} />;

  const disputes = data?.items ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-foreground">Disputes</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Review and resolve client disputes raised on completed requirements.
        </p>
      </div>

      {/* Status filter */}
      <div className="flex flex-wrap gap-2">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => setStatusFilter(f.value)}
            className={[
              "rounded-full border px-4 py-1.5 text-sm font-medium transition-colors",
              statusFilter === f.value
                ? "border-foreground bg-foreground text-background"
                : "border-border bg-card text-muted-foreground hover:border-foreground/40 hover:text-foreground",
            ].join(" ")}
          >
            {f.label}
          </button>
        ))}
      </div>

      {disputes.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-sm text-muted-foreground">No disputes found{statusFilter ? ` with status "${statusFilter}"` : ""}.</p>
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-muted/40">
              <tr>
                {["ID", "Requirement", "Type", "Description", "Status", "Raised", "Action"].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {disputes.map((d) => (
                <tr key={d.id} className="transition-colors hover:bg-muted/30">
                  <td className="px-4 py-3 font-mono text-sm text-muted-foreground">#{d.id}</td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    <Link href={`/requirements/${d.requirement_id}`} className="underline underline-offset-2 hover:text-foreground">
                      REQ-{d.requirement_id}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm capitalize text-muted-foreground">
                    {d.dispute_type.replace(/_/g, " ")}
                  </td>
                  <td className="max-w-xs px-4 py-3 text-sm text-muted-foreground">
                    <span className="line-clamp-2">{d.description}</span>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge value={d.status} />
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                    {d.created_at.slice(0, 10)}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/disputes/${d.id}`}
                      className="text-sm font-medium text-accent underline underline-offset-4 transition-colors hover:text-accent/80"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
