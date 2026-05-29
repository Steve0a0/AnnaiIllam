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
import { getErrorMessage } from "@/lib/get-error-message";
import { CreateAdminUserDialog } from "@/features/admin-users";

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-users"],
    queryFn: adminUsersService.list,
  });

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
  const [clientIdInput, setClientIdInput] = useState("");
  const [addError, setAddError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [removingId, setRemovingId] = useState<number | null>(null);

  const queryKey = ["admin-scoping", user.id];

  const { data: assignments = [], isLoading } = useQuery({
    queryKey,
    queryFn: () => scopingService.getAssignedClients(user.id),
    enabled: expanded,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey });

  const handleAdd = async () => {
    const clientId = parseInt(clientIdInput.trim(), 10);
    if (!clientId || clientId < 1) {
      setAddError("Enter a valid client profile ID.");
      return;
    }
    setAddError(null);
    setAdding(true);
    try {
      await scopingService.assignClient(user.id, clientId);
      setClientIdInput("");
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
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Assigned clients
          </p>

          {/* Add form */}
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="number"
              min={1}
              placeholder="Client profile ID"
              value={clientIdInput}
              onChange={(e) => { setClientIdInput(e.target.value); setAddError(null); }}
              className="h-8 w-40 rounded-md border border-input bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <Button size="sm" variant="secondary" disabled={adding} onClick={handleAdd}>
              {adding ? "Adding…" : "Add client"}
            </Button>
          </div>
          {addError && <p className="text-xs text-red-600">{addError}</p>}

          {isLoading ? (
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
