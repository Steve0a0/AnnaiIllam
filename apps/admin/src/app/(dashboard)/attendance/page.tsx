"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Search, X } from "lucide-react";
import PageHeader from "@/components/shared/page-header";
import LoadingState from "@/components/shared/loading-state";
import EmptyState from "@/components/shared/empty-state";
import ErrorState from "@/components/shared/error-state";
import StatusBadge from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import CorrectAttendanceForm from "@/features/attendance/correct-attendance-form";
import {
  useAttendanceLookup,
  type AttendanceLookupMode,
} from "@/features/attendance/use-attendance-lookup";
import { attendanceService } from "@/services/attendance.service";
import { getErrorMessage } from "@/lib/get-error-message";
import type { EnrichedAttendanceItem } from "@/types/attendance";

export default function AttendancePage() {
  const queryClient = useQueryClient();

  const [filterMode, setFilterMode] = useState<AttendanceLookupMode>("requirement");
  const [inputValue, setInputValue] = useState("");
  // committed search — triggers the query
  const [searchId, setSearchId] = useState<number | null>(null);
  const [activeMode, setActiveMode] = useState<AttendanceLookupMode>("requirement");

  const [verifyingId, setVerifyingId] = useState<number | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [correctingRecord, setCorrectingRecord] =
    useState<EnrichedAttendanceItem | null>(null);

  const {
    data: records = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useAttendanceLookup(searchId !== null ? activeMode : null, searchId);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const n = parseInt(inputValue.trim(), 10);
    if (!n || n <= 0) return;
    setSearchId(n);
    setActiveMode(filterMode);
    setVerifyError(null);
  }

  function handleModeSwitch(mode: AttendanceLookupMode) {
    setFilterMode(mode);
    setInputValue("");
    setSearchId(null);
    setVerifyError(null);
  }

  function handleClearInput() {
    setInputValue("");
    setSearchId(null);
    setVerifyError(null);
  }

  async function handleVerify(record: EnrichedAttendanceItem) {
    setVerifyingId(record.id);
    setVerifyError(null);
    try {
      await attendanceService.correctAttendance(record.id, {
        status: "approved",
        notes: "Verified by admin.",
      });
      queryClient.invalidateQueries({
        queryKey: ["attendance-lookup", activeMode, searchId],
      });
    } catch (err) {
      setVerifyError(getErrorMessage(err));
    } finally {
      setVerifyingId(null);
    }
  }

  function handleCorrectionSuccess() {
    setCorrectingRecord(null);
    queryClient.invalidateQueries({
      queryKey: ["attendance-lookup", activeMode, searchId],
    });
  }

  const hasSearch = searchId !== null;
  const total = records.length;
  const verified = records.filter((r) => r.status === "approved").length;
  const absent = records.filter((r) => r.status === "absent").length;
  const pending = total - verified - absent;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance"
        description="View and verify worker attendance records by requirement or assignment."
      />

      {/* ── Filter bar ──────────────────────────────────────────────────── */}
      <Card className="border-border bg-white shadow-sm">
        <CardContent className="p-5">
          <form
            onSubmit={handleSearch}
            className="flex flex-col gap-4 sm:flex-row sm:items-end"
          >
            {/* Mode toggle */}
            <div className="flex shrink-0 gap-1 rounded-lg border border-input bg-muted/40 p-1">
              {(["requirement", "assignment"] as AttendanceLookupMode[]).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => handleModeSwitch(m)}
                  className={`rounded-md px-4 py-1.5 text-sm font-medium capitalize transition-colors ${
                    filterMode === m
                      ? "bg-white text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  By {m} ID
                </button>
              ))}
            </div>

            {/* ID input + submit */}
            <div className="flex flex-1 gap-2">
              <div className="relative flex-1 max-w-xs">
                <Input
                  type="number"
                  min={1}
                  placeholder={
                    filterMode === "requirement"
                      ? "Requirement ID e.g. 42"
                      : "Assignment ID e.g. 18"
                  }
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  className="pr-8"
                />
                {inputValue && (
                  <button
                    type="button"
                    onClick={handleClearInput}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    aria-label="Clear"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
              <Button type="submit" disabled={!inputValue.trim()} className="gap-1.5">
                <Search className="h-4 w-4" />
                Load
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* ── No search yet ───────────────────────────────────────────────── */}
      {!hasSearch && (
        <EmptyState
          title="Enter an ID above to load records"
          description="Search by Requirement ID to see all workers on a job, or by Assignment ID for a single worker-job pairing."
        />
      )}

      {/* ── Loading ─────────────────────────────────────────────────────── */}
      {hasSearch && isLoading && (
        <LoadingState
          title="Loading attendance"
          description="Fetching records…"
        />
      )}

      {/* ── Error ───────────────────────────────────────────────────────── */}
      {hasSearch && isError && (
        <ErrorState
          title="Could not load attendance records"
          description={getErrorMessage(error)}
          onRetry={() => refetch()}
        />
      )}

      {/* ── Verify error banner ─────────────────────────────────────────── */}
      {verifyError && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {verifyError}
        </div>
      )}

      {/* ── Results ─────────────────────────────────────────────────────── */}
      {hasSearch && !isLoading && !isError && (
        <>
          {/* Summary strip */}
          {total > 0 && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <SummaryCard label="Total" value={total} tone="neutral" />
              <SummaryCard label="Verified" value={verified} tone="success" />
              <SummaryCard label="Pending review" value={pending} tone="warning" />
              <SummaryCard label="Absent" value={absent} tone="danger" />
            </div>
          )}

          {/* Empty results */}
          {records.length === 0 ? (
            <EmptyState
              title="No attendance records found"
              description={`No attendance has been recorded for ${activeMode} #${searchId} yet.`}
            />
          ) : (
            <Card className="overflow-hidden border-border bg-white shadow-sm">
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-muted/40">
                    <tr>
                      {[
                        "Worker",
                        "Date",
                        "Assignment",
                        "Check-in",
                        "Check-out",
                        "Hours",
                        "Status",
                        "Actions",
                      ].map((h) => (
                        <th
                          key={h}
                          className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-widest text-muted-foreground"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {records.map((record) => {
                      const hours = calcHours(
                        record.check_in_time,
                        record.check_out_time
                      );
                      const isVerified = record.status === "approved";
                      const isBusy = verifyingId === record.id;

                      return (
                        <tr
                          key={record.id}
                          className="transition-colors hover:bg-muted/30"
                        >
                          {/* Worker */}
                          <td className="px-4 py-3">
                            <p className="text-sm font-medium text-foreground">
                              {record.worker_name}
                            </p>
                            <p className="font-mono text-xs text-muted-foreground">
                              Profile #{record.worker_profile_id}
                            </p>
                          </td>

                          {/* Date */}
                          <td className="whitespace-nowrap px-4 py-3 font-mono text-sm text-foreground">
                            {record.attendance_date}
                          </td>

                          {/* Assignment */}
                          <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                            #{record.assignment_id}
                          </td>

                          {/* Check-in */}
                          <td className="whitespace-nowrap px-4 py-3 font-mono text-sm text-foreground">
                            {fmtTime(record.check_in_time)}
                          </td>

                          {/* Check-out */}
                          <td className="whitespace-nowrap px-4 py-3 font-mono text-sm text-foreground">
                            {fmtTime(record.check_out_time)}
                          </td>

                          {/* Hours */}
                          <td className="px-4 py-3 font-mono text-sm text-foreground">
                            {hours}
                          </td>

                          {/* Status */}
                          <td className="px-4 py-3">
                            <StatusBadge value={record.status} />
                          </td>

                          {/* Actions */}
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              {!isVerified && (
                                <Button
                                  type="button"
                                  size="sm"
                                  disabled={isBusy || verifyingId !== null}
                                  onClick={() => handleVerify(record)}
                                  className="gap-1.5"
                                >
                                  <CheckCircle2 className="h-3.5 w-3.5" />
                                  {isBusy ? "Saving…" : "Verify"}
                                </Button>
                              )}
                              <Button
                                type="button"
                                size="sm"
                                variant="outline"
                                onClick={() => setCorrectingRecord(record)}
                              >
                                Correct
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Footer row count */}
              <div className="border-t border-border px-4 py-3">
                <p className="text-xs text-muted-foreground">
                  {records.length} record{records.length !== 1 ? "s" : ""} for{" "}
                  {activeMode} #{searchId}
                </p>
              </div>
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
            <DialogTitle>Correct attendance record</DialogTitle>
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
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmtTime(value: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  }).format(new Date(value));
}

function calcHours(checkIn: string | null, checkOut: string | null) {
  if (!checkIn || !checkOut) return "—";
  const diffH =
    (new Date(checkOut).getTime() - new Date(checkIn).getTime()) / 3_600_000;
  return diffH > 0 ? `${diffH.toFixed(1)}h` : "—";
}

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
