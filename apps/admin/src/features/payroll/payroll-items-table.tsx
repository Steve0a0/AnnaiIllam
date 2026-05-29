"use client";

import { useState } from "react";
import StatusBadge from "@/components/shared/status-badge";
import AddDeductionForm from "@/features/payroll/add-deduction-form";
import CreateWorkerPayoutForm from "@/features/finance/create-worker-payout-form";
import WorkerPayoutsList from "@/features/finance/worker-payouts-list";
import { formatCurrency } from "@/lib/format-currency";
import { payrollService } from "@/services/payroll.service";
import { getErrorMessage } from "@/lib/get-error-message";
import type { PayrollItem } from "@/types/payroll";

export default function PayrollItemsTable({
  items,
  payrollLocked,
  onRefresh,
}: {
  items: PayrollItem[];
  payrollLocked: boolean;
  onRefresh: () => void;
}) {
  if (!items.length) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-600">
        No payroll items found for this run.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div
          key={item.id}
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold text-slate-900">
                Payroll Item #{item.id}
              </h3>
              <p className="mt-1 text-sm text-slate-600">
                Worker Profile ID: {item.worker_profile_id} | Assignment ID:{" "}
                {item.assignment_id}
              </p>
            </div>

            <StatusBadge value={item.payment_status} />
            {item.is_stale && (
              <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-700">
                Stale — needs recalculation
              </span>
            )}
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-3 xl:grid-cols-6">
            <Detail label="Gross" value={formatCurrency(item.gross_amount)} />
            <Detail
              label="Deductions"
              value={formatCurrency(item.total_deduction_amount)}
            />
            <Detail label="Net" value={formatCurrency(item.net_amount)} />
            <Detail label="Present Days" value={item.attendance_days} />
            <Detail label="Half Days" value={item.half_days} />
            <Detail label="Absent Days" value={item.absent_days} />
          </div>

          {item.platform_margin !== null && (
            <div className={`mt-3 rounded-lg px-3 py-2 text-sm ${item.platform_margin < 0 ? "bg-red-50 text-red-700" : "bg-blue-50 text-blue-700"}`}>
              Platform margin: {item.platform_margin < 0 ? "−" : "+"}{formatCurrency(Math.abs(item.platform_margin))}
              {item.platform_margin < 0 && " — Worker salary exceeds client rate. Negative margin."}
            </div>
          )}

          {item.is_stale && item.payment_status !== "paid" && !payrollLocked && (
            <StaleRecalculateBar itemId={item.id} onSuccess={onRefresh} />
          )}

          <div className="mt-5">
            <h4 className="text-sm font-semibold text-slate-800">Deductions</h4>

            {item.deductions.length ? (
              <div className="mt-2 space-y-2">
                {item.deductions.map((deduction) => (
                  <div
                    key={deduction.id}
                    className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700"
                  >
                    {deduction.deduction_type.replaceAll("_", " ")} -{" "}
                    {formatCurrency(deduction.amount)}
                    {deduction.reason ? ` (${deduction.reason})` : ""}
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-2 text-sm text-slate-500">
                No deductions added yet.
              </p>
            )}
          </div>

          <div className="mt-5">
            <h4 className="mb-2 text-sm font-semibold text-slate-800">
              Add Deduction
            </h4>
            <AddDeductionForm
              payrollItemId={item.id}
              disabled={payrollLocked}
              onSuccess={onRefresh}
            />
            {payrollLocked ? (
              <p className="mt-2 text-xs text-red-600">
                This payroll run is locked. Deductions cannot be changed.
              </p>
            ) : null}
          </div>

          <div className="mt-5">
            <h4 className="mb-2 text-sm font-semibold text-slate-800">
              Worker Payouts
            </h4>

            <CreateWorkerPayoutForm
              payrollItemId={item.id}
              onSuccess={onRefresh}
            />

            <div className="mt-4">
              <WorkerPayoutsList payrollItemId={item.id} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function Detail({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="mt-1 text-sm font-medium text-slate-800">{value}</p>
    </div>
  );
}

function StaleRecalculateBar({
  itemId,
  onSuccess,
}: {
  itemId: number;
  onSuccess: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleRecalculate() {
    setLoading(true);
    setError("");
    try {
      await payrollService.recalculatePayrollItem(itemId);
      onSuccess();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mt-3 flex flex-wrap items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
      <p className="flex-1 text-sm text-amber-800">
        Payroll needs recalculation due to attendance correction.
      </p>
      <button
        type="button"
        disabled={loading}
        onClick={handleRecalculate}
        className="rounded-md bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-700 disabled:opacity-50"
      >
        {loading ? "Recalculating…" : "Recalculate"}
      </button>
      {error ? <p className="w-full text-xs text-red-600">{error}</p> : null}
    </div>
  );
}
