"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, ShieldAlert } from "lucide-react";
import { Input } from "@/components/ui/input";
import { auditService } from "@/services/audit.service";
import type { AuditLogItem } from "@/types/audit";

// ─── Helpers ────────────────────────────────────────────────────────────────

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  return `${d}d ago`;
}

function fullDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

type ActionCategory = "auth" | "password" | "write" | "delete" | "system";

function categorise(action: string): ActionCategory {
  if (/login|logout|token|otp|session/.test(action)) return "auth";
  if (/password/.test(action)) return "password";
  if (/delete|remove|revoke|deactivate/.test(action)) return "delete";
  if (/create|update|assign|edit|add|mark|set|send|approve|reject|disburse/.test(action)) return "write";
  return "system";
}

const CATEGORY_STYLES: Record<ActionCategory, { bg: string; text: string; label: string }> = {
  auth:     { bg: "var(--color-brand-50)",  text: "var(--color-brand-700)", label: "Auth"     },
  password: { bg: "#fefce8",               text: "#854d0e",                label: "Password"  },
  write:    { bg: "#f0fdf4",               text: "#166534",                label: "Write"     },
  delete:   { bg: "#fef2f2",               text: "#991b1b",                label: "Delete"    },
  system:   { bg: "#f8fafc",               text: "#475569",                label: "System"    },
};

function ActionBadge({ action }: { action: string }) {
  const cat = categorise(action);
  const style = CATEGORY_STYLES[cat];
  return (
    <span
      className="inline-block rounded-full px-2 py-0.5 text-xs font-medium"
      style={{ background: style.bg, color: style.text }}
    >
      {action.replace(/_/g, " ")}
    </span>
  );
}

function DetailsView({ details }: { details: Record<string, unknown> }) {
  const entries = Object.entries(details);
  if (entries.length === 0) return <span className="text-xs text-muted-foreground">—</span>;

  return (
    <div className="flex flex-wrap gap-1.5">
      {entries.map(([k, v]) => (
        <span
          key={k}
          className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs"
          style={{ background: "var(--color-brand-50)" }}
        >
          <span className="font-medium" style={{ color: "var(--color-brand-700)" }}>
            {k.replace(/_/g, " ")}
          </span>
          <span className="text-muted-foreground">
            {v === null || v === undefined ? "—" : String(v)}
          </span>
        </span>
      ))}
    </div>
  );
}

// ─── Skeleton ────────────────────────────────────────────────────────────────

function AuditSkeleton() {
  return (
    <div className="divide-y divide-border">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3.5">
          <div
            className="h-4 w-16 shrink-0 animate-pulse rounded"
            style={{ background: "var(--color-brand-50)" }}
          />
          <div
            className="h-5 w-32 animate-pulse rounded-full"
            style={{ background: "var(--color-brand-50)" }}
          />
          <div className="flex flex-1 gap-1.5">
            <div
              className="h-4 w-20 animate-pulse rounded-md"
              style={{ background: "var(--color-brand-50)" }}
            />
            <div
              className="h-4 w-28 animate-pulse rounded-md"
              style={{ background: "var(--color-brand-50)" }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Row ─────────────────────────────────────────────────────────────────────

function AuditRow({ item }: { item: AuditLogItem }) {
  return (
    <tr className="group transition-colors hover:bg-muted/30">
      <td className="whitespace-nowrap px-4 py-3 align-top">
        <span
          className="text-xs font-medium tabular-nums"
          title={fullDateTime(item.created_at)}
          style={{ color: "var(--color-brand-600)" }}
        >
          {relativeTime(item.created_at)}
        </span>
        <p className="mt-0.5 text-[11px] text-muted-foreground tabular-nums">
          {fullDateTime(item.created_at)}
        </p>
      </td>
      <td className="px-4 py-3 align-top">
        <ActionBadge action={item.action} />
      </td>
      <td className="px-4 py-3 align-top">
        <DetailsView details={item.details} />
      </td>
    </tr>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function AuditPage() {
  const [search, setSearch] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => auditService.getAuditLogs(150),
    refetchInterval: 30_000,
  });

  const rows = useMemo(() => {
    const all = data?.data ?? [];
    if (!search.trim()) return all;
    const q = search.toLowerCase();
    return all.filter(
      (item) =>
        item.action.toLowerCase().includes(q) ||
        JSON.stringify(item.details).toLowerCase().includes(q),
    );
  }, [data, search]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <section className="border-b border-border pb-6">
        <p className="text-xs font-medium uppercase tracking-[0.22em] text-muted-foreground">
          Management
        </p>
        <h1 className="mt-2 font-display text-3xl font-semibold tracking-[-0.02em] text-foreground">
          Audit Log
        </h1>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          Recent admin and system activity. Auto-refreshes every 30 seconds.
        </p>
      </section>

      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative w-full max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Filter by action or detail…"
            className="h-9 pl-9 text-sm"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {!isLoading && !isError && (
          <p className="shrink-0 text-sm text-muted-foreground">
            {rows.length} {rows.length === 1 ? "entry" : "entries"}
            {search && ` of ${data?.data.length ?? 0}`}
          </p>
        )}
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
        {isLoading ? (
          <AuditSkeleton />
        ) : isError ? (
          <div className="flex flex-col items-center gap-3 py-16 text-center">
            <ShieldAlert className="h-8 w-8 text-destructive/60" />
            <p className="text-sm font-medium text-destructive">Failed to load audit logs.</p>
            <p className="text-xs text-muted-foreground">Check your connection or try refreshing.</p>
          </div>
        ) : rows.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-16 text-center">
            <ShieldAlert className="h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm font-medium text-foreground">
              {search ? "No matching entries" : "No audit logs yet"}
            </p>
            <p className="text-xs text-muted-foreground">
              {search
                ? "Try a different search term."
                : "Activity will appear here as admins use the workspace."}
            </p>
          </div>
        ) : (
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                  Time
                </th>
                <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                  Action
                </th>
                <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {rows.map((item) => (
                <AuditRow key={item.id} item={item} />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
