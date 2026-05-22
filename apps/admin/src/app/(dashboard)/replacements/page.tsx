"use client";

import { useState } from "react";
import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";
import { useReplacements } from "@/features/complaints/use-replacements";
import { complaintsService } from "@/services/complaints.service";
import { getErrorMessage } from "@/lib/get-error-message";
import { Card } from "@/components/ui/card";
import Select from "@/components/ui/select";
import { Button } from "@/components/ui/button";

const STATUS_OPTIONS = [
  { label: "Created", value: "created" },
  { label: "In Progress", value: "in_progress" },
  { label: "Completed", value: "completed" },
  { label: "Cancelled", value: "cancelled" },
];

const ALL_VALUE = "__all__";

function UpdateStatusCell({
  replacementId,
  currentStatus,
  onUpdated,
}: {
  replacementId: number;
  currentStatus: string;
  onUpdated: () => void;
}) {
  const [status, setStatus] = useState(currentStatus);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleUpdate() {
    if (status === currentStatus) return;
    setLoading(true);
    setError(null);
    try {
      await complaintsService.updateReplacementStatus(replacementId, { status });
      onUpdated();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <Select
          options={STATUS_OPTIONS}
          value={status}
          onChange={setStatus}
          disabled={loading}
          className="w-36"
        />
        <Button
          size="sm"
          variant="outline"
          disabled={loading || status === currentStatus}
          onClick={handleUpdate}
          className="h-9 shrink-0 text-xs"
        >
          {loading ? "Saving..." : "Save"}
        </Button>
      </div>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

export default function ReplacementsPage() {
  const [statusFilter, setStatusFilter] = useState<string>(ALL_VALUE);
  const queryClient = useQueryClient();
  const { data, isLoading, isError, error } = useReplacements(
    statusFilter === ALL_VALUE ? undefined : statusFilter,
  );

  const items = data?.data?.items ?? [];

  function refresh() {
    queryClient.invalidateQueries({ queryKey: ["replacements"] });
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-foreground">
          Replacement Requests
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Worker replacement requests raised by clients. Update status as each
          request is processed.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <Select
          options={[{ label: "All statuses", value: ALL_VALUE }, ...STATUS_OPTIONS]}
          value={statusFilter}
          onChange={setStatusFilter}
          className="w-44"
        />
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-sm text-muted-foreground">
          Loading replacements...
        </div>
      ) : null}

      {isError ? (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {error?.message ?? "Failed to load replacements."}
        </div>
      ) : null}

      {!isLoading && !isError && !items.length ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500">
          No replacement requests found.
        </div>
      ) : null}

      {!isLoading && !isError && items.length ? (
        <Card className="overflow-hidden">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-muted/40">
              <tr>
                {[
                  "ID",
                  "Complaint",
                  "Old Assignment",
                  "New Assignment",
                  "Old Worker",
                  "New Worker",
                  "Reason",
                  "Created",
                  "Status",
                ].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {items.map((item) => (
                <tr key={item.id} className="transition-colors hover:bg-muted/30">
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {item.id}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <Link
                      href={`/complaints/${item.complaint_id}`}
                      className="text-accent underline underline-offset-4 transition-colors hover:text-accent/80"
                    >
                      #{item.complaint_id}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {item.old_assignment_id}
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {item.new_assignment_id ?? "-"}
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {item.old_worker_profile_id}
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {item.new_worker_profile_id ?? "-"}
                  </td>
                  <td className="max-w-[180px] truncate px-4 py-3 text-sm text-muted-foreground">
                    {item.reason ?? "-"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                    {item.created_at.slice(0, 10)}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <UpdateStatusCell
                      replacementId={item.id}
                      currentStatus={item.status}
                      onUpdated={refresh}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
    </div>
  );
}