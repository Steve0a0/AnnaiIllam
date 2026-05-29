"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, LogOut, Pencil, XCircle, X } from "lucide-react";
import PageHeader from "@/components/shared/page-header";
import LoadingState from "@/components/shared/loading-state";
import EmptyState from "@/components/shared/empty-state";
import ErrorState from "@/components/shared/error-state";
import StatusBadge from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import CorrectAttendanceForm from "@/features/attendance/correct-attendance-form";
import { attendanceService } from "@/services/attendance.service";
import { getErrorMessage } from "@/lib/get-error-message";
import type { AttendanceItem } from "@/types/attendance";

// ── helpers ───────────────────────────────────────────────────────────────────

function todayISO() {
  return new Date().toISOString().split("T")[0];
}

function formatTime(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}

function calcHours(checkIn: string | null, checkOut: string | null) {
  if (!checkIn || !checkOut) return "—";
  const diffH =
    (new Date(checkOut).getTime() - new Date(checkIn).getTime()) / 3_600_000;
  return diffH > 0 ? `${diffH.toFixed(1)}h` : "—";
}

const STATUS_OPTIONS = [
  { label: "All", value: "" },
  { label: "Present", value: "present" },
  { label: "Absent", value: "absent" },
  { label: "No-show", value: "no_show" },
  { label: "Late", value: "late" },
  { label: "Half day", value: "half_day" },
  { label: "Corrected", value: "corrected" },
  { label: "Excused", value: "excused" },
];

type SummaryTone = "neutral" | "success" | "warning" | "danger";

function SummaryCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: SummaryTone;
}) {
  const bg: Record<SummaryTone, string> = {
    neutral: "bg-white",
    success: "bg-green-50",
    warning: "bg-amber-50",
    danger: "bg-red-50",
  };
  const textColor: Record<SummaryTone, string> = {
    neutral: "text-foreground",
    success: "text-green-700",
    warning: "text-amber-700",
    danger: "text-red-700",
  };
  return (
    <Card className={`border-border shadow-sm ${bg[tone]}`}>
      <CardContent className="p-4">
        <p className={`text-2xl font-bold ${textColor[tone]}`}>{value}</p>
        <p className="mt-0.5 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          {label}
        </p>
      </CardContent>
    </Card>
  );
}

// ── page ──────────────────────────────────────────────────────────────────────

