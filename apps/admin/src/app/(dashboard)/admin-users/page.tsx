"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, Plus, ShieldCheck, Trash2 } from "lucide-react";
import PageHeader from "@/components/shared/page-header";
import LoadingState from "@/components/shared/loading-state";
import EmptyState from "@/components/shared/empty-state";
import ErrorState from "@/components/shared/error-state";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { adminUsersService, PERMISSION_GROUP_LABELS, type AdminUserRecord } from "@/services/admin-users.service";
import { scopingService } from "@/services/scoping.service";
import { peopleService } from "@/services/people.service";
import { getErrorMessage } from "@/lib/get-error-message";
import { CreateAdminUserDialog } from "@/features/admin-users";
import { useAuthStore } from "@/store/auth-store";

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const currentUser = useAuthStore((s) => s.user);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-users"],
    queryFn: adminUsersService.list,
    enabled: currentUser?.permission_group === "super_admin",
  });

  if (currentUser && currentUser.permission_group !== "super_admin") {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <ShieldCheck className="mb-4 h-10 w-10 text-muted-foreground" />
        <h2 className="text-base font-semibold text-foreground">Access restricted</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Only super admins can manage admin users.
        </p>
      </div>
    );
  }

  const users: AdminUserRecord[] = data?.data ?? [];
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["admin-users"] });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Admin Users"
        description="Create and manage admin dashboard accounts."
        action={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus />
            Create User
          </Button>
        }
      />

      {isLoading ? (
        <LoadingState title="Loading" description="Fetching admin users…" />
      ) : isError ? (
        <ErrorState title="Failed to load admin users" onRetry={refetch} />
      ) : users.length === 0 ? (
        <EmptyState
          title="No admin users yet"
          description="Create the first admin account to get started."
        />
      ) : (
        <Card className="divide-y divide-border overflow-hidden">
          {users.map((u) => (
            <AdminUserRow key={u.id} user={u} />
          ))}
        </Card>
      )}

      <CreateAdminUserDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSuccess={() => {
          setCreateOpen(false);
          invalidate();
        }}
      />
    </div>
  );
}

function AdminUserRow({ user }: { user: AdminUserRecord }) {
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const [selectedClientId, setSelectedClientId] = useState("");
  const [addError, setAddError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [removingId, setRemovingId] = useState<number | null>(null);

  const queryKey = ["admin-scoping", user.id];

  const { data: assignments = [], isLoading: assignmentsLoading } = useQuery({
    queryKey,
    queryFn: () => scopingService.getAssignedClients(user.id),
    enabled: expanded,
  });

  const { data: clientsData, isLoading: clientsLoading } = useQuery({
    queryKey: ["admin-clients-all"],
    queryFn: () => peopleService.getClients(),
    enabled: expanded,
  });

  const allClients = clientsData?.data?.items ?? [];
  const assignedIds = new Set(assignments.map((a) => a.client_profile_id));
  const availableClients = allClients.filter((c) => c.is_active && !assignedIds.has(c.id));

  const invalidate = () => queryClient.invalidateQueries({ queryKey });

  const handleAdd = async () => {
    const clientId = parseInt(selectedClientId, 10);
    if (!clientId || clientId < 1) {
      setAddError("Select a client to assign.");
      return;
    }
    setAddError(null);
    setAdding(true);
    try {
      await scopingService.assignClient(user.id, clientId);
      setSelectedClientId("");
      invalidate();
    } catch (err) {
      setAddError(getErrorMessage(err));
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (assignmentId: number) => {
    setRemovingId(assignmentId);
    try {
      await scopingService.removeAssignment(assignmentId);
      invalidate();
    } catch {
      // silent; list will stay unchanged
    } finally {
      setRemovingId(null);
    }
  };

  const isSuperAdmin = user.permission_group === "super_admin";

  return (
    <div className="divide-y divide-border">
      <div className="flex items-center justify-between px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">
              {user.name ?? <span className="text-muted-foreground italic">No name</span>}
            </p>
            <p className="text-xs text-muted-foreground">{user.email}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={user.is_active ? "default" : "secondary"}>
            {user.is_active ? "Active" : "Inactive"}
          </Badge>
          {user.permission_group ? (
            <Badge variant="outline">
              {PERMISSION_GROUP_LABELS[user.permission_group] ?? user.permission_group}
            </Badge>
          ) : null}
          {!isSuperAdmin && (
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className="flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:border-foreground/30 hover:text-foreground"
            >
              Client access
              {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </button>
          )}
        </div>
      </div>

      {expanded && !isSuperAdmin && (
        <div className="bg-muted/30 px-5 py-4 space-y-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Assigned clients
            </p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              This admin can only see and manage the clients listed below.
            </p>
          </div>

          {/* Add form */}
          <div className="flex flex-wrap items-center gap-2">
            {clientsLoading ? (
              <p className="text-xs text-muted-foreground">Loading clients…</p>
            ) : availableClients.length === 0 ? (
              <p className="text-xs text-muted-foreground italic">All clients already assigned.</p>
            ) : (
              <>
                <select
                  value={selectedClientId}
                  onChange={(e) => { setSelectedClientId(e.target.value); setAddError(null); }}
                  className="h-8 rounded-md border border-input bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">Select a client…</option>
                  {availableClients.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.company_name ?? c.contact_name} (#{c.id})
                    </option>
                  ))}
                </select>
                <Button size="sm" variant="secondary" disabled={adding || !selectedClientId} onClick={handleAdd}>
                  {adding ? "Adding…" : "Add client"}
                </Button>
              </>
            )}
          </div>
          {addError && <p className="text-xs text-red-600">{addError}</p>}

          {assignmentsLoading ? (
            <p className="text-xs text-muted-foreground">Loading…</p>
          ) : assignments.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              No clients assigned — this admin sees nothing. Add at least one client.
            </p>
          ) : (
            <div className="divide-y divide-border rounded-lg border border-border bg-white">
              {assignments.map((a) => (
                <div key={a.assignment_id} className="flex items-center justify-between px-3 py-2.5">
                  <div>
                    <span className="text-sm font-medium text-foreground">
                      {a.client_name ?? `Client #${a.client_profile_id}`}
                    </span>
                    <span className="ml-2 font-mono text-xs text-muted-foreground">
                      #{a.client_profile_id}
                    </span>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 px-2 text-red-600 hover:bg-red-50 hover:text-red-700"
                    disabled={removingId === a.assignment_id}
                    onClick={() => handleRemove(a.assignment_id)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    {removingId === a.assignment_id ? "Removing…" : "Remove"}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
