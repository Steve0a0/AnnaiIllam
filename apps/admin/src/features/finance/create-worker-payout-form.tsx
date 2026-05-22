"use client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

import { useState } from "react";
import { financeService } from "@/services/finance.service";
import { getErrorMessage } from "@/lib/get-error-message";

const payoutModes = ["bank", "cash", "manual"];

export default function CreateWorkerPayoutForm({
  payrollItemId,
  onSuccess,
}: {
  payrollItemId: number;
  onSuccess: () => void;
}) {
  const [amount, setAmount] = useState("");
  const [payoutMode, setPayoutMode] = useState("bank");
  const [transactionReference, setTransactionReference] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsedAmount = Number(amount);
    if (!parsedAmount || parsedAmount <= 0) {
      setMessage("Amount must be a positive number.");
      return;
    }
    setLoading(true);
    setMessage("");

    try {
      await financeService.createWorkerPayout({
        payroll_item_id: payrollItemId,
        amount: parsedAmount,
        payout_mode: payoutMode,
        transaction_reference: transactionReference || null,
        notes: notes || null,
      });

      setAmount("");
      setTransactionReference("");
      setNotes("");
      setMessage("Worker payout record created successfully.");
      onSuccess();
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      className="space-y-4 rounded-xl border border-border bg-white p-6 shadow-sm"
      onSubmit={handleSubmit}
    >
      <div>
        <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">Payout</p>
        <h3 className="mt-1 font-display text-xl font-semibold text-foreground">
          Create Worker Payout
        </h3>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Input
          type="number"
          min="0"
          step="0.01"
          label="Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="Enter payout amount"
          required
        />

        <div className="grid gap-1.5">
          <label
            htmlFor="payout-mode"
            className="text-sm font-medium leading-none text-foreground"
          >
            Payout Mode
          </label>
          <select
            id="payout-mode"
            className="flex h-9 w-full rounded-lg border border-input bg-card px-3 py-1 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={payoutMode}
            onChange={(e) => setPayoutMode(e.target.value)}
          >
            {payoutModes.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>

        <Input
          type="text"
          label="Transaction Reference"
          value={transactionReference}
          onChange={(e) => setTransactionReference(e.target.value)}
          placeholder="UTR / Ref"
        />
      </div>

      <Textarea
        label="Notes"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Enter payout notes"
        rows={2}
      />

      {message ? (
        <div className="rounded-lg bg-secondary px-3 py-2 text-sm text-muted-foreground">
          {message}
        </div>
      ) : null}

      <Button
        type="submit"
        disabled={loading}
        variant="accent" size="sm"
      >
        {loading ? "Saving..." : "Create Worker Payout"}
      </Button>
    </form>
  );
}
