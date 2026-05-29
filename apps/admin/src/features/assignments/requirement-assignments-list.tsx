"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Check, CheckCircle2, ClipboardList, Plus, RefreshCw, Search, UserCheck } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useRequirementAssignments } from "@/features/assignments/use-requirement-assignments";
import AssignmentsLoading from "@/features/assignments/assignments-loading";
import AssignmentsError from "@/features/assignments/assignments-error";
import StatusBadge from "@/components/shared/status-badge";
import UpdateAssignmentStatus from "@/features/assignments/update-assignment-status";
import { assignmentsService } from "@/services/assignments.service";
import { getErrorMessage } from "@/lib/get-error-message";
import type { AssignmentItem, WorkerMatch } from "@/types/assignment";

export type ReplacementHint = {
  assignedRole: string | null;
  assignedShift: string | null;
  startDate: string | null;
  endDate: string | null;
  salaryAmount: number | null;
};

export default function RequirementAssignmentsList({
  requirementId,
  requiredWorkers,
  canAddWorkers = false,
  onAddWorkers,
  onReplace,
}: {
  requirementId: number;
  requiredWorkers?: number;
  canAddWorkers?: boolean;
  onAddWorkers?: () => void;
  onReplace?: (hint: ReplacementHint) => void;
}) {
  const { data, isLoading, isError, error, refetch } =
    useRequirementAssignments(requirementId);
  const queryClient = useQueryClient();

  const [replaceTargetId, setReplaceTargetId] = useState<number | null>(null);
  const [replaceWorkerId, setReplaceWorkerId] = useState<number | null>(null);
  const [replaceReason, setReplaceReason] = useState("");
  const [replaceReasonError, setReplaceReasonError] = useState("");
  const [replacing, setReplacing] = useState(false);
  const [replaceMessage, setReplaceMessage] = useState("");
  const [replaceQuery, setReplaceQuery] = useState("");

  const { data: matchesData, isLoading: matchesLoading } = useQuery({
    queryKey: ["worker-matches", requirementId],
    queryFn: () => assignmentsService.getWorkerMatches(requirementId),
    enabled: !!replaceTargetId,
  });

  const allMatches = matchesData?.data ?? [];
  const assignableMatches = allMatches.filter(isAssignableWorker);
  const normalizedReplaceQuery = replaceQuery.trim().toLowerCase();
  const visibleReplaceMatches = useMemo(
    () =>
      normalizedReplaceQuery
        ? assignableMatches.filter((w) =>
            [w.full_name, w.category, w.city, w.state]
              .join(" ")
              .toLowerCase()
              .includes(normalizedReplaceQuery),
          )
        : assignableMatches,
    [assignableMatches, normalizedReplaceQuery],
  );

  function handleOpenReplace(assignmentId: number) {
    setReplaceTargetId(assignmentId);
    setReplaceWorkerId(null);
    setReplaceReason("");
    setReplaceReasonError("");
    setReplaceMessage("");
    setReplaceQuery("");
  }

  function handleCloseReplace() {
    setReplaceTargetId(null);
  }

  async function handleReplaceSubmit() {
    if (!replaceTargetId || !replaceWorkerId) return;
    if (replaceReason.trim().length < 10) {
      setReplaceReasonError("Reason must be at least 10 characters.");
      return;
    }
    setReplaceReasonError("");
    setReplacing(true);
    setReplaceMessage("");
    try {
      await assignmentsService.replaceWorker(
        replaceTargetId,
        replaceWorkerId,
        replaceReason.trim(),
      );
      setReplaceTargetId(null);
      await queryClient.invalidateQueries({
        queryKey: ["requirement-assignments", requirementId],
      });
      await queryClient.invalidateQueries({
        queryKey: ["worker-matches", requirementId],
      });
      refetch();
    } catch (err) {
      setReplaceMessage(getErrorMessage(err));
    } finally {
      setReplacing(false);
    }
  }

  if (isLoading) {
    return <AssignmentsLoading />;
  }

  if (isError) {
    return <AssignmentsError message={error?.message} />;
  }

  const assignments = data?.data || [];
  // Only count workers who have confirmed (accepted/active/completed) — not just invited
  const confirmedAssignments = assignments.filter((item) =>
    ["accepted", "active", "completed"].includes(item.status),
  );
  const pendingAssignments = assignments.filter(
    (item) => item.status === "assigned",
  );
  const assignedCount = confirmedAssignments.length;
  const neededCount = Math.max((requiredWorkers ?? assignedCount) - assignedCount, 0);
  const isComplete = neededCount === 0 && (requiredWorkers ?? 0) > 0;

  const progressPercent = requiredWorkers
    ? Math.min(100, Math.round((assignedCount / requiredWorkers) * 100))
    : confirmedAssignments.length
      ? 100
      : 0;

  return (
    <section className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
      <div className="border-b border-border bg-[#FAFAF9] px-5 py-5">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
          <div className="flex min-w-0 flex-1 items-start gap-4">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-[#EDFAF3] text-[#1A6640]">
              {isComplete ? (
                <CheckCircle2 className="size-5" />
              ) : (
                <UserCheck className="size-5" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="font-display text-xl font-semibold text-foreground">
                Assignment progress
              </h3>
              <p className="mt-1 text-sm text-muted-foreground">
                {requiredWorkers
                  ? `${assignedCount} of ${requiredWorkers} workers confirmed`
                  : `${assignedCount} workers confirmed`}
                {pendingAssignments.length > 0
                  ? ` · ${pendingAssignments.length} awaiting response`
                  : ""}
              </p>
              <div className="mt-4 h-2 overflow-hidden rounded-full bg-[#E7E5E4]">
                <div
                  className="h-full rounded-full bg-[#1A6640] transition-all"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div
              className={
                isComplete
                  ? "rounded-full bg-[#DCFCE7] px-3 py-1 text-xs font-medium text-[#15803D]"
                  : "rounded-full bg-[#FEF3C7] px-3 py-1 text-xs font-medium text-[#B45309]"
              }
            >
              {isComplete ? "Assignment complete" : `${neededCount} more needed`}
            </div>
            {canAddWorkers ? (
              <Button
                type="button"
                variant="accent"
                size="sm"
                onClick={onAddWorkers}
              >
                <Plus className="size-4" />
                Add Workers
              </Button>
            ) : null}
          </div>
        </div>
      </div>

      {!assignments.length ? (
        <div className="px-6 py-10 text-center">
          <div className="mx-auto flex size-11 items-center justify-center rounded-full bg-secondary text-muted-foreground">
            <ClipboardList className="size-5" />
          </div>
          <h3 className="mt-4 text-base font-medium text-foreground">
            No workers assigned yet
          </h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Use the add-worker panel below once the request is approved.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-[1180px] table-fixed">
            <colgroup>
              <col className="w-[120px]" />
              <col className="w-[210px]" />
              <col className="w-[150px]" />
              <col className="w-[170px]" />
              <col className="w-[160px]" />
              <col className="w-[110px]" />
              <col className="w-[120px]" />
              <col className="w-[260px]" />
            </colgroup>
            <thead className="bg-[#FAFAF9]">
              <tr className="border-b border-border">
                <TableHead>Assignment</TableHead>
                <TableHead>Worker</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Shift</TableHead>
                <TableHead>Dates</TableHead>
                <TableHead>Payout</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Manage</TableHead>
              </tr>
            </thead>

            <tbody>
              {assignments.map((item) => (
                <tr
                  key={item.id}
                  className="border-b border-muted transition hover:bg-[#FAFAF9] last:border-b-0"
                >
                  <td className="align-middle whitespace-nowrap px-4 py-4">
                    <div className="font-mono text-sm font-medium text-foreground">
                      ASN-{item.id}
                    </div>
                  </td>
                  <td className="align-middle px-4 py-4 text-sm">
                    <div className="truncate font-medium text-foreground">
                      {item.worker_name}
                    </div>
                    <div className="mt-1 truncate text-xs text-muted-foreground">
                      #{item.worker_profile_id}
                      {item.worker_city ? ` - ${item.worker_city}` : ""}
                    </div>
                  </td>
                  <td className="align-middle px-4 py-4 text-sm text-foreground">
                    <span className="block truncate">
                      {item.assigned_role || "-"}
                    </span>
                  </td>
                  <td className="align-middle px-4 py-4 text-sm text-foreground">
                    <span className="block truncate">
                      {item.assigned_shift || "-"}
                    </span>
                  </td>
                  <td className="align-middle px-4 py-4 font-mono text-xs text-foreground">
                    {item.start_date ? (
                      <span>
                        {formatShortDate(item.start_date)}
                        {item.end_date ? (
                          <><br /><span className="text-muted-foreground">→ {formatShortDate(item.end_date)}</span></>
                        ) : null}
                      </span>
                    ) : (
                      <span className="text-muted-foreground text-xs">Full req.</span>
                    )}
                  </td>
                  <td className="align-middle whitespace-nowrap px-4 py-4 font-mono text-sm text-foreground">
                    {item.salary_amount
                      ? `Rs. ${item.salary_amount.toLocaleString("en-IN")}`
                      : "-"}
                  </td>
                  <td className="align-middle px-4 py-4 text-sm">
                    <div className="flex flex-col gap-1">
                      <StatusBadge value={item.status} />
                      {item.status === "assigned" &&
                        item.response_deadline &&
                        new Date(item.response_deadline) < new Date() ? (
                          <span className="whitespace-nowrap rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-semibold text-red-700">
                            Response overdue
                          </span>
                        ) : null}
                    </div>
                  </td>
                  <td className="align-middle px-4 py-4 text-right text-sm">
                    <div className="flex items-center justify-end gap-3">
                      <UpdateAssignmentStatus
                        assignmentId={item.id}
                        currentStatus={item.status}
                        onSuccess={() => refetch()}
                      />
                      {item.status === "assigned" ||
                      item.status === "accepted" ||
                      item.status === "active" ? (
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          onClick={() => handleOpenReplace(item.id)}
                          title="Replace this worker with another"
                        >
                          <RefreshCw className="size-3.5" />
                          Replace
                        </Button>
                      ) : null}
                      {canAddWorkers &&
                        onReplace &&
                        (item.status === "declined" || item.status === "cancelled") ? (
                          <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            onClick={() => onReplace(buildHint(item))}
                            title="Open assignment form pre-filled with this worker's slot"
                          >
                            <RefreshCw className="size-3.5" />
                            Replace
                          </Button>
                        ) : null}
                      <Link
                        href={`/assignments/${item.id}`}
                        className="whitespace-nowrap rounded-lg px-2 py-1 text-xs font-medium text-primary hover:bg-[#EDFAF3]"
                      >
                        Attendance
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Dialog open={replaceTargetId !== null} onOpenChange={(open) => { if (!open) handleCloseReplace(); }}>
        <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Replace Worker</DialogTitle>
            <DialogDescription>
              Select a replacement and provide a reason. The current worker will be marked as replaced.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <input
                value={replaceQuery}
                onChange={(e) => setReplaceQuery(e.target.value)}
                placeholder="Search by name, skill or city"
                className="h-10 w-full rounded-lg border border-input bg-white pl-9 pr-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            {matchesLoading ? (
              <p className="text-sm text-muted-foreground">Loading worker matches…</p>
            ) : visibleReplaceMatches.length === 0 ? (
              <p className="rounded-xl border border-dashed border-border bg-[#FAFAF9] p-4 text-sm text-muted-foreground">
                {allMatches.length === 0
                  ? "No worker matches found for this requirement."
                  : "No available workers match this search."}
              </p>
            ) : (
              <div className="grid gap-2 sm:grid-cols-2">
                {visibleReplaceMatches.map((worker) => {
                  const selected = replaceWorkerId === worker.worker_profile_id;
                  return (
                    <button
                      key={worker.worker_profile_id}
                      type="button"
                      onClick={() => setReplaceWorkerId(worker.worker_profile_id)}
                      className={`rounded-xl border p-3 text-left text-sm transition ${
                        selected
                          ? "border-[#1A6640] bg-[#EDFAF3] shadow-sm"
                          : "border-border bg-white hover:border-[#1A6640]"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span
                              className={`flex size-4 items-center justify-center rounded-full border ${
                                selected
                                  ? "border-[#1A6640] bg-[#1A6640] text-white"
                                  : "border-border bg-white text-transparent"
                              }`}
                            >
                              <Check className="size-3" />
                            </span>
                            <p className="font-semibold text-foreground truncate">{worker.full_name}</p>
                          </div>
                          <p className="mt-1 text-xs text-muted-foreground truncate">
                            {worker.category} · {worker.city}, {worker.state}
                          </p>
                        </div>
                        <div className="flex shrink-0 flex-col items-end gap-1">
                          <span className="rounded-full bg-[#F5F5F4] px-2 py-0.5 text-xs font-semibold text-muted-foreground">
                            {worker.score}
                          </span>
                          {worker.has_interest ? (
                            <span className="rounded-full bg-[#DCFCE7] px-2 py-0.5 text-[10px] font-semibold text-[#15803D]">
                              Interested
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}

            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">
                Replacement reason <span className="text-red-500">*</span>
              </label>
              <textarea
                className="min-h-20 w-full rounded-lg border border-input bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={replaceReason}
                onChange={(e) => setReplaceReason(e.target.value)}
                placeholder="Explain why this worker is being replaced (min 10 chars)"
              />
              {replaceReasonError ? (
                <p className="mt-1 text-xs text-red-600">{replaceReasonError}</p>
              ) : null}
            </div>

            {replaceMessage ? (
              <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                {replaceMessage}
              </div>
            ) : null}
          </div>

          <DialogFooter>
            <Button type="button" variant="secondary" onClick={handleCloseReplace}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="accent"
              disabled={replacing || !replaceWorkerId}
              onClick={handleReplaceSubmit}
            >
              {replacing ? "Replacing…" : "Replace Worker"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}

function isAssignableWorker(worker: WorkerMatch) {
  return (
    worker.is_available &&
    ["approved", "verified"].includes(worker.verification_status) &&
    !worker.reasons.some((reason) => reason.startsWith("not available")) &&
    !worker.conflict
  );
}

function buildHint(item: AssignmentItem): ReplacementHint {
  return {
    assignedRole: item.assigned_role,
    assignedShift: item.assigned_shift,
    startDate: item.start_date,
    endDate: item.end_date,
    salaryAmount: item.salary_amount,
  };
}

function formatShortDate(value: string) {
  const d = new Date(value);
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
  }).format(d);
}

function TableHead({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <th
      scope="col"
      className={`whitespace-nowrap px-4 py-3 text-left text-[13px] font-medium text-muted-foreground ${className}`}
    >
      {children}
    </th>
  );
}
