"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BadgeCheck, Banknote, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getErrorMessage } from "@/lib/get-error-message";
import { requirementsService } from "@/services/requirements.service";
import type { WorkerPaymentItem } from "@/types/requirement";

const PAYOUT_MODES = [
  { value: "upi", label: "UPI" },
  { value: "bank_transfer", label: "Bank transfer" },
  { value: "cash", label: "Cash" },
];

export default function WorkerPaymentsSection({
  requirementId,
}: {
  requirementId: number;
}) {
  const { data, isLoading } = useQuery({
    queryKey: ["worker-payments", requirementId],
    queryFn: () => requirementsService.getWorkerPayments(requirementId),
    staleTime: 30_000,
  });

  const workers = data?.data ?? [];

  return (
    <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="mb-5 flex items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700">
          <Banknote className="size-5" />
        </div>
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">
            Worker payouts
          </p>
          <h2 className="font-display text-xl font-semibold text-foreground">
            Pay workers
          </h2>
        </div>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading worker data…</p>
      ) : workers.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No workers assigned to this requirement.
        </p>
      ) : (
        <div className="space-y-3">
          {workers.map((worker) => (
            <WorkerPaymentCard
              key={worker.assignment_id}
              worker={worker}
              requirementId={requirementId}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function WorkerPaymentCard({
  worker,
  requirementId,
}: {
  worker: WorkerPaymentItem;
  requirementId: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const queryClient = useQueryClient();

  const [amount, setAmount] = useState(String(worker.suggested_amount));
  const [payoutMode, setPayoutMode] = useState("upi");
  const [reference, setReference] = useState("");
  const [notes, setNotes] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      requirementsService.recordWorkerPayment(requirementId, {
        assignment_id: worker.assignment_id,
        amount: Number(amount),
        payout_mode: payoutMode,
        transaction_reference: reference || null,
        notes: notes || null,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["worker-payments", requirementId],
      });
      setExpanded(false);
    },
    onError: (err: unknown) => {
      setFormError(getErrorMessage(err));
    },
  });

  const initials = worker.worker_name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  const isPaid = worker.payout !== null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    const parsedAmount = Number(amount);
    if (!amount || isNaN(parsedAmount) || parsedAmount < 0) {
      setFormError("Enter a valid amount");
      return;
    }
    mutation.mutate();
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-white">
      <div className="flex items-center gap-4 px-4 py-4">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-800">
          {initials}
        </div>

        <div className="min-w-0 flex-1">
          <p className="font-medium text-foreground">{worker.worker_name}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {worker.attendance_days} days
            {worker.half_days > 0 ? ` · ${worker.half_days} half` : ""}
            {worker.absent_days > 0 ? ` · ${worker.absent_days} absent` : ""}
            {worker.salary_amount
              ? ` · ₹${worker.salary_amount.toLocaleString("en-IN")}/day`
              : ""}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          {isPaid ? (
            <div className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
              <BadgeCheck className="size-3.5" />
              Paid ₹{worker.payout!.amount.toLocaleString("en-IN")}
            </div>
          ) : (
            <>
              <span className="text-xs text-muted-foreground">
                Suggested ₹{worker.suggested_amount.toLocaleString("en-IN")}
              </span>
              <button
                onClick={() => setExpanded((prev) => !prev)}
                className="flex items-center gap-1 rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-200"
              >
                Record payment
                {expanded ? (
                  <ChevronUp className="size-3.5" />
                ) : (
                  <ChevronDown className="size-3.5" />
                )}
              </button>
            </>
          )}
        </div>
      </div>

      {isPaid && worker.payout && (
        <div className="border-t border-border bg-emerald-50/50 px-4 py-3">
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-muted-foreground">
            <span>
              Mode:{" "}
              <span className="font-medium text-foreground capitalize">
                {worker.payout.payout_mode.replace("_", " ")}
              </span>
            </span>
            {worker.payout.transaction_reference && (
              <span>
                Ref:{" "}
                <span className="font-mono font-medium text-foreground">
                  {worker.payout.transaction_reference}
                </span>
              </span>
            )}
            {worker.payout.paid_at && (
              <span>
                Paid:{" "}
                <span className="font-medium text-foreground">
                  {new Date(worker.payout.paid_at).toLocaleDateString("en-IN", {
                    day: "2-digit",
                    month: "short",
                    year: "numeric",
                  })}
                </span>
              </span>
            )}
            {worker.payout.notes && (
              <span>
                Note:{" "}
                <span className="font-medium text-foreground">
                  {worker.payout.notes}
                </span>
              </span>
            )}
          </div>
        </div>
      )}

      {expanded && !isPaid && (
        <form
          onSubmit={handleSubmit}
          className="border-t border-border bg-slate-50 px-4 py-4"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground">
                Amount (₹)
              </label>
              <input
                type="number"
                min={0}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm font-mono text-foreground focus:outline-none focus:ring-2 focus:ring-brand"
                placeholder="0"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground">
                Payment mode
              </label>
              <select
                value={payoutMode}
                onChange={(e) => setPayoutMode(e.target.value)}
                className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand"
              >
                {PAYOUT_MODES.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground">
                Transaction reference{" "}
                <span className="text-muted-foreground">(optional)</span>
              </label>
              <input
                type="text"
                value={reference}
                onChange={(e) => setReference(e.target.value)}
                className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm font-mono text-foreground focus:outline-none focus:ring-2 focus:ring-brand"
                placeholder="UPI / bank ref"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground">
                Notes{" "}
                <span className="text-muted-foreground">(optional)</span>
              </label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand"
                placeholder="Any note"
              />
            </div>
          </div>

          {formError && (
            <p className="mt-3 text-xs font-medium text-red-600">{formError}</p>
          )}

          <div className="mt-4 flex items-center gap-3">
            <Button
              type="submit"
              variant="accent"
              disabled={mutation.isPending}
            >
              {mutation.isPending ? "Saving…" : "Confirm payment"}
            </Button>
            <button
              type="button"
              onClick={() => setExpanded(false)}
              className="text-xs font-medium text-muted-foreground hover:text-foreground"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
