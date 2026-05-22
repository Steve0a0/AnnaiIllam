"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { peopleService } from "@/services/people.service";
import { getErrorMessage } from "@/lib/get-error-message";
import type { AdminClient } from "@/types/people";

export default function EditClientDialog({
  client,
  onClose,
  onSuccess,
}: {
  client: AdminClient | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [form, setForm] = useState({
    client_type: "company" as "company" | "individual",
    company_name: "",
    contact_name: "",
    city: "",
    state: "",
    gst_number: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (client) {
      setForm({
        client_type: client.client_type ?? "company",
        company_name: client.company_name ?? "",
        contact_name: client.contact_name,
        city: client.city,
        state: client.state,
        gst_number: client.gst_number ?? "",
      });
      setError(null);
    }
  }, [client]);

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleClose = () => {
    setError(null);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!client) return;
    setLoading(true);
    setError(null);
    try {
      await peopleService.updateClient(client.id, {
        client_type: form.client_type,
        company_name: form.client_type === "company" ? form.company_name.trim() : null,
        contact_name: form.contact_name.trim(),
        city: form.city.trim(),
        state: form.state.trim(),
        gst_number: form.gst_number.trim() || null,
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
    <Dialog open={!!client} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Client</DialogTitle>
          <DialogDescription>
            Update the profile details for {client?.company_name ?? client?.contact_name ?? "this client"}.
          </DialogDescription>
        </DialogHeader>

        <form id="edit-client-form" onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label>Client type *</Label>
            <div className="flex gap-2">
              {(["company", "individual"] as const).map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setForm((prev) => ({ ...prev, client_type: type }))}
                  className={`flex-1 rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
                    form.client_type === type
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-input bg-background text-foreground hover:bg-muted"
                  }`}
                >
                  {type === "company" ? "Company" : "Individual"}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {form.client_type === "company" && (
              <div className="space-y-1.5">
                <Label htmlFor="ec-company">Company name *</Label>
                <Input
                  id="ec-company"
                  value={form.company_name}
                  onChange={set("company_name")}
                  required
                  minLength={2}
                />
              </div>
            )}
            <div className={`space-y-1.5 ${form.client_type === "individual" ? "col-span-2" : ""}`}>
              <Label htmlFor="ec-contact">Contact name *</Label>
              <Input
                id="ec-contact"
                value={form.contact_name}
                onChange={set("contact_name")}
                required
                minLength={2}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="ec-city">City *</Label>
              <Input
                id="ec-city"
                value={form.city}
                onChange={set("city")}
                required
                minLength={2}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="ec-state">State *</Label>
              <Input
                id="ec-state"
                value={form.state}
                onChange={set("state")}
                required
                minLength={2}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="ec-gst">GST number (optional — clear to remove)</Label>
            <Input
              id="ec-gst"
              value={form.gst_number}
              onChange={set("gst_number")}
              placeholder="Leave blank to clear"
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
          <Button type="submit" form="edit-client-form" disabled={loading}>
            {loading ? "Saving…" : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
