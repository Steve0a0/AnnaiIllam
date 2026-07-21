"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, ShieldCheck, Trash2 } from "lucide-react";

import EmptyState from "@/components/shared/empty-state";
import ErrorState from "@/components/shared/error-state";
import LoadingState from "@/components/shared/loading-state";
import PageHeader from "@/components/shared/page-header";
import StatusBadge from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import Select from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage } from "@/lib/get-error-message";
import { privacyService } from "@/services/privacy.service";
import { useAuthStore } from "@/store/auth-store";
import type {
  PrivacyRequest,
  PrivacyRequestStatus,
  PrivacyRequestType,
} from "@/types/privacy";

type Resolution = "completed" | "rejected";

export default function PrivacyRequestsPage() {
  const currentUser = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("open");
  const [typeFilter, setTypeFilter] = useState("all");
  const [selected, setSelected] = useState<PrivacyRequest | null>(null);
  const [resolution, setResolution] = useState<Resolution>("completed");
  const [notes, setNotes] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["privacy-requests", statusFilter, typeFilter],
    queryFn: () =>
      privacyService.list({
        status:
          statusFilter === "all" || statusFilter === "open"
            ? undefined
            : (statusFilter as PrivacyRequestStatus),
        requestType:
          typeFilter === "all" ? undefined : (typeFilter as PrivacyRequestType),
      }),
    enabled: currentUser?.permission_group === "super_admin",
  });

  const mutation = useMutation({
    mutationFn: ({ request, outcome }: { request: PrivacyRequest; outcome: Resolution | "in_review" }) =>
      privacyService.resolve(request.id, {
        status: outcome,
        resolution_notes: outcome === "in_review" ? undefined : notes.trim(),
      }),
    onSuccess: async () => {
      setSelected(null);
      setNotes("");
      setActionError(null);
      await queryClient.invalidateQueries({ queryKey: ["privacy-requests"] });
    },
    onError: (error) => setActionError(getErrorMessage(error)),
  });

  if (currentUser && currentUser.permission_group !== "super_admin") {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <ShieldCheck className="mb-4 h-10 w-10 text-muted-foreground" />
        <h2 className="text-base font-semibold text-foreground">Access restricted</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Only super admins can resolve privacy requests.
        </p>
      </div>
    );
  }

  const allItems = query.data?.data?.items ?? [];
  const items =
    statusFilter === "open"
      ? allItems.filter((item) => item.status === "pending" || item.status === "in_review")
      : allItems;

  const openResolution = (request: PrivacyRequest, outcome: Resolution) => {
    setSelected(request);
    setResolution(outcome);
    setNotes("");
    setActionError(null);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Privacy Requests"
        description="Review data exports and account deletion requests. Completion is recorded in the audit log."
      />

      <div className="grid gap-3 sm:grid-cols-2 sm:max-w-xl">
        <Select
          label="Status"
          value={statusFilter}
          onChange={setStatusFilter}
          options={[
            { label: "Open requests", value: "open" },
            { label: "All statuses", value: "all" },
            { label: "Pending", value: "pending" },
            { label: "In review", value: "in_review" },
            { label: "Completed", value: "completed" },
            { label: "Rejected", value: "rejected" },
          ]}
        />
        <Select
          label="Request type"
          value={typeFilter}
          onChange={setTypeFilter}
          options={[
            { label: "All request types", value: "all" },
            { label: "Account deletion", value: "deletion" },
            { label: "Data export", value: "export" },
          ]}
        />
      </div>

      {query.isLoading ? (
        <LoadingState title="Loading privacy requests" />
      ) : query.isError ? (
        <ErrorState title="Failed to load privacy requests" onRetry={() => query.refetch()} />
      ) : items.length === 0 ? (
        <EmptyState
          title="No matching privacy requests"
          description="New account deletion and data export requests will appear here."
        />
      ) : (
        <Card className="overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Requested</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item) => {
                const isOpen = item.status === "pending" || item.status === "in_review";
                return (
                  <TableRow key={item.id}>
                    <TableCell>
                      <div className="min-w-44">
                        <p className="font-medium text-foreground">
                          {item.user_name ?? `User #${item.user_id}`}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {item.user_contact ?? "Contact removed"} · {item.user_role}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 capitalize">
                        {item.request_type === "deletion" ? <Trash2 /> : <Download />}
                        {item.request_type === "deletion" ? "Account deletion" : "Data export"}
                      </div>
                    </TableCell>
                    <TableCell><StatusBadge value={item.status} /></TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Intl.DateTimeFormat("en-IN", {
                        dateStyle: "medium",
                        timeStyle: "short",
                      }).format(new Date(item.requested_at))}
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-2">
                        {item.status === "pending" ? (
                          <Button
                            size="sm"
                            variant="secondary"
                            disabled={mutation.isPending}
                            onClick={() => mutation.mutate({ request: item, outcome: "in_review" })}
                          >
                            Start review
                          </Button>
                        ) : null}
                        {isOpen ? (
                          <>
                            <Button size="sm" variant="outline" onClick={() => openResolution(item, "rejected")}>
                              Reject
                            </Button>
                            <Button size="sm" onClick={() => openResolution(item, "completed")}>
                              Complete
                            </Button>
                          </>
                        ) : null}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Card>
      )}

      <Dialog open={selected !== null} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {resolution === "completed"
                ? selected?.request_type === "deletion"
                  ? "Complete account deletion"
                  : "Mark data export ready"
                : "Reject privacy request"}
            </DialogTitle>
            <DialogDescription>
              {resolution === "completed" && selected?.request_type === "deletion"
                ? "This permanently removes login credentials, profile identifiers, sessions, and identity documents. Statutory invoice and payroll records remain under anonymized IDs."
                : "Add a clear note explaining the outcome. The user can see this note."}
            </DialogDescription>
          </DialogHeader>
          <Textarea
            label="Resolution notes"
            value={notes}
            maxLength={2000}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Record what was reviewed and the reason for this outcome."
          />
          {actionError ? <p className="text-sm text-destructive">{actionError}</p> : null}
          <DialogFooter>
            <Button variant="secondary" onClick={() => setSelected(null)}>Cancel</Button>
            <Button
              variant={resolution === "completed" && selected?.request_type === "deletion" ? "destructive" : "default"}
              disabled={!notes.trim() || mutation.isPending || !selected}
              onClick={() => selected && mutation.mutate({ request: selected, outcome: resolution })}
            >
              {mutation.isPending ? "Saving..." : resolution === "completed" ? "Confirm completion" : "Reject request"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
