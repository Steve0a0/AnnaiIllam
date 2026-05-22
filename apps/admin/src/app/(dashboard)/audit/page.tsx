"use client";

import { useQuery } from "@tanstack/react-query";
import PageHeader from "@/components/shared/page-header";
import { Card } from "@/components/ui/card";
import { auditService } from "@/services/audit.service";

export default function AuditPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => auditService.getAuditLogs(150),
    refetchInterval: 30000,
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Audit log" description="Recent admin and system activity." />

      <Card className="overflow-hidden">
        <table className="min-w-full divide-y divide-border">
          <thead className="bg-muted/40">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">Time</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">Action</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading ? (
              <tr><td className="px-4 py-6 text-sm text-muted-foreground" colSpan={3}>Loading audit logs...</td></tr>
            ) : isError ? (
              <tr><td className="px-4 py-6 text-sm text-destructive" colSpan={3}>Failed to load audit logs.</td></tr>
            ) : (data?.data ?? []).length === 0 ? (
              <tr><td className="px-4 py-6 text-sm text-muted-foreground" colSpan={3}>No audit logs found.</td></tr>
            ) : (
              data?.data.map((item) => (
                <tr key={item.id} className="transition-colors hover:bg-muted/30">
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm font-semibold text-foreground">{item.action}</td>
                  <td className="px-4 py-3">
                    <pre className="max-w-2xl overflow-auto rounded-lg bg-muted/50 p-2 text-xs text-muted-foreground">
                      {JSON.stringify(item.details, null, 2)}
                    </pre>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
