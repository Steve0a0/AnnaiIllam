"use client";

import { RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Select from "@/components/ui/select";
import type { ReportFilters } from "@/types/report";

type StatusOption = {
  label: string;
  value: string;
};

type ReportFiltersProps = {
  filters: ReportFilters;
  statusOptions: StatusOption[];
  onChange: (filters: ReportFilters) => void;
};

const allStatusesValue = "__all__";

export default function ReportFilters({
  filters,
  statusOptions,
  onChange,
}: ReportFiltersProps) {
  const updateFilter = (key: keyof ReportFilters, value: string) => {
    onChange({
      ...filters,
      [key]: value || undefined,
    });
  };

  const resetFilters = () => onChange({});

  return (
    <div className="grid gap-3 rounded-xl border border-border bg-card p-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_auto] md:items-end">
      <Input
        label="From date"
        type="date"
        value={filters.from_date ?? ""}
        onChange={(event) => updateFilter("from_date", event.target.value)}
      />
      <Input
        label="To date"
        type="date"
        value={filters.to_date ?? ""}
        onChange={(event) => updateFilter("to_date", event.target.value)}
      />
      <Select
        label="Status"
        value={filters.status ?? allStatusesValue}
        onChange={(value) =>
          updateFilter("status", value === allStatusesValue ? "" : value)
        }
        options={[
          { label: "All statuses", value: allStatusesValue },
          ...statusOptions,
        ]}
      />
      <Button type="button" variant="secondary" onClick={resetFilters}>
        <RotateCcw />
        Reset
      </Button>
    </div>
  );
}
