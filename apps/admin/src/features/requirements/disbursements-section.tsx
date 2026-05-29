"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BadgeIndianRupee, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import StatusBadge from "@/components/shared/status-badge";
import { assignmentsService } from "@/services/assignments.service";
import { disbursementsService, type DisbursementItem } from "@/services/disbursements.service";
import { getErrorMessage } from "@/lib/get-error-message";
import type { AssignmentItem } from "@/types/assignment";

function fmt(paise: number) {
  return `Rs. ${(paise / 100).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function fmtDate(iso: string) {
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(iso));
}

function today() {
  return new Date().toISOString().split("T")[0];
}

export default function DisbursementsSection({
  requirementId,
}: {
  requirementId: number;
}) {
  const queryClient = useQueryClient();

  const { data: assignments = [], isLoading: loadingAssignments } = useQuery({
    queryKey: ["assignments-for-requirement", requirementId],
    queryFn: () =>
      assignmentsService
        .getAssignmentsByRequirement(requirementId)
        .then((r) => r.data),
    staleTime: 30_000,
  });

  const { data: disbursements = [], isLoading: loadingDisb } = useQuery({
    queryKey: ["disbursements-requirement", requirementId],
    queryFn: () => disbursementsService.getByRequirement(requirementId),
    staleTime: 30_000,
  });

  const disbursedAssignmentIds = new Set(disbursements.map((d) => d.assignment_id));
  const completedAssignments = assignments.filter(
    (a) => a.status === "completed" && !disbursedAssignmentIds.has(a.id)
  );

  const invalidate = () => {
    void queryClient.invalidateQueries({
      queryKey: ["disbursements-requirement", requirementId],
    });
  };

  const isLoading = loadingAssignments || loadingDisb;

  return (
    <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="mb-5 flex items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-lg bg-violet-50 text-violet-700">
          <BadgeIndianRupee className="size-5" />
        </div>
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">
            Salary disbursements
          </p>
          <h2 className="font-display text-xl font-semibold text-foreground">
            Worker payment tracking
          </h2>
        </div>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading disbursements…</p>
      ) : (
        <div className="space-y-5">
          {disbursements.length === 0 && completedAssignments.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No completed assignments found. Disbursements can be created once
              an assignment is marked completed.
            </p>
          ) : null}

          {disbursements.length > 0 && (
            <div className="divide-y divide-border rounded-lg border border-border">
              {disbursements.map((d) => (
                <DisbursementRow
                  key={d.id}
                  disbursement={d}
                  assignment={assignments.find((a) => a.id === d.assignment_id)}
                  onMutated={invalidate}
                />
              ))}
            </div>
          )}

          {completedAssignments.length > 0 && (
            <div className="space-y-3">
              <p className="text-sm font-medium text-foreground">
                Completed assignments awaiting disbursement
              </p>
              {completedAssignments.map((a) => (
                <CreateDisbursementRow
                  key={a.id}
                  assignment={a}
                  onCreated={invalidate}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function DisbursementRow({
  disbursement,
  assignment,
  onMutated,
}: {
  disbursement: DisbursementItem;
  assignment: AssignmentItem | undefined;
  onMutated: () => void;
}) {
  const [action, setAction] = useState<"paid" | "failed" | null>(null);
  const [paymentRef, setPaymentRef] = useState("");
  const [failNotes, setFailNotes] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const paidMutation = useMutation({
    mutationFn: () =>
      disbursementsService.markPaid(disbursement.id, paymentRef.trim()),
    onSuccess: () => {
      onMutated();
      setAction(null);
      setPaymentRef("");
    },
    onError: (err) => setFormError(getErrorMessage(err)),
  });

  const failedMutation = useMutation({
    mutationFn: () =>
      disbursementsService.markFailed(disbursement.id, failNotes.trim()),
    onSuccess: () => {
      onMutated();
      setAction(null);
      setFailNotes("");
    },
    onError: (err) => setFormError(getErrorMessage(err)),
  });

  const isPending =
    disbursement.disbursement_status === "pending" ||
    disbursement.disbursement_status === "processing";

  const workerLabel = assignment?.worker_name ?? `Worker #${disbursement.worker_profile_id}`;

  return (
    <div className="px-4 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-foreground">{workerLabel}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Assignment #{disbursement.assignment_id} ·{" "}
            <span className="font-mono">{fmt(disbursement.amount)}</span> ·
            Scheduled {fmtDate(disbursement.scheduled_date)}
          </p>
          {disbursement.payment_reference && (
            <p className="mt-0.5 text-xs text-muted-foreground">
              Ref: <span className="font-mono">{disbursement.payment_reference}</span>
            </p>
          )}
          {disbursement.paid_at && (
            <p className="mt-0.5 text-xs text-muted-foreground">
              Paid {fmtDate(disbursement.paid_at)}
            </p>
          )}
          {disbursement.notes && (
            <p className="mt-0.5 text-xs text-muted-foreground italic">
              {disbursement.notes}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge value={disbursement.disbursement_status} />
          {isPending && action === null && (
            <>
              <Button
                size="sm"
                variant="outline"
                className="h-7 border-green-300 text-green-700 hover:bg-green-50"
                onClick={() => {
                  setAction("paid");
                  setFormError(null);
                }}
              >
                <CheckCircle2 className="mr-1 size-3.5" />
                Mark paid
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-7 border-red-300 text-red-700 hover:bg-red-50"
                onClick={() => {
                  setAction("failed");
                  setFormError(null);
                }}
              >
                <XCircle className="mr-1 size-3.5" />
                Mark failed
              </Button>
            </>
          )}
        </div>
      </div>

      {action === "paid" && (
        <div className="mt-3 space-y-2 rounded-lg bg-green-50 p-3">
          <label className="block text-xs font-medium text-foreground">
            Payment reference <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. NEFT-20260528-001"
            className="h-9 w-full rounded-md border border-input bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            value={paymentRef}
            onChange={(e) => {
              setPaymentRef(e.target.value);
              setFormError(null);
            }}
          />
          {formError && <p className="text-xs text-red-600">{formError}</p>}
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="accent"
              disabled={paidMutation.isPending}
              onClick={() => {
                if (!paymentRef.trim()) {
                  setFormError("Payment reference is required.");
                  return;
                }
                paidMutation.mutate();
              }}
            >
              {paidMutation.isPending ? "Saving…" : "Confirm paid"}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setAction(null);
                setPaymentRef("");
                setFormError(null);
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {action === "failed" && (
        <div className="mt-3 space-y-2 rounded-lg bg-red-50 p-3">
          <label className="block text-xs font-medium text-foreground">
            Failure notes <span className="text-red-500">*</span>
          </label>
          <textarea
            rows={2}
            placeholder="e.g. Bank transfer rejected — invalid account number."
            className="w-full rounded-md border border-input bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            value={failNotes}
            onChange={(e) => {
              setFailNotes(e.target.value);
              setFormError(null);
            }}
          />
          {formError && <p className="text-xs text-red-600">{formError}</p>}
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="destructive"
              disabled={failedMutation.isPending}
              onClick={() => {
                if (!failNotes.trim()) {
                  setFormError("Failure notes are required.");
                  return;
                }
                failedMutation.mutate();
              }}
            >
              {failedMutation.isPending ? "Saving…" : "Confirm failed"}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setAction(null);
                setFailNotes("");
                setFormError(null);
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

function CreateDisbursementRow({
  assignment,
  onCreated,
}: {
  assignment: AssignmentItem;
  onCreated: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [amount, setAmount] = useState(
    assignment.salary_amount ? String(assignment.salary_amount) : ""
  );
  const [scheduledDate, setScheduledDate] = useState(today());
  const [formError, setFormError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      disbursementsService.create({
        assignment_id: assignment.id,
        amount: Math.round(Number(amount) * 100), // Rs. → paise
        scheduled_date: scheduledDate,
      }),
    onSuccess: () => {
      onCreated();
      setExpanded(false);
    },
    onError: (err) => setFormError(getErrorMessage(err)),
  });

  const handleSubmit = () => {
    setFormError(null);
    const parsed = Number(amount);
    if (!amount || isNaN(parsed) || parsed <= 0) {
      setFormError("Enter a valid amount in rupees.");
      return;
    }
    if (!scheduledDate) {
      setFormError("Scheduled date is required.");
      return;
    }
    mutation.mutate();
  };

  return (
    <div className="rounded-lg border border-border bg-muted/30 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-foreground">{assignment.worker_name}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Assignment #{assignment.id}
            {assignment.salary_amount
              ? ` · Suggested Rs. ${assignment.salary_amount.toLocaleString("en-IN")}`
              : ""}
          </p>
        </div>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => {
            setExpanded((v) => !v);
            setFormError(null);
          }}
        >
          {expanded ? "Cancel" : "Create disbursement"}
        </Button>
      </div>

      {expanded && (
        <div className="mt-3 space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-foreground">
                Amount (Rs.) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                min={1}
                step={0.01}
                placeholder="e.g. 500"
                className="h-9 w-full rounded-md border border-input bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={amount}
                onChange={(e) => {
                  setAmount(e.target.value);
                  setFormError(null);
                }}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-foreground">
                Scheduled date <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                className="h-9 w-full rounded-md border border-input bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={scheduledDate}
                onChange={(e) => {
                  setScheduledDate(e.target.value);
                  setFormError(null);
                }}
              />
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Amount is entered in rupees (Rs.). It will be stored as paise internally.
          </p>
          {formError && <p className="text-xs text-red-600">{formError}</p>}
          <Button
            size="sm"
            variant="accent"
            disabled={mutation.isPending}
            onClick={handleSubmit}
          >
            {mutation.isPending ? "Creating…" : "Create disbursement"}
          </Button>
        </div>
      )}
    </div>
  );
}
