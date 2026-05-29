"use client";

import { useMemo, useState } from "react";
import { Check, Search, X } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { assignmentsService } from "@/services/assignments.service";
import { complaintsService } from "@/services/complaints.service";
import { getErrorMessage } from "@/lib/get-error-message";
import type { WorkerMatch } from "@/types/assignment";

export default function CreateReplacementForm({
  complaintId,
  oldAssignmentId,
  requirementId,
  onSuccess,
}: {
  complaintId: number;
  oldAssignmentId: number;
  requirementId: number;
  onSuccess: () => void;
}) {
  const [selectedWorkerId, setSelectedWorkerId] = useState<number | null>(null);
  const [reason, setReason] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const { data: matchesData, isLoading: matchesLoading } = useQuery({
    queryKey: ["worker-matches", requirementId],
    queryFn: () => assignmentsService.getWorkerMatches(requirementId),
    enabled: !!requirementId,
  });

  const matches = matchesData?.data ?? [];
  const assignableMatches = matches.filter(isAssignableWorker);
  const blockedMatches = matches.filter((w) => !isAssignableWorker(w));
  const normalizedQuery = query.trim().toLowerCase();

  const visibleAssignable = useMemo(
    () => filterWorkers(assignableMatches, normalizedQuery),
    [assignableMatches, normalizedQuery],
  );
  const visibleBlocked = useMemo(
    () => filterWorkers(blockedMatches, normalizedQuery),
    [blockedMatches, normalizedQuery],
  );

  const selectedWorker =
    matches.find((w) => w.worker_profile_id === selectedWorkerId) ?? null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWorkerId) {
      setMessage("Select a replacement worker first.");
      return;
    }
    setLoading(true);
    setMessage("");
    try {
      await complaintsService.createReplacement({
        complaint_id: complaintId,
        old_assignment_id: oldAssignmentId,
        new_worker_profile_id: selectedWorkerId,
        reason: reason || null,
      });
      setSelectedWorkerId(null);
      setReason("");
      setMessage("Replacement created successfully.");
      onSuccess();
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      className="space-y-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={handleSubmit}
    >
      <h3 className="text-base font-semibold text-slate-900">
        Create Replacement
      </h3>

      {/* Search */}
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by name, category, city, or reason"
          className="h-10 w-full rounded-lg border border-input bg-white pl-9 pr-3 text-sm text-foreground shadow-sm outline-none transition focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* Selected worker chip */}
      {selectedWorker ? (
        <div className="flex items-center gap-2 rounded-lg border border-[#1A6640] bg-[#EDFAF3] px-3 py-2 text-sm">
          <span className="font-semibold text-[#1A6640]">
            {selectedWorker.full_name}
          </span>
          <span className="text-[#1A6640]">·</span>
          <span className="text-[#1A6640]">
            {selectedWorker.category}, {selectedWorker.city}
          </span>
          <button
            type="button"
            onClick={() => setSelectedWorkerId(null)}
            className="ml-auto rounded-full p-0.5 hover:bg-[#1A6640]/10"
            aria-label="Deselect worker"
          >
            <X className="size-3.5 text-[#1A6640]" />
          </button>
        </div>
      ) : null}

      {/* Loading */}
      {matchesLoading ? (
        <p className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
          Loading eligible workers...
        </p>
      ) : null}

      {/* No workers at all */}
      {!matchesLoading && matches.length === 0 ? (
        <p className="rounded-xl border-l-4 border-l-amber-500 border-y border-r border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          No worker profiles found for this requirement. Approve workers first.
        </p>
      ) : null}

      {/* All workers blocked */}
      {!matchesLoading && matches.length > 0 && assignableMatches.length === 0 ? (
        <p className="rounded-xl border-l-4 border-l-amber-500 border-y border-r border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          No eligible workers available right now. All workers are blocked — see details below.
        </p>
      ) : null}

      {/* Eligible workers */}
      {!matchesLoading && assignableMatches.length > 0 ? (
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Eligible workers ({assignableMatches.length})
          </p>
          {visibleAssignable.length === 0 ? (
            <p className="rounded-xl border border-dashed border-border bg-[#FAFAF9] p-3 text-sm text-muted-foreground">
              No eligible workers match this search.
            </p>
          ) : (
            <div className="grid gap-2 sm:grid-cols-2">
              {visibleAssignable.map((worker) => (
                <ReplacementWorkerCard
                  key={worker.worker_profile_id}
                  worker={worker}
                  selected={selectedWorkerId === worker.worker_profile_id}
                  onSelect={() =>
                    setSelectedWorkerId(
                      selectedWorkerId === worker.worker_profile_id
                        ? null
                        : worker.worker_profile_id,
                    )
                  }
                />
              ))}
            </div>
          )}
        </div>
      ) : null}

      {/* Blocked workers (collapsible) */}
      {!matchesLoading && blockedMatches.length > 0 ? (
        <details className="group rounded-xl border border-border">
          <summary className="flex cursor-pointer list-none items-center justify-between px-4 py-3 text-sm font-medium text-muted-foreground select-none">
            Blocked workers ({blockedMatches.length})
            <span className="text-xs group-open:hidden">Show</span>
            <span className="hidden text-xs group-open:inline">Hide</span>
          </summary>
          <div className="grid gap-2 border-t border-border p-4 sm:grid-cols-2">
            {visibleBlocked.length > 0 ? (
              visibleBlocked.map((worker) => (
                <BlockedWorkerCard
                  key={worker.worker_profile_id}
                  worker={worker}
                />
              ))
            ) : (
              <p className="col-span-2 text-sm text-muted-foreground">
                No blocked workers match this search.
              </p>
            )}
          </div>
        </details>
      ) : null}

      {/* Reason */}
      <div className="space-y-1.5">
        <label className="text-sm font-medium text-foreground">Reason</label>
        <textarea
          className="w-full rounded-lg border border-input bg-white px-3 py-2 text-sm"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Enter replacement reason"
          rows={3}
        />
      </div>

      {message ? (
        <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
          {message}
        </div>
      ) : null}

      <Button
        type="submit"
        disabled={loading || !selectedWorkerId}
        variant="accent"
        size="sm"
      >
        {loading ? "Saving..." : "Create Replacement"}
      </Button>
    </form>
  );
}

