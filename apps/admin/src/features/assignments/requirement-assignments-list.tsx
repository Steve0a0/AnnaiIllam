"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { CheckCircle2, ClipboardList, Plus, UserCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRequirementAssignments } from "@/features/assignments/use-requirement-assignments";
import AssignmentsLoading from "@/features/assignments/assignments-loading";
import AssignmentsError from "@/features/assignments/assignments-error";
import StatusBadge from "@/components/shared/status-badge";
import UpdateAssignmentStatus from "@/features/assignments/update-assignment-status";

export default function RequirementAssignmentsList({
  requirementId,
  requiredWorkers,
  canAddWorkers = false,
  onAddWorkers,
}: {
  requirementId: number;
  requiredWorkers?: number;
  canAddWorkers?: boolean;
  onAddWorkers?: () => void;
}) {
  const { data, isLoading, isError, error, refetch } =
    useRequirementAssignments(requirementId);

  if (isLoading) {
    return <AssignmentsLoading />;
  }

  if (isError) {
    return <AssignmentsError message={error?.message} />;
  }

  const assignments = data?.data || [];
  const activeAssignments = assignments.filter(
    (item) => item.status !== "declined" && item.status !== "replaced",
  );
  const assignedCount = activeAssignments.length;
  const neededCount = Math.max((requiredWorkers ?? assignedCount) - assignedCount, 0);
  const isComplete = neededCount === 0 && (requiredWorkers ?? 0) > 0;

  const progressPercent = requiredWorkers
    ? Math.min(100, Math.round((assignedCount / requiredWorkers) * 100))
    : assignments.length
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
                  ? `${assignedCount} of ${requiredWorkers} workers assigned`
                  : `${assignedCount} workers assigned`}
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
          <table className="min-w-[1040px] table-fixed">
            <colgroup>
              <col className="w-[120px]" />
              <col className="w-[240px]" />
              <col className="w-[170px]" />
              <col className="w-[190px]" />
              <col className="w-[120px]" />
              <col className="w-[130px]" />
              <col className="w-[270px]" />
            </colgroup>
            <thead className="bg-[#FAFAF9]">
              <tr className="border-b border-border">
                <TableHead>Assignment</TableHead>
                <TableHead>Worker</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Shift</TableHead>
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
                  <td className="align-middle whitespace-nowrap px-4 py-4 font-mono text-sm text-foreground">
                    {item.salary_amount
                      ? `Rs. ${item.salary_amount.toLocaleString("en-IN")}`
                      : "-"}
                  </td>
                  <td className="align-middle px-4 py-4 text-sm">
                    <StatusBadge value={item.status} />
                  </td>
                  <td className="align-middle px-4 py-4 text-right text-sm">
                    <div className="flex items-center justify-end gap-3">
                      <UpdateAssignmentStatus
                        assignmentId={item.id}
                        currentStatus={item.status}
                        onSuccess={() => refetch()}
                      />
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
    </section>
  );
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
