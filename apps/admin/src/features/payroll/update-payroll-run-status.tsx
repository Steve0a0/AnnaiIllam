"use client";
import { Button } from "@/components/ui/button";

import { useState } from "react";
import { payrollService } from "@/services/payroll.service";
import { getErrorMessage } from "@/lib/get-error-message";

const payrollStatuses = ["draft", "generated", "approved", "paid", "locked"];

export default function UpdatePayrollRunStatus({
  payrollRunId,
  currentStatus,
  onSuccess,
}: {
  payrollRunId: number;
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
      await payrollService.updatePayrollRunStatus(payrollRunId, { status });
      setMessage("Payroll status updated.");
      onSuccess();
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          {payrollStatuses.map((item) => (
            <option key={item} value={item}>
              {item.replaceAll("_", " ")}
            </option>
          ))}
        </select>

        <Button
          type="button"
          onClick={handleUpdate}
          disabled={loading}
          variant="accent" size="sm"
        >
          {loading ? "Saving..." : "Update Status"}
        </Button>
      </div>

      {message ? <p className="text-sm text-slate-600">{message}</p> : null}
    </div>
  );
}
