"use client";

import Link from "next/link";
import { useState } from "react";
import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  BriefcaseBusiness,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  CreditCard,
  FileText,
  MapPin,
  Send,
  TrendingUp,
  Users,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useRequirementDetail } from "@/features/requirements/use-requirement-detail";
import RequirementsLoading from "@/features/requirements/requirements-loading";
import RequirementsError from "@/features/requirements/requirements-error";
import StatusBadge from "@/components/shared/status-badge";
import MarkUnderReviewButton from "@/features/requirements/mark-under-review-button";
import CreateQuoteForm from "@/features/requirements/create-quote-form";
import CreateAssignmentForm from "@/features/assignments/create-assignment-form";
import RequirementAssignmentsList, { type ReplacementHint } from "@/features/assignments/requirement-assignments-list";
import CoverageCalendar from "@/features/assignments/coverage-calendar";
import WorkerPaymentsSection from "@/features/requirements/worker-payments-section";
import DisbursementsSection from "@/features/requirements/disbursements-section";
import { requirementsService } from "@/services/requirements.service";
import { financeService } from "@/services/finance.service";
import { assignmentsService } from "@/services/assignments.service";
import { invoicesService } from "@/services/invoices.service";
import { getErrorMessage } from "@/lib/get-error-message";
import type { AdminRequirementDetail, RequirementInterestItem } from "@/types/requirement";

const ASSIGNABLE_STATUSES = new Set([
  "approved",
  "workers_assigned",
]);

const TIMELINE_STEPS = [
  { status: "submitted", label: "Submitted", helper: "Client sent request" },
  { status: "under_review", label: "Under review", helper: "Admin review started" },
  { status: "quoted", label: "Quoted", helper: "Quote sent to client" },
  { status: "approved", label: "Approved", helper: "Ready for assignment" },
  { status: "workers_assigned", label: "Workers assigned", helper: "Workers selected" },
  { status: "in_progress", label: "In progress", helper: "Attendance underway" },
  { status: "completed", label: "Completed", helper: "Job closed" },
];

