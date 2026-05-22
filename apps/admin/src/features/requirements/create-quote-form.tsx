"use client";
import { Button } from "@/components/ui/button";

import { useState } from "react";
import { requirementsService } from "@/services/requirements.service";
import { getErrorMessage } from "@/lib/get-error-message";
import type { AdminRequirementDetail } from "@/types/requirement";

export default function CreateQuoteForm({
  requirement,
  onSuccess,
}: {
  requirement: AdminRequirementDetail;
  onSuccess: () => void;
}) {
  const defaultWorkerDays = Math.max(
    1,
    requirement.number_of_workers * requirement.duration_days
  );
  const [ratePerWorker, setRatePerWorker] = useState("");
  const [advanceAmount, setAdvanceAmount] = useState("");
  const [paymentModel, setPaymentModel] = useState("client_pays_company");
  const [validUntil, setValidUntil] = useState("");
  const [termsNotes, setTermsNotes] = useState("");
  const [internalNotes, setInternalNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const quotedAmount = Number(ratePerWorker || 0) * defaultWorkerDays;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      if (!ratePerWorker || quotedAmount <= 0) {
        setMessage("Enter a valid rate per worker per day.");
        setLoading(false);
        return;
      }

      await requirementsService.createQuote(requirement.id, {
        requirement_id: requirement.id,
        quoted_amount: quotedAmount,
        rate_per_worker: Number(ratePerWorker),
        total_worker_days: defaultWorkerDays,
        advance_amount: advanceAmount ? Number(advanceAmount) : null,
        payment_model: paymentModel,
        valid_until: validUntil || null,
        terms_notes: termsNotes || null,
        internal_notes: internalNotes || null,
      });

      setMessage("Quote created successfully.");
      onSuccess();
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
    >
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Send Quote</h2>
        <p className="mt-1 text-sm text-slate-600">
          Calculate the client-facing estimate from worker count, duration, and
          daily rate.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Rate Per Worker Per Day">
          <input
            type="number"
            min="1"
            step="1"
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            value={ratePerWorker}
            onChange={(e) => setRatePerWorker(e.target.value)}
            placeholder="Enter daily rate"
            required
          />
        </Field>

        <Field label="Advance Amount">
          <input
            type="number"
            min="0"
            step="0.01"
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            value={advanceAmount}
            onChange={(e) => setAdvanceAmount(e.target.value)}
            placeholder="Enter advance amount"
          />
        </Field>

        <Field label="Payment Model">
          <select
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            value={paymentModel}
            onChange={(e) => setPaymentModel(e.target.value)}
          >
            <option value="client_pays_company">Client Pays Company</option>
            <option value="client_pays_worker_directly">
              Client Pays Worker Directly
            </option>
            <option value="mixed">Mixed</option>
          </select>
        </Field>

        <Field label="Valid Until">
          <input
            type="date"
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            value={validUntil}
            onChange={(e) => setValidUntil(e.target.value)}
          />
        </Field>
      </div>

      <div className="grid gap-3 rounded-xl border border-emerald-100 bg-emerald-50 p-4 text-sm text-emerald-950 md:grid-cols-3">
        <SummaryItem label="Workers" value={requirement.number_of_workers} />
        <SummaryItem label="Duration" value={`${requirement.duration_days} days`} />
        <SummaryItem label="Worker Days" value={defaultWorkerDays} />
        <SummaryItem
          label="Quote Total"
          value={quotedAmount > 0 ? `Rs. ${quotedAmount.toLocaleString("en-IN")}` : "Enter rate"}
        />
      </div>

      <Field label="Terms Notes">
        <textarea
          className="w-full rounded-lg border border-slate-300 px-3 py-2"
          value={termsNotes}
          onChange={(e) => setTermsNotes(e.target.value)}
          placeholder="Enter client-facing quote notes"
        />
      </Field>

      <Field label="Internal Notes">
        <textarea
          className="w-full rounded-lg border border-slate-300 px-3 py-2"
          value={internalNotes}
          onChange={(e) => setInternalNotes(e.target.value)}
          placeholder="Enter internal notes"
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
        variant="accent"
      >
        {loading ? "Sending..." : "Send Quote to Client"}
      </Button>
    </form>
  );
}

function SummaryItem({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
        {label}
      </p>
      <p className="mt-1 font-semibold">{value}</p>
    </div>
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
