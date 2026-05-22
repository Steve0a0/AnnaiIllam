"use client";
import { Button } from "@/components/ui/button";

import { useState } from "react";
import { financeService } from "@/services/finance.service";
import { getErrorMessage } from "@/lib/get-error-message";

const paymentModels = [
  "client_pays_company",
  "client_pays_worker_directly",
  "mixed",
];

const paymentModes = ["cash", "bank", "manual", "gateway"];
const paymentStatuses = ["pending", "paid", "failed", "refunded"];

export default function ManualClientPaymentForm({
  requirementId,
  onSuccess,
}: {
  requirementId: number;
  onSuccess: () => void;
}) {
  const [amount, setAmount] = useState("");
  const [paymentModel, setPaymentModel] = useState("client_pays_company");
  const [paymentMode, setPaymentMode] = useState("bank");
  const [paymentStatus, setPaymentStatus] = useState("paid");
  const [referenceNote, setReferenceNote] = useState("");
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
      await financeService.recordManualClientPayment({
        requirement_id: requirementId,
        amount: parsedAmount,
        payment_model: paymentModel,
        payment_mode: paymentMode,
        payment_status: paymentStatus,
        reference_note: referenceNote || null,
      });

      setAmount("");
      setReferenceNote("");
      setMessage("Manual client payment recorded successfully.");
      onSuccess();
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
      onSubmit={handleSubmit}
    >
      <h2 className="text-lg font-semibold text-slate-900">
        Record Client Payment
      </h2>

      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Amount">
          <input
            type="number"
            min="1"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="Enter amount"
            required
          />
        </Field>

        <Field label="Payment Model">
          <select
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={paymentModel}
            onChange={(e) => setPaymentModel(e.target.value)}
          >
            {paymentModels.map((item) => (
              <option key={item} value={item}>
                {item.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Payment Mode">
          <select
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={paymentMode}
            onChange={(e) => setPaymentMode(e.target.value)}
          >
            {paymentModes.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Payment Status">
          <select
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={paymentStatus}
            onChange={(e) => setPaymentStatus(e.target.value)}
          >
            {paymentStatuses.map((item) => (
              <option key={item} value={item}>
                {item.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </Field>
      </div>

      <Field label="Reference Note">
        <textarea
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={referenceNote}
          onChange={(e) => setReferenceNote(e.target.value)}
          placeholder="Enter reference note"
          rows={2}
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
        {loading ? "Saving..." : "Record Client Payment"}
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
