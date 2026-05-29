"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Banknote, ArrowRight } from "lucide-react";
import PageHeader from "@/components/shared/page-header";
import { http } from "@/lib/http";
import type { AdminRequirementListItem } from "@/types/requirement";

function useCompletedRequirements() {
  return useQuery({
    queryKey: ["requirements", "completed"],
    queryFn: async () => {
      const res = await http.get("/admin/requirements", {
        params: { status: "completed", page_size: 100 },
      });
      return res.data;
    },
    staleTime: 30_000,
  });
}

function formatLabel(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (l) => l.toUpperCase());
}

function formatDate(value: string) {
  const d = new Date(value);
  if (isNaN(d.getTime())) return value;
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(d);
}

export default function PayrollPage() {
  const { data, isLoading } = useCompletedRequirements();
  const requirements: AdminRequirementListItem[] = data?.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Pay Workers"
        description="Select a completed requirement to record worker payments."
      />

      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="mb-5 flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700">
            <Banknote className="size-5" />
          </div>
          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">
              Completed jobs
            </p>
            <h2 className="font-display text-xl font-semibold text-foreground">
              Ready to pay
            </h2>
          </div>
        </div>

        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : requirements.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No completed requirements yet. Worker payments will appear here once
            a job is marked complete.
          </p>
        ) : (
          <div className="divide-y divide-border">
            {requirements.map((req) => (
              <div
                key={req.id}
                className="flex items-center gap-4 py-4 first:pt-0 last:pb-0"
              >
                <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 font-mono text-xs font-semibold text-slate-600">
                  #{req.id}
                </div>

                <div className="min-w-0 flex-1">
                  <p className="font-medium text-foreground">
                    {formatLabel(req.category)}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {req.city} · {req.number_of_workers}{" "}
                    {req.number_of_workers === 1 ? "worker" : "workers"} ·
                    Started {formatDate(req.start_date)}
                  </p>
                </div>

                <Link
                  href={`/requirements/${req.id}`}
                  className="flex shrink-0 items-center gap-1.5 rounded-lg bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 transition hover:bg-emerald-100"
                >
                  Pay workers
                  <ArrowRight className="size-3.5" />
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
