"use client";
import { Button } from "@/components/ui/button";

import { useState } from "react";
import { complaintsService } from "@/services/complaints.service";
import { getErrorMessage } from "@/lib/get-error-message";

export default function CreateReplacementForm({
  complaintId,
  oldAssignmentId,
  onSuccess,
}: {
  complaintId: number;
  oldAssignmentId: number;
  onSuccess: () => void;
}) {
  const [newWorkerProfileId, setNewWorkerProfileId] = useState("");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsedId = Number(newWorkerProfileId);
    if (!parsedId || parsedId <= 0) {
      setMessage("New worker profile ID must be a positive number.");
      return;
    }
    setLoading(true);
    setMessage("");

    try {
      await complaintsService.createReplacement({
        complaint_id: complaintId,
        old_assignment_id: oldAssignmentId,
        new_worker_profile_id: parsedId,
        reason: reason || null,
      });

      setNewWorkerProfileId("");
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
      className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={handleSubmit}
    >
      <h3 className="text-base font-semibold text-slate-900">
        Create Replacement
      </h3>

      <div className="grid gap-4 md:grid-cols-2">
        <Field label="New Worker Profile ID">
          <input
            type="number"
            min="1"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={newWorkerProfileId}
            onChange={(e) => setNewWorkerProfileId(e.target.value)}
            placeholder="Enter new worker profile ID"
            required
          />
        </Field>
      </div>

      <Field label="Reason">
        <textarea
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Enter replacement reason"
          rows={3}
        />
      </Field>

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
        {loading ? "Saving..." : "Create Replacement"}
      </Button>
    </form>
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