export default function RequirementDetailView({
  requirementId,
}: {
  requirementId: number;
}) {
  const { data, isLoading, isError, error, refetch } =
    useRequirementDetail(requirementId);

  const [showQuoteForm, setShowQuoteForm] = useState(false);
  const [showAssignmentDialog, setShowAssignmentDialog] = useState(false);
  const [replacementHint, setReplacementHint] = useState<ReplacementHint | null>(null);
  const [completing, setCompleting] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [rejectReasonError, setRejectReasonError] = useState("");
  const [rejecting, setRejecting] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [cancelReasonError, setCancelReasonError] = useState("");
  const [cancelling, setCancelling] = useState(false);

  const [showExtensionDialog, setShowExtensionDialog] = useState(false);
  const [extensionDays, setExtensionDays] = useState("");
  const [extensionRate, setExtensionRate] = useState("");
  const [extensionError, setExtensionError] = useState("");
  const [extending, setExtending] = useState(false);

  const { data: paymentsData } = useQuery({
    queryKey: ["requirement-payments", requirementId],
    queryFn: () => financeService.getClientPaymentsByRequirement(requirementId),
    enabled: ASSIGNABLE_STATUSES.has(data?.data?.status ?? ""),
  });
  const hasPaidPayment =
    paymentsData?.data?.some((p) => p.payment_status === "paid") ?? false;

  if (isLoading) {
    return <RequirementsLoading />;
  }

  if (isError || !data?.data) {
    return <RequirementsError message={error?.message} />;
  }

  const requirement = data.data;
  const canMarkUnderReview = requirement.status === "submitted";
  const canCreateQuote =
    requirement.status === "under_review" &&
    (!requirement.quote ||
      ["rejected", "expired"].includes(requirement.quote.status));
  const canReject =
    requirement.status === "under_review" || requirement.status === "quoted";
  const canCancel = !["completed", "rejected", "cancelled"].includes(requirement.status);
  const statusAllowsAssignment = ASSIGNABLE_STATUSES.has(requirement.status);
  const canAssignWorkers = statusAllowsAssignment && hasPaidPayment;
  const awaitingPayment = statusAllowsAssignment && !hasPaidPayment;
  const canMarkComplete = requirement.status === "in_progress";
  const canRequestExtension =
    requirement.status === "in_progress" || requirement.status === "workers_assigned";

  const handleMarkComplete = async () => {
    try {
      setCompleting(true);
      await requirementsService.markRequirementComplete(requirement.id);
      refetch();
    } catch {
      // error is surfaced to console; no toast system in this view
    } finally {
      setCompleting(false);
    }
  };

  const handleReject = async () => {
    const trimmed = rejectReason.trim();
    if (!trimmed) {
      setRejectReasonError("Rejection reason is required.");
      return;
    }
    try {
      setRejecting(true);
      await requirementsService.rejectRequirement(requirement.id, trimmed);
      setShowRejectDialog(false);
      setRejectReason("");
      setRejectReasonError("");
      refetch();
    } catch {
      setRejectReasonError("Failed to reject. Please try again.");
    } finally {
      setRejecting(false);
    }
  };

  const handleRequestExtension = async () => {
    const days = parseInt(extensionDays, 10);
    const rate = parseInt(extensionRate, 10);
    if (!days || days < 1) {
      setExtensionError("Additional days must be at least 1.");
      return;
    }
    if (!rate || rate < 1) {
      setExtensionError("Rate per worker per day must be at least 1.");
      return;
    }
    try {
      setExtending(true);
      setExtensionError("");
      await requirementsService.requestExtension(requirement.id, days, rate);
      setShowExtensionDialog(false);
      setExtensionDays("");
      setExtensionRate("");
      refetch();
    } catch (err) {
      setExtensionError(getErrorMessage(err));
    } finally {
      setExtending(false);
    }
  };

  const handleCancel = async () => {
    const trimmed = cancelReason.trim();
    if (trimmed.length < 10) {
      setCancelReasonError("Cancellation reason must be at least 10 characters.");
      return;
    }
    try {
      setCancelling(true);
      await requirementsService.cancelRequirement(requirement.id, trimmed);
      setShowCancelDialog(false);
      setCancelReason("");
      setCancelReasonError("");
      refetch();
    } catch {
      setCancelReasonError("Failed to cancel. Please try again.");
    } finally {
      setCancelling(false);
    }
  };

  return (
    <div className="space-y-6">
      <header className="border-b border-border pb-6">
        <Link
          href="/requirements"
          className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground transition hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          All requirements
        </Link>

        <div className="mt-5 flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">
              Requests / REQ-{requirement.id}
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <h1 className="font-display text-3xl font-semibold tracking-[-0.02em] text-foreground">
                {formatLabel(requirement.category)} Requirement
              </h1>
              <StatusBadge value={requirement.status} />
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                <MapPin className="size-4" />
                {requirement.city}, {requirement.state}
              </span>
              <span className="inline-flex items-center gap-1.5 font-mono">
                <CalendarDays className="size-4" />
                {formatDate(requirement.start_date)}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Users className="size-4" />
                {requirement.number_of_workers} workers
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-start gap-3">
            {canMarkUnderReview ? (
              <MarkUnderReviewButton
                requirementId={requirement.id}
                onSuccess={() => refetch()}
              />
            ) : null}
            {canCreateQuote ? (
              <Button
                onClick={() => setShowQuoteForm((prev) => !prev)}
                variant="accent"
              >
                {showQuoteForm ? "Close Quote Form" : "Create Quote"}
              </Button>
            ) : null}
            {canReject ? (
              <Button
                onClick={() => setShowRejectDialog(true)}
                variant="destructive"
              >
                <XCircle className="mr-1.5 size-4" />
                Reject
              </Button>
            ) : null}
            {canCancel ? (
              <Button
                onClick={() => setShowCancelDialog(true)}
                variant="outline"
                className="border-red-300 text-red-700 hover:bg-red-50"
              >
                <XCircle className="mr-1.5 size-4" />
                Cancel
              </Button>
            ) : null}
            {canRequestExtension ? (
              <Button
                onClick={() => setShowExtensionDialog(true)}
                variant="secondary"
              >
                <CalendarDays className="mr-1.5 size-4" />
                Request Extension
              </Button>
            ) : null}
            {canMarkComplete ? (
              <Button
                onClick={handleMarkComplete}
                disabled={completing}
                variant="accent"
              >
                <CheckCircle2 className="mr-1.5 size-4" />
                {completing ? "Completing…" : "Mark Complete"}
              </Button>
            ) : null}
          </div>
        </div>
      </header>

      {awaitingPayment && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-4">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-red-100">
            <CreditCard className="size-5 text-red-600" />
          </div>
          <div className="flex-1">
            <p className="font-semibold text-red-800">Advance payment not confirmed</p>
            <p className="mt-0.5 text-sm text-red-700">
              The client has approved the quote but the advance payment has not been marked paid yet.
              Worker assignment is locked until payment is confirmed in Finance.
            </p>
          </div>
          <Link
            href="/finance"
            className="shrink-0 rounded-lg bg-red-100 px-3 py-1.5 text-xs font-semibold text-red-700 transition hover:bg-red-200"
          >
            Go to Finance →
          </Link>
        </div>
      )}

      {requirement.status === "rejected" && requirement.rejection_reason && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-4">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-red-100">
            <XCircle className="size-5 text-red-600" />
          </div>
          <div>
            <p className="font-semibold text-red-800">Requirement rejected</p>
            <p className="mt-0.5 text-sm text-red-700">{requirement.rejection_reason}</p>
          </div>
        </div>
      )}

      {requirement.status === "cancelled" && requirement.cancellation_reason && (
        <div className="flex items-start gap-3 rounded-xl border border-orange-200 bg-orange-50 px-4 py-4">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-orange-100">
            <XCircle className="size-5 text-orange-600" />
          </div>
          <div>
            <p className="font-semibold text-orange-800">Requirement cancelled</p>
            <p className="mt-0.5 text-sm text-orange-700">{requirement.cancellation_reason}</p>
          </div>
        </div>
      )}

      {/* Reject dialog */}
      <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Reject requirement</DialogTitle>
            <DialogDescription>
              Provide a reason for rejection. This will be visible to the client.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-2 space-y-3">
            <textarea
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              rows={4}
              placeholder="e.g. Requirement details are incomplete or outside our service area."
              value={rejectReason}
              onChange={(e) => {
                setRejectReason(e.target.value);
                if (rejectReasonError) setRejectReasonError("");
              }}
            />
            {rejectReasonError && (
              <p className="text-sm text-red-600">{rejectReasonError}</p>
            )}
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setShowRejectDialog(false);
                  setRejectReason("");
                  setRejectReasonError("");
                }}
                disabled={rejecting}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleReject}
                disabled={rejecting}
              >
                {rejecting ? "Rejecting…" : "Confirm rejection"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Extension dialog */}
      <Dialog open={showExtensionDialog} onOpenChange={setShowExtensionDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Request job extension</DialogTitle>
            <DialogDescription>
              An extension quote will be sent to the client for approval. Assignment end-dates are updated once the client approves.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-2 space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">
                Additional days <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                min={1}
                className="h-10 w-full rounded-lg border border-input bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="e.g. 7"
                value={extensionDays}
                onChange={(e) => setExtensionDays(e.target.value)}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">
                Rate per worker per day (Rs.) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                min={1}
                className="h-10 w-full rounded-lg border border-input bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="e.g. 500"
                value={extensionRate}
                onChange={(e) => setExtensionRate(e.target.value)}
              />
              {extensionDays && extensionRate && requirement.number_of_workers && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Extension total: Rs.{" "}
                  {(
                    parseInt(extensionDays || "0", 10) *
                    parseInt(extensionRate || "0", 10) *
                    requirement.number_of_workers
                  ).toLocaleString("en-IN")}{" "}
                  ({requirement.number_of_workers} workers × {extensionDays} days × Rs. {extensionRate})
                </p>
              )}
            </div>
            {extensionError && (
              <p className="text-sm text-red-600">{extensionError}</p>
            )}
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setShowExtensionDialog(false);
                  setExtensionDays("");
                  setExtensionRate("");
                  setExtensionError("");
                }}
                disabled={extending}
              >
                Cancel
              </Button>
              <Button
                variant="accent"
                onClick={handleRequestExtension}
                disabled={extending}
              >
                {extending ? "Sending quote…" : "Send extension quote"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Cancel dialog */}
      <Dialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Cancel requirement</DialogTitle>
            <DialogDescription>
              Provide a reason for cancellation (min 10 characters). All active assignments will be cancelled and workers freed.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-2 space-y-3">
            <textarea
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              rows={4}
              placeholder="e.g. Client has withdrawn the requirement due to project delay."
              value={cancelReason}
              onChange={(e) => {
                setCancelReason(e.target.value);
                if (cancelReasonError) setCancelReasonError("");
              }}
            />
            {cancelReasonError && (
              <p className="text-sm text-red-600">{cancelReasonError}</p>
            )}
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setShowCancelDialog(false);
                  setCancelReason("");
                  setCancelReasonError("");
                }}
                disabled={cancelling}
              >
                Go back
              </Button>
              <Button
                variant="destructive"
                onClick={handleCancel}
                disabled={cancelling}
              >
                {cancelling ? "Cancelling…" : "Confirm cancellation"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <main className="space-y-6">
          <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">
                  Request info
                </p>
                <h2 className="mt-2 font-display text-xl font-semibold text-foreground">
                  Manpower requirement details
                </h2>
              </div>
              <div className="rounded-full bg-[#EDFAF3] px-3 py-1 font-mono text-xs font-medium text-[#1A6640]">
                REQ-{requirement.id}
              </div>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <DetailItem label="Category" value={formatLabel(requirement.category)} />
              <DetailItem
                label="Subcategory"
                value={requirement.subcategory ? formatLabel(requirement.subcategory) : "-"}
              />
              <DetailItem
                label="Workers needed"
                value={requirement.number_of_workers}
                mono
              />
              <DetailItem label="Work location" value={requirement.work_location} />
              <DetailItem label="City" value={requirement.city} />
              <DetailItem label="State" value={requirement.state} />
              <DetailItem
                label="Start date"
                value={formatDate(requirement.start_date)}
                mono
              />
              <DetailItem
                label="Duration"
                value={`${requirement.duration_days} days`}
                mono
              />
              <DetailItem label="Shift" value={requirement.shift_details || "-"} />
              <DetailItem
                label="Food at site"
                value={requirement.food_required ? "Required" : "Not required"}
              />
              <DetailItem
                label="Accommodation"
                value={
                  requirement.accommodation_required
                    ? "Required"
                    : "Not required"
                }
              />
              <DetailItem
                label="Geofence check-in"
                value={requirement.require_geofence ? "Required" : "Not required"}
              />
              <DetailItem
                label="Client budget"
                value={
                  requirement.budget_amount
                    ? `Rs. ${requirement.budget_amount.toLocaleString("en-IN")}`
                    : "-"
                }
                mono
              />
            </div>

            <div className="mt-6 border-t border-border pt-5">
              <p className="text-sm font-medium text-foreground">Notes</p>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                {requirement.notes || "No notes provided."}
              </p>
            </div>
          </section>

          <QuoteSummary quote={requirement.quote} />

          <InterestedWorkers requirementId={requirement.id} />

          {showQuoteForm ? (
            <CreateQuoteForm
              requirement={requirement}
              onSuccess={() => {
                setShowQuoteForm(false);
                refetch();
              }}
            />
          ) : null}

          <section className="space-y-4">
            <SectionHeader
              eyebrow="Worker assignment"
              title="Assignments"
              description="Track assigned workers first, then add another worker only when the request still needs coverage."
            />

              <RequirementAssignmentsList
                requirementId={requirement.id}
                requiredWorkers={requirement.number_of_workers}
                canAddWorkers={canAssignWorkers}
                onAddWorkers={() => { setReplacementHint(null); setShowAssignmentDialog(true); }}
                onReplace={(hint) => { setReplacementHint(hint); setShowAssignmentDialog(true); }}
              />

            {["workers_assigned", "in_progress", "completed"].includes(requirement.status) && (
              <CoverageCalendar
                requirementId={requirement.id}
                requiredPerDay={requirement.number_of_workers}
              />
            )}

            {canAssignWorkers ? (
              <Dialog
                open={showAssignmentDialog}
                onOpenChange={setShowAssignmentDialog}
              >
                <DialogContent className="max-h-[90vh] max-w-5xl overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Add workers to requirement</DialogTitle>
                    <DialogDescription>
                      Select one or more approved, available workers and
                      apply the same role, shift, and optional payout to the
                      batch.
                    </DialogDescription>
                  </DialogHeader>
                  <CreateAssignmentForm
                    requirement={requirement}
                    requirementId={requirement.id}
                    replacementHint={replacementHint ?? undefined}
                    onSuccess={() => {
                      setShowAssignmentDialog(false);
                      setReplacementHint(null);
                      refetch();
                    }}
                  />
                </DialogContent>
              </Dialog>
            ) : !awaitingPayment ? (
              <NoticeCard>
                Assign workers after the client approves the quote.
              </NoticeCard>
            ) : null}
          </section>

          {["workers_assigned", "in_progress", "completed"].includes(requirement.status) && (
            <WorkerPaymentsSection requirementId={requirement.id} />
          )}

          {requirement.status === "completed" && (
            <InvoicesSection requirementId={requirement.id} />
          )}

          {requirement.status === "completed" && (
            <DisbursementsSection requirementId={requirement.id} />
          )}
        </main>

        <aside className="space-y-6 xl:sticky xl:top-6 xl:self-start">
          <QuickInfoCard requirement={requirement} />
          <BudgetSummaryCard requirement={requirement} />
          <StatusTimeline status={requirement.status} quote={requirement.quote} />
        </aside>
      </div>
    </div>
  );
}

