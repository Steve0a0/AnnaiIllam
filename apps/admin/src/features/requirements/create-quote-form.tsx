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
  const [workerDailyRate, setWorkerDailyRate] = useState("");
  const [advancePercent, setAdvancePercent] = useState<number>(20);
  const [paymentModel, setPaymentModel] = useState("client_pays_company");
  const [validUntil, setValidUntil] = useState("");
  const [termsNotes, setTermsNotes] = useState("");
  const [internalNotes, setInternalNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const quotedAmount = Number(ratePerWorker || 0) * defaultWorkerDays;
  const workerTotalPayout = Number(workerDailyRate || 0) * defaultWorkerDays;
  const platformMargin = quotedAmount > 0 && workerTotalPayout > 0 ? quotedAmount - workerTotalPayout : null;
  const advanceAmount = advancePercent > 0 && quotedAmount > 0
    ? Math.round(quotedAmount * advancePercent / 100)
    : null;

  const PRESET_PERCENTS = [0, 10, 20, 25, 30, 50];

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
        worker_daily_rate: workerDailyRate ? Number(workerDailyRate) : null,
        total_worker_days: defaultWorkerDays,
        advance_amount: advanceAmount,
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
        <Field label="Client Rate Per Worker Per Day (₹)">
          <input
            type="number"
            min="1"
            step="1"
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            value={ratePerWorker}
            onChange={(e) => setRatePerWorker(e.target.value)}
            placeholder="What client pays per worker/day"
            required
          />
        </Field>

        <Field label="Worker Pay Per Day (₹)">
          <input
            type="number"
            min="1"
            step="1"
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            value={workerDailyRate}
            onChange={(e) => setWorkerDailyRate(e.target.value)}
            placeholder="What worker receives per day"
          />
          {platformMargin !== null && (
            <p className={`mt-1 text-xs font-semibold ${platformMargin < 0 ? "text-red-600" : "text-emerald-700"}`}>
              Platform margin: ₹{Math.abs(platformMargin).toLocaleString("en-IN")} total
              {platformMargin < 0 ? " — worker rate exceeds client rate!" : ""}
            </p>
          )}
        </Field>

        <Field label="Advance Payment">
          <div className="space-y-2">
            <div className="flex flex-wrap gap-1.5">
              {PRESET_PERCENTS.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setAdvancePercent(p)}
                  className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
                    advancePercent === p
                      ? "bg-emerald-600 text-white"
                      : "border border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {p === 0 ? "None" : `${p}%`}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="0"
                max="100"
                step="1"
                className="w-24 rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={advancePercent}
                onChange={(e) => setAdvancePercent(Math.min(100, Math.max(0, Number(e.target.value))))}
                placeholder="Custom %"
              />
              <span className="text-sm text-slate-500">% of total</span>
              {advanceAmount !== null && quotedAmount > 0 ? (
                <span className="ml-auto text-sm font-semibold text-emerald-700">
                  = ₹{advanceAmount.toLocaleString("en-IN")}
                </span>
              ) : (
                <span className="ml-auto text-xs text-slate-400">Enter rate first</span>
              )}
            </div>
          </div>
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
          label="Client Total"
          value={quotedAmount > 0 ? `₹${quotedAmount.toLocaleString("en-IN")}` : "Enter rate"}
        />
        <SummaryItem
          label="Worker Payout"
          value={workerTotalPayout > 0 ? `₹${workerTotalPayout.toLocaleString("en-IN")}` : "Enter worker rate"}
        />
        <SummaryItem
          label="Platform Margin"
          value={
            platformMargin !== null
              ? `₹${platformMargin.toLocaleString("en-IN")}`
              : "Enter both rates"
          }
        />
        <SummaryItem
          label="Advance Due"
          value={
            advanceAmount !== null && quotedAmount > 0
              ? `₹${advanceAmount.toLocaleString("en-IN")} (${advancePercent}%)`
              : advancePercent === 0 ? "None" : "Enter rate"
          }
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
