"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import StatusBadge from "@/components/shared/status-badge";
import LoadingState from "@/components/shared/loading-state";
import ErrorState from "@/components/shared/error-state";
import { disputesService } from "@/services/disputes.service";
import { getErrorMessage } from "@/lib/get-error-message";

export default function DisputeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const disputeId = Number(params.id);
  const queryKey = ["admin-dispute-detail", disputeId];

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey,
    queryFn: () => disputesService.getById(disputeId),
  });

  const [actionError, setActionError] = useState<string | null>(null);
  const [reviewing, setReviewing] = useState(false);
  const [closing, setClosing] = useState(false);
  const [showResolveForm, setShowResolveForm] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [creditAmount, setCreditAmount] = useState("");
  const [resolveError, setResolveError] = useState<string | null>(null);
  const [resolving, setResolving] = useState(false);

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey });
    void queryClient.invalidateQueries({ queryKey: ["admin-disputes"] });
  };

  if (isLoading) return <LoadingState title="Loading dispute" description="Fetching dispute details…" />;
  if (isError || !data) return <ErrorState title="Could not load dispute" description="It may not exist." onRetry={() => refetch()} />;

  const dispute = data;
  const canReview = dispute.status === "open";
  const canResolveOrClose = dispute.status === "open" || dispute.status === "under_review";

  const handleReview = async () => {
    setActionError(null);
    setReviewing(true);
    try {
      await disputesService.review(disputeId);
      invalidate();
    } catch (err) {
      setActionError(getErrorMessage(err));
    } finally {
      setReviewing(false);
    }
  };

  const handleClose = async () => {
    setActionError(null);
    setClosing(true);
    try {
      await disputesService.close(disputeId);
      invalidate();
    } catch (err) {
      setActionError(getErrorMessage(err));
    } finally {
      setClosing(false);
    }
  };

  const handleResolve = async () => {
    if (!resolutionNotes.trim()) {
      setResolveError("Resolution notes are required.");
      return;
    }
    const credit = creditAmount ? parseInt(creditAmount, 10) : undefined;
    setResolveError(null);
    setResolving(true);
    try {
      await disputesService.resolve(disputeId, resolutionNotes.trim(), credit);
      setShowResolveForm(false);
      invalidate();
    } catch (err) {
      setResolveError(getErrorMessage(err));
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <button
          type="button"
          onClick={() => router.push("/disputes")}
          className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          All disputes
        </button>
        <div className="flex items-center gap-3">
          <h1 className="font-display text-2xl font-semibold text-foreground">
            Dispute #{dispute.id}
          </h1>
          <StatusBadge value={dispute.status} />
        </div>
      </div>

      {actionError && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {actionError}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main details */}
        <Card className="p-6 lg:col-span-2 space-y-5">
          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">Type</p>
            <p className="mt-1 text-sm font-medium capitalize text-foreground">
              {dispute.dispute_type.replace(/_/g, " ")}
            </p>
          </div>
          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">Description</p>
            <p className="mt-1 text-sm text-foreground leading-6 whitespace-pre-wrap">{dispute.description}</p>
          </div>
          {dispute.resolution_notes && (
            <div className="rounded-lg bg-green-50 border border-green-200 p-4">
              <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-green-700">Resolution</p>
              <p className="mt-1 text-sm text-green-800 leading-6">{dispute.resolution_notes}</p>
              {dispute.credit_amount && dispute.credit_amount > 0 && (
                <p className="mt-2 text-sm font-semibold text-green-800">
                  Credit issued: Rs. {(dispute.credit_amount / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </p>
              )}
            </div>
          )}
        </Card>

        {/* Metadata */}
        <Card className="p-6 space-y-4">
          <MetaRow label="Requirement" value={`REQ-${dispute.requirement_id}`} />
          <MetaRow label="Raised by user" value={`#${dispute.raised_by_user_id}`} />
          <MetaRow label="Raised on" value={dispute.created_at.slice(0, 10)} mono />
          {dispute.resolved_at && (
            <MetaRow label="Resolved on" value={dispute.resolved_at.slice(0, 10)} mono />
          )}
        </Card>
      </div>

      {/* Actions */}
      {canResolveOrClose && (
        <Card className="p-6 space-y-4">
          <p className="text-sm font-semibold text-foreground">Actions</p>
          <div className="flex flex-wrap gap-3">
            {canReview && (
              <Button variant="secondary" onClick={handleReview} disabled={reviewing}>
                {reviewing ? "Moving to review…" : "Mark under review"}
              </Button>
            )}
            <Button
              variant="accent"
              onClick={() => { setShowResolveForm((v) => !v); setResolveError(null); }}
            >
              {showResolveForm ? "Cancel" : "Resolve dispute"}
            </Button>
            <Button
              variant="outline"
              className="border-red-300 text-red-700 hover:bg-red-50"
              onClick={handleClose}
              disabled={closing}
            >
              {closing ? "Closing…" : "Close without resolution"}
            </Button>
          </div>

          {showResolveForm && (
            <div className="space-y-3 rounded-xl border border-border bg-muted/30 p-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-foreground">
                  Resolution notes <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={4}
                  className="w-full rounded-lg border border-input bg-white px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Describe what action was taken and why…"
                  value={resolutionNotes}
                  onChange={(e) => { setResolutionNotes(e.target.value); setResolveError(null); }}
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-foreground">
                  Credit amount (Rs.) — optional
                </label>
                <input
                  type="number"
                  min={0}
                  step={0.01}
                  className="h-10 w-48 rounded-lg border border-input bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="e.g. 500"
                  value={creditAmount}
                  onChange={(e) => setCreditAmount(e.target.value)}
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  Entered in rupees — stored as paise internally.
                </p>
              </div>
              {resolveError && <p className="text-sm text-red-600">{resolveError}</p>}
              <div className="flex gap-2">
                <Button variant="accent" onClick={handleResolve} disabled={resolving}>
                  {resolving ? "Resolving…" : "Confirm resolution"}
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function MetaRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-muted-foreground">{label}</p>
      <p className={["mt-0.5 text-sm text-foreground", mono ? "font-mono" : ""].join(" ")}>{value}</p>
    </div>
  );
}
