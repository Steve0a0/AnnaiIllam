"use client";
import { Button } from "@/components/ui/button";

import { useState } from "react";
import { financeService } from "@/services/finance.service";
import { getErrorMessage } from "@/lib/get-error-message";

const payoutStatuses = ["pending", "processing", "paid", "failed"];

export default function UpdateWorkerPayoutStatus({
  payoutId,
  currentStatus,
  onSuccess,
}: {
  payoutId: number;
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
      await financeService.updateWorkerPayoutStatus(payoutId, {
        payout_status: status,
      });
      setMessage("Payout status updated.");
      onSuccess();
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <select
        className="flex h-9 rounded-lg border border-input bg-card px-3 py-1 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={status}
        onChange={(e) => setStatus(e.target.value)}
      >
        {payoutStatuses.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>

      <Button
        type="button"
        onClick={handleUpdate}
        disabled={loading}
        variant="accent" size="sm"
      >
        {loading ? "Saving..." : "Update"}
      </Button>

      {message ? (
        <span className="text-xs text-muted-foreground">{message}</span>
      ) : null}
    </div>
  );
}
