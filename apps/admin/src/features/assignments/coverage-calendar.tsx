"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CalendarDays, ChevronDown, ChevronUp } from "lucide-react";
import { assignmentsService, type CoverageDay } from "@/services/assignments.service";

export default function CoverageCalendar({
  requirementId,
  requiredPerDay,
}: {
  requirementId: number;
  requiredPerDay: number;
}) {
  const [expandedDay, setExpandedDay] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["coverage-calendar", requirementId],
    queryFn: () => assignmentsService.getCoverageCalendar(requirementId),
    staleTime: 30_000,
  });

  const days = data?.data?.days ?? [];

  const uncoveredCount = days.filter((d) => d.coverage_status === "uncovered").length;
  const partialCount = days.filter((d) => d.coverage_status === "partial").length;
  const fullCount = days.filter((d) => d.coverage_status === "full").length;

  return (
    <section className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
      <div className="border-b border-border bg-[#FAFAF9] px-5 py-5">
        <div className="flex items-start gap-4">
          <div className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-[#EFF6FF] text-[#1D4ED8]">
            <CalendarDays className="size-5" />
          </div>
          <div className="flex-1">
            <h3 className="font-display text-xl font-semibold text-foreground">
              Coverage calendar
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Day-by-day view of confirmed worker coverage. Needs {requiredPerDay} worker
              {requiredPerDay !== 1 ? "s" : ""} per day.
            </p>
            {!isLoading && days.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-3">
                <Pill color="green" label={`${fullCount} fully covered`} />
                {partialCount > 0 && <Pill color="yellow" label={`${partialCount} partial`} />}
                {uncoveredCount > 0 && <Pill color="red" label={`${uncoveredCount} uncovered`} />}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="p-5">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading coverage…</p>
        ) : days.length === 0 ? (
          <p className="text-sm text-muted-foreground">No days to display.</p>
        ) : (
          <div className="space-y-1.5">
            {days.map((day) => (
              <DayRow
                key={day.date}
                day={day}
                expanded={expandedDay === day.date}
                onToggle={() =>
                  setExpandedDay(expandedDay === day.date ? null : day.date)
                }
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function DayRow({
  day,
  expanded,
  onToggle,
}: {
  day: CoverageDay;
  expanded: boolean;
  onToggle: () => void;
}) {
  const barColor =
    day.coverage_status === "full"
      ? "bg-[#1A6640]"
      : day.coverage_status === "partial"
        ? "bg-[#B45309]"
        : "bg-[#B91C1C]";

  const bgColor =
    day.coverage_status === "full"
      ? "bg-[#F0FDF4]"
      : day.coverage_status === "partial"
        ? "bg-[#FFFBEB]"
        : "bg-[#FFF5F5]";

  const textColor =
    day.coverage_status === "full"
      ? "text-[#15803D]"
      : day.coverage_status === "partial"
        ? "text-[#B45309]"
        : "text-[#B91C1C]";

  const fillPct = day.required > 0
    ? Math.min(100, Math.round((day.confirmed_count / day.required) * 100))
    : 0;

  const dateLabel = new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    weekday: "short",
  }).format(new Date(day.date));

  return (
    <div className={`overflow-hidden rounded-lg border border-border ${bgColor}`}>
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center gap-4 px-4 py-3 text-left"
      >
        <span className="w-28 shrink-0 font-mono text-xs font-medium text-foreground">
          {dateLabel}
        </span>
        <div className="flex-1">
          <div className="h-2 overflow-hidden rounded-full bg-[#E7E5E4]">
            <div
              className={`h-full rounded-full transition-all ${barColor}`}
              style={{ width: `${fillPct}%` }}
            />
          </div>
        </div>
        <span className={`w-24 shrink-0 text-right text-xs font-semibold ${textColor}`}>
          {day.confirmed_count}/{day.required} confirmed
        </span>
        <span className="text-muted-foreground">
          {expanded ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
        </span>
      </button>

      {expanded && day.workers.length > 0 && (
        <div className="border-t border-border px-4 pb-3 pt-2">
          <div className="flex flex-wrap gap-2">
            {day.workers.map((w) => (
              <WorkerChip key={w.assignment_id} name={w.worker_name} status={w.status} />
            ))}
          </div>
          {day.checked_in_count > 0 && (
            <p className="mt-2 text-xs text-muted-foreground">
              {day.checked_in_count} checked in today
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function WorkerChip({ name, status }: { name: string; status: string }) {
  const confirmed = ["accepted", "active", "completed"].includes(status);
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
        confirmed
          ? "bg-[#DCFCE7] text-[#15803D]"
          : "bg-[#F5F5F4] text-[#78716C]"
      }`}
    >
      <span
        className={`size-1.5 rounded-full ${confirmed ? "bg-[#15803D]" : "bg-[#A8A29E]"}`}
      />
      {name}
    </span>
  );
}

function Pill({ color, label }: { color: "green" | "yellow" | "red"; label: string }) {
  const cls = {
    green: "bg-[#DCFCE7] text-[#15803D]",
    yellow: "bg-[#FEF3C7] text-[#B45309]",
    red: "bg-[#FEE2E2] text-[#B91C1C]",
  }[color];
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${cls}`}>
      {label}
    </span>
  );
}