function QuoteSummary({
  quote,
}: {
  quote: AdminRequirementDetail["quote"];
}) {
  if (!quote) {
    return (
      <NoticeCard>
        No quote has been created yet. Move the request under review, then send
        a client-facing quote.
      </NoticeCard>
    );
  }

  const isExpired =
    quote.valid_until != null &&
    new Date(quote.valid_until) < new Date(new Date().toDateString());

  return (
    <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">
            Quote
          </p>
          <h2 className="mt-2 font-display text-xl font-semibold text-foreground">
            Client-facing estimate
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Quote details waiting for approval or already decided by the
            client.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isExpired && (
            <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800">
              Expired
            </span>
          )}
          <StatusBadge value={quote.status} />
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <DetailItem
          label="Quoted amount"
          value={`Rs. ${quote.quoted_amount.toLocaleString("en-IN")}`}
          mono
        />
        <DetailItem
          label="Rate per worker per day"
          value={
            quote.rate_per_worker
              ? `Rs. ${quote.rate_per_worker.toLocaleString("en-IN")}`
              : "-"
          }
          mono
        />
        <DetailItem
          label="Total worker days"
          value={quote.total_worker_days ?? "-"}
          mono
        />
        <DetailItem
          label="Advance amount"
          value={
            quote.advance_amount
              ? `Rs. ${quote.advance_amount.toLocaleString("en-IN")}`
              : "-"
          }
          mono
        />
        <DetailItem label="Payment model" value={formatLabel(quote.payment_model)} />
        <DetailItem
          label="Valid until"
          value={quote.valid_until ? formatDate(quote.valid_until) : "-"}
          mono
        />
      </div>

      {quote.terms_notes ? (
        <TextBlock label="Terms notes" value={quote.terms_notes} />
      ) : null}

      {quote.internal_notes ? (
        <TextBlock label="Internal notes" value={quote.internal_notes} />
      ) : null}
    </section>
  );
}

