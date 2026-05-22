"use client";

import { useState } from "react";
import { CheckCircle2, CircleDot, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { complaintsService } from "@/services/complaints.service";
import { getErrorMessage } from "@/lib/get-error-message";

export default function UpdateComplaintStatusForm({
  complaintId,
  currentStatus,
  currentResolutionNotes,
  onSuccess,
}: {
  complaintId: number;
  currentStatus: string;
  currentResolutionNotes?: string | null;
  onSuccess: () => void;
}) {
  const [status, setStatus] = useState(currentStatus);
  const [resolutionNotes, setResolutionNotes] = useState(
    currentResolutionNotes ?? "",
  );
  const [pendingStatus, setPendingStatus] = useState<string | null>(null);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const updateStatus = async (nextStatus: string) => {
    setPendingStatus(nextStatus);
    setMessage(null);

    try {
      await complaintsService.updateComplaintStatus(complaintId, {
        status: nextStatus,
        resolution_notes: resolutionNotes || null,
      });

      setStatus(nextStatus);
      setMessage({
        type: "success",
        text:
          nextStatus === "resolved"
            ? "Complaint resolved successfully."
            : "Complaint status updated successfully.",
      });
      onSuccess();
    } catch (error) {
      setMessage({ type: "error", text: getErrorMessage(error) });
    } finally {
      setPendingStatus(null);
    }
  };

  const isSaving = pendingStatus !== null;

  return (
    <Card>
      <CardHeader className="border-b border-border">
        <CardTitle>Resolution</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 pt-6">
        <Textarea
          label="Resolution Notes"
          value={resolutionNotes}
          onChange={(e) => setResolutionNotes(e.target.value)}
          placeholder="Enter notes for the client or internal audit trail"
          rows={4}
        />

        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant={status === "under_review" ? "default" : "secondary"}
            disabled={isSaving}
            onClick={() => updateStatus("under_review")}
          >
            <CircleDot />
            {pendingStatus === "under_review" ? "Saving..." : "Mark In Review"}
          </Button>
          <Button
            type="button"
            variant="accent"
            disabled={isSaving}
            onClick={() => updateStatus("resolved")}
          >
            <CheckCircle2 />
            {pendingStatus === "resolved" ? "Resolving..." : "Resolve"}
          </Button>
          <Button
            type="button"
            variant="destructive"
            disabled={isSaving}
            onClick={() => updateStatus("closed")}
          >
            <XCircle />
            {pendingStatus === "closed" ? "Saving..." : "Reject / Close"}
          </Button>
        </div>

        {message ? (
          <div
            className={
              message.type === "success"
                ? "rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800"
                : "rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
            }
          >
            {message.text}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
