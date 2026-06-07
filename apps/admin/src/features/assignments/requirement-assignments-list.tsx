"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Check, ChevronDown, ChevronRight, ClipboardList, RefreshCw, Search } from "lucide-react";
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
}: {
  requirementId: number;
  requiredWorkers?: number;
}) {
  const { data, isLoading, isError, error, refetch } =
    useRequirementAssignments(requirementId);
  const queryClient = useQueryClient();

  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
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

  const { data: coverageData } = useQuery({
    queryKey: ["coverage-calendar", requirementId],
    queryFn: () => assignmentsService.getCoverageCalendar(requirementId),
    staleTime: 30_000,
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
  const groupedAssignments = useMemo(
    () => groupAssignments(data?.data ?? []),
    [data],
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
      await queryClient.invalidateQueries({
        queryKey: ["coverage-calendar", requirementId],
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
  const pendingAssignments = assignments.filter((item) => item.status === "assigned");

  const coverageDays = coverageData?.data?.days ?? [];
  const totalDays = coverageDays.length;
  const fullDays = coverageDays.filter((d) => d.coverage_status === "full").length;
  const partialDays = coverageDays.filter((d) => d.coverage_status === "partial").length;
  const uncoveredDays = coverageDays.filter((d) => d.coverage_status === "uncovered").length;
  const dayProgressPercent = totalDays > 0 ? Math.round((fullDays / totalDays) * 100) : 0;
  const allDaysCovered = totalDays > 0 && fullDays === totalDays;

  return (
    <section className="overflow-hidden rounded-xl border border-[oklch(0.90_0.003_145)] bg-white">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[oklch(0.90_0.003_145)] px-5 py-4">
        <div className="flex min-w-0 flex-1 items-center gap-5">
          <div>
            <p className="text-[14px] font-semibold text-[oklch(0.20_0.006_145)]">Day coverage</p>
            <p className="mt-0.5 text-[13px] text-[oklch(0.44_0.005_145)]">
              {totalDays > 0
                ? `${fullDays} of ${totalDays} days fully covered`
                : `${assignments.length} worker${assignments.length !== 1 ? "s" : ""} assigned`}
              {pendingAssignments.length > 0
                ? ` · ${pendingAssignments.length} awaiting response`
                : ""}
            </p>
          </div>
          {totalDays > 0 && (
            <div className="hidden min-w-0 flex-1 flex-col sm:flex" style={{ maxWidth: 160 }}>
              <div className="h-1.5 overflow-hidden rounded-full bg-[oklch(0.90_0.003_145)]">
                <div
                  className="h-full rounded-full bg-[oklch(0.42_0.115_145)] transition-all"
                  style={{ width: `${dayProgressPercent}%` }}
                />
              </div>
              <p className="mt-1 font-mono text-[11px] text-[oklch(0.48_0.005_145)]">{dayProgressPercent}%</p>
            </div>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2.5">
          {totalDays > 0 && (
            <span
              className={
                allDaysCovered
                  ? "rounded-full bg-[oklch(0.91_0.026_145)] px-2.5 py-1 text-[12px] font-medium text-[oklch(0.34_0.094_145)]"
                  : uncoveredDays > 0
                    ? "rounded-full bg-[#FEE2E2] px-2.5 py-1 text-[12px] font-medium text-[#B91C1C]"
                    : "rounded-full bg-[#FEF3C7] px-2.5 py-1 text-[12px] font-medium text-[#B45309]"
              }
            >
              {allDaysCovered
                ? "All days covered"
                : uncoveredDays > 0
                  ? `${uncoveredDays} day${uncoveredDays !== 1 ? "s" : ""} uncovered`
                  : `${partialDays} day${partialDays !== 1 ? "s" : ""} partial`}
            </span>
          )}
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
          <table className="min-w-[820px] table-fixed">
            <colgroup>
              <col className="w-[220px]" />
              <col className="w-[200px]" />
              <col className="w-[130px]" />
              <col className="w-[100px]" />
              <col className="w-[130px]" />
              <col />
            </colgroup>
            <thead className="bg-[oklch(0.97_0.008_145)]">
              <tr className="border-b border-[oklch(0.90_0.003_145)]">
                <TableHead>Worker</TableHead>
                <TableHead>Role &amp; shift</TableHead>
                <TableHead>Dates</TableHead>
                <TableHead>Pay</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </tr>
            </thead>

            <tbody>
              {groupedAssignments.map((group) => {
                const isExpanded = expandedGroups.has(group.key);
                const isMulti = group.assignments.length > 1;
                return (
                  <>
                    {/* Group summary row */}
                    <tr
                      key={group.key}
                      className="border-b border-[oklch(0.95_0.013_145)] transition hover:bg-[oklch(0.97_0.008_145)]"
                    >
                      <td className="px-4 py-3.5 align-middle">
                        <div className="flex items-center gap-2.5">
                          {isMulti && (
                            <button
                              type="button"
                              onClick={() =>
                                setExpandedGroups((prev) => {
                                  const next = new Set(prev);
                                  if (next.has(group.key)) next.delete(group.key);
                                  else next.add(group.key);
                                  return next;
                                })
                              }
                              className="shrink-0 rounded p-0.5 text-[oklch(0.44_0.005_145)] hover:bg-[oklch(0.91_0.026_145)]"
                            >
                              {isExpanded ? <ChevronDown className="size-3.5" /> : <ChevronRight className="size-3.5" />}
                            </button>
                          )}
                          <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-[oklch(0.91_0.026_145)] text-[12px] font-semibold text-[oklch(0.34_0.094_145)]">
                            {group.worker_name.split(" ").map((n: string) => n[0]).join("").slice(0, 2).toUpperCase()}
                          </div>
                          <div className="min-w-0">
                            <p className="truncate text-[14px] font-semibold text-[oklch(0.20_0.006_145)]">
                              {group.worker_name}
                            </p>
                            <p className="font-mono text-[11px] text-[oklch(0.48_0.005_145)]">
                              {group.worker_city ?? ""}
                              {isMulti ? ` · ${group.assignments.length} days` : group.worker_city ? "" : ""}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3.5 align-middle">
                        <p className="truncate text-[13px] text-[oklch(0.20_0.006_145)]">
                          {group.assignments[0].assigned_role || "—"}
                        </p>
                        {group.assignments[0].assigned_shift && (
                          <p className="mt-0.5 truncate text-[12px] text-[oklch(0.44_0.005_145)]">
                            {group.assignments[0].assigned_shift}
                          </p>
                        )}
                      </td>
                      <td className="px-4 py-3.5 align-middle">
                        {isMulti ? (
                          <div className="flex flex-nowrap items-center gap-1">
                            {group.assignments.slice(0, 3).map((a) => (
                              <span
                                key={a.id}
                                className="rounded-md bg-[oklch(0.91_0.026_145)] px-1.5 py-0.5 font-mono text-[11px] font-medium text-[oklch(0.34_0.094_145)]"
                              >
                                {formatShortDate(a.start_date ?? "")}
                              </span>
                            ))}
                            {group.assignments.length > 3 && (
                              <span className="rounded-md bg-[oklch(0.95_0.013_145)] px-1.5 py-0.5 font-mono text-[11px] text-[oklch(0.48_0.005_145)]">
                                +{group.assignments.length - 3}
                              </span>
                            )}
                          </div>
                        ) : group.earliestStart ? (
                          <span className="font-mono text-[12px] text-[oklch(0.20_0.006_145)]">
                            {formatShortDate(group.earliestStart)}
                          </span>
                        ) : (
                          <span className="font-mono text-[12px] text-[oklch(0.62_0.004_145)]">Full req.</span>
                        )}
                      </td>
                      <td className="px-4 py-3.5 align-middle font-mono">
                        <span className="text-[13px] text-[oklch(0.20_0.006_145)]">
                          {group.assignments[0].salary_amount
                            ? `₹${group.assignments[0].salary_amount.toLocaleString("en-IN")}`
                            : "—"}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 align-middle">
                        <StatusBadge value={group.status} />
                      </td>
                      <td className="px-4 py-3.5 align-middle text-right">
                        {!isMulti && (
                          <div className="flex items-center justify-end gap-2">
                            <UpdateAssignmentStatus
                              assignmentId={group.assignments[0].id}
                              currentStatus={group.assignments[0].status}
                              onSuccess={() => {
                                refetch();
                                queryClient.invalidateQueries({ queryKey: ["coverage-calendar", requirementId] });
                              }}
                            />
                            {["assigned", "accepted", "active"].includes(group.assignments[0].status) && (
                              <Button type="button" variant="ghost" size="sm" onClick={() => handleOpenReplace(group.assignments[0].id)} title="Replace">
                                <RefreshCw className="size-3.5" />
                              </Button>
                            )}
                            <Link href={`/assignments/${group.assignments[0].id}`} className="whitespace-nowrap rounded-lg px-2.5 py-1.5 text-[12px] font-medium text-[oklch(0.42_0.115_145)] transition hover:bg-[oklch(0.95_0.013_145)]">
                              Attendance
                            </Link>
                          </div>
                        )}
                        {isMulti && (
                          <button
                            type="button"
                            onClick={() =>
                              setExpandedGroups((prev) => {
                                const next = new Set(prev);
                                if (next.has(group.key)) next.delete(group.key);
                                else next.add(group.key);
                                return next;
                              })
                            }
                            className="text-[12px] font-medium text-[oklch(0.42_0.115_145)] hover:underline"
                          >
                            {isExpanded ? "Collapse" : `Show ${group.assignments.length} rows`}
                          </button>
                        )}
                      </td>
                    </tr>

                    {/* Expanded individual sub-rows */}
                    {isMulti && isExpanded && group.assignments.map((item) => (
                      <tr
                        key={item.id}
                        className="border-b border-[oklch(0.95_0.013_145)] bg-[oklch(0.97_0.008_145)] transition hover:bg-[oklch(0.95_0.013_145)]"
                      >
                        <td className="py-2.5 pl-14 pr-4 align-middle">
                          <p className="font-mono text-[11px] text-[oklch(0.48_0.005_145)]">
                            ASN-{item.id}
                          </p>
                        </td>
                        <td className="px-4 py-2.5 align-middle" />
                        <td className="px-4 py-2.5 align-middle font-mono">
                          {item.start_date ? (
                            <p className="text-[12px] text-[oklch(0.20_0.006_145)]">
                              {formatShortDate(item.start_date)}
                              {item.end_date && item.end_date !== item.start_date
                                ? ` – ${formatShortDate(item.end_date)}`
                                : ""}
                            </p>
                          ) : (
                            <span className="text-[12px] text-[oklch(0.62_0.004_145)]">Full req.</span>
                          )}
                        </td>
                        <td className="px-4 py-2.5 align-middle font-mono">
                          <span className="text-[12px] text-[oklch(0.48_0.005_145)]">
                            {item.salary_amount ? `₹${item.salary_amount.toLocaleString("en-IN")}` : "—"}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 align-middle">
                          <div className="flex flex-col gap-1">
                            <StatusBadge value={item.status} />
                            {item.status === "assigned" && item.response_deadline && new Date(item.response_deadline) < new Date() ? (
                              <span className="whitespace-nowrap rounded-full bg-[#FEE2E2] px-2 py-0.5 text-[10px] font-semibold text-[#B91C1C]">Response overdue</span>
                            ) : null}
                          </div>
                        </td>
                        <td className="px-4 py-2.5 align-middle text-right">
                          <div className="flex items-center justify-end gap-2">
                            <UpdateAssignmentStatus
                              assignmentId={item.id}
                              currentStatus={item.status}
                              onSuccess={() => {
                                refetch();
                                queryClient.invalidateQueries({ queryKey: ["coverage-calendar", requirementId] });
                              }}
                            />
                            {["assigned", "accepted", "active"].includes(item.status) && (
                              <Button type="button" variant="ghost" size="sm" onClick={() => handleOpenReplace(item.id)} title="Replace">
                                <RefreshCw className="size-3.5" />
                              </Button>
                            )}
                            <Link href={`/assignments/${item.id}`} className="whitespace-nowrap rounded-lg px-2.5 py-1.5 text-[12px] font-medium text-[oklch(0.42_0.115_145)] transition hover:bg-[oklch(0.95_0.013_145)]">
                              Attendance
                            </Link>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </>
                );
              })}
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

type AssignmentGroup = {
  key: string;
  worker_profile_id: number;
  worker_name: string;
  worker_city: string | null;
  assignments: AssignmentItem[];
  earliestStart: string | null;
  latestEnd: string | null;
  status: string;
};

function groupAssignments(items: AssignmentItem[]): AssignmentGroup[] {
  // Sort by worker name then date so same-worker assignments are adjacent
  const sorted = [...items].sort((a, b) => {
    const nameCompare = a.worker_name.localeCompare(b.worker_name);
    if (nameCompare !== 0) return nameCompare;
    return (a.start_date ?? "").localeCompare(b.start_date ?? "");
  });
  const groups: AssignmentGroup[] = [];
  for (const item of sorted) {
    const last = groups[groups.length - 1];
    // Group all assignments for the same worker+status together (not just consecutive)
    const sameGroup =
      last &&
      last.worker_profile_id === item.worker_profile_id &&
      last.status === item.status;
    if (sameGroup) {
      last.assignments.push(item);
      if (item.end_date && (!last.latestEnd || item.end_date > last.latestEnd)) {
        last.latestEnd = item.end_date;
      }
    } else {
      groups.push({
        key: `${item.worker_profile_id}-${item.status}-${groups.length}`,
        worker_profile_id: item.worker_profile_id,
        worker_name: item.worker_name,
        worker_city: item.worker_city,
        assignments: [item],
        earliestStart: item.start_date,
        latestEnd: item.end_date,
        status: item.status,
      });
    }
  }
  return groups;
}

function isAssignableWorker(worker: WorkerMatch) {
  return (
    worker.is_available &&
    ["approved", "verified"].includes(worker.verification_status) &&
    !worker.reasons.some((reason) => reason.startsWith("not available")) &&
    !worker.conflict
  );
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
      className={`whitespace-nowrap px-4 py-2.5 text-left text-[12px] font-medium text-[oklch(0.48_0.005_145)] ${className}`}
    >
      {children}
    </th>
  );
}
