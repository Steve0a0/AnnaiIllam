"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  IndianRupee,
  RefreshCw,
  Send,
  Wallet,
  XCircle,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/format-currency";
import { cn } from "@/lib/cn";
import { financeService } from "@/services/finance.service";
import type { AdminClientPaymentRecord, PayrollQueueRun } from "@/types/finance";

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function FinancePage() {
  const [activeTab, setActiveTab] = useState<"incoming" | "payroll">("incoming");

  // Incoming Payments state
  const [payments, setPayments] = useState<AdminClientPaymentRecord[]>([]);
  const [isLoadingPayments, setIsLoadingPayments] = useState(true);
  const [paymentsError, setPaymentsError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState<number | null>(null);
  const [rejecting, setRejecting] = useState<number | null>(null);

  // Payroll Queue state
  const [payrollRuns, setPayrollRuns] = useState<PayrollQueueRun[]>([]);
  const [isLoadingPayroll, setIsLoadingPayroll] = useState(true);
  const [payrollError, setPayrollError] = useState<string | null>(null);
  const [transferring, setTransferring] = useState<number | null>(null);

  const [toast, setToast] = useState<string | null>(null);

  const loadPayments = useCallback(async () => {
    setIsLoadingPayments(true);
    setPaymentsError(null);
    try {
      const res = await financeService.listAllClientPayments();
      setPayments(res.data);
    } catch {
      setPaymentsError("Could not load payments. Check your connection.");
    } finally {
      setIsLoadingPayments(false);
    }
  }, []);

  const loadPayrollQueue = useCallback(async () => {
    setIsLoadingPayroll(true);
    setPayrollError(null);
    try {
      const res = await financeService.getPayrollQueue();
      setPayrollRuns(res.data);
    } catch {
      setPayrollError("Could not load payroll queue. Check your connection.");
    } finally {
      setIsLoadingPayroll(false);
    }
  }, []);

  useEffect(() => { loadPayments(); }, [loadPayments]);
  useEffect(() => { loadPayrollQueue(); }, [loadPayrollQueue]);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 4000);
  };

  const handleConfirm = async (payment: AdminClientPaymentRecord) => {
    setConfirming(payment.id);
    try {
      const res = await financeService.updateClientPaymentStatus(payment.id, {
        payment_status: "paid",
      });
      await loadPayments();
      if (res.data.requirement_auto_transitioned) {
        showToast(`Payment confirmed ✓  ·  Requirement #${payment.requirement_id} auto-moved to Assigned`);
      } else {
        showToast("Payment confirmed and marked as paid.");
      }
    } catch {
      showToast("Could not confirm payment. Please try again.");
    } finally {
      setConfirming(null);
    }
  };

  const handleReject = async (payment: AdminClientPaymentRecord) => {
    setRejecting(payment.id);
    try {
      await financeService.updateClientPaymentStatus(payment.id, {
        payment_status: "failed",
      });
      await loadPayments();
      showToast("Payment marked as failed. Client will need to resubmit.");
    } catch {
      showToast("Could not reject payment. Please try again.");
    } finally {
      setRejecting(null);
    }
  };

  const handleTransferAll = async (runId: number) => {
    setTransferring(runId);
    try {
      const res = await financeService.markRunPaid(runId, { payout_mode: "bank_transfer" });
      await loadPayrollQueue();
      showToast(`Run #${runId} paid ✓ · ${res.data.payouts_created} payout(s) created`);
    } catch {
      showToast("Could not mark run as paid. Please try again.");
    } finally {
      setTransferring(null);
    }
  };

  // Derived totals from real data
  const totalCollected = payments
    .filter((p) => p.payment_status === "paid")
    .reduce((s, p) => s + p.amount, 0);
  const pendingVerifyAmt = payments
    .filter((p) => p.is_advance && p.payment_status === "pending")
    .reduce((s, p) => s + p.amount, 0);
  const totalWorkerPayout = payrollRuns
    .flatMap((r) => r.items)
    .reduce((s, item) => s + item.net_amount, 0);

  // Rate-based margin: sum of (client_rate - worker_rate) × payable_days per item.
  // Falls back to cash-based (collected - payout) when no items have rate data yet.
  const allPayrollItems = payrollRuns.flatMap((r) => r.items);
  const itemsWithMargin = allPayrollItems.filter((item) => item.platform_margin !== null);
  const platformMargin =
    itemsWithMargin.length > 0
      ? itemsWithMargin.reduce((s, item) => s + (item.platform_margin as number), 0)
      : totalCollected - totalWorkerPayout;

  return (
    <div className="space-y-6">
      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-3 text-sm font-medium text-emerald-800 shadow-lg">
          {toast}
        </div>
      )}

      {/* Page header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Finance</h1>
        <p className="mt-1 text-sm text-slate-600">
          Reconcile incoming client payments and release worker payroll.
        </p>
      </div>

      {/* Tab strip */}
      <div className="flex w-fit gap-1 rounded-xl bg-slate-100 p-1">
        {(
          [
            { id: "incoming", label: "Incoming Payments" },
            { id: "payroll",  label: "Payroll Queue"    },
          ] as const
        ).map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "rounded-lg px-5 py-2 text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            )}
          >
            {tab.label}
            {tab.id === "incoming" && !isLoadingPayments && (
              <span className={cn(
                "ml-2 rounded-full px-1.5 py-0.5 text-xs font-bold",
                payments.filter((p) => p.is_advance && p.payment_status === "pending").length > 0
                  ? "bg-amber-100 text-amber-700"
                  : "bg-slate-200 text-slate-500"
              )}>
                {payments.filter((p) => p.is_advance && p.payment_status === "pending").length}
              </span>
            )}
            {tab.id === "payroll" && !isLoadingPayroll && (
              <span className={cn(
                "ml-2 rounded-full px-1.5 py-0.5 text-xs font-bold",
                payrollRuns.filter((r) => r.status !== "paid").length > 0
                  ? "bg-amber-100 text-amber-700"
                  : "bg-slate-200 text-slate-500"
              )}>
                {payrollRuns.filter((r) => r.status !== "paid").length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── Incoming Payments tab ── */}
      {activeTab === "incoming" && (
        <IncomingPayments
          payments={payments}
          isLoading={isLoadingPayments}
          error={paymentsError}
          pendingVerifyAmt={pendingVerifyAmt}
          totalCollected={totalCollected}
          totalWorkerPayout={totalWorkerPayout}
          platformMargin={platformMargin}
          confirming={confirming}
          rejecting={rejecting}
          onConfirm={handleConfirm}
          onReject={handleReject}
          onRefresh={loadPayments}
        />
      )}

      {/* ── Payroll Queue tab ── */}
      {activeTab === "payroll" && (
        <PayrollQueue
          runs={payrollRuns}
          isLoading={isLoadingPayroll}
          error={payrollError}
          totalWorkerPayout={totalWorkerPayout}
          platformMargin={platformMargin}
          transferring={transferring}
          onTransferAll={handleTransferAll}
          onRefresh={loadPayrollQueue}
        />
      )}
    </div>
  );
}

// ─── Incoming Payments view ───────────────────────────────────────────────────

const STATUS_META: Record<
  string,
  { label: string; variant: "success" | "warning" | "danger" | "neutral" }
> = {
  pending:  { label: "Pending verify", variant: "warning" },
  paid:     { label: "Verified",       variant: "success" },
  failed:   { label: "Failed",         variant: "danger"  },
  refunded: { label: "Refunded",       variant: "neutral" },
};

function IncomingPayments({
  payments,
  isLoading,
  error,
  pendingVerifyAmt,
  totalCollected,
  totalWorkerPayout,
  platformMargin,
  confirming,
  rejecting,
  onConfirm,
  onReject,
  onRefresh,
}: {
  payments: AdminClientPaymentRecord[];
  isLoading: boolean;
  error: string | null;
  pendingVerifyAmt: number;
  totalCollected: number;
  totalWorkerPayout: number;
  platformMargin: number;
  confirming: number | null;
  rejecting: number | null;
  onConfirm: (p: AdminClientPaymentRecord) => void;
  onReject: (p: AdminClientPaymentRecord) => void;
  onRefresh: () => void;
}) {
  return (
    <div className="space-y-6">
      {/* Summary metric cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          icon={<IndianRupee className="size-4 text-amber-600" />}
          label="Pending verification"
          value={formatCurrency(pendingVerifyAmt)}
          tone="amber"
        />
        <MetricCard
          icon={<Wallet className="size-4 text-red-600" />}
          label="Payroll due to workers"
          value={formatCurrency(totalWorkerPayout)}
          tone="red"
        />
        <MetricCard
          icon={<CheckCircle2 className="size-4 text-emerald-600" />}
          label="Collected this month"
          value={formatCurrency(totalCollected)}
          tone="green"
        />
        <MetricCard
          icon={<IndianRupee className="size-4 text-blue-600" />}
          label="Platform margin"
          value={formatCurrency(platformMargin)}
          tone="blue"
        />
      </div>

      {/* Payments table */}
      <Card className="overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-5 py-3">
          <p className="text-sm font-semibold text-slate-700">All payments</p>
          <Button size="sm" variant="ghost" onClick={onRefresh} className="gap-1.5 text-slate-500">
            <RefreshCw className="size-3.5" />
            Refresh
          </Button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-slate-400">
            <RefreshCw className="size-5 animate-spin" />
            <span className="ml-2 text-sm">Loading payments…</span>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center gap-2 py-12 text-red-500">
            <AlertCircle className="size-5" />
            <span className="text-sm">{error}</span>
          </div>
        ) : payments.length === 0 ? (
          <div className="py-16 text-center text-sm text-slate-400">
            No payment records yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  {["Client", "Job / Requirement", "Amount", "Mode", "Reference", "Status", "Actions"].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {payments.map((row) => {
                  const meta = STATUS_META[row.payment_status] ?? {
                    label: row.payment_status,
                    variant: "neutral" as const,
                  };
                  const isConfirming = confirming === row.id;
                  const isRejecting = rejecting === row.id;
                  const busy = isConfirming || isRejecting;

                  return (
                    <tr key={row.id} className="hover:bg-slate-50/60">
                      <td className="px-4 py-3.5 text-sm font-medium text-slate-900">
                        {row.client_name}
                      </td>
                      <td className="px-4 py-3.5 text-sm text-slate-600">
                        <span className="font-medium">{row.requirement_category ?? "—"}</span>
                        {row.requirement_city && (
                          <span className="ml-1 text-slate-400">· {row.requirement_city}</span>
                        )}
                        <br />
                        <span className="text-xs text-slate-400">Req #{row.requirement_id}</span>
                      </td>
                      <td className="px-4 py-3.5 text-sm font-semibold text-slate-900">
                        {formatCurrency(row.amount)}
                      </td>
                      <td className="px-4 py-3.5 text-sm uppercase text-slate-500">
                        {row.payment_mode}
                      </td>
                      <td className="px-4 py-3.5 font-mono text-xs text-slate-500">
                        {row.reference_note ?? row.gateway_payment_id ?? "—"}
                      </td>
                      <td className="px-4 py-3.5">
                        <Badge variant={meta.variant}>{meta.label}</Badge>
                      </td>
                      <td className="px-4 py-3.5">
                        {row.is_advance && row.payment_status === "pending" ? (
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              disabled={busy}
                              onClick={() => onConfirm(row)}
                              className="gap-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60"
                            >
                              <CheckCircle2 className="size-3.5" />
                              {isConfirming ? "Confirming…" : "Confirm advance"}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={busy}
                              onClick={() => onReject(row)}
                              className="gap-1.5 border-red-200 text-red-600 hover:bg-red-50 disabled:opacity-60"
                            >
                              <XCircle className="size-3.5" />
                              {isRejecting ? "Rejecting…" : "Reject"}
                            </Button>
                          </div>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

// ─── Payroll Queue view ───────────────────────────────────────────────────────

function PayrollQueue({
  runs,
  isLoading,
  error,
  totalWorkerPayout,
  platformMargin,
  transferring,
  onTransferAll,
  onRefresh,
}: {
  runs: PayrollQueueRun[];
  isLoading: boolean;
  error: string | null;
  totalWorkerPayout: number;
  platformMargin: number;
  transferring: number | null;
  onTransferAll: (runId: number) => void;
  onRefresh: () => void;
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16 text-slate-400">
        <RefreshCw className="size-5 animate-spin" />
        <span className="ml-2 text-sm">Loading payroll queue…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center gap-2 py-12 text-red-500">
        <AlertCircle className="size-5" />
        <span className="text-sm">{error}</span>
      </div>
    );
  }

  if (runs.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white py-16 text-center text-sm text-slate-400">
        No payroll runs ready to pay out. Create a payroll run via the Payroll page first.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with refresh */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">{runs.length} payroll run(s)</p>
        <Button size="sm" variant="ghost" onClick={onRefresh} className="gap-1.5 text-slate-500">
          <RefreshCw className="size-3.5" />
          Refresh
        </Button>
      </div>

      {runs.map((run) => {
        const isPaid = run.status === "paid";
        const isBusy = transferring === run.payroll_run_id;
        const runNet = run.items.reduce((s, item) => s + item.net_amount, 0);

        return (
          <Card key={run.payroll_run_id} className="overflow-hidden">
            {/* Run header */}
            <div className="flex items-start justify-between gap-4 border-b border-slate-100 bg-slate-50 px-5 py-4">
              <div>
                <h2 className="font-semibold text-slate-900">
                  Payroll Run #{run.payroll_run_id}
                </h2>
                <p className="mt-0.5 text-sm text-slate-500">
                  {run.period_start} → {run.period_end} · {run.items.length} worker(s) ·{" "}
                  {formatCurrency(runNet)} net
                </p>
                {run.notes && (
                  <p className="mt-0.5 text-xs text-slate-400">{run.notes}</p>
                )}
              </div>
              <Badge variant={isPaid ? "success" : "warning"}>
                {isPaid ? "Paid" : run.status}
              </Badge>
            </div>

            {/* Worker rows */}
            <div className="divide-y divide-slate-100">
              {run.items.map((item) => {
                const initials = item.worker_name
                  .split(" ")
                  .slice(0, 2)
                  .map((w) => w[0])
                  .join("")
                  .toUpperCase();

                return (
                  <div key={item.payroll_item_id} className="flex items-start gap-4 px-5 py-4">
                    <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-800">
                      {initials}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-slate-900">{item.worker_name}</span>
                      </div>
                      <p className="mt-0.5 text-sm text-slate-500">
                        {item.attendance_days} days present
                        {item.half_days > 0 ? ` · ${item.half_days} half-days` : ""} ·{" "}
                        Gross {formatCurrency(item.gross_amount)}
                      </p>
                      {item.deductions.length > 0 && (
                        <p className="mt-0.5 text-sm text-red-600">
                          Deductions: −{formatCurrency(item.total_deduction_amount)}
                          {item.deductions
                            .map((d) => ` (${d.deduction_type.replace("_", " ")})`)
                            .join("")}
                        </p>
                      )}
                      {item.platform_margin !== null && (
                        <p className={cn(
                          "mt-0.5 text-sm",
                          item.platform_margin < 0 ? "text-red-600" : "text-blue-600"
                        )}>
                          Margin: {item.platform_margin < 0 ? "−" : "+"}{formatCurrency(Math.abs(item.platform_margin))}
                          {item.platform_margin < 0 && " · Worker salary exceeds client rate"}
                        </p>
                      )}
                      {item.is_stale && (
                        <p className="mt-0.5 text-xs font-semibold text-amber-700">
                          ⚠ Stale — payroll needs recalculation due to attendance correction
                        </p>
                      )}
                    </div>
                    <div className="flex shrink-0 flex-col items-end gap-1.5">
                      <span className="font-bold text-slate-900">
                        {formatCurrency(item.net_amount)}
                      </span>
                      <Badge variant={item.payment_status === "paid" ? "success" : "neutral"}>
                        {item.payment_status}
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Transfer all button */}
            <div className="flex items-center justify-end border-t border-slate-200 px-5 py-4">
              <Button
                variant="default"
                disabled={isPaid || isBusy || transferring !== null}
                onClick={() => onTransferAll(run.payroll_run_id)}
                className="gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60"
              >
                <Send className="size-4" />
                {isBusy ? "Processing…" : isPaid ? "Paid out" : "Transfer all & send payslips"}
              </Button>
            </div>
          </Card>
        );
      })}

      {/* Footer totals */}
      <div className="rounded-2xl border border-slate-200 bg-white px-6 py-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-full bg-emerald-100">
              <IndianRupee className="size-4 text-emerald-700" />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Total net to workers (all runs)
              </p>
              <p className="text-xl font-bold text-slate-900">{formatCurrency(totalWorkerPayout)}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-full bg-blue-50">
              <Wallet className="size-4 text-blue-600" />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Platform retained
              </p>
              <p className="text-xl font-bold text-slate-900">{formatCurrency(platformMargin)}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


// ─── Shared components ────────────────────────────────────────────────────────

function MetricCard({
  icon,
  label,
  value,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  tone: "amber" | "red" | "green" | "blue";
}) {
  const bg: Record<typeof tone, string> = {
    amber: "bg-amber-50",
    red:   "bg-red-50",
    green: "bg-emerald-50",
    blue:  "bg-blue-50",
  };

  return (
    <Card className={cn("p-4", bg[tone])}>
      <div className="mb-2 flex items-center gap-1.5">
        {icon}
        <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
          {label}
        </span>
      </div>
      <p className="text-2xl font-bold text-slate-900">{value}</p>
    </Card>
  );
}

