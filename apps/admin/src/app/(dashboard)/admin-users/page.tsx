"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, ShieldCheck } from "lucide-react";
import PageHeader from "@/components/shared/page-header";
import LoadingState from "@/components/shared/loading-state";
import EmptyState from "@/components/shared/empty-state";
import ErrorState from "@/components/shared/error-state";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { adminUsersService, type AdminUserRecord } from "@/services/admin-users.service";
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
            <div
              key={u.id}
              className="flex items-center justify-between px-5 py-4"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <ShieldCheck className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {u.name ?? <span className="text-muted-foreground italic">No name</span>}
                  </p>
                  <p className="text-xs text-muted-foreground">{u.email}</p>
                </div>
              </div>
              <Badge variant={u.is_active ? "default" : "secondary"}>
                {u.is_active ? "Active" : "Inactive"}
              </Badge>
            </div>
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