// ─── Worker card components ───────────────────────────────────────

function ReplacementWorkerCard({
  worker,
  selected,
  onSelect,
}: {
  worker: WorkerMatch;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`rounded-xl border p-3 text-left text-sm transition ${
        selected
          ? "border-[#1A6640] bg-[#EDFAF3] shadow-sm"
          : "border-border bg-white hover:border-[#1A6640]"
      }`}
    >
      <div className="flex items-start gap-3">
        <span
          className={`mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full border ${
            selected
              ? "border-[#1A6640] bg-[#1A6640] text-white"
              : "border-border bg-white text-transparent"
          }`}
        >
          <Check className="size-3" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-foreground">{worker.full_name}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {worker.category} · {worker.city}, {worker.state}
          </p>
          <div className="mt-1.5 flex flex-wrap gap-1">
            <WorkerTag
              label={worker.verification_status}
              tone={
                ["approved", "verified"].includes(worker.verification_status)
                  ? "green"
                  : "amber"
              }
            />
            <WorkerTag
              label={worker.is_available ? "Available" : "Unavailable"}
              tone={worker.is_available ? "green" : "red"}
            />
            {worker.has_interest ? (
              <WorkerTag label="Interested" tone="blue" />
            ) : null}
          </div>
        </div>
      </div>
    </button>
  );
}

function BlockedWorkerCard({ worker }: { worker: WorkerMatch }) {
  const reason = getBlockedReason(worker);
  return (
    <div className="rounded-xl border border-border bg-[#FAFAF9] p-3 text-sm">
      <p className="font-semibold text-foreground">{worker.full_name}</p>
      <p className="mt-0.5 text-xs text-muted-foreground">
        {worker.category} · {worker.city}, {worker.state}
      </p>
      <span className="mt-2 inline-flex rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
        {reason}
      </span>
    </div>
  );
}

function WorkerTag({
  label,
  tone,
}: {
  label: string;
  tone: "green" | "amber" | "red" | "blue";
}) {
  const cls: Record<string, string> = {
    green: "bg-[#DCFCE7] text-[#15803D]",
    amber: "bg-amber-100 text-amber-800",
    red: "bg-red-100 text-red-700",
    blue: "bg-blue-100 text-blue-700",
  };
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-[11px] font-medium capitalize ${cls[tone]}`}
    >
      {label}
    </span>
  );
}

// ─── Helpers (mirrors create-assignment-form logic) ───────────────

function isAssignableWorker(worker: WorkerMatch) {
  return (
    worker.is_available &&
    ["approved", "verified"].includes(worker.verification_status) &&
    !worker.reasons.some((r) => r.startsWith("not available")) &&
    !worker.conflict
  );
}

function getBlockedReason(worker: WorkerMatch) {
  if (worker.conflict)
    return `Conflict with request #${worker.conflict.requirement_id}`;
  if (!["approved", "verified"].includes(worker.verification_status))
    return `Needs approval (${worker.verification_status})`;
  if (!worker.is_available) return "Worker is marked unavailable";
  const r = worker.reasons.find((reason) => reason.startsWith("not available"));
  if (r) return r;
  return "Not ready for this assignment";
}

function filterWorkers(workers: WorkerMatch[], query: string) {
  if (!query) return workers;
  return workers.filter((w) =>
    [
      w.full_name,
      w.category,
      w.city,
      w.state,
      w.verification_status,
      ...w.reasons,
      getBlockedReason(w),
    ]
      .join(" ")
      .toLowerCase()
      .includes(query),
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      {children}
    </div>
  );
}
