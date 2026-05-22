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
import { peopleService } from "@/services/people.service";
import { getErrorMessage } from "@/lib/get-error-message";
import type { AdminClient } from "@/types/people";

export default function DeactivateClientDialog({
  client,
  onClose,
  onSuccess,
}: {
  client: AdminClient | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClose = () => {
    setError(null);
    onClose();
  };

  const handleConfirm = async () => {
    if (!client) return;
    setLoading(true);
    setError(null);
    try {
      await peopleService.deactivateClient(client.id);
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
          <DialogTitle>Deactivate {client?.company_name ?? client?.contact_name ?? "this client"}?</DialogTitle>
          <DialogDescription>
            The client will no longer be able to log in. Their job history and request data will
            be preserved and remains accessible to admin.
          </DialogDescription>
        </DialogHeader>

        {error ? (
          <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        ) : null}

        <DialogFooter>
          <Button type="button" variant="ghost" onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="button" variant="destructive" onClick={handleConfirm} disabled={loading}>
            {loading ? "Deactivating…" : "Deactivate Client"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
