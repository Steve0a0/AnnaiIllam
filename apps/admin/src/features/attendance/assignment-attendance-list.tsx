"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useAssignmentAttendance } from "@/features/attendance/use-assignment-attendance";
import AttendanceLoading from "@/features/attendance/attendance-loading";
import AttendanceError from "@/features/attendance/attendance-error";
import AttendanceEmpty from "@/features/attendance/attendance-empty";
import StatusBadge from "@/components/shared/status-badge";
import CorrectAttendanceForm from "@/features/attendance/correct-attendance-form";
import { attendanceService } from "@/services/attendance.service";
import { getErrorMessage } from "@/lib/get-error-message";

export default function AssignmentAttendanceList({
  assignmentId,
}: {
  assignmentId: number;
}) {
  const { data, isLoading, isError, error, refetch } =
    useAssignmentAttendance(assignmentId);

  const [editingAttendanceId, setEditingAttendanceId] = useState<number | null>(
    null
  );
  const [verifyingId, setVerifyingId] = useState<number | null>(null);
  const [message, setMessage] = useState("");

  if (isLoading) {
    return <AttendanceLoading />;
  }

  if (isError) {
    return <AttendanceError message={error?.message} />;
  }

  const attendance = data?.data || [];

  const verifyAttendance = async (attendanceId: number) => {
    setVerifyingId(attendanceId);
    setMessage("");

    try {
      await attendanceService.correctAttendance(attendanceId, {
        status: "approved",
        notes: "Verified by admin.",
      });
      await refetch();
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setVerifyingId(null);
    }
  };

  if (!attendance.length) {
    return <AttendanceEmpty />;
  }

  return (
    <div className="space-y-4">
      {message ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {message}
        </div>
      ) : null}

      <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
        <table className="min-w-full">
          <thead className="bg-secondary">
            <tr>
              <th className="px-4 py-3 text-left text-[13px] font-medium text-muted-foreground">
                Date
              </th>
              <th className="px-4 py-3 text-left text-[13px] font-medium text-muted-foreground">
                Worker Profile ID
              </th>
              <th className="px-4 py-3 text-left text-[13px] font-medium text-muted-foreground">
                Status
              </th>
              <th className="px-4 py-3 text-left text-[13px] font-medium text-muted-foreground">
                Check In
              </th>
              <th className="px-4 py-3 text-left text-[13px] font-medium text-muted-foreground">
                Check Out
              </th>
              <th className="px-4 py-3 text-left text-[13px] font-medium text-muted-foreground">
                Notes
              </th>
              <th className="px-4 py-3 text-right text-[13px] font-medium text-muted-foreground">
                Action
              </th>
            </tr>
          </thead>

          <tbody>
            {attendance.map((item) => (
              <tr key={item.id} className="border-b border-muted last:border-b-0">
                <td className="px-4 py-3 font-mono text-sm text-foreground">
                  {item.attendance_date}
                </td>
                <td className="px-4 py-3 font-mono text-sm text-foreground">
                  {item.worker_profile_id}
                </td>
                <td className="px-4 py-3 text-sm">
                  <StatusBadge value={item.status} />
                </td>
                <td className="px-4 py-3 font-mono text-sm text-foreground">
                  {formatDateTime(item.check_in_time)}
                </td>
                <td className="px-4 py-3 font-mono text-sm text-foreground">
                  {formatDateTime(item.check_out_time)}
                </td>
                <td className="max-w-[260px] truncate px-4 py-3 text-sm text-muted-foreground">
                  {item.notes || "-"}
                </td>
                <td className="px-4 py-3 text-right text-sm">
                  <div className="flex items-center justify-end gap-3">
                    {item.status !== "approved" ? (
                      <Button
                        type="button"
                        variant="accent"
                        size="sm"
                        disabled={verifyingId === item.id}
                        onClick={() => verifyAttendance(item.id)}
                      >
                        {verifyingId === item.id ? "Saving..." : "Verify"}
                      </Button>
                    ) : (
                      <span className="text-xs font-medium text-emerald-600">
                        ✓ Approved
                      </span>
                    )}
                    <button
                      type="button"
                      onClick={() =>
                        setEditingAttendanceId(
                          editingAttendanceId === item.id ? null : item.id
                        )
                      }
                      className="text-xs text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
                    >
                      {editingAttendanceId === item.id ? "Close" : "Edit"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {attendance.map((item) =>
        editingAttendanceId === item.id ? (
          <div
            key={`form-${item.id}`}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <h3 className="mb-3 text-base font-semibold text-slate-900">
              Correct Attendance #{item.id}
            </h3>
            <CorrectAttendanceForm
              attendanceId={item.id}
              currentStatus={item.status}
              currentNotes={item.notes}
              onSuccess={() => {
                setEditingAttendanceId(null);
                refetch();
              }}
            />
          </div>
        ) : null
      )}
    </div>
  );
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
