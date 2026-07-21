"use client";

import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  FileText,
  Search,
  ShieldCheck,
  UserCheck,
  UserX,
  XCircle,
} from "lucide-react";
import PageHeader from "@/components/shared/page-header";
import LoadingState from "@/components/shared/loading-state";
import EmptyState from "@/components/shared/empty-state";
import ErrorState from "@/components/shared/error-state";
import StatusBadge from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { peopleService } from "@/services/people.service";
import type { AdminWorker, WorkerImportItem } from "@/types/people";

const sampleCsv = "phone,full_name,category,city,state,skills\n+919999999999,Ravi Kumar,Security,Chennai,Tamil Nadu,night shift";

function parseCsv(input: string): WorkerImportItem[] {
  const lines = input.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length < 2) return [];
  const headers = lines[0].split(",").map((item) => item.trim());
  return lines.slice(1).map((line) => {
    const values = line.split(",").map((item) => item.trim());
    const row = Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
    return {
      phone: row.phone,
      email: row.email || undefined,
      full_name: row.full_name,
      category: row.category,
      subcategory: row.subcategory || undefined,
      city: row.city,
      state: row.state,
      address: row.address || undefined,
      date_of_birth: row.date_of_birth || undefined,
      skills: row.skills || undefined,
      experience_notes: row.experience_notes || undefined,
    };
  });
}

