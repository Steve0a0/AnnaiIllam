"use client";
import { useState } from "react";
import { ChevronDown, Loader2 } from "lucide-react";
import { assignmentsService } from "@/services/assignments.service";
import { getErrorMessage } from "@/lib/get-error-message";

const statuses = [
  "assigned",
  "accepted",
  "declined",
  "active",
  "completed",
  "cancelled",
  "replaced",
];

const statusStyles: Record<string, { bg: string; text: string; border: string }> = {
  assigned:  { bg: "#DBEAFE", text: "#1D4ED8", border: "#BFDBFE" },
  accepted:  { bg: "#DCFCE7", text: "#15803D", border: "#BBF7D0" },
  declined:  { bg: "#FEE2E2", text: "#B91C1C", border: "#FECACA" },
  active:    { bg: "#CFFAFE", text: "#0E7490", border: "#A5F3FC" },
  completed: { bg: "#DCFCE7", text: "#15803D", border: "#BBF7D0" },
  cancelled: { bg: "#FEE2E2", text: "#B91C1C", border: "#FECACA" },
  replaced:  { bg: "#FEF3C7", text: "#B45309", border: "#FDE68A" },
};

export default function UpdateAssignmentStatus({
  assignmentId,
  currentStatus,
  onSuccess,
}: {
  assignmentId: number;
  currentStatus: string;
  onSuccess: () => void;
}) {
  const [status, setStatus] = useState(currentStatus);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const style = statusStyles[status];

  async function handleChange(val: string) {
    if (val === status) return;
    const prev = status;
    setStatus(val);
    setLoading(true);
    setError("");
    try {
      await assignmentsService.updateAssignmentStatus(assignmentId, { status: val });
      onSuccess();
    } catch (err) {
      setStatus(prev);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="relative inline-flex items-center">
        <select
          aria-label="Assignment status"
          className="h-7 appearance-none rounded-full border pl-3 pr-7 text-[12px] font-semibold focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-60"
          style={
            style
              ? { backgroundColor: style.bg, color: style.text, borderColor: style.border }
              : { backgroundColor: "#F5F5F4", color: "#78716C", borderColor: "#E7E5E4" }
          }
          value={status}
          onChange={(e) => handleChange(e.target.value)}
          disabled={loading}
        >
          {statuses.map((s) => (
            <option key={s} value={s}>
              {s.replaceAll("_", " ")}
            </option>
          ))}
        </select>
        <span
          className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2"
          style={style ? { color: style.text } : { color: "#78716C" }}
        >
          {loading ? (
            <Loader2 className="size-3 animate-spin" />
          ) : (
            <ChevronDown className="size-3" />
          )}
        </span>
      </div>
      {error ? (
        <p className="max-w-[160px] text-right text-[10px] leading-tight text-[#B91C1C]">
          {error}
        </p>
      ) : null}
    </div>
  );
}
