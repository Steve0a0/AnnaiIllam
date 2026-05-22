"use client";

import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Check, Search, X } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { assignmentsService } from "@/services/assignments.service";
import { getErrorMessage } from "@/lib/get-error-message";
import type { WorkerMatch } from "@/types/assignment";
import type { AdminRequirementDetail } from "@/types/requirement";

const roleFallbacks = [
  "General Worker",
  "Helper",
  "Skilled Worker",
  "Supervisor",
  "Cleaner",
  "Security",
  "Cook",
  "Driver",
  "Other",
];

const shiftFallbacks = [
  "General Shift - 09:00 to 18:00",
  "Morning Shift - 06:00 to 14:00",
  "Evening Shift - 14:00 to 22:00",
  "Night Shift - 22:00 to 06:00",
  "Double Shift",
  "Other",
];

export default function CreateAssignmentForm({
  requirement,
  requirementId,
  onSuccess,
}: {
  requirement: AdminRequirementDetail;
  requirementId: number;
  onSuccess: () => void;
}) {
  const [selectedWorkerIds, setSelectedWorkerIds] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const roleOptions = buildOptions(
    [requirement.subcategory, requirement.category],
    roleFallbacks,
  );
  const shiftOptions = buildOptions([requirement.shift_details], shiftFallbacks);
  const salaryOptions = buildSalaryOptions(requirement.quote?.rate_per_worker);
  const [assignedRole, setAssignedRole] = useState(roleOptions[0] || "");
  const [customRole, setCustomRole] = useState("");
  const [assignedShift, setAssignedShift] = useState(shiftOptions[0] || "");
  const [customShift, setCustomShift] = useState("");
  const [salaryMode, setSalaryMode] = useState(salaryOptions[0]?.value || "");
  const [salaryAmount, setSalaryAmount] = useState("");
  const [notes, setNotes] = useState("");
  const [skipPaymentCheck, setSkipPaymentCheck] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const queryClient = useQueryClient();

  const { data: matchesData, isLoading: matchesLoading } = useQuery({
    queryKey: ["worker-matches", requirementId],
    queryFn: () => assignmentsService.getWorkerMatches(requirementId),
    enabled: !!requirementId,
  });

  const matches = matchesData?.data || [];
  const assignableMatches = matches.filter(isAssignableWorker);
  const blockedMatches = matches.filter((worker) => !isAssignableWorker(worker));
  const normalizedQuery = query.trim().toLowerCase();
  const visibleReadyToAssignMatches = useMemo(
    () =>
      filterWorkers(
        [
          ...assignableMatches.filter((worker) => worker.has_interest),
          ...assignableMatches.filter((worker) => !worker.has_interest),
        ],
        normalizedQuery,
      ),
    [assignableMatches, normalizedQuery],
  );
  const visibleBlockedMatches = useMemo(
    () => filterWorkers(blockedMatches, normalizedQuery),
    [blockedMatches, normalizedQuery],
  );
  const selectedWorkers = assignableMatches.filter((worker) =>
    selectedWorkerIds.includes(String(worker.worker_profile_id)),
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage("");

    if (!selectedWorkerIds.length) {
      setMessage("Select at least one available worker.");
      return;
    }

    if (salaryAmount && Number(salaryAmount) < 0) {
      setMessage("Payout amount cannot be negative.");
      return;
    }

    const finalRole = assignedRole === "Other" ? customRole.trim() : assignedRole;
    const finalShift =
      assignedShift === "Other" ? customShift.trim() : assignedShift;
    const finalSalary = salaryMode === "custom" ? salaryAmount : salaryMode;

    if (assignedRole === "Other" && !finalRole) {
      setMessage("Enter the custom assigned role.");
      return;
    }

    if (assignedShift === "Other" && !finalShift) {
      setMessage("Enter the custom assigned shift.");
      return;
    }

    setLoading(true);

    try {
      await Promise.all(
        selectedWorkerIds.map((workerId) =>
          assignmentsService.createAssignment(
            {
              requirement_id: requirementId,
              worker_profile_id: Number(workerId),
              assigned_role: finalRole || null,
              assigned_shift: finalShift || null,
              salary_amount: finalSalary ? Number(finalSalary) : null,
              notes: notes || null,
            },
            skipPaymentCheck,
          ),
        ),
      );

      const assignedCount = selectedWorkerIds.length;
      resetForm();
      setMessage(
        assignedCount === 1
          ? "Worker assigned successfully."
          : `${assignedCount} workers assigned successfully.`,
      );

      try {
        await queryClient.invalidateQueries({
          queryKey: ["requirement-assignments", requirementId],
        });
        await queryClient.invalidateQueries({
          queryKey: ["worker-matches", requirementId],
        });
        onSuccess();
      } catch {
        setMessage(
          "Workers assigned successfully. Refresh the page if the list does not update.",
        );
      }
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  function resetForm() {
    setSelectedWorkerIds([]);
    setQuery("");
    setAssignedRole(roleOptions[0] || "");
    setAssignedShift(shiftOptions[0] || "");
    setCustomRole("");
    setCustomShift("");
    setSalaryMode(salaryOptions[0]?.value || "");
    setSalaryAmount("");
    setNotes("");
    setSkipPaymentCheck(false);
  }

  function toggleWorker(workerProfileId: number) {
    const workerId = String(workerProfileId);
    setSelectedWorkerIds((current) =>
      current.includes(workerId)
        ? current.filter((id) => id !== workerId)
        : [...current, workerId],
    );
  }

  function selectAllAssignable() {
    setSelectedWorkerIds(
      assignableMatches.map((worker) => String(worker.worker_profile_id)),
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.8fr)]">
        <section className="space-y-4">
          <div className="rounded-xl border border-border bg-[#FAFAF9] p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-sm font-semibold text-foreground">
                  Choose workers
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Ready workers can be assigned now. Blocked workers show the exact reason they are unavailable.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  disabled={!assignableMatches.length}
                  onClick={selectAllAssignable}
                >
                  Select all ready
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  disabled={!selectedWorkerIds.length}
                  onClick={() => setSelectedWorkerIds([])}
                >
                  Clear
                </Button>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 text-center">
              <MatchCount label="ready" value={assignableMatches.length} tone="success" />
              <MatchCount label="blocked" value={blockedMatches.length} tone="warning" />
              <MatchCount label="selected" value={selectedWorkerIds.length} tone="neutral" />
            </div>
          </div>

          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by name, skill, city, or reason"
              className="h-11 w-full rounded-lg border border-input bg-white pl-9 pr-3 text-sm text-foreground shadow-sm outline-none transition focus:ring-2 focus:ring-ring"
            />
          </div>

          {matchesLoading ? (
            <div className="rounded-xl border border-dashed border-border bg-white p-5 text-sm text-muted-foreground">
              Loading worker matches...
            </div>
          ) : null}

          {!matchesLoading && matches.length > 0 && assignableMatches.length === 0 ? (
            <div className="rounded-xl border-l-4 border-l-[#B45309] border-y border-r border-[#FEF3C7] bg-[#FFFBEB] px-4 py-3 text-sm text-[#B45309]">
              No workers are ready for this requirement yet. Use the blocked list below to see what needs fixing.
            </div>
          ) : null}

          {!matchesLoading && matches.length === 0 ? (
            <div className="rounded-xl border-l-4 border-l-[#B45309] border-y border-r border-[#FEF3C7] bg-[#FFFBEB] px-4 py-3 text-sm text-[#B45309]">
              No worker profiles are available yet. Approve a worker profile first, then return here.
            </div>
          ) : null}

          {assignableMatches.length ? (
            <WorkerGroup
              title="Ready to assign"
              description="Approved, available workers who match the requested date and shift."
              count={assignableMatches.length}
              countLabel="ready"
            >
              {visibleReadyToAssignMatches.length ? (
                <div className="grid gap-3 md:grid-cols-2">
                  {visibleReadyToAssignMatches.map((worker) => (
                    <WorkerCard
                      key={worker.worker_profile_id}
                      worker={worker}
                      selected={selectedWorkerIds.includes(
                        String(worker.worker_profile_id),
                      )}
                      onSelect={() => toggleWorker(worker.worker_profile_id)}
                      badge={worker.has_interest ? "Interested" : undefined}
                    />
                  ))}
                </div>
              ) : (
                <EmptyGroup>No ready workers match this search.</EmptyGroup>
              )}
            </WorkerGroup>
          ) : null}

          {blockedMatches.length ? (
            <WorkerGroup
              title="Blocked workers"
              description="These workers cannot be assigned until the reason is resolved."
              count={blockedMatches.length}
              countLabel="blocked"
            >
              {visibleBlockedMatches.length ? (
                <div className="grid gap-3 md:grid-cols-2">
                  {visibleBlockedMatches.slice(0, 8).map((worker) => (
                    <BlockedWorkerCard
                      key={worker.worker_profile_id}
                      worker={worker}
                    />
                  ))}
                </div>
              ) : (
                <EmptyGroup>No blocked workers match this search.</EmptyGroup>
              )}
            </WorkerGroup>
          ) : null}
        </section>

        <aside className="space-y-4 lg:sticky lg:top-0 lg:self-start">
          <section className="rounded-xl border border-border bg-white p-4 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-foreground">
                  Assignment details
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  These settings apply to every selected worker.
                </p>
              </div>
              <span className="rounded-full bg-[#EDFAF3] px-3 py-1 text-xs font-semibold text-[#1A6640]">
                {selectedWorkerIds.length} selected
              </span>
            </div>

            {selectedWorkers.length ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {selectedWorkers.map((worker) => (
                  <button
                    key={worker.worker_profile_id}
                    type="button"
                    onClick={() => toggleWorker(worker.worker_profile_id)}
                    className="inline-flex items-center gap-1 rounded-full border border-border bg-[#FAFAF9] px-2.5 py-1 text-xs font-medium text-foreground"
                  >
                    {worker.full_name}
                    <X className="size-3" />
                  </button>
                ))}
              </div>
            ) : (
              <div className="mt-4 rounded-lg border border-dashed border-border bg-[#FAFAF9] p-3 text-xs text-muted-foreground">
                Select workers from the list to enable assignment.
              </div>
            )}

            <div className="mt-5 space-y-4">
              <Field label="Assigned role">
                <select
                  className="h-11 w-full rounded-lg border border-input bg-white px-3 text-sm"
                  value={assignedRole}
                  onChange={(e) => setAssignedRole(e.target.value)}
                >
                  {roleOptions.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
                {assignedRole === "Other" ? (
                  <input
                    className="mt-2 h-11 w-full rounded-lg border border-input bg-white px-3 text-sm"
                    value={customRole}
                    onChange={(e) => setCustomRole(e.target.value)}
                    placeholder="Enter custom role"
                  />
                ) : null}
              </Field>

              <Field label="Assigned shift">
                <select
                  className="h-11 w-full rounded-lg border border-input bg-white px-3 text-sm"
                  value={assignedShift}
                  onChange={(e) => setAssignedShift(e.target.value)}
                >
                  {shiftOptions.map((shift) => (
                    <option key={shift} value={shift}>
                      {shift}
                    </option>
                  ))}
                </select>
                {assignedShift === "Other" ? (
                  <input
                    className="mt-2 h-11 w-full rounded-lg border border-input bg-white px-3 text-sm"
                    value={customShift}
                    onChange={(e) => setCustomShift(e.target.value)}
                    placeholder="Enter custom shift"
                  />
                ) : null}
              </Field>

              <Field label="Worker payout, optional">
                <select
                  className="h-11 w-full rounded-lg border border-input bg-white px-3 text-sm"
                  value={salaryMode}
                  onChange={(e) => setSalaryMode(e.target.value)}
                >
                  {salaryOptions.map((option) => (
                    <option key={option.value || "none"} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                  <option value="custom">Custom amount</option>
                </select>
                {salaryMode === "custom" ? (
                  <input
                    type="number"
                    min="0"
                    step="1"
                    className="mt-2 h-11 w-full rounded-lg border border-input bg-white px-3 text-sm"
                    value={salaryAmount}
                    onChange={(e) => setSalaryAmount(e.target.value)}
                    placeholder="Enter payout amount"
                  />
                ) : null}
                <p className="mt-2 text-xs text-muted-foreground">
                  Leave unset for MVP if payout is handled offline.
                </p>
              </Field>

              <Field label="Notes">
                <textarea
                  className="min-h-24 w-full rounded-lg border border-input bg-white px-3 py-2 text-sm"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add assignment notes"
                />
              </Field>
            </div>

            <label className="mt-5 flex cursor-pointer items-start gap-2.5 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5">
              <input
                type="checkbox"
                checked={skipPaymentCheck}
                onChange={(e) => setSkipPaymentCheck(e.target.checked)}
                className="mt-0.5 shrink-0 accent-amber-600"
              />
              <div>
                <p className="text-xs font-semibold text-amber-800">
                  Override payment gate (admin override)
                </p>
                <p className="mt-0.5 text-xs text-amber-700">
                  Bypasses the confirmed-advance requirement. Use only for demos or manual flows where payment is handled offline.
                </p>
              </div>
            </label>

            {message ? (
              <div className="mt-4 rounded-lg bg-[#FAFAF9] px-3 py-2 text-sm text-foreground">
                {message}
              </div>
            ) : null}

            <Button
              type="submit"
              disabled={loading || !selectedWorkerIds.length}
              variant="accent"
              className="mt-5 w-full"
            >
              {loading
                ? "Assigning..."
                : selectedWorkerIds.length > 1
                  ? `Assign ${selectedWorkerIds.length} Workers`
                  : "Assign Worker"}
            </Button>
          </section>
        </aside>
      </div>
    </form>
  );
}

function WorkerGroup({
  title,
  description,
  count,
  countLabel,
  children,
}: {
  title: string;
  description: string;
  count: number;
  countLabel: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-border bg-white p-4 shadow-sm">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-foreground">{title}</p>
          <p className="mt-1 text-xs text-muted-foreground">{description}</p>
        </div>
        <span className="rounded-full bg-[#EDFAF3] px-3 py-1 text-xs font-semibold text-[#1A6640]">
          {count} {countLabel}
        </span>
      </div>
      {children}
    </section>
  );
}

function MatchCount({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "success" | "warning" | "neutral";
}) {
  const toneClass = {
    success: "bg-[#EDFAF3] text-[#1A6640]",
    warning: "bg-[#FFFBEB] text-[#B45309]",
    neutral: "bg-white text-muted-foreground",
  }[tone];

  return (
    <div className={`rounded-lg border border-border px-3 py-2 ${toneClass}`}>
      <p className="text-lg font-semibold leading-none">{value}</p>
      <p className="mt-1 text-[11px] font-medium uppercase tracking-wide">{label}</p>
    </div>
  );
}

function EmptyGroup({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-[#FAFAF9] p-4 text-sm text-muted-foreground">
      {children}
    </div>
  );
}

function WorkerCard({
  worker,
  selected,
  onSelect,
  badge,
}: {
  worker: WorkerMatch;
  selected: boolean;
  onSelect: () => void;
  badge?: string;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`rounded-xl border p-3 text-left text-sm transition ${
        selected
          ? "border-[#1A6640] bg-[#EDFAF3] shadow-sm"
          : "border-border bg-white hover:border-[#1A6640]"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span
              className={`flex size-5 items-center justify-center rounded-full border ${
                selected
                  ? "border-[#1A6640] bg-[#1A6640] text-white"
                  : "border-border bg-white text-transparent"
              }`}
            >
              <Check className="size-3.5" />
            </span>
            <p className="font-semibold text-foreground">{worker.full_name}</p>
          </div>
          <p className="mt-2 text-muted-foreground">
            {worker.category} - {worker.city}, {worker.state}
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1">
          <span className="rounded-full bg-[#F5F5F4] px-2 py-1 text-xs font-semibold text-muted-foreground">
            {worker.score}
          </span>
          {badge ? (
            <span className="rounded-full bg-[#DCFCE7] px-2 py-0.5 text-xs font-semibold text-[#15803D]">
              {badge}
            </span>
          ) : null}
        </div>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        {worker.reasons.filter((reason) => reason !== "interested").join(", ") ||
          "Available"}
      </p>
    </button>
  );
}

function BlockedWorkerCard({ worker }: { worker: WorkerMatch }) {
  const reason = getBlockedReason(worker);

  return (
    <div className="rounded-xl border border-border bg-[#FAFAF9] p-3 text-left text-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-foreground">{worker.full_name}</p>
          <p className="mt-1 text-muted-foreground">
            {worker.category} - {worker.city}, {worker.state}
          </p>
        </div>
        <span className="rounded-full bg-white px-2 py-1 text-xs font-semibold text-muted-foreground">
          {worker.score}
        </span>
      </div>
      <p className="mt-2 inline-flex rounded-full bg-[#FEF3C7] px-2 py-1 text-xs font-medium text-[#B45309]">
        {reason}
      </p>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">
        {getBlockedFix(worker, reason)}
      </p>
    </div>
  );
}

function filterWorkers(workers: WorkerMatch[], query: string) {
  if (!query) {
    return workers;
  }

  return workers.filter((worker) =>
    [
      worker.full_name,
      worker.category,
      worker.city,
      worker.state,
      worker.verification_status,
      ...worker.reasons,
      getBlockedReason(worker),
    ]
      .join(" ")
      .toLowerCase()
      .includes(query),
  );
}

function buildOptions(
  preferred: Array<string | null | undefined>,
  fallbacks: string[],
) {
  return Array.from(
    new Set(
      [...preferred, ...fallbacks]
        .map((item) => item?.trim())
        .filter((item): item is string => Boolean(item)),
    ),
  );
}

function isAssignableWorker(worker: WorkerMatch) {
  return (
    worker.is_available &&
    ["approved", "verified"].includes(worker.verification_status) &&
    !worker.reasons.some((reason) => reason.startsWith("not available")) &&
    !worker.conflict
  );
}

function getBlockedReason(worker: WorkerMatch) {
  if (worker.conflict) {
    return `Conflict with request #${worker.conflict.requirement_id}`;
  }

  if (!["approved", "verified"].includes(worker.verification_status)) {
    return `Needs worker approval (${worker.verification_status})`;
  }

  if (!worker.is_available) {
    return "Worker is marked unavailable";
  }

  const availabilityReason = worker.reasons.find((reason) =>
    reason.startsWith("not available"),
  );
  if (availabilityReason) {
    return availabilityReason;
  }

  return "Not ready for this assignment";
}

function getBlockedFix(worker: WorkerMatch, reason: string) {
  if (reason === "not available for requested shift") {
    return `Worker shifts: ${worker.available_shifts || "not set"}. Update worker availability or choose a compatible request shift.`;
  }

  if (reason === "not available on requested day") {
    return `Worker days: ${worker.available_days || "not set"}. Update worker availability or choose another start date.`;
  }

  if (reason.startsWith("Needs worker approval")) {
    return "Approve this worker from the Workers page before assigning.";
  }

  if (reason === "Worker is marked unavailable") {
    return "Mark this worker available from the Workers page.";
  }

  if (reason.startsWith("Conflict")) {
    return "This worker already has an active assignment during the request dates.";
  }

  return "Review the worker profile and requirement dates before assigning.";
}

function buildSalaryOptions(ratePerWorker?: number | null) {
  const presets = [{ label: "Not set yet", value: "" }];

  if (ratePerWorker && ratePerWorker > 0) {
    presets.push(
      {
        label: `70% of client rate - Rs. ${Math.round(
          ratePerWorker * 0.7,
        ).toLocaleString("en-IN")}`,
        value: String(Math.round(ratePerWorker * 0.7)),
      },
      {
        label: `80% of client rate - Rs. ${Math.round(
          ratePerWorker * 0.8,
        ).toLocaleString("en-IN")}`,
        value: String(Math.round(ratePerWorker * 0.8)),
      },
      {
        label: `90% of client rate - Rs. ${Math.round(
          ratePerWorker * 0.9,
        ).toLocaleString("en-IN")}`,
        value: String(Math.round(ratePerWorker * 0.9)),
      },
    );
  }

  presets.push(
    { label: "Rs. 500", value: "500" },
    { label: "Rs. 700", value: "700" },
    { label: "Rs. 900", value: "900" },
    { label: "Rs. 1,200", value: "1200" },
  );

  return presets;
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-foreground">
        {label}
      </label>
      {children}
    </div>
  );
}
