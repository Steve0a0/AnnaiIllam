"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import PageHeader from "@/components/shared/page-header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { slaService } from "@/services/sla.service";
import type { ComplaintSlaPolicy } from "@/types/sla";

export default function SlaPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["complaint-sla-policies"],
    queryFn: slaService.getComplaintPolicies,
  });
  const mutation = useMutation({
    mutationFn: slaService.updateComplaintPolicy,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["complaint-sla-policies"] }),
  });

  return (
    <div className="space-y-6">
      <PageHeader title="SLA policies" description="Configure complaint response and resolution targets." />

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading SLA policies...</p>
      ) : isError ? (
        <p className="text-sm text-destructive">Failed to load SLA policies.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {(data?.data ?? []).map((policy) => (
            <SlaCard
              key={policy.id}
              policy={policy}
              disabled={mutation.isPending}
              onSave={(next) => mutation.mutate(next)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function SlaCard({
  policy,
  disabled,
  onSave,
}: {
  policy: ComplaintSlaPolicy;
  disabled: boolean;
  onSave: (policy: { severity: string; response_hours: number; resolution_hours: number }) => void;
}) {
  return (
    <Card className="p-4">
      <form
        className="space-y-3"
        action={(formData) => {
          onSave({
            severity: policy.severity,
            response_hours: Number(formData.get("response_hours")),
            resolution_hours: Number(formData.get("resolution_hours")),
          });
        }}
      >
        <h2 className="text-sm font-semibold capitalize text-foreground">{policy.severity}</h2>
        <div className="space-y-1">
          <Label className="text-xs uppercase tracking-wide text-muted-foreground">
            Response hours
          </Label>
          <input
            name="response_hours"
            type="number"
            min={1}
            defaultValue={policy.response_hours}
            className="flex h-9 w-full rounded-lg border border-input bg-card px-3 py-1 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs uppercase tracking-wide text-muted-foreground">
            Resolution hours
          </Label>
          <input
            name="resolution_hours"
            type="number"
            min={1}
            defaultValue={policy.resolution_hours}
            className="flex h-9 w-full rounded-lg border border-input bg-card px-3 py-1 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
        <Button type="submit" variant="accent" size="sm" className="w-full" disabled={disabled}>
          Save policy
        </Button>
      </form>
    </Card>
  );
}

