"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Search, Plus, Pencil, UserX } from "lucide-react";
import PageHeader from "@/components/shared/page-header";
import LoadingState from "@/components/shared/loading-state";
import EmptyState from "@/components/shared/empty-state";
import ErrorState from "@/components/shared/error-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { peopleService } from "@/services/people.service";
import {
  CreateClientDialog,
  EditClientDialog,
  DeactivateClientDialog,
} from "@/features/clients";
import type { AdminClient } from "@/types/people";

export default function ClientsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<AdminClient | null>(null);
  const [deactivatingClient, setDeactivatingClient] = useState<AdminClient | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-clients"],
    queryFn: peopleService.getClients,
  });

  const clients = useMemo(() => {
    const all = data?.data?.items ?? [];
    if (!search.trim()) return all;
    const q = search.toLowerCase();
    return all.filter(
      (c) =>
        (c.company_name ?? "").toLowerCase().includes(q) ||
        c.contact_name.toLowerCase().includes(q) ||
        c.city.toLowerCase().includes(q) ||
        c.state.toLowerCase().includes(q),
    );
  }, [data, search]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["admin-clients"] });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Clients"
        description="Manage client companies and contact profiles."
        action={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus />
            Add Client
          </Button>
        }
      />

      <div className="relative w-72">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          className="pl-9"
          placeholder="Search by name, contact, or city…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading ? (
        <LoadingState title="Loading clients" description="Fetching client profiles…" />
      ) : isError ? (
        <ErrorState
          title="Could not load clients"
          description="Check your connection and try again."
          onRetry={() => refetch()}
        />
      ) : clients.length === 0 ? (
        <EmptyState
          title={search ? "No clients match your search" : "No clients yet"}
          description={
            search
              ? "Try a different company name, contact, or city."
              : "Client profiles will appear here once clients sign up or you add one."
          }
          actionLabel={!search ? "Add Client" : undefined}
          onAction={!search ? () => setCreateOpen(true) : undefined}
        />
      ) : (
        <Card className="overflow-hidden">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-muted/40">
              <tr>
                {["Client", "Contact", "Location", "GST"].map((heading) => (
                  <th
                    key={heading}
                    className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-widest text-muted-foreground"
                  >
                    {heading}
                  </th>
                ))}
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {clients.map((client) => (
                <tr
                  key={client.id}
                  className={`group cursor-pointer transition-colors hover:bg-muted/30 ${!client.is_active ? "opacity-50" : ""}`}
                  onClick={() => router.push(`/clients/${client.id}`)}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted text-xs font-semibold text-muted-foreground">
                        {(client.client_type === "individual" ? client.contact_name : client.company_name)?.slice(0, 2).toUpperCase() ?? '??'}
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-sm font-semibold text-foreground">
                            {client.client_type === "individual" ? client.contact_name : client.company_name}
                          </span>
                          {client.client_type === "individual" ? (
                            <Badge variant="secondary" className="text-xs py-0">Individual</Badge>
                          ) : null}
                          {!client.is_active ? (
                            <Badge variant="outline" className="text-xs py-0 text-muted-foreground">Deactivated</Badge>
                          ) : null}
                        </div>
                        {client.client_type === "company" && client.contact_name ? (
                          <span className="text-xs text-muted-foreground">{client.contact_name}</span>
                        ) : null}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {client.client_type === "individual" ? client.phone ?? "—" : client.contact_name}
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {client.city}, {client.state}
                  </td>
                  <td className="px-4 py-3 font-mono text-sm text-muted-foreground">
                    {client.gst_number ?? "—"}
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Edit client"
                        onClick={() => setEditingClient(client)}
                      >
                        <Pencil />
                      </Button>
                      {client.is_active ? (
                        <Button
                          variant="ghost"
                          size="icon"
                          title="Deactivate client"
                          onClick={() => setDeactivatingClient(client)}
                        >
                          <UserX />
                        </Button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="border-t border-border px-4 py-3">
            <p className="text-xs text-muted-foreground">
              {clients.length === (data?.data?.total ?? 0)
                ? `${clients.length} client${clients.length !== 1 ? "s" : ""}`
                : `Showing ${clients.length} of ${data?.data?.total ?? 0} clients`}
            </p>
          </div>
        </Card>
      )}

      <CreateClientDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSuccess={invalidate}
      />
      <EditClientDialog
        client={editingClient}
        onClose={() => setEditingClient(null)}
        onSuccess={invalidate}
      />
      <DeactivateClientDialog
        client={deactivatingClient}
        onClose={() => setDeactivatingClient(null)}
        onSuccess={invalidate}
      />
    </div>
  );
}