export default function WorkersPage() {
  const queryClient = useQueryClient();
  const [csv, setCsv] = useState(sampleCsv);
  const [search, setSearch] = useState("");
  const [verificationStatus, setVerificationStatus] = useState("under_review");
  const [availabilityFilter, setAvailabilityFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [page, setPage] = useState(1);
  const [selectedWorker, setSelectedWorker] = useState<AdminWorker | null>(null);
  const [rejectWorker, setRejectWorker] = useState<AdminWorker | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [openingDocumentId, setOpeningDocumentId] = useState<number | null>(null);

  const PAGE_SIZE = 20;

  const queryParams = {
    verification_status: verificationStatus || undefined,
    is_available: availabilityFilter === "available" ? true : availabilityFilter === "unavailable" ? false : undefined,
    category: categoryFilter || undefined,
    page,
    page_size: PAGE_SIZE,
  };

  const workersQuery = useQuery({
    queryKey: ["admin-workers", queryParams],
    queryFn: () => peopleService.getWorkers(queryParams),
  });
  const parsedWorkers = useMemo(() => parseCsv(csv), [csv]);

  const pageData = workersQuery.data?.data;
  const workers = pageData?.items ?? [];
  const totalPages = pageData?.total_pages ?? 1;
  const total = pageData?.total ?? 0;

  const pendingReviewCount = workers.filter((w) => w.onboarding_step === "profile_submitted").length;
  const approvedCount = workers.filter((w) => w.onboarding_step === "approved").length;
  const rejectedCount = workers.filter((w) => w.verification_status === "rejected").length;

  // Client-side search on the current page only
  const filteredWorkers = workers.filter((worker) => {
    const query = search.trim().toLowerCase();
    return (
      query.length === 0 ||
      [worker.full_name, worker.phone, worker.city, worker.state, worker.skills]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(query))
    );
  });

  const activeWorker = selectedWorker ?? filteredWorkers[0] ?? null;

  function resetFilters() {
    setPage(1);
    setSelectedWorker(null);
  }

  function handleVerificationStatusChange(value: string) {
    setVerificationStatus(value);
    resetFilters();
  }

  function handleAvailabilityChange(value: string) {
    setAvailabilityFilter(value);
    resetFilters();
  }

  function handleCategoryChange(value: string) {
    setCategoryFilter(value);
    resetFilters();
  }

  const importMutation = useMutation({
    mutationFn: () => peopleService.importWorkers(parsedWorkers),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-workers"] }),
  });

  const approveMutation = useMutation({
    mutationFn: peopleService.approveWorker,
    onSuccess: () => {
      setSelectedWorker(null);
      queryClient.invalidateQueries({ queryKey: ["admin-workers"] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: peopleService.rejectWorker,
    onSuccess: () => {
      setRejectWorker(null);
      setRejectReason("");
      queryClient.invalidateQueries({ queryKey: ["admin-workers"] });
    },
  });

  const availabilityMutation = useMutation({
    mutationFn: ({ userId, isAvailable }: { userId: number; isAvailable: boolean }) =>
      peopleService.setWorkerAvailability(userId, isAvailable),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-workers"] });
    },
  });

  function handleApprove(worker: AdminWorker) {
    approveMutation.mutate(worker.user_id);
  }

  function handleReject() {
    if (!rejectWorker || rejectReason.trim().length < 10) return;
    rejectMutation.mutate({ userId: rejectWorker.user_id, reason: rejectReason.trim() });
  }

  async function handleOpenDocument(documentId: number) {
    setOpeningDocumentId(documentId);
    try {
      const result = await peopleService.getWorkerDocumentViewUrl(documentId);
      if (result.data.mode === "s3" && result.data.url) {
        window.open(result.data.url, "_blank", "noopener,noreferrer");
        return;
      }

      const blob = await peopleService.getWorkerDocumentContent(documentId);
      const objectUrl = URL.createObjectURL(blob);
      window.open(objectUrl, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
    } finally {
      setOpeningDocumentId(null);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workers"
        description="Review submitted worker profiles, verify documents, then approve or reject access."
        action={
          pendingReviewCount > 0 ? (
            <span className="inline-flex items-center rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-200">
              {pendingReviewCount} pending review
            </span>
          ) : undefined
        }
      />

      <section className="grid gap-4 md:grid-cols-3">
        <ReviewMetric
          title="Pending Review"
          value={pendingReviewCount}
          detail="submitted profiles"
          icon={<Clock3 className="h-4 w-4" />}
          tone="warning"
        />
        <ReviewMetric
          title="Approved Workers"
          value={approvedCount}
          detail="ready for biometric setup"
          icon={<UserCheck className="h-4 w-4" />}
          tone="success"
        />
        <ReviewMetric
          title="Rejected Profiles"
          value={rejectedCount}
          detail="needs correction"
          icon={<XCircle className="h-4 w-4" />}
          tone="danger"
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(420px,0.85fr)]">
        <Card className="overflow-hidden border-border bg-white shadow-sm">
          <CardHeader className="border-b border-border">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <CardTitle className="font-display text-xl font-semibold">
                Workers
                {total > 0 && (
                  <span className="ml-2 text-sm font-normal text-muted-foreground">({total})</span>
                )}
              </CardTitle>
              <div className="relative w-full lg:w-72">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search on this page"
                  className="pl-9"
                />
              </div>
            </div>

            {/* Verification status filter */}
            <div className="flex flex-wrap gap-2 pt-2">
              {(
                [
                  ["under_review", "Pending review"],
                  ["approved", "Approved"],
                  ["rejected", "Rejected"],
                  ["", "All"],
                ] as const
              ).map(([value, label]) => (
                <Button
                  key={value}
                  type="button"
                  variant={verificationStatus === value ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleVerificationStatusChange(value)}
                >
                  {label}
                </Button>
              ))}
            </div>

            {/* Availability + category filters */}
            <div className="flex flex-wrap items-center gap-3 pt-1">
              <div className="flex gap-1.5">
                {(
                  [
                    ["", "Any availability"],
                    ["available", "Available"],
                    ["unavailable", "Unavailable"],
                  ] as const
                ).map(([value, label]) => (
                  <Button
                    key={value}
                    type="button"
                    variant={availabilityFilter === value ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => handleAvailabilityChange(value)}
                    className="h-7 text-xs"
                  >
                    {label}
                  </Button>
                ))}
              </div>
              <div className="relative">
                <Input
                  value={categoryFilter}
                  onChange={(e) => handleCategoryChange(e.target.value)}
                  placeholder="Filter by category"
                  className="h-7 w-40 text-xs"
                />
              </div>
            </div>
          </CardHeader>

          {workersQuery.isLoading ? (
            <div className="p-6">
              <LoadingState title="Loading workers" description="Fetching worker profiles…" />
            </div>
          ) : workersQuery.isError ? (
            <div className="p-6">
              <ErrorState
                title="Could not load workers"
                description="Check your connection and try again."
                onRetry={() => workersQuery.refetch()}
              />
            </div>
          ) : filteredWorkers.length === 0 ? (
            <div className="p-6">
              <EmptyState
                title={search || verificationStatus || availabilityFilter || categoryFilter ? "No workers match your filters" : "No workers yet"}
                description={
                  search || verificationStatus || availabilityFilter || categoryFilter
                    ? "Try a different search term or adjust the filters."
                    : "Worker profiles will appear here once workers complete onboarding."
                }
              />
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-muted/40">
                    <tr>
                      {["Worker", "Category", "Location", "Availability", "Status", ""].map((heading) => (
                        <th
                          key={heading}
                          className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-widest text-muted-foreground"
                        >
                          {heading}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {filteredWorkers.map((worker) => (
                      <tr
                        key={worker.id}
                        className="cursor-pointer transition-colors hover:bg-muted/30"
                        onClick={() => setSelectedWorker(worker)}
                      >
                        <td className="px-4 py-4">
                          <p className="text-sm font-medium text-foreground">{worker.full_name}</p>
                          <p className="mt-1 font-mono text-xs text-muted-foreground">{worker.phone ?? "No phone"}</p>
                        </td>
                        <td className="px-4 py-4 text-sm text-muted-foreground">
                          {worker.category}
                          {worker.subcategory ? (
                            <span className="block text-xs text-muted-foreground/70">{worker.subcategory}</span>
                          ) : null}
                        </td>
                        <td className="px-4 py-4 text-sm text-muted-foreground">
                          {worker.city}, {worker.state}
                        </td>
                        <td className="px-4 py-4">
                          <span
                            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                              worker.is_available
                                ? "bg-green-50 text-green-700"
                                : "bg-amber-50 text-amber-700"
                            }`}
                          >
                            {worker.is_available ? "Available" : "On leave"}
                          </span>
                        </td>
                        <td className="px-4 py-4">
                          <StatusBadge value={worker.verification_status} />
                        </td>
                        <td className="px-4 py-4">
                          <Link
                            href={`/workers/${worker.id}`}
                            onClick={(e) => e.stopPropagation()}
                            onMouseEnter={() =>
                              queryClient.prefetchQuery({
                                queryKey: ["admin-worker-detail", worker.id],
                                queryFn: () => peopleService.getWorkerById(worker.id),
                              })
                            }
                            className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
                          >
                            View
                            <ArrowUpRight className="h-3 w-3" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="border-t border-border px-4 py-3">
                <div className="flex items-center justify-between gap-4">
                  <p className="text-xs text-muted-foreground">
                    {filteredWorkers.length < workers.length
                      ? `${filteredWorkers.length} match on page ${page} of ${totalPages} (${total} total)`
                      : `Page ${page} of ${totalPages} — ${total} worker${total !== 1 ? "s" : ""} total`}
                  </p>
                  {totalPages > 1 && (
                    <div className="flex items-center gap-1">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={page <= 1}
                        onClick={() => { setPage((p) => p - 1); setSelectedWorker(null); }}
                        className="h-7 w-7 p-0"
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <span className="min-w-[4rem] text-center text-xs text-muted-foreground">
                        {page} / {totalPages}
                      </span>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={page >= totalPages}
                        onClick={() => { setPage((p) => p + 1); setSelectedWorker(null); }}
                        className="h-7 w-7 p-0"
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </Card>

        <WorkerReviewPanel
          worker={activeWorker}
          onApprove={handleApprove}
          onReject={(worker) => {
            setRejectWorker(worker);
            setRejectReason("");
          }}
          onOpenDocument={handleOpenDocument}
          onToggleAvailability={(worker, isAvailable) =>
            availabilityMutation.mutate({ userId: worker.user_id, isAvailable })
          }
          isApproving={approveMutation.isPending}
          isTogglingAvailability={availabilityMutation.isPending}
          openingDocumentId={openingDocumentId}
        />
      </section>

      <Card className="border-border bg-white shadow-sm">
        <CardHeader className="flex-row items-start justify-between gap-4">
          <div>
            <CardTitle className="font-display text-xl font-semibold">Bulk import workers</CardTitle>
            <CardDescription className="mt-1">
              Use this only for admin-created worker profiles. Mobile-submitted profiles should go through the review queue above.
            </CardDescription>
          </div>
          <span className="inline-flex items-center rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
            {parsedWorkers.length} rows
          </span>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea
            className="min-h-32"
            value={csv}
            onChange={(event) => setCsv(event.target.value)}
            aria-label="Worker import CSV"
          />
          <Button
            size="sm"
            disabled={parsedWorkers.length === 0 || importMutation.isPending}
            onClick={() => importMutation.mutate()}
          >
            {importMutation.isPending ? "Importing…" : "Import workers"}
          </Button>
          {importMutation.data?.data ? (
            <p className="text-sm text-muted-foreground">
              Created {importMutation.data.data.created_count}, skipped {importMutation.data.data.skipped_count}.
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Dialog open={rejectWorker !== null} onOpenChange={(open) => !open && setRejectWorker(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject worker profile</DialogTitle>
            <DialogDescription>
              {rejectWorker?.full_name} will stay under onboarding and will not reach biometric setup or the worker
              dashboard. Add a clear reason so the profile can be corrected.
            </DialogDescription>
          </DialogHeader>
          <Textarea
            label="Rejection reason"
            value={rejectReason}
            onChange={(event) => setRejectReason(event.target.value)}
            placeholder="Example: Government ID photo is unreadable. Please upload a clearer image."
          />
          {rejectReason.length > 0 && rejectReason.trim().length < 10 ? (
            <p className="text-sm text-destructive">Reason must be at least 10 characters.</p>
          ) : null}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setRejectWorker(null)}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={rejectReason.trim().length < 10 || rejectMutation.isPending}
              onClick={handleReject}
            >
              {rejectMutation.isPending ? "Rejecting…" : "Reject profile"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function WorkerReviewPanel({
  worker,
  onApprove,
  onReject,
  onOpenDocument,
  onToggleAvailability,
  isApproving,
  isTogglingAvailability,
  openingDocumentId,
}: {
  worker: AdminWorker | null;
  onApprove: (worker: AdminWorker) => void;
  onReject: (worker: AdminWorker) => void;
  onOpenDocument: (documentId: number) => void;
  onToggleAvailability: (worker: AdminWorker, isAvailable: boolean) => void;
  isApproving: boolean;
  isTogglingAvailability: boolean;
  openingDocumentId: number | null;
}) {
  const queryClient = useQueryClient();

  if (!worker) {
    return (
      <Card className="border-border bg-white shadow-sm">
        <CardContent className="flex min-h-[420px] flex-col items-center justify-center gap-4 p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <ShieldCheck className="h-6 w-6 text-muted-foreground" />
          </div>
          <div>
            <h2 className="font-display text-lg font-semibold text-foreground">No worker selected</h2>
            <p className="mt-1 max-w-xs text-sm leading-6 text-muted-foreground">
              Select a submitted worker profile from the queue to review details and documents.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const canReview = worker.onboarding_step === "profile_submitted";
  const initials = worker.full_name
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0])
    .join("")
    .toUpperCase();

  return (
    <Card className="border-border bg-white shadow-sm">
      <CardHeader className="border-b border-border">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            {worker.photo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={worker.photo_url}
                alt={worker.full_name}
                className="h-14 w-14 rounded-full object-cover ring-2 ring-border"
              />
            ) : (
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-brand-100)] ring-2 ring-border">
                <span className="text-lg font-semibold text-[var(--color-brand-700)]">{initials}</span>
              </div>
            )}
            <div>
              <div className="mb-1">
                <StatusBadge value={worker.verification_status} />
              </div>
              <CardTitle className="font-display text-2xl font-semibold">{worker.full_name}</CardTitle>
              <p className="mt-0.5 font-mono text-sm text-muted-foreground">{worker.phone ?? "No phone on file"}</p>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            {canReview ? (
              <span className="inline-flex items-center rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-200">
                Needs review
              </span>
            ) : null}
            <Link
              href={`/workers/${worker.id}`}
              onMouseEnter={() =>
                queryClient.prefetchQuery({
                  queryKey: ["admin-worker-detail", worker.id],
                  queryFn: () => peopleService.getWorkerById(worker.id),
                })
              }
              className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              View full profile
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6 p-5">
        <section className="grid gap-4 sm:grid-cols-2">
          <ReviewField label="City" value={`${worker.city}, ${worker.state}`} />
          <ReviewField label="Category" value={worker.category} />
          <ReviewField label="Experience" value={String(worker.experience_years ?? "Not provided")} />
          <ReviewField
            label="Availability"
            value={`${formatList(worker.available_days)} / ${formatList(worker.available_shifts)}`}
          />
          <ReviewField label="Skills" value={formatList(worker.skills)} wide />
          <ReviewField label="Address" value={worker.address ?? "Not provided"} wide />
        </section>

        {worker.experience_notes ? (
          <section className="rounded-lg border border-border bg-muted/40 p-4">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Experience notes</p>
            <p className="mt-2 text-sm leading-6 text-foreground">{worker.experience_notes}</p>
          </section>
        ) : null}

        <section>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-medium text-foreground">Identity documents</h3>
            <span className="inline-flex items-center rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
              {worker.documents.length} files
            </span>
          </div>
          <div className="space-y-3">
            {worker.documents.length === 0 ? (
              <div className="rounded-lg border border-dashed border-border p-4 text-center text-sm text-muted-foreground">
                No identity documents are attached to this profile.
              </div>
            ) : (
              worker.documents.map((document) => (
                <button
                  key={document.id}
                  type="button"
                  onClick={() => onOpenDocument(document.id)}
                  className="flex w-full items-center justify-between gap-3 rounded-lg border border-border p-3 text-left transition-colors hover:bg-muted/30"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--color-brand-50)] text-[var(--color-brand-600)]">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium capitalize text-foreground">
                        {document.document_type.replaceAll("_", " ")}
                      </p>
                      <p className="mt-1 font-mono text-xs text-muted-foreground">
                        {formatDate(document.uploaded_at)}
                      </p>
                    </div>
                  </div>
                  {openingDocumentId === document.id ? (
                    <span className="text-xs text-muted-foreground">Opening…</span>
                  ) : (
                    <StatusBadge value={document.verification_status} />
                  )}
                </button>
              ))
            )}
          </div>
        </section>

        {canReview ? (
          <div className="flex flex-col-reverse gap-3 border-t border-border pt-5 sm:flex-row sm:justify-end">
            <Button type="button" variant="outline" onClick={() => onReject(worker)}>
              <XCircle className="h-4 w-4" />
              Reject
            </Button>
            <Button type="button" disabled={isApproving} onClick={() => onApprove(worker)}>
              <CheckCircle2 className="h-4 w-4" />
              {isApproving ? "Approving…" : "Approve worker"}
            </Button>
          </div>
        ) : worker.onboarding_step === "approved" ? (
          <div className="space-y-3 border-t border-border pt-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">Availability</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {worker.is_available
                    ? "Available for assignment"
                    : "On leave — will not appear in assignment list"}
                </p>
              </div>
              <span
                className={`rounded-full px-3 py-1 text-xs font-medium ${
                  worker.is_available ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-700"
                }`}
              >
                {worker.is_available ? "Available" : "On leave"}
              </span>
            </div>
            <div className="flex gap-2">
              <Button
                type="button"
                size="sm"
                variant={worker.is_available ? "outline" : "default"}
                disabled={worker.is_available || isTogglingAvailability}
                onClick={() => onToggleAvailability(worker, true)}
              >
                <CheckCircle2 className="h-4 w-4" />
                Mark available
              </Button>
              <Button
                type="button"
                size="sm"
                variant={!worker.is_available ? "outline" : "destructive"}
                disabled={!worker.is_available || isTogglingAvailability}
                onClick={() => onToggleAvailability(worker, false)}
              >
                <UserX className="h-4 w-4" />
                Mark on leave
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex items-start gap-3 rounded-lg border border-border bg-muted/40 p-4">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            <p className="text-sm leading-6 text-muted-foreground">
              This worker is not in the submitted review state, so approval actions are disabled.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ReviewMetric({
  title,
  value,
  detail,
  icon,
  tone,
}: {
  title: string;
  value: number;
  detail: string;
  icon: ReactNode;
  tone: "warning" | "success" | "danger";
}) {
  const toneClass = {
    warning: "bg-amber-50 text-amber-700",
    success: "bg-green-50 text-green-700",
    danger: "bg-red-50 text-red-700",
  }[tone];

  return (
    <Card className="border-border bg-white shadow-sm">
      <CardContent className="p-5">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${toneClass}`}>{icon}</div>
        <p className="mt-4 font-display text-4xl font-semibold leading-none tracking-tight text-foreground">{value}</p>
        <p className="mt-2 text-xs font-semibold uppercase tracking-widest text-muted-foreground">{title}</p>
        <p className="mt-1 font-mono text-xs text-muted-foreground">{detail}</p>
      </CardContent>
    </Card>
  );
}

function ReviewField({ label, value, wide = false }: { label: string; value: string; wide?: boolean }) {
  return (
    <div className={wide ? "sm:col-span-2" : undefined}>
      <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm leading-6 text-foreground">{value}</p>
    </div>
  );
}

function formatList(value: string | string[] | null) {
  if (!value) return "Not provided";
  const items = Array.isArray(value)
    ? value
    : value.split(",").map((item) => item.trim());
  const filtered = items.filter(Boolean);
  return filtered.length ? filtered.join(", ") : "Not provided";
}

function formatDate(value: string | null) {
  if (!value) return "Not available";
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}
