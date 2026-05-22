"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Briefcase,
  Calendar,
  Edit2,
  Mail,
  MapPin,
  Phone,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import LoadingState from "@/components/shared/loading-state";
import EmptyState from "@/components/shared/empty-state";
import ErrorState from "@/components/shared/error-state";
import StatusBadge from "@/components/shared/status-badge";
import { formatCurrency } from "@/lib/format-currency";
import { peopleService } from "@/services/people.service";
import type { AdminWorkerUpdatePayload } from "@/types/people";

export default function WorkerDetailView({
  workerProfileId,
}: {
  workerProfileId: number;
}) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [editOpen, setEditOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [form, setForm] = useState<AdminWorkerUpdatePayload>({});

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-worker-detail", workerProfileId],
    queryFn: () => peopleService.getWorkerById(workerProfileId),
    enabled: !!workerProfileId,
  });

  const worker = data?.data;

  function openEdit() {
    if (!worker) return;
    setSaveError(null);
    setForm({
      city: worker.city,
      state: worker.state,
      skills: worker.skills ?? "",
      available_days: worker.available_days ?? "",
      available_shifts: worker.available_shifts ?? "",
      phone: worker.phone ?? "",
      email: worker.email ?? "",
    });
    setEditOpen(true);
  }

  async function handleSave() {
    if (!worker) return;
    setSaving(true);
    setSaveError(null);
    try {
      await peopleService.updateWorker(workerProfileId, form);
      setEditOpen(false);
      await queryClient.invalidateQueries({
        queryKey: ["admin-worker-detail", workerProfileId],
      });
    } catch {
      setSaveError("Could not save changes. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  if (isLoading) {
    return <LoadingState title="Loading worker" description="Fetching worker profile…" />;
  }

  if (isError || !worker) {
    return (
      <ErrorState
        title="Could not load worker"
        description="The worker may not exist or the connection failed."
        onRetry={() => refetch()}
      />
    );
  }

  const activeAssignments = worker.assignments.filter((a) =>
    ["assigned", "accepted", "active"].includes(a.status),
  ).length;
  const completedAssignments = worker.assignments.filter(
    (a) => a.status === "completed",
  ).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <button
          type="button"
          onClick={() => router.push("/workers")}
          className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Workers
        </button>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="font-display text-2xl font-semibold tracking-tight text-foreground">
              {worker.full_name}
            </h1>
            <p className="mt-0.5 text-sm text-muted-foreground">
              {worker.category}
              {worker.subcategory ? ` · ${worker.subcategory}` : ""}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge value={worker.verification_status} />
            <Button size="sm" variant="outline" onClick={openEdit}>
              <Edit2 className="h-3.5 w-3.5" />
              Edit
            </Button>
          </div>
        </div>
      </div>

      {/* Info grid */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Profile card */}
        <Card className="p-6 lg:col-span-2">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            Profile
          </h2>
          <dl className="grid gap-4 sm:grid-cols-2">
            <InfoRow icon={<Phone className="h-4 w-4" />} label="Phone">
              {worker.phone ?? "—"}
            </InfoRow>
            <InfoRow icon={<Mail className="h-4 w-4" />} label="Email">
              {worker.email ?? "—"}
            </InfoRow>
            <InfoRow icon={<MapPin className="h-4 w-4" />} label="Location">
              {worker.city}, {worker.state}
            </InfoRow>
            <InfoRow icon={<Briefcase className="h-4 w-4" />} label="Experience">
              {worker.experience_years ?? "—"}
            </InfoRow>
            <InfoRow icon={<Calendar className="h-4 w-4" />} label="Available days">
              {worker.available_days ?? "—"}
            </InfoRow>
            <InfoRow icon={<Calendar className="h-4 w-4" />} label="Shifts">
              {worker.available_shifts ?? "—"}
            </InfoRow>
            {worker.skills ? (
              <div className="sm:col-span-2">
                <dt className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
                  Skills
                </dt>
                <dd className="mt-0.5 text-sm text-foreground">{worker.skills}</dd>
              </div>
            ) : null}
            {worker.address ? (
              <div className="sm:col-span-2">
                <dt className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
                  Address
                </dt>
                <dd className="mt-0.5 text-sm text-foreground">{worker.address}</dd>
              </div>
            ) : null}
          </dl>
        </Card>

        {/* Stats sidebar */}
        <Card className="p-6">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            Summary
          </h2>
          <div className="space-y-3">
            <StatRow label="Total assignments" value={worker.assignments.length} />
            <StatRow label="Active" value={activeAssignments} />
            <StatRow label="Completed" value={completedAssignments} />
            <StatRow label="Payroll records" value={worker.payroll_items.length} />
            <div className="border-t border-border pt-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Availability</span>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    worker.is_available
                      ? "bg-green-50 text-green-700"
                      : "bg-amber-50 text-amber-700"
                  }`}
                >
                  {worker.is_available ? "Available" : "On leave"}
                </span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Assignment history */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          Assignment history
        </h2>
        {worker.assignments.length === 0 ? (
          <EmptyState
            title="No assignments yet"
            description="This worker has not been assigned to any requirements."
          />
        ) : (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-border">
                <thead className="bg-muted/40">
                  <tr>
                    {["#", "Requirement", "Role", "Shift", "Salary", "Status", "Assigned"].map(
                      (h) => (
                        <th
                          key={h}
                          className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-widest text-muted-foreground"
                        >
                          {h}
                        </th>
                      ),
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {worker.assignments.map((a) => (
                    <tr
                      key={a.id}
                      className="cursor-pointer transition-colors hover:bg-muted/30"
                      onClick={() => router.push(`/requirements/${a.requirement_id}`)}
                    >
                      <td className="px-4 py-3 font-mono text-sm text-muted-foreground">
                        #{a.id}
                      </td>
                      <td className="px-4 py-3 font-mono text-sm text-muted-foreground">
                        Req #{a.requirement_id}
                      </td>
                      <td className="px-4 py-3 text-sm text-foreground">
                        {a.assigned_role ?? "—"}
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground">
                        {a.assigned_shift ?? "—"}
                      </td>
                      <td className="px-4 py-3 text-sm text-foreground">
                        {a.salary_amount != null ? formatCurrency(a.salary_amount) : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge value={a.status} />
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                        {a.assigned_at
                          ? new Date(a.assigned_at).toLocaleDateString("en-IN", {
                              day: "2-digit",
                              month: "short",
                              year: "numeric",
                            })
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="border-t border-border px-4 py-3">
              <p className="text-xs text-muted-foreground">
                {worker.assignments.length} assignment
                {worker.assignments.length !== 1 ? "s" : ""}
              </p>
            </div>
          </Card>
        )}
      </div>

      {/* Payroll items */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          Payroll records
        </h2>
        {worker.payroll_items.length === 0 ? (
          <EmptyState
            title="No payroll records"
            description="This worker has no payroll items yet."
          />
        ) : (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-border">
                <thead className="bg-muted/40">
                  <tr>
                    {["#", "Run", "Assignment", "Days", "Gross", "Deductions", "Net", "Status"].map(
                      (h) => (
                        <th
                          key={h}
                          className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-widest text-muted-foreground"
                        >
                          {h}
                        </th>
                      ),
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {worker.payroll_items.map((pi) => (
                    <tr key={pi.id} className="transition-colors hover:bg-muted/30">
                      <td className="px-4 py-3 font-mono text-sm text-muted-foreground">
                        #{pi.id}
                      </td>
                      <td className="px-4 py-3 font-mono text-sm text-muted-foreground">
                        #{pi.payroll_run_id}
                      </td>
                      <td className="px-4 py-3 font-mono text-sm text-muted-foreground">
                        #{pi.assignment_id}
                      </td>
                      <td className="px-4 py-3 text-sm text-foreground">
                        {pi.attendance_days}
                      </td>
                      <td className="px-4 py-3 text-sm text-foreground">
                        {formatCurrency(pi.gross_amount)}
                      </td>
                      <td className="px-4 py-3 text-sm text-red-600">
                        -{formatCurrency(pi.total_deduction_amount)}
                      </td>
                      <td className="px-4 py-3 text-sm font-semibold text-foreground">
                        {formatCurrency(pi.net_amount)}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge value={pi.payment_status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="border-t border-border px-4 py-3">
              <p className="text-xs text-muted-foreground">
                {worker.payroll_items.length} record
                {worker.payroll_items.length !== 1 ? "s" : ""}
              </p>
            </div>
          </Card>
        )}
      </div>

      {/* Edit dialog */}
      <Dialog open={editOpen} onOpenChange={(open) => !open && setEditOpen(false)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit worker profile</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-1">
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Phone">
                <input
                  className={inputCls}
                  value={form.phone ?? ""}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                />
              </FormField>
              <FormField label="Email">
                <input
                  className={inputCls}
                  value={form.email ?? ""}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </FormField>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="City">
                <input
                  className={inputCls}
                  value={form.city ?? ""}
                  onChange={(e) => setForm({ ...form, city: e.target.value })}
                />
              </FormField>
              <FormField label="State">
                <input
                  className={inputCls}
                  value={form.state ?? ""}
                  onChange={(e) => setForm({ ...form, state: e.target.value })}
                />
              </FormField>
            </div>
            <FormField label="Skills">
              <textarea
                className={`${inputCls} min-h-[80px] py-2`}
                value={form.skills ?? ""}
                onChange={(e) => setForm({ ...form, skills: e.target.value })}
              />
            </FormField>
            <FormField label="Available days (e.g. Mon,Tue,Wed)">
              <input
                className={inputCls}
                value={form.available_days ?? ""}
                onChange={(e) => setForm({ ...form, available_days: e.target.value })}
              />
            </FormField>
            <FormField label="Available shifts (e.g. Morning,Evening)">
              <input
                className={inputCls}
                value={form.available_shifts ?? ""}
                onChange={(e) => setForm({ ...form, available_shifts: e.target.value })}
              />
            </FormField>
            {saveError && (
              <p className="text-sm text-destructive">{saveError}</p>
            )}
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setEditOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "Saving…" : "Save changes"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const inputCls =
  "h-10 w-full rounded-lg border border-input bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring";

function InfoRow({
  icon,
  label,
  children,
}: {
  icon: React.ReactNode;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex gap-3">
      <span className="mt-0.5 shrink-0 text-muted-foreground">{icon}</span>
      <div>
        <dt className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
          {label}
        </dt>
        <dd className="mt-0.5 text-sm text-foreground">{children}</dd>
      </div>
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="font-mono text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}

function FormField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-muted-foreground">{label}</label>
      {children}
    </div>
  );
}
