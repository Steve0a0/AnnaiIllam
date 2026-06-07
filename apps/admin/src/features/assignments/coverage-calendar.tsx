"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, Search, X } from "lucide-react";
import { assignmentsService, type CoverageDay } from "@/services/assignments.service";
import { getErrorMessage } from "@/lib/get-error-message";
import type { WorkerMatch } from "@/types/assignment";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

function isAssignableWorker(w: WorkerMatch, requirementId: number) {
  // A conflict with the same requirement is not a blocker — the worker can cover
  // multiple days on the same requirement. Only block cross-requirement conflicts.
  const hasBlockingConflict =
    w.conflict != null && w.conflict.requirement_id !== requirementId;
  return (
    w.is_available &&
    ["approved", "verified"].includes(w.verification_status) &&
    !w.reasons.some((r) => r.startsWith("not available")) &&
    !hasBlockingConflict
  );
}

export default function CoverageCalendar({
  requirementId,
  requiredPerDay,
  canAssign = false,
}: {
  requirementId: number;
  requiredPerDay: number;
  canAssign?: boolean;
}) {
  const [selectedDays, setSelectedDays] = useState<Set<string>>(new Set());
  const [lastClickedDay, setLastClickedDay] = useState<string | null>(null);
  const [showAssignPanel, setShowAssignPanel] = useState(false);
  const [assigningId, setAssigningId] = useState<number | null>(null);
  const [assignProgress, setAssignProgress] = useState<{ done: number; total: number } | null>(null);
  const [assignError, setAssignError] = useState("");
  const [workerSearch, setWorkerSearch] = useState("");
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["coverage-calendar", requirementId],
    queryFn: () => assignmentsService.getCoverageCalendar(requirementId),
    staleTime: 30_000,
  });

  const { data: matchesData, isLoading: matchesLoading } = useQuery({
    queryKey: ["worker-matches", requirementId],
    queryFn: () => assignmentsService.getWorkerMatches(requirementId),
    enabled: showAssignPanel,
    staleTime: 0,
  });

  const days = data?.data?.days ?? [];

  const uncoveredCount = days.filter((d) => d.coverage_status === "uncovered").length;
  const partialCount = days.filter((d) => d.coverage_status === "partial").length;
  const fullCount = days.filter((d) => d.coverage_status === "full").length;

  const weeks = useMemo<(CoverageDay | null)[][]>(() => {
    const result: (CoverageDay | null)[][] = [];
    for (let i = 0; i < days.length; i += 7) {
      const chunk: (CoverageDay | null)[] = [...days.slice(i, i + 7)];
      while (chunk.length < 7) chunk.push(null);
      result.push(chunk);
    }
    return result;
  }, [days]);

  const selectedDaysArray = useMemo(
    () => Array.from(selectedDays).sort(),
    [selectedDays],
  );

  // Detail panel driven by last clicked day
  const focusedDayData = days.find((d) => d.date === lastClickedDay) ?? null;

  // Exclude workers already covering the focused day
  const alreadyCoveringIds = new Set(
    focusedDayData?.workers.map((w) => w.worker_profile_id) ?? []
  );
  const allMatches = matchesData?.data ?? [];
  const normalizedSearch = workerSearch.trim().toLowerCase();
  const availableWorkers = allMatches
    .filter((w) => isAssignableWorker(w, requirementId) && !alreadyCoveringIds.has(w.worker_profile_id))
    .filter((w) =>
      normalizedSearch
        ? [w.full_name, w.category, w.city].join(" ").toLowerCase().includes(normalizedSearch)
        : true
    );

  function toggleDay(date: string) {
    setSelectedDays((prev) => {
      const next = new Set(prev);
      if (next.has(date)) {
        next.delete(date);
      } else {
        next.add(date);
      }
      return next;
    });
    setLastClickedDay(date);
    setShowAssignPanel(false);
    setAssignError("");
    setWorkerSearch("");
  }

  function clearSelection() {
    setSelectedDays(new Set());
    setLastClickedDay(null);
    setShowAssignPanel(false);
    setAssignError("");
    setWorkerSearch("");
  }

  async function handleAssignWorker(workerProfileId: number) {
    if (selectedDaysArray.length === 0) return;
    setAssigningId(workerProfileId);
    setAssignError("");
    setAssignProgress({ done: 0, total: selectedDaysArray.length });
    const errors: string[] = [];
    for (let i = 0; i < selectedDaysArray.length; i++) {
      try {
        await assignmentsService.createAssignment({
          requirement_id: requirementId,
          worker_profile_id: workerProfileId,
          start_date: selectedDaysArray[i],
          end_date: selectedDaysArray[i],
        });
      } catch (err) {
        errors.push(`${selectedDaysArray[i]}: ${getErrorMessage(err)}`);
      }
      setAssignProgress({ done: i + 1, total: selectedDaysArray.length });
    }
    await queryClient.invalidateQueries({ queryKey: ["coverage-calendar", requirementId] });
    await queryClient.invalidateQueries({ queryKey: ["requirement-assignments", requirementId] });
    await queryClient.invalidateQueries({ queryKey: ["worker-matches", requirementId] });
    if (errors.length > 0) {
      setAssignError(errors.join(" · "));
    } else {
      setShowAssignPanel(false);
      setWorkerSearch("");
      setSelectedDays(new Set());
      setLastClickedDay(null);
    }
    setAssignProgress(null);
    setAssigningId(null);
  }

  return (
    <Card className="overflow-hidden">
      {/* Header */}
      <CardHeader className="flex flex-row items-center justify-between space-y-0 border-b px-5 py-4">
        <div>
          <CardTitle className="text-[15px]">Coverage calendar</CardTitle>
          <CardDescription className="mt-0.5 text-[13px]">
            {requiredPerDay} worker{requiredPerDay !== 1 ? "s" : ""} needed per day
            {days.length > 0 ? ` · ${days.length} days total` : ""}
            {selectedDays.size > 0 ? ` · ${selectedDays.size} day${selectedDays.size !== 1 ? "s" : ""} selected` : ""}
          </CardDescription>
        </div>
        <div className="flex items-center gap-2">
          {selectedDays.size > 0 && (
            <Button variant="outline" size="sm" onClick={clearSelection} className="h-7 gap-1 text-[12px]">
              <X className="size-3" /> Clear
            </Button>
          )}
          {!isLoading && days.length > 0 && (
            <>
              {fullCount > 0 && (
                <Badge variant="outline" className="bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]">
                  {fullCount} covered
                </Badge>
              )}
              {partialCount > 0 && (
                <Badge variant="outline" className="bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]">
                  {partialCount} partial
                </Badge>
              )}
              {uncoveredCount > 0 && (
                <Badge variant="outline" className="bg-[#FEE2E2] text-[#B91C1C] border-[#FECACA]">
                  {uncoveredCount} uncovered
                </Badge>
              )}
            </>
          )}
        </div>
      </CardHeader>

      {/* Body */}
      {isLoading ? (
        <CardContent className="px-5 py-6">
          <p className="text-[13px] text-muted-foreground">Loading coverage…</p>
        </CardContent>
      ) : days.length === 0 ? (
        <CardContent className="px-5 py-6">
          <p className="text-[13px] text-muted-foreground">No days to display.</p>
        </CardContent>
      ) : (
        <CardContent className="p-4">
          {/* Hint */}
          {canAssign && selectedDays.size === 0 && (
            <p className="mb-3 text-xs text-muted-foreground">
              Click one or more days to select, then assign a worker to all of them at once.
            </p>
          )}

          {/* Heatmap grid */}
          <div className="space-y-1">
            {weeks.map((week, wi) => (
              <div key={wi} className="grid grid-cols-7 gap-1">
                {week.map((day, di) =>
                  day ? (
                    <DayCell
                      key={day.date}
                      day={day}
                      selected={selectedDays.has(day.date)}
                      onSelect={() => toggleDay(day.date)}
                    />
                  ) : (
                    <div key={`pad-${wi}-${di}`} className="rounded-lg bg-muted" />
                  )
                )}
              </div>
            ))}
          </div>

          {/* Detail panel — shown when any days selected */}
          {selectedDays.size > 0 && (
            <Card className="mt-3">
              <CardContent className="p-4">
                {/* Selected days header */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-foreground">
                    {selectedDays.size === 1
                      ? formatLongDate(selectedDaysArray[0])
                      : `${selectedDays.size} days selected`}
                  </p>
                  <div className="flex items-center gap-2">
                    {focusedDayData && (
                      <Badge
                        variant="outline"
                        className={
                          focusedDayData.coverage_status === "full"
                            ? "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]"
                            : focusedDayData.coverage_status === "partial"
                              ? "bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]"
                              : "bg-[#FEE2E2] text-[#B91C1C] border-[#FECACA]"
                        }
                      >
                        {focusedDayData.covering_count}/{focusedDayData.required} assigned
                      </Badge>
                    )}
                    {canAssign && (
                      <Button
                        variant={showAssignPanel ? "secondary" : "default"}
                        size="sm"
                        className="h-7 gap-1 text-[12px]"
                        onClick={() => {
                          setShowAssignPanel((p) => !p);
                          setAssignError("");
                          setWorkerSearch("");
                        }}
                      >
                        {showAssignPanel ? (
                          <><X className="size-3" /> Close</>
                        ) : (
                          <><Plus className="size-3" /> Assign</>
                        )}
                      </Button>
                    )}
                  </div>
                </div>

                {/* Selected day chips (multi-select mode) */}
                {selectedDays.size > 1 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {selectedDaysArray.map((date) => (
                      <Badge key={date} variant="secondary" className="gap-1 pr-1.5">
                        {formatShortDate(date)}
                        <button
                          type="button"
                          onClick={() => toggleDay(date)}
                          className="ml-0.5 rounded-full opacity-60 hover:opacity-100"
                        >
                          <X className="size-2.5" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}

                {/* Workers on focused day */}
                {focusedDayData && (
                  <div className="mt-3">
                    {focusedDayData.workers.length === 0 ? (
                      <p className="text-xs text-muted-foreground">
                        No workers on {formatShortDate(focusedDayData.date)}.
                      </p>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {focusedDayData.workers.map((w) => (
                          <WorkerChip key={w.assignment_id} name={w.worker_name} status={w.status} />
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Assign panel */}
                {showAssignPanel && canAssign && (
                  <>
                    <Separator className="my-3" />
                    <div className="space-y-2.5">
                      <p className="text-xs font-medium text-muted-foreground">
                        {selectedDays.size === 1
                          ? "Assign a worker for this day"
                          : `Assign a worker for all ${selectedDays.size} selected days`}
                      </p>
                      <div className="relative">
                        <Search className="pointer-events-none absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
                        <Input
                          value={workerSearch}
                          onChange={(e) => setWorkerSearch(e.target.value)}
                          placeholder="Search workers…"
                          className="h-8 pl-8 text-sm"
                        />
                      </div>
                      {assignError && (
                        <p className="rounded-lg bg-[#FEE2E2] px-3 py-2 text-xs text-[#B91C1C]">
                          {assignError}
                        </p>
                      )}
                      {matchesLoading ? (
                        <div className="flex items-center gap-2 py-2 text-xs text-muted-foreground">
                          <Loader2 className="size-3.5 animate-spin" /> Loading workers…
                        </div>
                      ) : availableWorkers.length === 0 ? (
                        <p className="rounded-lg border border-dashed px-3 py-3 text-xs text-muted-foreground">
                          No available workers found.
                        </p>
                      ) : (
                        <ScrollArea className="h-52">
                          <div className="space-y-1 pr-3">
                            {availableWorkers.map((w) => {
                              const isAssigning = assigningId === w.worker_profile_id;
                              return (
                                <button
                                  key={w.worker_profile_id}
                                  type="button"
                                  disabled={assigningId !== null}
                                  onClick={() => handleAssignWorker(w.worker_profile_id)}
                                  className="flex w-full items-center justify-between gap-3 rounded-lg border bg-card px-3 py-2 text-left text-sm transition hover:border-primary hover:bg-accent disabled:opacity-50"
                                >
                                  <div className="flex items-center gap-2.5">
                                    <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-[oklch(0.91_0.026_145)] text-[11px] font-semibold text-[oklch(0.34_0.094_145)]">
                                      {w.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
                                    </div>
                                    <div>
                                      <p className="font-semibold text-foreground">{w.full_name}</p>
                                      <p className="text-xs text-muted-foreground">
                                        {w.category} · {w.city}
                                      </p>
                                    </div>
                                  </div>
                                  <div className="flex shrink-0 items-center gap-2">
                                    {w.has_interest && (
                                      <Badge variant="outline" className="bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0] text-[10px]">
                                        Interested
                                      </Badge>
                                    )}
                                    {isAssigning ? (
                                      <div className="flex items-center gap-1 text-xs text-primary">
                                        <Loader2 className="size-3.5 animate-spin" />
                                        {assignProgress && `${assignProgress.done}/${assignProgress.total}`}
                                      </div>
                                    ) : (
                                      <Plus className="size-3.5 text-muted-foreground" />
                                    )}
                                  </div>
                                </button>
                              );
                            })}
                          </div>
                        </ScrollArea>
                      )}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          )}
        </CardContent>
      )}
    </Card>
  );
}

function formatShortDate(dateStr: string) {
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
  }).format(new Date(dateStr + "T00:00:00"));
}

function formatLongDate(dateStr: string) {
  return new Intl.DateTimeFormat("en-IN", {
    weekday: "short",
    day: "2-digit",
    month: "short",
  }).format(new Date(dateStr + "T00:00:00"));
}

function DayCell({
  day,
  selected,
  onSelect,
}: {
  day: CoverageDay;
  selected: boolean;
  onSelect: () => void;
}) {
  const date = new Date(day.date + "T00:00:00");
  const dayNum = date.getDate();
  const showMonth = dayNum === 1;

  const bgCls =
    day.coverage_status === "full"
      ? "bg-[#DCFCE7]"
      : day.coverage_status === "partial"
        ? "bg-[#FEF3C7]"
        : "bg-[#FEE2E2]";

  const textCls =
    day.coverage_status === "full"
      ? "text-[#15803D]"
      : day.coverage_status === "partial"
        ? "text-[#B45309]"
        : "text-[#B91C1C]";

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`${bgCls} flex flex-col items-center justify-center rounded-lg py-2.5 transition-opacity hover:opacity-80 ${
        selected ? "ring-2 ring-[oklch(0.42_0.115_145)] ring-offset-1" : ""
      }`}
    >
      {showMonth && (
        <span className="mb-0.5 text-[8px] font-bold uppercase leading-none tracking-wide text-[oklch(0.48_0.005_145)]">
          {date.toLocaleString("en-IN", { month: "short" })}
        </span>
      )}
      <span className={`text-[15px] font-bold leading-none ${textCls}`}>
        {String(dayNum).padStart(2, "0")}
      </span>
      <span className={`mt-1 font-mono text-[10px] leading-none opacity-80 ${textCls}`}>
        {day.covering_count}/{day.required}
      </span>
    </button>
  );
}

function WorkerChip({ name, status }: { name: string; status: string }) {
  const active = ["accepted", "active", "completed"].includes(status);
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[12px] font-medium ${
        active
          ? "bg-[#DCFCE7] text-[#15803D]"
          : "bg-[oklch(0.93_0.003_145)] text-[oklch(0.44_0.005_145)]"
      }`}
    >
      <span className={`size-1.5 rounded-full ${active ? "bg-[#15803D]" : "bg-[oklch(0.62_0.004_145)]"}`} />
      {name}
    </span>
  );
}
