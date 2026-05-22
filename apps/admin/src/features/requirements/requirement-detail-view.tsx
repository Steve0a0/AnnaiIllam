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
  MapPin,
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
import RequirementAssignmentsList from "@/features/assignments/requirement-assignments-list";
import { requirementsService } from "@/services/requirements.service";
import type { AdminRequirementDetail, RequirementInterestItem } from "@/types/requirement";

const ASSIGNABLE_STATUSES = new Set([
  "approved",
  "workers_assigned",
  "assigned",
  "accepted",
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

  if (isLoading) {
    return <RequirementsLoading />;
  }

  if (isError || !data?.data) {
    return <RequirementsError message={error?.message} />;
  }

  const requirement = data.data;
  const canMarkUnderReview = requirement.status === "submitted";
  const canCreateQuote =
    requirement.status === "under_review" && !requirement.quote;
  const canAssignWorkers = ASSIGNABLE_STATUSES.has(requirement.status);

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
          </div>
        </div>
      </header>

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
                onAddWorkers={() => setShowAssignmentDialog(true)}
              />

            {canAssignWorkers ? (
              <>
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
                      onSuccess={() => {
                        setShowAssignmentDialog(false);
                        refetch();
                      }}
                    />
                  </DialogContent>
                </Dialog>
              </>
            ) : (
              <NoticeCard>
                Assign workers after the client approves the quote.
              </NoticeCard>
            )}
          </section>
        </main>

        <aside className="space-y-6 xl:sticky xl:top-6 xl:self-start">
          <QuickInfoCard requirement={requirement} />
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
        <StatusBadge value={quote.status} />
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
  if (status === "approved" && quote?.status === "pending_client_approval") {
    return "quoted";
  }

  if (["assigned", "accepted", "workers_assigned"].includes(status)) {
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

function NoticeCard({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl border-l-4 border-l-[#B45309] border-y border-r border-[#FEF3C7] bg-[#FFFBEB] px-4 py-3 text-sm text-[#B45309]">
      {children}
    </div>
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
