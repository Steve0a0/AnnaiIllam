"use client";
import { Button } from "@/components/ui/button";

import { useState } from "react";
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
  const [message, setMessage] = useState("");

  const handleUpdate = async () => {
    setLoading(true);
    setMessage("");

    try {
      await assignmentsService.updateAssignmentStatus(assignmentId, { status });
      setMessage("Assignment status updated.");
      onSuccess();
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-end gap-2">
      <select
        aria-label="Assignment status"
        className="h-9 w-[128px] rounded-lg border border-input bg-white px-3 text-sm text-foreground shadow-sm"
        value={status}
        onChange={(e) => setStatus(e.target.value)}
      >
        {statuses.map((item) => (
          <option key={item} value={item}>
            {item.replaceAll("_", " ")}
          </option>
        ))}
      </select>

      <Button
        type="button"
        onClick={handleUpdate}
        disabled={loading}
        variant="secondary"
        size="sm"
      >
        {loading ? "Saving..." : "Update"}
      </Button>

      {message ? (
        <span className="sr-only" aria-live="polite">
          {message}
        </span>
      ) : null}
    </div>
  );
}
