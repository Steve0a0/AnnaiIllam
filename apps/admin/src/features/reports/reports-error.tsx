import { AlertTriangle } from "lucide-react";

export default function ReportsError({ message }: { message?: string }) {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <AlertTriangle className="h-7 w-7 text-destructive/60" />
      <p className="text-sm font-medium text-destructive">
        {message ?? "Failed to load report data."}
      </p>
      <p className="text-xs text-muted-foreground">Try refreshing the page.</p>
    </div>
  );
}
