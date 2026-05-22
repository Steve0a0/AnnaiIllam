"use client";

import StatusBadge from "@/components/shared/status-badge";
import AddDeductionForm from "@/features/payroll/add-deduction-form";
import CreateWorkerPayoutForm from "@/features/finance/create-worker-payout-form";
import WorkerPayoutsList from "@/features/finance/worker-payouts-list";
import { formatCurrency } from "@/lib/format-currency";
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
