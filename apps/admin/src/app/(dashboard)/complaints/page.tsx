"use client";

import Link from "next/link";
import { useComplaints } from "@/features/complaints/use-complaints";
import ComplaintsLoading from "@/features/complaints/complaints-loading";
import ComplaintsError from "@/features/complaints/complaints-error";
import ComplaintsEmpty from "@/features/complaints/complaints-empty";
import StatusBadge from "@/components/shared/status-badge";
import { Card } from "@/components/ui/card";

export default function ComplaintsPage() {
  const { data, isLoading, isError, error } = useComplaints();

  if (isLoading) return <ComplaintsLoading />;
  if (isError) return <ComplaintsError message={error?.message} />;

  const complaints = data?.data?.items ?? [];
  if (!complaints.length) return <ComplaintsEmpty />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-foreground">Complaints</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Review client complaints and manage replacements.
        </p>
      </div>

      <Card className="overflow-hidden">
        <table className="min-w-full divide-y divide-border">
          <thead className="bg-muted/40">
            <tr>
              {["ID","Requirement","Assignment","Type","Severity","Status","Created","Action"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {complaints.map((item) => (
              <tr key={item.id} className="transition-colors hover:bg-muted/30">
                <td className="px-4 py-3 text-sm text-muted-foreground">{item.id}</td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{item.requirement_id}</td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{item.assignment_id ?? "-"}</td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{item.complaint_type.replaceAll("_", " ")}</td>
                <td className="px-4 py-3 text-sm"><StatusBadge value={item.severity} /></td>
                <td className="px-4 py-3 text-sm"><StatusBadge value={item.status} /></td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{item.created_at}</td>
                <td className="px-4 py-3 text-sm">
                  <Link
                    href={`/complaints/${item.id}`}
                    className="text-accent underline underline-offset-4 hover:text-accent/80 transition-colors"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

