"use client";

import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Check, RefreshCw, Search, X } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { assignmentsService } from "@/services/assignments.service";
import { getErrorMessage } from "@/lib/get-error-message";
import type { WorkerMatch } from "@/types/assignment";
import type { AdminRequirementDetail } from "@/types/requirement";
import type { ReplacementHint } from "@/features/assignments/requirement-assignments-list";

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
  replacementHint,
  onSuccess,
}: {
  requirement: AdminRequirementDetail;
  requirementId: number;
  replacementHint?: ReplacementHint;
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

  const defaultStartDate = replacementHint?.startDate ?? requirement.start_date ?? "";
  const defaultEndDate = replacementHint?.endDate ?? (() => {
    if (!requirement.start_date || !requirement.duration_days) return "";
    const d = new Date(requirement.start_date);
    d.setDate(d.getDate() + requirement.duration_days - 1);
    return d.toISOString().slice(0, 10);
  })();

  // Requirement date window for constraining datepicker inputs
  const reqMinDate = requirement.start_date ?? undefined;
  const reqMaxDate = (() => {
    if (!requirement.start_date || !requirement.duration_days) return undefined;
    const d = new Date(requirement.start_date);
    d.setDate(d.getDate() + requirement.duration_days - 1);
    return d.toISOString().slice(0, 10);
  })();
  const defaultRole = replacementHint?.assignedRole ?? roleOptions[0] ?? "";
  const defaultShift = replacementHint?.assignedShift ?? shiftOptions[0] ?? "";
  const defaultSalary = replacementHint?.salaryAmount
    ? String(replacementHint.salaryAmount)
    : "";

  const [assignedRole, setAssignedRole] = useState(defaultRole);
  const [customRole, setCustomRole] = useState("");
  const [assignedShift, setAssignedShift] = useState(defaultShift);
  const [customShift, setCustomShift] = useState("");
  const [salaryMode, setSalaryMode] = useState(
    replacementHint?.salaryAmount ? "custom" : salaryOptions[0]?.value || "",
  );
  const [salaryAmount, setSalaryAmount] = useState(defaultSalary);
  const [notes, setNotes] = useState("");
  const [startDate, setStartDate] = useState(defaultStartDate);
  const [endDate, setEndDate] = useState(defaultEndDate);
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
      const responses = await Promise.all(
        selectedWorkerIds.map((workerId) =>
          assignmentsService.createAssignment({
            requirement_id: requirementId,
            worker_profile_id: Number(workerId),
            assigned_role: finalRole || null,
            assigned_shift: finalShift || null,
            salary_amount: finalSalary ? Number(finalSalary) : null,
            notes: notes || null,
            start_date: startDate || null,
            end_date: endDate || null,
          }),
        ),
      );

      const assignedCount = selectedWorkerIds.length;
      const warnings = responses
        .map((r) => r.data?.warning)
        .filter((w): w is NonNullable<typeof w> => w !== null && w !== undefined);
      resetForm();
      const baseMsg =
        assignedCount === 1
          ? "Worker assigned successfully."
          : `${assignedCount} workers assigned successfully.`;
      const warningMsg =
        warnings.length > 0
          ? ` Warning: ${warnings[0].message}`
          : "";
      setMessage(baseMsg + warningMsg);

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
    setStartDate(requirement.start_date ?? "");
    setEndDate(() => {
      if (!requirement.start_date || !requirement.duration_days) return "";
      const d = new Date(requirement.start_date);
      d.setDate(d.getDate() + requirement.duration_days - 1);
      return d.toISOString().slice(0, 10);
    });
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
      {replacementHint && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
          <RefreshCw className="mt-0.5 size-4 shrink-0 text-amber-600" />
          <p className="text-[14px] text-amber-800">
            <span className="font-semibold">Replacement mode</span> — dates and role pre-filled from the declined slot. Select a new worker below.
          </p>
        </div>
      )}

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.8fr)]">
        {/* Worker picker */}
        <section className="space-y-4">
          <div className="rounded-xl border border-[oklch(0.90_0.003_145)] bg-[oklch(0.97_0.008_145)] p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-[14px] font-semibold text-[oklch(0.20_0.006_145)]">Choose workers</p>
                <p className="mt-1 text-[13px] text-[oklch(0.44_0.005_145)]">
                  Ready workers can be selected. Blocked workers show what needs fixing.
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
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
            <div className="mt-3 flex items-center gap-5 border-t border-[oklch(0.90_0.003_145)] pt-3">
              <Stat dot="bg-[oklch(0.42_0.115_145)]" value={assignableMatches.length} label="ready" />
              <Stat dot="bg-[#F59E0B]" value={blockedMatches.length} label="blocked" />
              <Stat dot="bg-[oklch(0.62_0.004_145)]" value={selectedWorkerIds.length} label="selected" />
            </div>
          </div>

          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[oklch(0.62_0.004_145)]" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by name, skill, city, or reason"
              className="h-11 w-full rounded-xl border border-[oklch(0.90_0.003_145)] bg-white pl-9 pr-4 text-[14px] text-[oklch(0.20_0.006_145)] outline-none transition placeholder:text-[oklch(0.62_0.004_145)] focus:border-[oklch(0.42_0.115_145)] focus:ring-2 focus:ring-[oklch(0.42_0.115_145)]/20"
            />
          </div>

          {matchesLoading ? (
            <div className="rounded-xl border border-dashed border-[oklch(0.90_0.003_145)] bg-white p-6 text-center text-[13px] text-[oklch(0.48_0.005_145)]">
              Loading worker matches...
            </div>
          ) : null}

          {!matchesLoading && matches.length === 0 ? (
            <EmptyState
              title="No worker profiles yet"
              detail="Approve a worker profile first, then return here to assign."
            />
          ) : null}

          {!matchesLoading && matches.length > 0 && assignableMatches.length === 0 ? (
            <EmptyState
              title="No workers ready for this requirement"
              detail="Check the blocked list below to see what needs fixing."
            />
          ) : null}

          {assignableMatches.length ? (
            <WorkerGroup title="Ready to assign" count={assignableMatches.length} countTone="ready">
              {visibleReadyToAssignMatches.length ? (
                visibleReadyToAssignMatches.map((worker) => (
                  <WorkerCard
                    key={worker.worker_profile_id}
                    worker={worker}
                    selected={selectedWorkerIds.includes(String(worker.worker_profile_id))}
                    onSelect={() => toggleWorker(worker.worker_profile_id)}
                    badge={worker.has_interest ? "Interested" : undefined}
                  />
                ))
              ) : (
                <div className="px-4 py-4 text-[13px] text-[oklch(0.48_0.005_145)]">No ready workers match this search.</div>
              )}
            </WorkerGroup>
          ) : null}

          {blockedMatches.length ? (
            <WorkerGroup title="Blocked" count={blockedMatches.length} countTone="blocked">
              {visibleBlockedMatches.length ? (
                visibleBlockedMatches.slice(0, 8).map((worker) => (
                  <BlockedWorkerCard key={worker.worker_profile_id} worker={worker} />
                ))
              ) : (
                <div className="px-4 py-4 text-[13px] text-[oklch(0.48_0.005_145)]">No blocked workers match this search.</div>
              )}
            </WorkerGroup>
          ) : null}
        </section>

        {/* Assignment details sidebar */}
        <aside className="lg:sticky lg:top-0 lg:self-start">
          <div className="rounded-xl border border-[oklch(0.90_0.003_145)] bg-white">
            <div className="flex items-center justify-between border-b border-[oklch(0.90_0.003_145)] px-5 py-4">
              <div>
                <p className="text-[14px] font-semibold text-[oklch(0.20_0.006_145)]">Assignment details</p>
                <p className="mt-0.5 text-[13px] text-[oklch(0.44_0.005_145)]">Applied to every selected worker</p>
              </div>
              {selectedWorkerIds.length > 0 && (
                <span className="rounded-full bg-[oklch(0.91_0.026_145)] px-3 py-1 text-[12px] font-semibold text-[oklch(0.34_0.094_145)]">
                  {selectedWorkerIds.length} selected
                </span>
              )}
            </div>

            {/* Selected workers */}
            <div className="px-5 pt-4 pb-3">
              {selectedWorkers.length ? (
                <div className="flex flex-wrap gap-1.5">
                  {selectedWorkers.map((worker) => (
                    <button
                      key={worker.worker_profile_id}
                      type="button"
                      onClick={() => toggleWorker(worker.worker_profile_id)}
                      className="inline-flex items-center gap-1 rounded-full border border-[oklch(0.90_0.003_145)] bg-[oklch(0.97_0.008_145)] px-2.5 py-1 text-[12px] font-medium text-[oklch(0.38_0.005_145)] transition hover:border-[oklch(0.42_0.115_145)] hover:text-[oklch(0.20_0.006_145)]"
                    >
                      {worker.full_name}
                      <X className="size-3" />
                    </button>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-[oklch(0.90_0.003_145)] bg-[oklch(0.97_0.008_145)] px-4 py-3.5 text-center text-[13px] text-[oklch(0.48_0.005_145)]">
                  Select workers from the list to begin
                </div>
              )}
            </div>

            {/* Role & shift */}
            <div className="space-y-3 border-t border-[oklch(0.90_0.003_145)] px-5 py-4">
              <Field label="Role">
                <FormSelect value={assignedRole} onChange={(e) => setAssignedRole(e.target.value)}>
                  {roleOptions.map((role) => (
                    <option key={role} value={role}>{role}</option>
                  ))}
                </FormSelect>
                {assignedRole === "Other" && (
                  <FormInput
                    className="mt-2"
                    value={customRole}
                    onChange={(e) => setCustomRole(e.target.value)}
                    placeholder="Enter custom role"
                  />
                )}
              </Field>
              <Field label="Shift">
                <FormSelect value={assignedShift} onChange={(e) => setAssignedShift(e.target.value)}>
                  {shiftOptions.map((shift) => (
                    <option key={shift} value={shift}>{shift}</option>
                  ))}
                </FormSelect>
                {assignedShift === "Other" && (
                  <FormInput
                    className="mt-2"
                    value={customShift}
                    onChange={(e) => setCustomShift(e.target.value)}
                    placeholder="Enter custom shift"
                  />
                )}
              </Field>
            </div>

            {/* Pay */}
            <div className="border-t border-[oklch(0.90_0.003_145)] px-5 py-4">
              <Field label="Daily rate">
                <FormSelect value={salaryMode} onChange={(e) => setSalaryMode(e.target.value)}>
                  {salaryOptions.map((option) => (
                    <option key={option.value || "none"} value={option.value}>{option.label}</option>
                  ))}
                  <option value="custom">Custom amount</option>
                </FormSelect>
                {salaryMode === "custom" && (
                  <div className="relative mt-2">
                    <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 font-mono text-[13px] text-[oklch(0.48_0.005_145)]">₹</span>
                    <input
                      type="number"
                      min="0"
                      step="1"
                      className="h-11 w-full rounded-xl border border-[oklch(0.90_0.003_145)] bg-white py-0 pl-8 pr-3 font-mono text-[14px] text-[oklch(0.20_0.006_145)] outline-none transition focus:border-[oklch(0.42_0.115_145)] focus:ring-2 focus:ring-[oklch(0.42_0.115_145)]/20"
                      value={salaryAmount}
                      onChange={(e) => setSalaryAmount(e.target.value)}
                      placeholder="0"
                    />
                  </div>
                )}
                <p className="mt-1.5 text-[12px] text-[oklch(0.48_0.005_145)]">
                  Per day — payroll calculates gross as daily rate × days worked.
                </p>
              </Field>
            </div>

            {/* Work period */}
            <div className="border-t border-[oklch(0.90_0.003_145)] px-5 py-4">
              <p className="mb-3 text-[13px] font-medium text-[oklch(0.38_0.005_145)]">Work period</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="mb-1.5 text-[12px] text-[oklch(0.48_0.005_145)]">Starts</p>
                  <input
                    type="date"
                    className="h-11 w-full rounded-xl border border-[oklch(0.90_0.003_145)] bg-white px-3 font-mono text-[13px] text-[oklch(0.20_0.006_145)] outline-none transition focus:border-[oklch(0.42_0.115_145)] focus:ring-2 focus:ring-[oklch(0.42_0.115_145)]/20"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    min={reqMinDate}
                    max={reqMaxDate}
                  />
                </div>
                <div>
                  <p className="mb-1.5 text-[12px] text-[oklch(0.48_0.005_145)]">Ends</p>
                  <input
                    type="date"
                    className="h-11 w-full rounded-xl border border-[oklch(0.90_0.003_145)] bg-white px-3 font-mono text-[13px] text-[oklch(0.20_0.006_145)] outline-none transition focus:border-[oklch(0.42_0.115_145)] focus:ring-2 focus:ring-[oklch(0.42_0.115_145)]/20"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    min={startDate || reqMinDate}
                    max={reqMaxDate}
                  />
                </div>
              </div>
              {reqMinDate && reqMaxDate ? (
                <p className="mt-2 font-mono text-[12px] text-[oklch(0.48_0.005_145)]">
                  Job window: {reqMinDate} → {reqMaxDate}
                </p>
              ) : (
                <p className="mt-2 text-[12px] text-[oklch(0.48_0.005_145)]">
                  Check-in is blocked outside this window.
                </p>
              )}
            </div>

            {/* Notes */}
            <div className="border-t border-[oklch(0.90_0.003_145)] px-5 py-4">
              <Field label="Notes">
                <textarea
                  className="min-h-[88px] w-full resize-none rounded-xl border border-[oklch(0.90_0.003_145)] bg-white px-3 py-2.5 text-[14px] text-[oklch(0.20_0.006_145)] outline-none transition placeholder:text-[oklch(0.62_0.004_145)] focus:border-[oklch(0.42_0.115_145)] focus:ring-2 focus:ring-[oklch(0.42_0.115_145)]/20"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add notes for this assignment"
                />
              </Field>
            </div>

            {/* Footer: message + submit */}
            <div className="border-t border-[oklch(0.90_0.003_145)] px-5 py-4">
              {message && (
                <div
                  className={`mb-3 rounded-xl px-3.5 py-2.5 text-[13px] ${
                    message.toLowerCase().includes("successfully")
                      ? "bg-[#F0FDF4] text-[#15803D]"
                      : "bg-[#FFF1F2] text-[#B91C1C]"
                  }`}
                >
                  {message}
                </div>
              )}
              <Button
                type="submit"
                disabled={loading || !selectedWorkerIds.length}
                variant="accent"
                className="w-full"
              >
                {loading
                  ? "Assigning..."
                  : selectedWorkerIds.length > 1
                    ? `Assign ${selectedWorkerIds.length} Workers`
                    : "Assign Worker"}
              </Button>
            </div>
          </div>
        </aside>
      </div>
    </form>
  );
}

function WorkerGroup({
  title,
  count,
  countTone,
  children,
}: {
  title: string;
  count: number;
  countTone: "ready" | "blocked";
  children: ReactNode;
}) {
  const pillClass =
    countTone === "ready"
      ? "bg-[oklch(0.91_0.026_145)] text-[oklch(0.34_0.094_145)]"
      : "bg-[#FEF3C7] text-[#B45309]";

  return (
    <div className="overflow-hidden rounded-xl border border-[oklch(0.90_0.003_145)]">
      <div className="flex items-center gap-2 bg-[oklch(0.97_0.008_145)] px-4 py-2.5">
        <p className="text-[13px] font-semibold text-[oklch(0.20_0.006_145)]">{title}</p>
        <span className={`rounded-full px-2 py-0.5 text-[12px] font-medium ${pillClass}`}>{count}</span>
      </div>
      <div className="divide-y divide-[oklch(0.95_0.013_145)] bg-white">
        {children}
      </div>
    </div>
  );
}

function Stat({
  dot,
  value,
  label,
}: {
  dot: string;
  value: number;
  label: string;
}) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={`size-2 rounded-full ${dot}`} />
      <span className="text-[13px] font-semibold text-[oklch(0.20_0.006_145)]">{value}</span>
      <span className="text-[13px] text-[oklch(0.44_0.005_145)]">{label}</span>
    </span>
  );
}

