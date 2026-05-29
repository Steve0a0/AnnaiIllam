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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { peopleService } from "@/services/people.service";
import { getErrorMessage } from "@/lib/get-error-message";

const EMPTY = { phone: "", client_type: "company" as "company" | "individual", company_name: "", contact_name: "", city: "", state: "", gst_number: "" };

export default function CreateClientDialog({
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

  const set = (field: keyof typeof EMPTY) => (e: React.ChangeEvent<HTMLInputElement>) =>
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
      await peopleService.createClient({
        phone: "+91" + form.phone.trim(),
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
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Client</DialogTitle>
          <DialogDescription>
            Create a new client account. They will log in using OTP on their phone number.
          </DialogDescription>
        </DialogHeader>

        <form id="create-client-form" onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="cc-phone">Phone number *</Label>
            <div className="flex">
              <span className="inline-flex items-center rounded-l-md border border-r-0 border-input bg-muted px-3 text-sm text-muted-foreground">
                +91
              </span>
              <Input
                id="cc-phone"
                type="tel"
                placeholder="98765 43210"
                value={form.phone}
                onChange={set("phone")}
                required
                minLength={5}
                className="rounded-l-none"
              />
            </div>
          </div>

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
                <Label htmlFor="cc-company">Company name *</Label>
                <Input
                  id="cc-company"
                  placeholder="Acme Pvt Ltd"
                  value={form.company_name}
                  onChange={set("company_name")}
                  required
                  minLength={2}
                />
              </div>
            )}
            <div className={`space-y-1.5 ${form.client_type === "individual" ? "col-span-2" : ""}`}>
              <Label htmlFor="cc-contact">Contact name *</Label>
              <Input
                id="cc-contact"
                placeholder="Ravi Kumar"
                value={form.contact_name}
                onChange={set("contact_name")}
                required
                minLength={2}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="cc-city">City *</Label>
              <Input
                id="cc-city"
                placeholder="Chennai"
                value={form.city}
                onChange={set("city")}
                required
                minLength={2}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="cc-state">State *</Label>
              <Input
                id="cc-state"
                placeholder="Tamil Nadu"
                value={form.state}
                onChange={set("state")}
                required
                minLength={2}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="cc-gst">GST number (optional)</Label>
            <Input
              id="cc-gst"
              placeholder="29ABCDE1234F1Z5"
              value={form.gst_number}
              onChange={set("gst_number")}
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
          <Button type="submit" form="create-client-form" disabled={loading}>
            {loading ? "Creating…" : "Create Client"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
