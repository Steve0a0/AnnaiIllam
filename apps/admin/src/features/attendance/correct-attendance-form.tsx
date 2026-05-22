"use client";
import { Button } from "@/components/ui/button";

import { useState } from "react";
import { attendanceService } from "@/services/attendance.service";
import { getErrorMessage } from "@/lib/get-error-message";

const attendanceStatuses = [
  "present",
  "absent",
  "half_day",
  "late",
  "approved",
  "corrected",
];

export default function CorrectAttendanceForm({
  attendanceId,
  currentStatus,
  currentNotes,
  onSuccess,
}: {
  attendanceId: number;
  currentStatus: string;
  currentNotes?: string | null;
  onSuccess: () => void;
}) {
  const [status, setStatus] = useState(currentStatus);
  const [notes, setNotes] = useState(currentNotes || "");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      await attendanceService.correctAttendance(attendanceId, {
        status,
        notes: notes || null,
      });
      setMessage("Attendance corrected successfully.");
      onSuccess();
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">
          Status
        </label>
        <select
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          {attendanceStatuses.map((item) => (
            <option key={item} value={item}>
              {item.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">
          Notes
        </label>
        <textarea
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add correction note"
        />
      </div>

      {message ? (
        <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
          {message}
        </div>
      ) : null}

      <Button
        type="submit"
        disabled={loading}
        variant="accent" size="sm"
      >
        {loading ? "Saving..." : "Save Correction"}
      </Button>
    </form>
  );
}