function EmptyGroup({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-[oklch(0.90_0.003_145)] bg-white p-4 text-[13px] text-[oklch(0.48_0.005_145)]">
      {children}
    </div>
  );
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="rounded-xl border border-dashed border-[oklch(0.90_0.003_145)] bg-[oklch(0.97_0.008_145)] px-5 py-6 text-center">
      <p className="text-[14px] font-medium text-[oklch(0.38_0.005_145)]">{title}</p>
      <p className="mt-1 text-[13px] text-[oklch(0.48_0.005_145)]">{detail}</p>
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
  const initials = worker.full_name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const signalReasons = worker.reasons.filter(
    (r) => r !== "interested" && r !== "document_expired",
  );

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors ${
        selected
          ? "bg-[oklch(0.95_0.013_145)]"
          : "bg-white hover:bg-[oklch(0.97_0.008_145)]"
      }`}
    >
      <div
        className={`flex size-8 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold transition-colors ${
          selected
            ? "bg-[oklch(0.42_0.115_145)] text-white"
            : "bg-[oklch(0.91_0.026_145)] text-[oklch(0.34_0.094_145)]"
        }`}
      >
        {selected ? <Check className="size-3.5" /> : initials}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <p className="text-[14px] font-semibold text-[oklch(0.20_0.006_145)]">
            {worker.full_name}
          </p>
          {badge && (
            <span className="rounded-full bg-[#DCFCE7] px-1.5 py-0.5 text-[11px] font-medium text-[#15803D]">
              {badge}
            </span>
          )}
          {(worker.expired_documents?.length ?? 0) > 0 && (
            <span className="rounded-full bg-[#FEF3C7] px-1.5 py-0.5 text-[11px] font-medium text-[#B45309]">
              Doc expired
            </span>
          )}
        </div>
        <p className="mt-0.5 text-[12px] text-[oklch(0.44_0.005_145)]">
          {worker.city}, {worker.state}
          {signalReasons.length > 0 && (
            <> · {signalReasons.join(" · ")}</>
          )}
        </p>
      </div>
      <span className="shrink-0 font-mono text-[12px] text-[oklch(0.62_0.004_145)]">
        {worker.score}
      </span>
    </button>
  );
}

function BlockedWorkerCard({ worker }: { worker: WorkerMatch }) {
  const reason = getBlockedReason(worker);
  const fix = getBlockedFix(worker, reason);

  const initials = worker.full_name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="flex items-start gap-3 bg-white px-4 py-3.5">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-[oklch(0.90_0.003_145)] text-[12px] font-semibold text-[oklch(0.48_0.005_145)]">
        {initials}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <p className="text-[14px] font-semibold text-[oklch(0.20_0.006_145)]">{worker.full_name}</p>
          <span className="shrink-0 font-mono text-[12px] text-[oklch(0.62_0.004_145)]">{worker.score}</span>
        </div>
        <p className="mt-0.5 text-[12px] text-[oklch(0.44_0.005_145)]">
          {worker.city}, {worker.state}
        </p>
        <div className="mt-2 flex items-start gap-2">
          <span className="shrink-0 rounded-full bg-[#FEF3C7] px-2 py-0.5 text-[11px] font-medium text-[#B45309]">
            {reason}
          </span>
          <p className="text-[12px] leading-relaxed text-[oklch(0.48_0.005_145)]">{fix}</p>
        </div>
      </div>
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
        label: `70% of client rate — Rs. ${Math.round(ratePerWorker * 0.7).toLocaleString("en-IN")} / day`,
        value: String(Math.round(ratePerWorker * 0.7)),
      },
      {
        label: `80% of client rate — Rs. ${Math.round(ratePerWorker * 0.8).toLocaleString("en-IN")} / day`,
        value: String(Math.round(ratePerWorker * 0.8)),
      },
      {
        label: `90% of client rate — Rs. ${Math.round(ratePerWorker * 0.9).toLocaleString("en-IN")} / day`,
        value: String(Math.round(ratePerWorker * 0.9)),
      },
    );
  }

  presets.push(
    { label: "Rs. 300 / day", value: "300" },
    { label: "Rs. 400 / day", value: "400" },
    { label: "Rs. 500 / day", value: "500" },
    { label: "Rs. 600 / day", value: "600" },
    { label: "Rs. 700 / day", value: "700" },
    { label: "Rs. 800 / day", value: "800" },
  );

  return presets;
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <label className="mb-1.5 block text-[13px] font-medium text-[oklch(0.38_0.005_145)]">
        {label}
      </label>
      {children}
    </div>
  );
}

function FormSelect({
  value,
  onChange,
  children,
}: {
  value?: string;
  onChange?: React.ChangeEventHandler<HTMLSelectElement>;
  children: ReactNode;
}) {
  return (
    <select
      value={value}
      onChange={onChange}
      className="h-11 w-full rounded-xl border border-[oklch(0.90_0.003_145)] bg-white px-3 text-[14px] text-[oklch(0.20_0.006_145)] outline-none transition focus:border-[oklch(0.42_0.115_145)] focus:ring-2 focus:ring-[oklch(0.42_0.115_145)]/20"
    >
      {children}
    </select>
  );
}

function FormInput({
  className = "",
  ...props
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`h-11 w-full rounded-xl border border-[oklch(0.90_0.003_145)] bg-white px-3 text-[14px] text-[oklch(0.20_0.006_145)] outline-none transition placeholder:text-[oklch(0.62_0.004_145)] focus:border-[oklch(0.42_0.115_145)] focus:ring-2 focus:ring-[oklch(0.42_0.115_145)]/20 ${className}`}
    />
  );
}