function QuickInfoCard({
  requirement,
}: {
  requirement: AdminRequirementDetail;
}) {
  return (
    <section className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-lg bg-[#EDFAF3] text-[#1A6640]">
          <BriefcaseBusiness className="size-5" />
        </div>
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">
            Quick info
          </p>
          <h2 className="font-display text-lg font-semibold text-foreground">
            Request summary
          </h2>
        </div>
      </div>

      <div className="mt-5 space-y-4">
        <CompactInfo label="Status" value={<StatusBadge value={requirement.status} />} />
        <CompactInfo
          label="Worker days"
          value={`${requirement.number_of_workers * requirement.duration_days}`}
          mono
        />
        <CompactInfo
          label="Location"
          value={`${requirement.city}, ${requirement.state}`}
        />
        <CompactInfo
          label="Shift"
          value={requirement.shift_details || "Not specified"}
        />
      </div>
    </section>
  );
}

function StatusTimeline({
  status,
  quote,
}: {
  status: string;
  quote: AdminRequirementDetail["quote"];
}) {
  const normalizedStatus = normalizeTimelineStatus(status, quote);
  const activeIndex = Math.max(
    0,
    TIMELINE_STEPS.findIndex((step) => step.status === normalizedStatus),
  );

  return (
    <section className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-lg bg-[#F5F3FF] text-[#6D28D9]">
          <ClipboardCheck className="size-5" />
        </div>
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">
            Status timeline
          </p>
          <h2 className="font-display text-lg font-semibold text-foreground">
            Request progress
          </h2>
        </div>
      </div>

      <ol className="mt-6 space-y-0">
        {TIMELINE_STEPS.map((step, index) => {
          const isComplete = index < activeIndex;
          const isCurrent = index === activeIndex;
          const nodeClass = isComplete || isCurrent
            ? "bg-[#1A6640]"
            : "bg-[#D6D3D1]";

          return (
            <li key={step.status} className="relative flex gap-3 pb-5 last:pb-0">
              {index < TIMELINE_STEPS.length - 1 ? (
                <span className="absolute left-[5px] top-4 h-full w-0.5 bg-border" />
              ) : null}
              <span
                className={`relative z-10 mt-1 size-3 rounded-full ${nodeClass} ${
                  isCurrent ? "ring-4 ring-[#D4F0E3]" : ""
                }`}
              />
              <span>
                <span className="block text-sm font-medium text-foreground">
                  {step.label}
                </span>
                <span className="mt-1 block text-xs text-muted-foreground">
                  {step.helper}
                </span>
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

function normalizeTimelineStatus(
  status: string,
  quote: AdminRequirementDetail["quote"],
) {
  if (status === "approved" && quote?.status === "sent") {
    return "quoted";
  }

  if (status === "workers_assigned") {
    return "workers_assigned";
  }

  return status;
}

function SectionHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div>
      <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">
        {eyebrow}
      </p>
      <h2 className="mt-2 font-display text-xl font-semibold text-foreground">
        {title}
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
    </div>
  );
}

function DetailItem({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string | number;
  mono?: boolean;
}) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-[0.02em] text-muted-foreground">
        {label}
      </p>
      <p
        className={`mt-1 text-sm text-foreground ${
          mono ? "font-mono" : ""
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function CompactInfo({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-muted pb-3 last:border-b-0 last:pb-0">
      <p className="text-sm text-muted-foreground">{label}</p>
      <div
        className={`text-right text-sm font-medium text-foreground ${
          mono ? "font-mono" : ""
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function TextBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="mt-6 border-t border-border pt-5">
      <p className="text-sm font-medium text-foreground">{label}</p>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{value}</p>
    </div>
  );
}

function InterestedWorkers({ requirementId }: { requirementId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ["requirement-interests", requirementId],
    queryFn: () => requirementsService.getRequirementInterests(requirementId),
  });

  const interests = data?.data ?? [];

  if (isLoading) {
    return (
      <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <p className="text-sm text-muted-foreground">Loading interested workers…</p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">
            Worker interest
          </p>
          <h2 className="mt-2 font-display text-xl font-semibold text-foreground">
            Interested workers
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Workers who expressed interest via the mobile app.
          </p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
          {interests.length} interested
        </span>
      </div>

      {interests.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No workers have expressed interest yet.
        </p>
      ) : (
        <div className="divide-y divide-border">
          {interests.map((item) => (
            <InterestedWorkerRow key={item.interest_id} item={item} />
          ))}
        </div>
      )}
    </section>
  );
}

function InterestedWorkerRow({ item }: { item: RequirementInterestItem }) {
  const initials = item.full_name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  const isWithdrawn = item.status === "withdrawn";

  return (
    <div className="flex items-center gap-4 py-3.5">
      <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-800">
        {initials}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium text-foreground">{item.full_name}</p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          {formatLabel(item.category)}
          {item.subcategory ? ` · ${formatLabel(item.subcategory)}` : ""} · {item.city}
        </p>
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1.5">
        <div className="flex items-center gap-1.5">
          {item.is_available ? (
            <CheckCircle2 className="size-3.5 text-emerald-600" />
          ) : (
            <XCircle className="size-3.5 text-slate-400" />
          )}
          <span className="text-xs text-muted-foreground">
            {item.is_available ? "Available" : "Unavailable"}
          </span>
        </div>
        <span
          className={`text-xs font-medium ${
            isWithdrawn ? "text-slate-400" : "text-emerald-700"
          }`}
        >
          {isWithdrawn ? "Withdrawn" : "Interested"}
        </span>
      </div>
    </div>
  );
}

function BudgetSummaryCard({
  requirement,
}: {
  requirement: AdminRequirementDetail;
}) {
  const { data } = useQuery({
    queryKey: ["requirement-assignments", requirement.id],
    queryFn: () => assignmentsService.getAssignmentsByRequirement(requirement.id),
    enabled: !!requirement.id,
  });

  const assignments = data?.data ?? [];
  const activeStatuses = new Set(["assigned", "accepted", "active", "completed"]);

  let totalAssignedCost = 0;
  for (const a of assignments) {
    if (!activeStatuses.has(a.status) || !a.salary_amount) continue;
    let days = requirement.duration_days;
    if (a.start_date && a.end_date) {
      const diff =
        (new Date(a.end_date).getTime() - new Date(a.start_date).getTime()) /
        (1000 * 60 * 60 * 24) + 1;
      days = Math.max(1, Math.round(diff));
    }
    totalAssignedCost += a.salary_amount * days;
  }

  const budget = requirement.budget_amount;
  const quoted = requirement.quote?.quoted_amount ?? null;
  const isOver = budget !== null && totalAssignedCost > budget;

  return (
    <section className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-lg bg-[#EFF6FF] text-[#1D4ED8]">
          <TrendingUp className="size-5" />
        </div>
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">
            Cost tracker
          </p>
          <h2 className="font-display text-lg font-semibold text-foreground">
            Budget vs. cost
          </h2>
        </div>
      </div>

      <div className="mt-5 space-y-4">
        <CompactInfo
          label="Assigned worker cost"
          value={
            totalAssignedCost > 0
              ? `Rs. ${totalAssignedCost.toLocaleString("en-IN")}`
              : "—"
          }
          mono
        />
        {quoted !== null && (
          <CompactInfo
            label="Client quoted total"
            value={`Rs. ${quoted.toLocaleString("en-IN")}`}
            mono
          />
        )}
        {budget !== null && (
          <CompactInfo
            label="Client stated budget"
            value={`Rs. ${budget.toLocaleString("en-IN")}`}
            mono
          />
        )}
        {quoted !== null && totalAssignedCost > 0 && (
          <CompactInfo
            label="Margin (quoted − worker cost)"
            value={`Rs. ${(quoted - totalAssignedCost).toLocaleString("en-IN")}`}
            mono
          />
        )}
      </div>

      {isOver && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700">
          Worker cost exceeds client budget
        </div>
      )}
    </section>
  );
}

function NoticeCard({
  children,
  variant = "warning",
}: {
  children: ReactNode;
  variant?: "warning" | "payment";
}) {
  const cls =
    variant === "payment"
      ? "rounded-xl border-l-4 border-l-[#B91C1C] border-y border-r border-[#FEE2E2] bg-[#FFF5F5] px-4 py-3 text-sm text-[#B91C1C]"
      : "rounded-xl border-l-4 border-l-[#B45309] border-y border-r border-[#FEF3C7] bg-[#FFFBEB] px-4 py-3 text-sm text-[#B45309]";
  return <div className={cls}>{children}</div>;
}

function InvoicesSection({ requirementId }: { requirementId: number }) {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["requirement-invoices", requirementId],
    queryFn: () => invoicesService.getByRequirement(requirementId),
  });

  const [generating, setGenerating] = useState(false);
  const [issuing, setIssuing] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const invoices = data?.data ?? [];
  const hasActiveInvoice = invoices.some((inv) => inv.status !== "cancelled");

  const handleGenerate = async () => {
    setGenerating(true);
    setActionError(null);
    try {
      await invoicesService.generate({ requirement_id: requirementId });
      await refetch();
    } catch (err) {
      setActionError(getErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  };

  const handleIssue = async (invoiceId: number) => {
    setIssuing(invoiceId);
    setActionError(null);
    try {
      await invoicesService.issue(invoiceId);
      await refetch();
    } catch (err) {
      setActionError(getErrorMessage(err));
    } finally {
      setIssuing(null);
    }
  };

  return (
    <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-[#DBEAFE] text-[#1D4ED8]">
            <FileText className="size-5" />
          </div>
          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">
              Billing
            </p>
            <h2 className="font-display text-xl font-semibold text-foreground">Invoices</h2>
          </div>
        </div>
        {!hasActiveInvoice && (
          <Button
            variant="accent"
            size="sm"
            disabled={generating}
            onClick={handleGenerate}
          >
            <FileText className="size-4" />
            {generating ? "Generating…" : "Generate Invoice"}
          </Button>
        )}
      </div>

      {actionError && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {actionError}
        </div>
      )}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading invoices…</p>
      ) : invoices.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No invoice generated yet. Click Generate Invoice to create one.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="pb-2 pr-6 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Invoice #
                </th>
                <th className="pb-2 pr-6 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Subtotal
                </th>
                <th className="pb-2 pr-6 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  GST ({invoices[0]?.gst_rate ?? 18}%)
                </th>
                <th className="pb-2 pr-6 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Total
                </th>
                <th className="pb-2 pr-6 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Due date
                </th>
                <th className="pb-2 pr-6 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Status
                </th>
                <th className="pb-2 text-right text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id} className="border-b border-muted last:border-b-0">
                  <td className="py-3 pr-6 font-mono font-medium text-foreground">
                    {inv.invoice_number}
                  </td>
                  <td className="py-3 pr-6 font-mono text-foreground">
                    Rs. {inv.subtotal.toLocaleString("en-IN")}
                  </td>
                  <td className="py-3 pr-6 font-mono text-muted-foreground">
                    Rs. {inv.gst_amount.toLocaleString("en-IN")}
                  </td>
                  <td className="py-3 pr-6 font-mono font-semibold text-foreground">
                    Rs. {inv.total_amount.toLocaleString("en-IN")}
                  </td>
                  <td className="py-3 pr-6 font-mono text-muted-foreground">
                    {inv.due_date ?? "—"}
                  </td>
                  <td className="py-3 pr-6">
                    <StatusBadge value={inv.status} />
                  </td>
                  <td className="py-3 text-right">
                    {inv.status === "draft" && (
                      <Button
                        variant="accent"
                        size="sm"
                        disabled={issuing === inv.id}
                        onClick={() => handleIssue(inv.id)}
                      >
                        <Send className="size-3.5" />
                        {issuing === inv.id ? "Issuing…" : "Issue to Client"}
                      </Button>
                    )}
                    {inv.status === "issued" && (
                      <span className="text-xs font-medium text-[#1D4ED8]">
                        Issued {inv.issued_at ? formatDate(inv.issued_at.slice(0, 10)) : ""}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function formatLabel(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value: string) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}
