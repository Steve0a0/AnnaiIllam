"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import Select from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  adminUsersService,
  PERMISSION_GROUP_LABELS,
  type PermissionGroup,
} from "@/services/admin-users.service";
import { getErrorMessage } from "@/lib/get-error-message";

const EMPTY = { email: "", name: "", password: "", permission_group: "ops_admin" as PermissionGroup };

export default function CreateAdminUserDialog({
  open,
  onClose,
  onSuccess,
}: {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [form, setForm] = useState(EMPTY);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (field: keyof Pick<typeof EMPTY, "email" | "name" | "password">) =>
    (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleClose = () => {
    setForm(EMPTY);
    setError(null);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await adminUsersService.create({
        email: form.email.trim().toLowerCase(),
        name: form.name.trim(),
        password: form.password,
        permission_group: form.permission_group,
      });
      handleClose();
      onSuccess();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Admin User</DialogTitle>
          <DialogDescription>
            Set up a login for a new admin. Share the email and password with them directly.
          </DialogDescription>
        </DialogHeader>

        <form id="create-admin-user-form" onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="au-email">Email address *</Label>
            <Input
              id="au-email"
              type="email"
              placeholder="admin@example.com"
              value={form.email}
              onChange={set("email")}
              required
              autoComplete="off"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="au-name">Full name *</Label>
            <Input
              id="au-name"
              placeholder="Priya Sharma"
              value={form.name}
              onChange={set("name")}
              required
              minLength={2}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="au-password">Password *</Label>
            <Input
              id="au-password"
              type="password"
              placeholder="Min. 8 characters"
              value={form.password}
              onChange={set("password")}
              required
              minLength={8}
              autoComplete="new-password"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="au-group">Permission group *</Label>
            <Select
              id="au-group"
              value={form.permission_group}
              onChange={(v) => setForm((prev) => ({ ...prev, permission_group: v as PermissionGroup }))}
              options={(Object.entries(PERMISSION_GROUP_LABELS) as [PermissionGroup, string][]).map(
                ([value, label]) => ({ value, label })
              )}
            />
          </div>

          {error ? (
            <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          ) : null}
        </form>

        <DialogFooter>
          <Button type="button" variant="ghost" onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" form="create-admin-user-form" disabled={loading}>
            {loading ? "Creating…" : "Create User"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
