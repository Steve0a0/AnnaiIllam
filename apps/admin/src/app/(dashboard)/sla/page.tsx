"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Clock, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { slaService } from "@/services/sla.service";
import type { ComplaintSlaPolicy } from "@/types/sla";

// ─── Severity config ──────────────────────────────────────────────────────────

type Severity = "critical" | "high" | "medium" | "low";

const SEVERITY_META: Record<
  Severity,
  { label: string; description: string; bg: string; text: string; dot: string }
> = {
  critical: {
    label: "Critical",
    description: "Life-safety or urgent welfare issues",
    bg: "#fef2f2",
    text: "#991b1b",
    dot: "#ef4444",
  },
  high: {
    label: "High",
    description: "Significant service disruption",
    bg: "#fff7ed",
    text: "#9a3412",
    dot: "#f97316",
  },
  medium: {
    label: "Medium",
    description: "Standard complaints and disputes",
    bg: "#fefce8",
    text: "#854d0e",
    dot: "#eab308",
  },
  low: {
    label: "Low",
    description: "Minor issues and general feedback",
    bg: "var(--color-brand-50)",
    text: "var(--color-brand-700)",
    dot: "var(--color-brand-400)",
  },
};

function getSeverityMeta(severity: string) {
  return (
    SEVERITY_META[severity as Severity] ?? {
      label: severity.charAt(0).toUpperCase() + severity.slice(1),
      description: "Complaint severity tier",
      bg: "#f8fafc",
      text: "#475569",
      dot: "#94a3b8",
    }
  );
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function SlaSkeleton() {
  return (
    <div className="divide-y divide-border">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="flex flex-col gap-4 px-6 py-5 sm:flex-row sm:items-center">
          <div className="flex min-w-[200px] items-center gap-3">
            <div
              className="h-2.5 w-2.5 animate-pulse rounded-full"
              style={{ background: "var(--color-brand-100)" }}
            />
            <div>
              <div
                className="h-4 w-20 animate-pulse rounded"
                style={{ background: "var(--color-brand-50)" }}
              />
              <div
                className="mt-1.5 h-3 w-36 animate-pulse rounded"
                style={{ background: "var(--color-brand-50)" }}
              />
            </div>
          </div>
          <div className="flex flex-1 gap-4">
            <div className="flex-1 space-y-1.5">
              <div
                className="h-3 w-24 animate-pulse rounded"
                style={{ background: "var(--color-brand-50)" }}
              />
              <div
                className="h-9 w-full animate-pulse rounded-lg"
                style={{ background: "var(--color-brand-50)" }}
              />
            </div>
            <div className="flex-1 space-y-1.5">
              <div
                className="h-3 w-28 animate-pulse rounded"
                style={{ background: "var(--color-brand-50)" }}
              />
              <div
                className="h-9 w-full animate-pulse rounded-lg"
                style={{ background: "var(--color-brand-50)" }}
              />
            </div>
            <div className="flex items-end">
              <div
                className="h-9 w-20 animate-pulse rounded-lg"
                style={{ background: "var(--color-brand-50)" }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Row ──────────────────────────────────────────────────────────────────────

function SlaRow({ policy }: { policy: ComplaintSlaPolicy }) {
  const queryClient = useQueryClient();
  const [saved, setSaved] = useState(false);
  const meta = getSeverityMeta(policy.severity);

  const mutation = useMutation({
    mutationFn: slaService.updateComplaintPolicy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["complaint-sla-policies"] });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  return (
    <form
      className="flex flex-col gap-4 px-6 py-5 transition-colors hover:bg-muted/20 sm:flex-row sm:items-center"
      action={(formData) => {
        setSaved(false);
        mutation.mutate({
          severity: policy.severity,
          response_hours: Number(formData.get("response_hours")),
          resolution_hours: Number(formData.get("resolution_hours")),
        });
      }}
    >
      {/* Severity label */}
      <div className="flex min-w-[200px] items-center gap-3">
        <span
          className="mt-0.5 h-2.5 w-2.5 shrink-0 rounded-full"
          style={{ background: meta.dot }}
        />
        <div>
          <span
            className="inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold"
            style={{ background: meta.bg, color: meta.text }}
          >
            {meta.label}
          </span>
          <p className="mt-1 text-xs text-muted-foreground">{meta.description}</p>
        </div>
      </div>

      {/* Inputs */}
      <div className="flex flex-1 flex-wrap items-end gap-4">
        <div className="min-w-[120px] flex-1 space-y-1.5">
          <Label htmlFor={`resp-${policy.id}`} className="flex items-center gap-1.5 text-xs">
            <Clock className="h-3 w-3 text-muted-foreground" />
            Response hours
          </Label>
          <Input
            id={`resp-${policy.id}`}
            name="response_hours"
            type="number"
            min={1}
            defaultValue={policy.response_hours}
            className="h-9 tabular-nums"
          />
        </div>

        <div className="min-w-[120px] flex-1 space-y-1.5">
          <Label htmlFor={`res-${policy.id}`} className="flex items-center gap-1.5 text-xs">
            <Clock className="h-3 w-3 text-muted-foreground" />
            Resolution hours
          </Label>
          <Input
            id={`res-${policy.id}`}
            name="resolution_hours"
            type="number"
            min={1}
            defaultValue={policy.resolution_hours}
            className="h-9 tabular-nums"
          />
        </div>

        {/* Save + feedback */}
        <div className="flex items-center gap-2">
          <Button
            type="submit"
            size="sm"
            disabled={mutation.isPending}
            className="h-9 shrink-0"
          >
            {mutation.isPending ? "Saving…" : "Save"}
          </Button>

          {saved && (
            <span className="flex items-center gap-1 text-xs font-medium" style={{ color: "var(--color-brand-600)" }}>
              <CheckCircle2 className="h-3.5 w-3.5" />
              Saved
            </span>
          )}
          {mutation.isError && !mutation.isPending && (
            <span className="flex items-center gap-1 text-xs font-medium text-destructive">
              <AlertTriangle className="h-3.5 w-3.5" />
              Failed
            </span>
          )}
        </div>
      </div>
    </form>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function SlaPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["complaint-sla-policies"],
    queryFn: slaService.getComplaintPolicies,
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <section className="border-b border-border pb-6">
        <p className="text-xs font-medium uppercase tracking-[0.22em] text-muted-foreground">
          Management
        </p>
        <h1 className="mt-2 font-display text-3xl font-semibold tracking-[-0.02em] text-foreground">
          SLA Policies
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Configure complaint response and resolution time targets by severity. Changes take effect immediately.
        </p>
      </section>

      {/* Policies */}
      <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
        {/* Table header */}
        <div className="border-b border-border bg-muted/30 px-6 py-3">
          <div className="flex flex-col gap-0 sm:flex-row sm:items-center">
            <span className="min-w-[200px] text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">
              Severity
            </span>
            <div className="flex flex-1 gap-4">
              <span className="min-w-[120px] flex-1 text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                Response target
              </span>
              <span className="min-w-[120px] flex-1 text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                Resolution target
              </span>
              <span className="w-[88px]" />
            </div>
          </div>
        </div>

        {isLoading ? (
          <SlaSkeleton />
        ) : isError ? (
          <div className="flex flex-col items-center gap-3 py-16 text-center">
            <AlertTriangle className="h-7 w-7 text-destructive/60" />
            <p className="text-sm font-medium text-destructive">Failed to load SLA policies.</p>
            <p className="text-xs text-muted-foreground">Try refreshing the page.</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {(data?.data ?? []).map((policy) => (
              <SlaRow key={policy.id} policy={policy} />
            ))}
          </div>
        )}
      </div>

      {/* Helper note */}
      <p className="text-xs text-muted-foreground">
        Response hours = time to first admin response. Resolution hours = time to fully close the complaint. Both are measured from the moment a complaint is created.
      </p>
    </div>
  );
}
