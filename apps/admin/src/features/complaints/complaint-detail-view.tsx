"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useComplaintDetail } from "@/features/complaints/use-complaint-detail";
import ComplaintsLoading from "@/features/complaints/complaints-loading";
import ComplaintsError from "@/features/complaints/complaints-error";
import StatusBadge from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import UpdateComplaintStatusForm from "@/features/complaints/update-complaint-status-form";
import CreateReplacementForm from "@/features/complaints/create-replacement-form";
import ReplacementsList from "@/features/complaints/replacements-list";

export default function ComplaintDetailView({
  complaintId,
}: {
  complaintId: number;
}) {
  const isInvalidComplaintId = !Number.isFinite(complaintId) || complaintId <= 0;
  const { data, isLoading, isError, error, refetch } =
    useComplaintDetail(complaintId);

  if (isInvalidComplaintId) {
    return <ComplaintsError message="Invalid complaint ID." />;
  }

  if (isLoading) {
    return <ComplaintsLoading />;
  }

  if (isError || !data?.data) {
    return <ComplaintsError message={error?.message} />;
  }

  const complaint = data.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Button asChild variant="ghost" size="sm" className="-ml-3 mb-2">
            <Link href="/complaints">
              <ArrowLeft />
              Back to complaints
            </Link>
          </Button>
          <h1 className="font-display text-2xl font-semibold text-foreground">
            Complaint #{complaint.id}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Review complaint details, add resolution notes, and resolve or reject the complaint.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge value={complaint.status} />
          <StatusBadge value={complaint.severity} />
        </div>
      </div>

      <Card>
        <CardHeader className="border-b border-border">
          <CardTitle>Complaint Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">
          <div className="grid gap-4 md:grid-cols-3">
            <Detail label="Requirement ID" value={complaint.requirement_id} />
            <Detail
              label="Assignment ID"
              value={complaint.assignment_id ?? "-"}
            />
            <Detail label="Raised By User ID" value={complaint.raised_by_user_id} />
            <Detail
              label="Complaint Type"
              value={complaint.complaint_type.replaceAll("_", " ")}
            />
            <Detail label="Created" value={formatDateTime(complaint.created_at)} />
            <Detail
              label="Resolved By User ID"
              value={complaint.resolved_by_user_id ?? "-"}
            />
          </div>

          <div>
            <p className="text-sm font-medium text-foreground">Description</p>
            <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
              {complaint.description}
            </p>
          </div>

          <div>
            <p className="text-sm font-medium text-foreground">
              Current Resolution Notes
            </p>
            <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
              {complaint.resolution_notes ?? "No resolution notes yet."}
            </p>
          </div>
        </CardContent>
      </Card>

      <UpdateComplaintStatusForm
        complaintId={complaint.id}
        currentStatus={complaint.status}
        currentResolutionNotes={complaint.resolution_notes}
        onSuccess={() => refetch()}
      />

      {complaint.assignment_id ? (
        <CreateReplacementForm
          complaintId={complaint.id}
          oldAssignmentId={complaint.assignment_id}
          onSuccess={() => refetch()}
        />
      ) : null}

      <div className="space-y-3">
        <div>
          <h2 className="font-display text-xl font-semibold text-foreground">
            Replacement History
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            View all replacements created for this complaint.
          </p>
        </div>

        <ReplacementsList replacements={complaint.replacements} />
      </div>
    </div>
  );
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
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
      <p className="text-sm font-medium text-foreground">{label}</p>
      <p className="mt-1 text-sm text-muted-foreground">{value}</p>
    </div>
  );
}
