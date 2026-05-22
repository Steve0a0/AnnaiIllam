"use client";
import { Button } from "@/components/ui/button";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { payrollService } from "@/services/payroll.service";
import { getErrorMessage } from "@/lib/get-error-message";

export default function PayrollRunCreateForm() {
  const router = useRouter();

  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      const response = await payrollService.createPayrollRun({
        period_start: periodStart,
        period_end: periodEnd,
        notes: notes || null,
      });

      const payrollRunId = response.data.payroll_run_id;
      router.push(`/payroll/${payrollRunId}`);
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
      <h2 className="text-lg font-semibold text-slate-900">
        Create Payroll Run
      </h2>

      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Period Start">
          <input
            type="date"
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            value={periodStart}
            onChange={(e) => setPeriodStart(e.target.value)}
          />
        </Field>

        <Field label="Period End">
          <input
            type="date"
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            value={periodEnd}
            onChange={(e) => setPeriodEnd(e.target.value)}
          />
        </Field>
      </div>

      <Field label="Notes">
        <textarea
          className="w-full rounded-lg border border-slate-300 px-3 py-2"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Enter payroll notes"
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
        {loading ? "Creating..." : "Create Payroll Run"}
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
