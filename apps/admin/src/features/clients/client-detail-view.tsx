"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Building2, MapPin, Phone, Receipt, Shield, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import LoadingState from "@/components/shared/loading-state";
import EmptyState from "@/components/shared/empty-state";
import ErrorState from "@/components/shared/error-state";
import StatusBadge from "@/components/shared/status-badge";
import { peopleService } from "@/services/people.service";
import { blacklistService } from "@/services/blacklist.service";
import { getErrorMessage } from "@/lib/get-error-message";

export default function ClientDetailView({ clientId }: { clientId: number }) {
  const router = useRouter();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-client-detail", clientId],
    queryFn: () => peopleService.getClientById(clientId),
    enabled: !!clientId,
  });

  const client = data?.data;

  if (isLoading) {
    return <LoadingState title="Loading client" description="Fetching client profile…" />;
  }

  if (isError || !client) {
    return (
      <ErrorState
        title="Could not load client"
        description="The client may not exist or the connection failed."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <button
          type="button"
          onClick={() => router.push("/clients")}
          className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Clients
        </button>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="font-display text-2xl font-semibold tracking-tight text-foreground">
              {client.company_name}
            </h1>
            <p className="mt-0.5 text-sm text-muted-foreground">{client.contact_name}</p>
          </div>
          {!client.is_active && (
            <span className="mt-1 rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              Deactivated
            </span>
          )}
        </div>
      </div>

      {/* Info grid */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Profile card — 2/3 */}
        <Card className="p-6 lg:col-span-2">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            Profile
          </h2>
          <dl className="grid gap-4 sm:grid-cols-2">
            <InfoRow icon={<Building2 className="h-4 w-4" />} label="Company">
              {client.company_name}
            </InfoRow>
            <InfoRow icon={<Phone className="h-4 w-4" />} label="Phone">
              {client.phone ?? "—"}
            </InfoRow>
            <InfoRow icon={<MapPin className="h-4 w-4" />} label="Location">
              {client.city}, {client.state}
            </InfoRow>
            <InfoRow icon={<Receipt className="h-4 w-4" />} label="GST number">
              <span className="font-mono">{client.gst_number ?? "—"}</span>
            </InfoRow>
          </dl>
        </Card>

        {/* Stats sidebar — 1/3 */}
        <Card className="p-6">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            Job history
          </h2>
          <div className="space-y-3">
            <StatRow label="Total requests" value={client.requirements.length} />
            <StatRow
              label="Active"
              value={
                client.requirements.filter((r) =>
                  ["submitted", "under_review", "approved", "workers_assigned", "in_progress"].includes(r.status),
                ).length
              }
            />
            <StatRow
              label="Completed"
              value={client.requirements.filter((r) => r.status === "completed").length}
            />
            <StatRow
              label="Cancelled / Rejected"
              value={
                client.requirements.filter((r) =>
                  ["cancelled", "rejected"].includes(r.status),
                ).length
              }
            />
          </div>
        </Card>
      </div>

      {/* Requirements history */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          Requests
        </h2>

        {client.requirements.length === 0 ? (
          <EmptyState
            title="No requests yet"
            description="This client has not submitted any worker requests."
          />
        ) : (
          <Card className="overflow-hidden">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-muted/40">
                <tr>
                  {["#", "Category", "Location", "Workers", "Start date", "Duration", "Status"].map(
                    (h) => (
                      <th
                        key={h}
                        className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-widest text-muted-foreground"
                      >
                        {h}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {client.requirements.map((req) => (
                  <tr
                    key={req.id}
                    className="cursor-pointer transition-colors hover:bg-muted/30"
                    onClick={() => router.push(`/requirements/${req.id}`)}
                  >
                    <td className="px-4 py-3 font-mono text-sm text-muted-foreground">
                      #{req.id}
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-foreground">
                      {req.category}
                      {req.subcategory ? (
                        <span className="ml-1 text-muted-foreground">/ {req.subcategory}</span>
                      ) : null}
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {req.city}, {req.state}
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {req.number_of_workers}
                    </td>
                    <td className="px-4 py-3 font-mono text-sm text-muted-foreground">
                      {req.start_date}
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {req.duration_days}d
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge value={req.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </div>

      {/* Worker blacklist */}
      <BlacklistSection clientProfileId={client.id} />
    </div>
  );
}

function BlacklistSection({ clientProfileId }: { clientProfileId: number }) {
  const queryClient = useQueryClient();
  const queryKey = ["client-blacklist", clientProfileId];

  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: () => blacklistService.getByClient(clientProfileId),
  });

  const [workerIdInput, setWorkerIdInput] = useState("");
  const [reasonInput, setReasonInput] = useState("");
  const [formError, setFormError] = useState("");
  const [adding, setAdding] = useState(false);
  const [removingId, setRemovingId] = useState<number | null>(null);

  const entries = data?.data?.items ?? [];

  const handleAdd = async () => {
    const workerId = parseInt(workerIdInput.trim(), 10);
    if (!workerId || workerId < 1) {
      setFormError("Enter a valid worker profile ID.");
      return;
    }
    if (!reasonInput.trim()) {
      setFormError("Reason is required.");
      return;
    }
    setFormError("");
    setAdding(true);
    try {
      await blacklistService.blacklistWorker({
        client_profile_id: clientProfileId,
        worker_profile_id: workerId,
        reason: reasonInput.trim(),
      });
      setWorkerIdInput("");
      setReasonInput("");
      queryClient.invalidateQueries({ queryKey });
    } catch (err) {
      setFormError(getErrorMessage(err));
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (entryId: number) => {
    setRemovingId(entryId);
    try {
      await blacklistService.removeFromBlacklist(entryId);
      queryClient.invalidateQueries({ queryKey });
    } catch {
      // silent — list will stay unchanged
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
        Worker blacklist
      </h2>
      <Card className="p-6">
        <div className="mb-5 flex items-center gap-3">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-red-50 text-red-600">
            <Shield className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">Blocked workers</p>
            <p className="text-xs text-muted-foreground">
              Blacklisted workers are excluded from match results for this client's requirements.
            </p>
          </div>
        </div>

        {/* Add form */}
        <div className="mb-5 rounded-xl border border-border bg-muted/30 p-4">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Add to blacklist
          </p>
          <div className="flex flex-wrap gap-3">
            <input
              type="number"
              min={1}
              placeholder="Worker profile ID"
              value={workerIdInput}
              onChange={(e) => setWorkerIdInput(e.target.value)}
              className="h-9 w-40 rounded-lg border border-input bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <input
              type="text"
              placeholder="Reason (required)"
              value={reasonInput}
              onChange={(e) => setReasonInput(e.target.value)}
              className="h-9 min-w-0 flex-1 rounded-lg border border-input bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <Button
              type="button"
              variant="destructive"
              size="sm"
              disabled={adding}
              onClick={handleAdd}
            >
              {adding ? "Adding…" : "Blacklist"}
            </Button>
          </div>
          {formError && (
            <p className="mt-2 text-xs text-red-600">{formError}</p>
          )}
        </div>

        {/* List */}
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading blacklist…</p>
        ) : entries.length === 0 ? (
          <p className="text-sm text-muted-foreground">No workers blacklisted for this client.</p>
        ) : (
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="pb-2 pr-6 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Worker ID
                </th>
                <th className="pb-2 pr-6 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Reason
                </th>
                <th className="pb-2 pr-6 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Blacklisted on
                </th>
                <th className="pb-2 text-right text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id} className="border-b border-muted last:border-b-0">
                  <td className="py-3 pr-6 font-mono text-foreground">
                    #{entry.worker_profile_id}
                  </td>
                  <td className="py-3 pr-6 text-muted-foreground">{entry.reason}</td>
                  <td className="py-3 pr-6 font-mono text-xs text-muted-foreground">
                    {entry.created_at.slice(0, 10)}
                  </td>
                  <td className="py-3 text-right">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-red-600 hover:bg-red-50 hover:text-red-700"
                      disabled={removingId === entry.id}
                      onClick={() => handleRemove(entry.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      {removingId === entry.id ? "Removing…" : "Remove"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}

function InfoRow({
  icon,
  label,
  children,
}: {
  icon: React.ReactNode;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex gap-3">
      <span className="mt-0.5 shrink-0 text-muted-foreground">{icon}</span>
      <div>
        <dt className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
          {label}
        </dt>
        <dd className="mt-0.5 text-sm text-foreground">{children}</dd>
      </div>
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="font-mono text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}
