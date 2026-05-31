import { FileText } from "lucide-react";

export default function ReportsEmpty({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <FileText className="h-8 w-8 text-muted-foreground/40" />
      <p className="text-sm font-medium text-foreground">No {label} found</p>
      <p className="text-xs text-muted-foreground">
        Try adjusting your filters or date range.
      </p>
    </div>
  );
}