export default function AttendancePage() {
  const queryClient = useQueryClient();

  const [dateFilter, setDateFilter] = useState(todayISO());
  const [requirementIdInput, setRequirementIdInput] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const [correctingRecord, setCorrectingRecord] = useState<AttendanceItem | null>(null);
  const [rejectingRecord, setRejectingRecord] = useState<AttendanceItem | null>(null);
  const [rejectNotes, setRejectNotes] = useState("");
  const [rejectNotesError, setRejectNotesError] = useState("");
  const [closingRecord, setClosingRecord] = useState<AttendanceItem | null>(null);
  const [closeNotes, setCloseNotes] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  const reqId =
    requirementIdInput.trim() ? parseInt(requirementIdInput.trim(), 10) : undefined;
  const queryParams = {
    date: dateFilter || undefined,
    requirement_id: reqId,
    status: statusFilter || undefined,
  };
  const queryKey = ["attendance-list", queryParams];

  const { data: response, isLoading, isError, error, refetch } = useQuery({
    queryKey,
    queryFn: () => attendanceService.listAll(queryParams),
    staleTime: 30_000,
  });
  const records: AttendanceItem[] = response?.data ?? [];

  const { mutate: approve, isPending: isApproving } = useMutation({
    mutationFn: ({ id }: { id: number }) => attendanceService.approveAttendance(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      setActionError(null);
    },
    onError: (err) => setActionError(getErrorMessage(err)),
  });

  const { mutate: reject, isPending: isRejecting } = useMutation({
    mutationFn: ({ id, notes }: { id: number; notes: string }) =>
      attendanceService.rejectAttendance(id, notes),
    onSuccess: () => {
      setRejectingRecord(null);
      setRejectNotes("");
      queryClient.invalidateQueries({ queryKey });
      setActionError(null);
    },
    onError: (err) => setActionError(getErrorMessage(err)),
  });

  const { mutate: closeShift, isPending: isClosingShift } = useMutation({
    mutationFn: ({ id, notes }: { id: number; notes: string }) =>
      attendanceService.closeShift(id, notes || undefined),
    onSuccess: () => {
      setClosingRecord(null);
      setCloseNotes("");
      queryClient.invalidateQueries({ queryKey });
      setActionError(null);
    },
    onError: (err) => setActionError(getErrorMessage(err)),
  });

  function handleCloseShiftSubmit() {
    if (!closingRecord) return;
    closeShift({ id: closingRecord.id, notes: closeNotes.trim() });
  }

  function handleCorrectionSuccess() {
    setCorrectingRecord(null);
    queryClient.invalidateQueries({ queryKey });
  }

  function handleRejectSubmit() {
    if (!rejectingRecord) return;
    if (!rejectNotes.trim()) {
      setRejectNotesError("Rejection reason is required.");
      return;
    }
    setRejectNotesError("");
    reject({ id: rejectingRecord.id, notes: rejectNotes.trim() });
  }

  const total = records.length;
  const approvedCount = records.filter((r) => r.approval_status === "approved").length;
  const rejectedCount = records.filter((r) => r.approval_status === "rejected").length;
  const pendingApproval = records.filter((r) => !r.approval_status || r.approval_status === "pending").length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance"
        description="Reconcile daily attendance across all active jobs."
      />

      {/* ── Filter bar ──────────────────────────────────────────────────── */}
      <Card className="border-border bg-white shadow-sm">
        <CardHeader className="pb-3 pt-5 px-5">
          <CardTitle className="text-sm font-medium text-muted-foreground">Filters</CardTitle>
        </CardHeader>
        <CardContent className="px-5 pb-5 space-y-4">
          {/* Row 1: Date + Requirement ID */}
          <div className="flex flex-wrap gap-3 items-end">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-muted-foreground">Date</label>
              <Input
                type="date"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="w-44"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-muted-foreground">
                Requirement ID
              </label>
              <div className="relative">
                <Input
                  type="number"
                  min={1}
                  placeholder="e.g. 42"
                  value={requirementIdInput}
                  onChange={(e) => setRequirementIdInput(e.target.value)}
                  className="w-36 pr-7"
                />
                {requirementIdInput && (
                  <button
                    type="button"
                    onClick={() => setRequirementIdInput("")}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    aria-label="Clear"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Row 2: Status buttons */}
          <div className="flex flex-wrap gap-1">
            {STATUS_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setStatusFilter(opt.value)}
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  statusFilter === opt.value
                    ? "bg-primary text-primary-foreground"
                    : "border border-input bg-background text-muted-foreground hover:text-foreground"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ── Loading ─────────────────────────────────────────────────────── */}
      {isLoading && (
        <LoadingState title="Loading attendance" description="Fetching records…" />
      )}

      {/* ── Error ───────────────────────────────────────────────────────── */}
      {!isLoading && isError && (
        <ErrorState
          title="Could not load attendance records"
          description={error ? getErrorMessage(error) : "Please try again."}
          onRetry={() => refetch()}
        />
      )}

      {/* ── Action error banner ─────────────────────────────────────────── */}
      {actionError && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {actionError}
        </div>
      )}

      {/* ── Results ─────────────────────────────────────────────────────── */}
      {!isLoading && !isError && (
        <>
          {total > 0 && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <SummaryCard label="Total" value={total} tone="neutral" />
              <SummaryCard label="Approved" value={approvedCount} tone="success" />
              <SummaryCard label="Pending approval" value={pendingApproval} tone="warning" />
              <SummaryCard label="Rejected" value={rejectedCount} tone="danger" />
            </div>
          )}

          {records.length === 0 ? (
            <EmptyState
              title="No attendance records"
              description={`No records for ${dateFilter || "today"}${reqId ? ` on requirement #${reqId}` : ""}${statusFilter ? ` with status "${statusFilter}"` : ""}.`}
            />
          ) : (
            <Card className="border-border bg-white shadow-sm">
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Worker</TableHead>
                      <TableHead className="hidden sm:table-cell">Req</TableHead>
                      <TableHead className="hidden md:table-cell">Assignment</TableHead>
                      <TableHead className="hidden lg:table-cell">Check-in</TableHead>
                      <TableHead className="hidden lg:table-cell">Check-out</TableHead>
                      <TableHead className="hidden lg:table-cell">Hours</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="hidden sm:table-cell">Approval</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {records.map((record) => (
                      <TableRow key={record.id}>
                        <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                          {record.attendance_date}
                        </TableCell>
                        <TableCell className="font-medium">{record.worker_name}</TableCell>
                        <TableCell className="hidden sm:table-cell text-sm text-muted-foreground">
                          {record.requirement_id ? `#${record.requirement_id}` : "—"}
                        </TableCell>
                        <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                          #{record.assignment_id}
                        </TableCell>
                        <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                          {formatTime(record.check_in_time)}
                        </TableCell>
                        <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                          {formatTime(record.check_out_time)}
                        </TableCell>
                        <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                          {calcHours(record.check_in_time, record.check_out_time)}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap items-center gap-1.5">
                            <StatusBadge value={record.status} />
                            {record.check_in_time && !record.check_out_time && (
                              <span className="inline-flex items-center rounded-full border border-amber-300 bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700">
                                Open Shift
                              </span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="hidden sm:table-cell">
                          {record.approval_status ? (
                            <StatusBadge value={record.approval_status} />
                          ) : (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex gap-1 justify-end">
                            {record.approval_status !== "approved" && record.approval_status !== "rejected" && (
                              <>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="h-7 px-2 gap-1 text-xs"
                                  disabled={isApproving}
                                  onClick={() => approve({ id: record.id })}
                                >
                                  <CheckCircle2 className="h-3.5 w-3.5" />
                                  Approve
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="h-7 px-2 gap-1 text-xs text-destructive border-destructive/40 hover:bg-destructive/10"
                                  disabled={isRejecting}
                                  onClick={() => {
                                    setRejectingRecord(record);
                                    setRejectNotes("");
                                    setRejectNotesError("");
                                  }}
                                >
                                  <XCircle className="h-3.5 w-3.5" />
                                  Reject
                                </Button>
                              </>
                            )}
                            {record.check_in_time && !record.check_out_time && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-7 px-2 gap-1 text-xs text-amber-700 border-amber-300 hover:bg-amber-50"
                                onClick={() => { setClosingRecord(record); setCloseNotes(""); }}
                              >
                                <LogOut className="h-3.5 w-3.5" />
                                Close Shift
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 px-2 gap-1 text-xs"
                              onClick={() => setCorrectingRecord(record)}
                            >
                              <Pencil className="h-3.5 w-3.5" />
                              Correct
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* ── Correction dialog ────────────────────────────────────────────── */}
      <Dialog
        open={correctingRecord !== null}
        onOpenChange={(open) => !open && setCorrectingRecord(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit attendance record</DialogTitle>
            {correctingRecord && (
              <DialogDescription>
                {correctingRecord.worker_name} &middot;{" "}
                {correctingRecord.attendance_date} &middot; Assignment #
                {correctingRecord.assignment_id}
              </DialogDescription>
            )}
          </DialogHeader>
          {correctingRecord && (
            <CorrectAttendanceForm
              attendanceId={correctingRecord.id}
              currentStatus={correctingRecord.status}
              currentNotes={correctingRecord.notes}
              onSuccess={handleCorrectionSuccess}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* ── Close Shift dialog ──────────────────────────────────────────── */}
      <Dialog
        open={closingRecord !== null}
        onOpenChange={(open) => { if (!open) { setClosingRecord(null); setCloseNotes(""); } }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Close open shift</DialogTitle>
            {closingRecord && (
              <DialogDescription>
                {closingRecord.worker_name} &middot;{" "}
                {closingRecord.attendance_date} &middot; Checked in at{" "}
                {formatTime(closingRecord.check_in_time)}
              </DialogDescription>
            )}
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">
                Admin notes <span className="text-muted-foreground">(optional)</span>
              </label>
              <textarea
                className="min-h-20 w-full rounded-lg border border-input bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={closeNotes}
                onChange={(e) => setCloseNotes(e.target.value)}
                placeholder="Reason for manually closing this shift"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => { setClosingRecord(null); setCloseNotes(""); }}
            >
              Cancel
            </Button>
            <Button
              type="button"
              disabled={isClosingShift}
              onClick={handleCloseShiftSubmit}
            >
              {isClosingShift ? "Closing…" : "Close shift"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Reject dialog ───────────────────────────────────────────────── */}
      <Dialog
        open={rejectingRecord !== null}
        onOpenChange={(open) => { if (!open) { setRejectingRecord(null); setRejectNotes(""); setRejectNotesError(""); } }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject attendance record</DialogTitle>
            {rejectingRecord && (
              <DialogDescription>
                {rejectingRecord.worker_name} &middot;{" "}
                {rejectingRecord.attendance_date} &middot; Assignment #
                {rejectingRecord.assignment_id}
              </DialogDescription>
            )}
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">
                Reason for rejection <span className="text-red-500">*</span>
              </label>
              <textarea
                className="min-h-20 w-full rounded-lg border border-input bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={rejectNotes}
                onChange={(e) => setRejectNotes(e.target.value)}
                placeholder="Explain why this attendance record is being rejected"
              />
              {rejectNotesError && (
                <p className="mt-1 text-xs text-red-600">{rejectNotesError}</p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => { setRejectingRecord(null); setRejectNotes(""); setRejectNotesError(""); }}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={isRejecting}
              onClick={handleRejectSubmit}
            >
              {isRejecting ? "Rejecting…" : "Reject"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
