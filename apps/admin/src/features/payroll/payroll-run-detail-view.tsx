"use client";
import { Button } from "@/components/ui/button";

import { usePayrollRunDetail } from "@/features/payroll/use-payroll-run-detail";
import PayrollLoading from "@/features/payroll/payroll-loading";
import PayrollError from "@/features/payroll/payroll-error";
import StatusBadge from "@/components/shared/status-badge";
import UpdatePayrollRunStatus from "@/features/payroll/update-payroll-run-status";
import PayrollItemsTable from "@/features/payroll/payroll-items-table";
import { payrollService } from "@/services/payroll.service";
import { getErrorMessage } from "@/lib/get-error-message";
import { useState } from "react";

export default function PayrollRunDetailView({
  payrollRunId,
}: {
  payrollRunId: number;
}) {
  const { data, isLoading, isError, error, refetch } =
    usePayrollRunDetail(payrollRunId);

  const [generating, setGenerating] = useState(false);
  const [generateMessage, setGenerateMessage] = useState("");

  if (isLoading) return <PayrollLoading />;

  if (isError || !data?.data) {
    return <PayrollError message={error?.message} />;
  }

  const { payroll_run, items } = data.data;
  const isLocked = payroll_run.status === "locked";

  const handleGenerate = async () => {
    setGenerating(true);
    setGenerateMessage("");
    try {
      await payrollService.generatePayrollRun(payrollRunId);
      setGenerateMessage("Payroll generated successfully.");
      refetch();
    } catch (err) {
      setGenerateMessage(getErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">
          Payroll Run #{payroll_run.id}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          {payroll_run.period_start} â€” {payroll_run.period_end}
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <StatusBadge value={payroll_run.status} />
            {payroll_run.notes ? (
              <p className="text-sm text-slate-600">{payroll_run.notes}</p>
            ) : null}
          </div>

          <div className="flex flex-wrap gap-3">
            <Button
              type="button"
              onClick={handleGenerate}
              disabled={generating || isLocked}
              variant="accent" size="sm"
            >
              {generating ? "Generating..." : "Generate Payroll"}
            </Button>
          </div>
        </div>

        {generateMessage ? (
          <p className="mt-3 text-sm text-slate-600">{generateMessage}</p>
        ) : null}

        <div className="mt-6">
          <h2 className="mb-3 text-base font-semibold text-slate-800">
            Update Status
          </h2>
          <UpdatePayrollRunStatus
            payrollRunId={payroll_run.id}
            currentStatus={payroll_run.status}
            onSuccess={() => refetch()}
          />
        </div>
      </div>

      <div>
        <h2 className="mb-4 text-xl font-semibold text-slate-900">
          Payroll Items
        </h2>
        <PayrollItemsTable
          items={items}
          payrollLocked={isLocked}
          onRefresh={() => refetch()}
        />
      </div>
    </div>
  );
}
