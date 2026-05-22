"use client";
import { Button } from "@/components/ui/button";

import { useState } from "react";
import { payrollService } from "@/services/payroll.service";
import { getErrorMessage } from "@/lib/get-error-message";

const deductionTypes = ["food", "accommodation", "advance", "manual"];

export default function AddDeductionForm({
  payrollItemId,
  disabled,
  onSuccess,
}: {
  payrollItemId: number;
  disabled?: boolean;
  onSuccess: () => void;
}) {
  const [deductionType, setDeductionType] = useState("food");
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (disabled) return;

    setLoading(true);
    setMessage("");

    try {
      await payrollService.addDeduction({
        payroll_item_id: payrollItemId,
        deduction_type: deductionType,
        amount: Number(amount),
        reason: reason || null,
      });

      setAmount("");
      setReason("");
      setMessage("Deduction added successfully.");
      onSuccess();
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="grid gap-3 md:grid-cols-3">
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={deductionType}
          onChange={(e) => setDeductionType(e.target.value)}
          disabled={disabled}
        >
          {deductionTypes.map((item) => (
            <option key={item} value={item}>
              {item.replaceAll("_", " ")}
            </option>
          ))}
        </select>

        <input
          type="number"
          min="0"
          step="0.01"
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="Amount"
          disabled={disabled}
        />

        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Reason"
          disabled={disabled}
        />
      </div>

      {message ? (
        <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
          {message}
        </div>
      ) : null}

      <Button
        type="submit"
        disabled={loading || disabled}
        variant="accent" size="sm"
      >
        {loading ? "Adding..." : "Add Deduction"}
      </Button>
    </form>
  );
}
